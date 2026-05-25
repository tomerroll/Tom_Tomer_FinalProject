import numpy as np
from scipy.signal import butter, filtfilt, detrend
from collections import deque

class ExtractHeartRate:
    def __init__(self, face_detected=None, min_signal_seconds=10.0, pos_window_seconds=2.5):
        self.face_detected = face_detected
        self.heart_rate = 0.0
        self.frequency = 0.0
        self.hr_buffer = deque(maxlen=5)
        
        self.min_signal_seconds = float(min_signal_seconds)
        self.pos_window_seconds = float(pos_window_seconds)
        
        # Placeholders for UI metrics
        self.confidence = 0.0
        self.signal_quality = 0.0

    def calc_hr_process(self, roi_sample_list, sampling_rate, bin_plotter):
        """Processes the accumulated window tracking lists."""
        if len(roi_sample_list) < (self.min_signal_seconds * sampling_rate):
            # Return matching 3-tuple structure so unpacking does not throw an error
            return 0.0, 0.0, f"Collecting data... ({len(roi_sample_list)} frames)"

        # Combine RGB data safely
        rgb_data = []
        for frame_rois in roi_sample_list:
            if frame_rois and isinstance(frame_rois, list) and len(frame_rois) > 0:
                if 'rgb' in frame_rois[0]:
                    rgb_data.append(frame_rois[0]['rgb'])
        
        if not rgb_data or len(rgb_data) < 10: 
            return 0.0, 0.0, "No Valid Signal Structure Data"
        
        # Plane-Orthogonal-to-Skin (POS) Core Execution
        rgb_arr = np.array(rgb_data, dtype=np.float64)
        mean_rgb = np.mean(rgb_arr, axis=0)
        norm_rgb = rgb_arr / (mean_rgb + 1e-6)
        
        s1 = norm_rgb[:, 1] - norm_rgb[:, 2]
        s2 = norm_rgb[:, 1] + norm_rgb[:, 2] - 2 * norm_rgb[:, 0]
        alpha = np.std(s1) / (np.std(s2) + 1e-6)
        bvp = detrend(s1 + alpha * s2)
        
        return self.estimate_hr_from_signal(bvp, sampling_rate, bin_plotter)

    def estimate_hr_from_signal(self, sig, fs, bin_plotter):
        # Handle tiny sequences edge cases gracefully 
        if len(sig) < 4:
            return 0.0, 0.0, "Signal too short"
            
        # Bandpass filter 0.7 - 2.5 Hz (42-150 BPM)
        nyq = 0.5 * fs
        low_cut = 0.7 / nyq
        high_cut = 2.5 / nyq
        
        # Ensure clipping filter parameters stay safely inside Nyquist boundaries
        low_cut = max(0.001, min(low_cut, 0.999))
        high_cut = max(0.002, min(high_cut, 0.999))
        
        try:
            b, a = butter(4, [low_cut, high_cut], btype='band')
            clean_sig = filtfilt(b, a, sig)
        except Exception:
            clean_sig = detrend(sig) # Fallback to avoid complete breakdown

        # Power Spectral Density extraction using FFT
        n_fft = max(2048, len(clean_sig))
        window = np.blackman(len(clean_sig))
        f_abs = np.abs(np.fft.rfft(clean_sig * window, n=n_fft))
        freqs = np.fft.rfftfreq(n_fft, d=1.0/fs)
        
        valid_idx = np.where((freqs >= 0.75) & (freqs <= 2.5))[0]
        if len(valid_idx) == 0: 
            return 0.0, 0.0, "Range Error"
        
        best_freq = freqs[valid_idx[np.argmax(f_abs[valid_idx])]]
        self.hr_buffer.append(best_freq * 60.0)
        
        self.heart_rate = np.median(self.hr_buffer)
        self.frequency = self.heart_rate / 60.0
        
        # Safely trigger real-time chart update if defined
        if bin_plotter:
            try:
                bin_plotter.update_bin_plot(f_abs[valid_idx])
            except Exception:
                pass
            
        return self.heart_rate, self.frequency, None