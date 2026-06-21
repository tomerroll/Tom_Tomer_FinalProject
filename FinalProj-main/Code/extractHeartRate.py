import numpy as np
from scipy.signal import butter, filtfilt, detrend
from collections import deque

class ExtractHeartRate:
    """
    A class dedicated to extracting physiological heart rate data from video-based 
    facial RGB signals using the POS (Plane-Orthogonal-to-Skin) algorithm.
    """
    def __init__(self, face_detected=None, min_signal_seconds=10.0, pos_window_seconds=2.5):
        """
        Initializes the heart rate extraction module.

        :param face_detected: Boolean flag indicating if a face is currently tracked.
        :param min_signal_seconds: The minimum buffer duration required before calculating HR.
        :param pos_window_seconds: The temporal window size for the POS algorithm projection.
        """
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
        """
        Processes a sequence of RGB means using the POS algorithm to extract a Blood Volume 
        Pulse (BVP) signal.

        :param roi_sample_list: A list containing dictionaries of ROI data per frame.
        :param sampling_rate: The current effective frames-per-second (FPS) of the capture.
        :param bin_plotter: Reference to the UI plotter for frequency spectrum visualization.
        :return: Tuple containing (heart_rate, frequency, error_message).
        """
        if len(roi_sample_list) < (self.min_signal_seconds * sampling_rate):
            return 0.0, 0.0, f"Collecting: {len(roi_sample_list)} frames"

        # Combine RGB data from samples
        rgb_data = []
        for frame_rois in roi_sample_list:
            if frame_rois:
                rgb_data.append(frame_rois[0]['rgb'])
        
        if not rgb_data: return 0.0, 0.0, "No Signal"
        
        # POS Algorithm logic: Projecting RGB channels onto a plane orthogonal to skin tone
        rgb_arr = np.array(rgb_data)
        mean_rgb = np.mean(rgb_arr, axis=0)
        norm_rgb = rgb_arr / (mean_rgb + 1e-6)
        
        s1 = norm_rgb[:, 1] - norm_rgb[:, 2]
        s2 = norm_rgb[:, 1] + norm_rgb[:, 2] - 2 * norm_rgb[:, 0]
        alpha = np.std(s1) / (np.std(s2) + 1e-6)
        bvp = detrend(s1 + alpha * s2)
        
        return self.estimate_hr_from_signal(bvp, sampling_rate, bin_plotter)

    def estimate_hr_from_signal(self, sig, fs, bin_plotter):
        """
        Applies bandpass filtering and Fast Fourier Transform (FFT) to the raw BVP signal 
        to isolate the dominant physiological frequency.

        :param sig: The 1D Blood Volume Pulse (BVP) signal array.
        :param fs: The sampling frequency (FPS).
        :param bin_plotter: Reference to the UI frequency plotter.
        :return: Tuple containing (heart_rate, frequency, error_message).
        """
        # Bandpass filter 0.7 - 2.5 Hz (42-150 BPM)
        nyq = 0.5 * fs
        b, a = butter(4, [0.7/nyq, 2.5/nyq], btype='band')
        clean_sig = filtfilt(b, a, sig)
        
        # FFT with Blackman window to reduce spectral leakage
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