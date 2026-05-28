import numpy as np
from scipy.signal import butter, filtfilt, detrend
from collections import deque

class ExtractHeartRate:
    def __init__(self, face_detected=None, min_signal_seconds=10.0, pos_window_seconds=2.5):
        """Explicitly including pos_window_seconds to match the UI call"""
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
        """Your UI expects this method to process the accumulated ROI samples[cite: 1, 4]"""
        if len(roi_sample_list) < (self.min_signal_seconds * sampling_rate):
            return 0.0, 0.0, f"Collecting: {len(roi_sample_list)} frames"

        # Combine RGB data from samples
        rgb_data = []
        for frame_rois in roi_sample_list:
            if frame_rois:
                rgb_data.append(frame_rois[0]['rgb'])
        
        if not rgb_data: return 0.0, 0.0, "No Signal"
        
        # POS Algorithm logic[cite: 4]
        rgb_arr = np.array(rgb_data)
        mean_rgb = np.mean(rgb_arr, axis=0)
        norm_rgb = rgb_arr / (mean_rgb + 1e-6)
        
        s1 = norm_rgb[:, 1] - norm_rgb[:, 2]
        s2 = norm_rgb[:, 1] + norm_rgb[:, 2] - 2 * norm_rgb[:, 0]
        alpha = np.std(s1) / (np.std(s2) + 1e-6)
        bvp = detrend(s1 + alpha * s2)
        
        return self.estimate_hr_from_signal(bvp, sampling_rate, bin_plotter)

    def estimate_hr_from_signal(self, sig, fs, bin_plotter):
        # Bandpass filter 0.7 - 2.5 Hz (42-150 BPM)
        nyq = 0.5 * fs
        b, a = butter(4, [0.7/nyq, 2.5/nyq], btype='band')
        clean_sig = filtfilt(b, a, sig)
        
        # FFT
        n_fft = 2048
        f_abs = np.abs(np.fft.rfft(clean_sig * np.blackman(len(clean_sig)), n=n_fft))
        freqs = np.fft.rfftfreq(n_fft, d=1.0/fs)
        
        valid_idx = np.where((freqs >= 0.75) & (freqs <= 2.5))[0]
        if len(valid_idx) == 0: return 0.0, 0.0, "Range Error"
        
        best_freq = freqs[valid_idx[np.argmax(f_abs[valid_idx])]]
        self.hr_buffer.append(best_freq * 60.0)
        
        self.heart_rate = np.median(self.hr_buffer)
        self.frequency = self.heart_rate / 60.0
        
        # Update the UI chart if provided
        if bin_plotter:
            bin_plotter.update_bin_plot(f_abs[valid_idx])
            
        return self.heart_rate, self.frequency, None