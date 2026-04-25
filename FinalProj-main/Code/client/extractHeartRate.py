import numpy as np
from scipy.signal import butter, filtfilt, detrend
from collections import deque

# =======================================================
# --- PRIMARY TUNING PARAMETERS (HIGH IMPACT) ---
# =======================================================
# משתנים אלו קובעים את התנהגות הליבה של האלגוריתם, ספי הקבלה וטווחי הזמן.
# אלו המשתנים הראשונים שכדאי לשנות כדי לשפר תוצאות.

# General HR Limits & Stability
MIN_HR_BPM = 48                    # דופק מינימלי אפשרי
MAX_HR_BPM = 132                   # דופק מקסימלי אפשרי
MAX_JUMP_BPM = 8.0                 # קפיצת דופק מקסימלית המותרת בין קריאות
HR_BUFFER_LEN = 5                  # גודל החוצץ (Buffer) להחלקת דופק יציב (Median)

# Accept/Reject Thresholds
CONFIDENCE_THRESHOLD = 1.30        # סף הביטחון המינימלי לקבלת קריאה מה-FFT
SIGNAL_QUALITY_THRESHOLD = 60.0    # ציון איכות האות המינימלי (מתוך 100) לקבלת הקריאה

# Signal & Windowing Timeframes
DEFAULT_MIN_SIGNAL_SECONDS = 10.0  # כמה שניות של אות צריך לפחות כדי להתחיל חישוב
DEFAULT_POS_WINDOW_SECONDS = 2.5   # חלון הזמן (בשניות) עבור אלגוריתם ה-POS
FFT_SECONDS = 20.0                 # אורך חלון האות הנלקח לטובת חישוב התדר (FFT)


# =======================================================
# --- SECONDARY & ADVANCED TUNING (LOWER IMPACT) ---
# =======================================================
# משקולות, פילטרים והגדרות מתמטיות של ההיוריסטיקה. 
# מומלץ לשנות רק לאופטימיזציה עדינה (Fine-tuning).

# Best Candidate Scoring Parameters (Heuristics)
RESTING_HR_MIN = 55
RESTING_HR_MAX = 90
RESTING_HR_BONUS = 0.18
HIGH_HR_PENALTY_THRESHOLD = 95
HIGH_HR_PENALTY = 0.25
LOW_FREQ_PREFERENCE_WEIGHT = 0.0025
CONTINUITY_PREFERENCE_WEIGHT = 0.045

# HR Temporal Smoothing (Alpha values for EMA)
ALPHA_SMOOTH_CONF_THRESHOLD = 2.0
ALPHA_SMOOTH_HIGH_CONF = 0.25
ALPHA_SMOOTH_LOW_CONF = 0.18

# Signal Quality Calculation Weights
QUAL_CONFIDENCE_DIVISOR = 2.5
QUAL_CONFIDENCE_WEIGHT = 45.0
QUAL_DOMINANCE_DIVISOR = 1.10
QUAL_DOMINANCE_WEIGHT = 20.0
QUAL_FRAMES_WEIGHT = 20.0
QUAL_ROI_DIVISOR = 700.0
QUAL_ROI_WEIGHT = 15.0
QUAL_MAX_SCORE = 100.0

# Harmonic Logic Tuning
HARMONIC_RATIO_1 = 1.5
HARMONIC_TOLERANCE_1 = 0.12
HARMONIC_RATIO_2 = 2.0
HARMONIC_TOLERANCE_2 = 0.15
HARMONIC_CONFIDENCE_RATIO = 0.55

# Technical Bounds & Filtering
MIN_WINDOW_LEN = 32
MAX_WINDOW_LEN = 96
MIN_FRAMES_PADDING = 20
FILTER_ORDER = 4
NYQ_MARGIN_LOW = 0.001
NYQ_MARGIN_HIGH = 0.999

# ROI & Pixel Quality
MIN_VALID_PIXELS = 60
SMOOTHING_KERNEL_SIZE = 5

# FFT & Peak Detection
MIN_FFT_SIZE = 2048
LOG2_MIN_SIG_LEN = 256
SPEC_SMOOTHING_KERNEL_SIZE = 5
TOP_K_PEAKS = 6
NOISE_FLOOR_EPSILON = 1e-8

# =======================================================


class ExtractHeartRate:
    def __init__(self, face_detected=None, min_signal_seconds=DEFAULT_MIN_SIGNAL_SECONDS, pos_window_seconds=DEFAULT_POS_WINDOW_SECONDS):
        self.face_detected = face_detected

        self.heart_rate = 0.0
        self.frequency = 0.0
        self.hr_buffer = deque(maxlen=HR_BUFFER_LEN)

        self.confidence = 0.0
        self.dominance = 0.0
        self.signal_quality = 0.0

        self.min_signal_seconds = float(min_signal_seconds)
        self.pos_window_seconds = float(pos_window_seconds)

    def butter_bandpass_filter(self, data, lowcut, highcut, fs, order=FILTER_ORDER):
        nyq = 0.5 * fs
        low = max(lowcut / nyq, NYQ_MARGIN_LOW)
        high = min(highcut / nyq, NYQ_MARGIN_HIGH)

        if low >= high:
            raise ValueError("Invalid bandpass range")

        b, a = butter(order, [low, high], btype="band")
        return filtfilt(b, a, data)

    def _get_window_len(self, sampling_rate):
        window_len = int(round(self.pos_window_seconds * sampling_rate))
        return max(MIN_WINDOW_LEN, min(window_len, MAX_WINDOW_LEN))

    def _min_required_frames(self, sampling_rate):
        window_len = self._get_window_len(sampling_rate)
        min_frames = int(round(self.min_signal_seconds * sampling_rate))
        return max(min_frames, window_len + MIN_FRAMES_PADDING)

    def _sanitize_roi_samples(self, roi_sample_list):
        cleaned = []

        for frame_item in roi_sample_list:
            if frame_item is None or not isinstance(frame_item, list):
                continue

            valid_rois = []

            for roi in frame_item:
                if not isinstance(roi, dict):
                    continue

                rgb = roi.get("rgb")
                quality = float(roi.get("quality", 0.0))
                valid_pixels = int(roi.get("valid_pixels", 0))

                if rgb is None or quality <= 0.0 or valid_pixels < MIN_VALID_PIXELS:
                    continue

                arr = np.asarray(rgb, dtype=np.float64).flatten()

                if arr.size != 3:
                    continue

                if np.any(np.isnan(arr)) or np.any(np.isinf(arr)):
                    continue

                valid_rois.append({
                    "name": roi.get("name", "unknown"),
                    "rgb": arr.tolist(),
                    "quality": quality,
                    "valid_pixels": valid_pixels
                })

            if valid_rois:
                cleaned.append(valid_rois)

        return cleaned

    def _combine_rois_per_frame(self, cleaned_roi_frames):
        combined_rgb = []
        qualities = []

        for frame_rois in cleaned_roi_frames:
            best_roi = max(frame_rois, key=lambda x: (x["quality"], x["valid_pixels"]))
            combined_rgb.append(best_roi["rgb"])
            qualities.append(best_roi["quality"])

        rgb_data = np.asarray(combined_rgb, dtype=np.float64)
        avg_roi_quality = float(np.mean(qualities)) if qualities else 0.0

        return rgb_data, avg_roi_quality

    def _smooth_rgb_temporally(self, rgb_data):
        rgb_data = np.asarray(rgb_data, dtype=np.float64)

        if len(rgb_data) >= SMOOTHING_KERNEL_SIZE:
            kernel = np.ones(SMOOTHING_KERNEL_SIZE, dtype=np.float64) / float(SMOOTHING_KERNEL_SIZE)

            for c in range(3):
                rgb_data[:, c] = np.convolve(rgb_data[:, c], kernel, mode="same")

        return rgb_data

    def extract_pulse_signal_pos(self, rgb_data, sampling_rate):
        N = len(rgb_data)
        window_len = self._get_window_len(sampling_rate)

        if N < window_len:
            return None

        pulse_signal = np.zeros(N, dtype=np.float64)
        counts = np.zeros(N, dtype=np.float64)

        shape = (N - window_len + 1, window_len, 3)
        strides = (
            rgb_data.strides[0],
            rgb_data.strides[0],
            rgb_data.strides[1]
        )

        windows = np.lib.stride_tricks.as_strided(
            rgb_data,
            shape=shape,
            strides=strides
        )

        mean_rgb = np.mean(windows, axis=1, keepdims=True)
        mean_rgb[mean_rgb == 0] = 1.0

        c_n = windows / mean_rgb

        x_s = c_n[:, :, 1] - c_n[:, :, 2]
        y_s = -2.0 * c_n[:, :, 0] + c_n[:, :, 1] + c_n[:, :, 2]

        std_x = np.std(x_s, axis=1, keepdims=True)
        std_y = np.std(y_s, axis=1, keepdims=True)

        alpha = np.divide(
            std_x,
            std_y,
            out=np.zeros_like(std_x),
            where=std_y != 0
        )

        h = x_s + alpha * y_s

        for i in range(h.shape[0]):
            segment = h[i] - np.mean(h[i])
            pulse_signal[i:i + window_len] += segment
            counts[i:i + window_len] += 1

        sig = np.divide(
            pulse_signal,
            counts,
            out=np.zeros_like(pulse_signal),
            where=counts != 0
        )

        sig = -sig
        sig = detrend(sig)
        sig = sig - np.mean(sig)

        return sig

    def _apply_harmonic_logic(self, candidates):
        if not candidates:
            return candidates

        corrected = []

        for hr, conf, val in candidates:
            selected_hr = hr
            selected_conf = conf
            selected_val = val

            for low_hr, low_conf, low_val in candidates:
                if low_hr >= hr:
                    continue

                ratio = hr / low_hr

                is_harmonic = (
                    abs(ratio - HARMONIC_RATIO_1) <= HARMONIC_TOLERANCE_1 or
                    abs(ratio - HARMONIC_RATIO_2) <= HARMONIC_TOLERANCE_2
                )

                if is_harmonic and low_conf >= conf * HARMONIC_CONFIDENCE_RATIO:
                    selected_hr = low_hr
                    selected_conf = low_conf
                    selected_val = low_val
                    break

            corrected.append((selected_hr, selected_conf, selected_val))

        unique = {}

        for hr, conf, val in corrected:
            key = round(hr, 1)

            if key not in unique or conf > unique[key][1]:
                unique[key] = (hr, conf, val)

        return list(unique.values())

    def _pick_best_candidate(self, candidates):
        if not candidates:
            return 0.0, 0.0

        candidates = self._apply_harmonic_logic(candidates)

        best_score = -1e9
        chosen_hr = candidates[0][0]
        chosen_conf = candidates[0][1]

        for hr, conf, _ in candidates:
            score = conf

            if RESTING_HR_MIN <= hr <= RESTING_HR_MAX:
                score += RESTING_HR_BONUS

            if hr >= HIGH_HR_PENALTY_THRESHOLD:
                score -= HIGH_HR_PENALTY

            score -= LOW_FREQ_PREFERENCE_WEIGHT * hr

            if self.heart_rate != 0:
                diff = abs(hr - self.heart_rate)
                score -= CONTINUITY_PREFERENCE_WEIGHT * diff

            if score > best_score:
                best_score = score
                chosen_hr = hr
                chosen_conf = conf

        return chosen_hr, chosen_conf

    def _calc_signal_quality(self, chosen_conf, dominance, valid_frames, min_required, avg_roi_quality):
        confidence_score = min(chosen_conf / QUAL_CONFIDENCE_DIVISOR, 1.0) * QUAL_CONFIDENCE_WEIGHT
        dominance_score = min(dominance / QUAL_DOMINANCE_DIVISOR, 1.0) * QUAL_DOMINANCE_WEIGHT
        frames_score = min(valid_frames / float(min_required), 1.0) * QUAL_FRAMES_WEIGHT
        roi_score = min(avg_roi_quality / QUAL_ROI_DIVISOR, 1.0) * QUAL_ROI_WEIGHT

        quality = confidence_score + dominance_score + frames_score + roi_score
        return float(min(QUAL_MAX_SCORE, max(0.0, quality)))

    def estimate_hr_from_signal(
        self,
        sig,
        sampling_rate,
        bin_plotter,
        valid_frames,
        min_required,
        avg_roi_quality
    ):
        try:
            sig = self.butter_bandpass_filter(
                sig,
                MIN_HR_BPM / 60.0,
                MAX_HR_BPM / 60.0,
                sampling_rate
            )
        except Exception as e:
            print(f"[HR-POS] Filtering error: {e}")
            return self.heart_rate, self.frequency, "Filtering error"

        max_samples = int(FFT_SECONDS * sampling_rate)

        if len(sig) > max_samples:
            sig = sig[-max_samples:]

        n_fft = max(MIN_FFT_SIZE, int(2 ** np.ceil(np.log2(max(len(sig), LOG2_MIN_SIG_LEN)))))

        windowed_sig = sig * np.blackman(len(sig))

        f_abs = np.abs(np.fft.rfft(windowed_sig, n=n_fft))
        freqs = np.fft.rfftfreq(n_fft, d=1.0 / sampling_rate)

        valid_idx = np.where(
            (freqs >= MIN_HR_BPM / 60.0) &
            (freqs <= MAX_HR_BPM / 60.0)
        )[0]

        if len(valid_idx) == 0:
            print("[HR-POS] No valid FFT bins.")
            return self.heart_rate, self.frequency, "No valid FFT bins"

        spec = f_abs[valid_idx]
        spec_freqs = freqs[valid_idx]

        if len(spec) >= SPEC_SMOOTHING_KERNEL_SIZE:
            spec = np.convolve(spec, np.ones(SPEC_SMOOTHING_KERNEL_SIZE) / float(SPEC_SMOOTHING_KERNEL_SIZE), mode="same")

        bin_plotter.update_bin_plot(spec)

        top_k = min(TOP_K_PEAKS, len(spec))
        top_positions = np.argsort(spec)[-top_k:]
        top_positions = top_positions[np.argsort(spec[top_positions])[::-1]]

        top_freqs = spec_freqs[top_positions]
        top_vals = spec[top_positions]

        noise_floor = np.median(spec) + NOISE_FLOOR_EPSILON

        candidates = []

        for freq, val in zip(top_freqs, top_vals):
            hr = float(freq * 60.0)
            conf = float(val / noise_floor)
            candidates.append((hr, conf, float(val)))

        dominance = 999.0

        if len(top_vals) >= 2:
            dominance = float(top_vals[0] / (top_vals[1] + NOISE_FLOOR_EPSILON))

        chosen_hr, chosen_conf = self._pick_best_candidate(candidates)

        self.confidence = chosen_conf
        self.dominance = dominance
        self.signal_quality = self._calc_signal_quality(
            chosen_conf,
            dominance,
            valid_frames,
            min_required,
            avg_roi_quality
        )

        print(f"[HR-POS] Top peaks: {[(round(c[0], 2), round(c[1], 3)) for c in candidates]}")
        print(f"[HR-POS] Peak dominance: {dominance:.3f}")
        print(f"[HR-POS] Chosen raw HR: {chosen_hr:.2f} BPM")
        print(f"[HR-POS] Confidence: {chosen_conf:.3f}")
        print(f"[HR-POS] Signal quality: {self.signal_quality:.1f}/100")

        if chosen_conf < CONFIDENCE_THRESHOLD or self.signal_quality < SIGNAL_QUALITY_THRESHOLD:
            print("[HR-POS] Rejected due to low confidence/quality.")

            if self.heart_rate != 0:
                return self.heart_rate, self.frequency, "Low confidence/quality"

            return 0.0, 0.0, "Low confidence/quality"

        raw_hr = chosen_hr

        if self.heart_rate != 0:
            diff = raw_hr - self.heart_rate

            if abs(diff) > MAX_JUMP_BPM:
                print(f"[HR-POS] Jump limited from {raw_hr:.2f} around previous {self.heart_rate:.2f}")
                raw_hr = self.heart_rate + np.sign(diff) * MAX_JUMP_BPM

        self.hr_buffer.append(raw_hr)

        stable_hr = float(np.median(self.hr_buffer))

        print(f"[HR-POS] HR buffer: {[round(float(x), 2) for x in self.hr_buffer]}")
        print(f"[HR-POS] Stable HR: {stable_hr:.2f}")

        if self.heart_rate == 0:
            self.heart_rate = stable_hr
        else:
            alpha_smooth = ALPHA_SMOOTH_HIGH_CONF if chosen_conf > ALPHA_SMOOTH_CONF_THRESHOLD else ALPHA_SMOOTH_LOW_CONF

            self.heart_rate = (
                alpha_smooth * stable_hr +
                (1.0 - alpha_smooth) * self.heart_rate
            )

        self.frequency = self.heart_rate / 60.0

        print(f"[HR-POS] Smoothed HR: {self.heart_rate:.2f} BPM")
        print(f"[HR-POS] Frequency: {self.frequency:.3f} Hz")

        return self.heart_rate, self.frequency, None

    def calc_hr_process(self, roi_sample_list, sampling_rate, bin_plotter):
        if self.face_detected is None:
            print("[HR-POS] No stable face detected yet.")
            return 0.0, 0.0, "Calibrating / Waiting for stable face..."

        sampling_rate = max(float(sampling_rate), 1.0)

        cleaned = self._sanitize_roi_samples(roi_sample_list)
        valid_frames = len(cleaned)

        print(f"[HR-POS] Valid ROI frames: {valid_frames}")

        min_required = self._min_required_frames(sampling_rate)

        if valid_frames < min_required:
            print(f"[HR-POS] Not enough valid ROI samples yet. Need about {min_required} frames.")
            return 0.0, 0.0, f"Collecting signal... need about {self.min_signal_seconds:.0f}s"

        rgb_data, avg_roi_quality = self._combine_rois_per_frame(cleaned)
        rgb_data = self._smooth_rgb_temporally(rgb_data)

        if rgb_data.size == 0:
            return 0.0, 0.0, "No valid RGB data"

        print(f"[HR-POS] Combined RGB shape: {rgb_data.shape}")
        print(f"[HR-POS] Avg ROI quality: {avg_roi_quality:.1f}")

        sig = self.extract_pulse_signal_pos(rgb_data, sampling_rate)

        if sig is None:
            print("[HR-POS] Failed to build pulse signal.")
            return 0.0, 0.0, "Not enough samples yet..."

        print(f"[HR-POS] Signal length: {len(sig)}")
        print(f"[HR-POS] Signal std: {np.std(sig):.6f}")

        return self.estimate_hr_from_signal(
            sig,
            sampling_rate,
            bin_plotter,
            valid_frames,
            min_required,
            avg_roi_quality
        )