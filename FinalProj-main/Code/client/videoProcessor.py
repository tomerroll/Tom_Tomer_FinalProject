import cv2
import numpy as np
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt


class VideoProcessor:
    def __init__(self, capture, video_window, is_webcam=False):
        self.capture = capture
        self.video_window = video_window
        self.is_webcam = is_webcam

        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )

        self.smoothed_face = None
        self.last_valid_box = None
        self.missed_faces = 0
        self.frame_counter = 0

    def _prepare_frame_for_detection(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mean_brightness = float(np.mean(gray))

        if mean_brightness > 190:
            frame = cv2.convertScaleAbs(frame, alpha=0.85, beta=-15)

        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    def _extract_face_rois(self, frame, sx, sy, sw, sh):
        frame_h, frame_w = frame.shape[:2]
        rois = []

        fh_x = max(0, sx + int(sw * 0.32))
        fh_y = max(0, sy + int(sh * 0.10))
        fh_w = min(frame_w - fh_x, int(sw * 0.36))
        fh_h = min(frame_h - fh_y, int(sh * 0.13))

        if fh_w > 0 and fh_h > 0:
            roi = frame[fh_y:fh_y + fh_h, fh_x:fh_x + fh_w]
            rois.append(("forehead", roi, (fh_x, fh_y, fh_w, fh_h)))

        return rois

    def _preprocess_roi_for_rgb(self, roi):
        if roi is None or roi.size == 0:
            return roi

        return cv2.GaussianBlur(roi, (3, 3), 0)

    def _extract_single_roi_rgb(self, roi_name, roi):
        if roi is None or roi.size == 0:
            return {
                "name": roi_name,
                "rgb": None,
                "quality": 0.0,
                "valid_pixels": 0
            }

        roi_area = roi.shape[0] * roi.shape[1]

        ycrcb_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2YCrCb)

        lower_skin = np.array([40, 120, 70], dtype=np.uint8)
        upper_skin = np.array([255, 190, 150], dtype=np.uint8)

        skin_mask = cv2.inRange(ycrcb_roi, lower_skin, upper_skin)

        kernel = np.ones((3, 3), np.uint8)
        skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_OPEN, kernel)
        skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_CLOSE, kernel)

        pixels = roi[skin_mask == 255]

        if pixels.size == 0:
            return {
                "name": roi_name,
                "rgb": None,
                "quality": 0.0,
                "valid_pixels": 0
            }

        pixels = pixels.astype(np.float32)

        if pixels.shape[0] < 100:
            return {
                "name": roi_name,
                "rgb": None,
                "quality": 0.0,
                "valid_pixels": int(pixels.shape[0])
            }

        lower = np.percentile(pixels, 15, axis=0)
        upper = np.percentile(pixels, 85, axis=0)

        keep_mask = np.all((pixels >= lower) & (pixels <= upper), axis=1)
        filtered_pixels = pixels[keep_mask]

        if filtered_pixels.shape[0] < 60:
            return {
                "name": roi_name,
                "rgb": None,
                "quality": 0.0,
                "valid_pixels": int(filtered_pixels.shape[0])
            }

        b_mean = float(np.median(filtered_pixels[:, 0]))
        g_mean = float(np.median(filtered_pixels[:, 1]))
        r_mean = float(np.median(filtered_pixels[:, 2]))

        green_std = float(np.std(filtered_pixels[:, 1]))

        skin_ratio = float(pixels.shape[0]) / float(roi_area)
        saturation_ratio = float(np.mean(np.any(roi > 245, axis=2)))
        dark_ratio = float(np.mean(np.any(roi < 10, axis=2)))

        quality = (
            skin_ratio * 1000.0
            - green_std * 2.0
            - saturation_ratio * 500.0
            - dark_ratio * 300.0
        )

        quality = max(0.0, quality)

        return {
            "name": roi_name,
            "rgb": (r_mean, g_mean, b_mean),
            "quality": quality,
            "valid_pixels": int(filtered_pixels.shape[0])
        }

    def _extract_multi_roi_data(self, rois):
        roi_results = []

        for roi_name, roi, _box in rois:
            clean_roi = self._preprocess_roi_for_rgb(roi)
            roi_results.append(self._extract_single_roi_rgb(roi_name, clean_roi))

        return roi_results

    def _draw_rois(self, frame, rois):
        for roi_name, _roi, (x, y, w, h) in rois:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    def update_video_feed(self):
        ret, raw_frame = self.capture.read()
        self.frame_counter += 1

        if not ret or raw_frame is None:
            print(f"[VIDEO] Failed reading frame #{self.frame_counter}")
            return None, None, False

        face_found = False
        roi_results = None

        frame_gray = self._prepare_frame_for_detection(raw_frame.copy())

        faces = self.face_cascade.detectMultiScale(
            frame_gray,
            scaleFactor=1.2,
            minNeighbors=6,
            minSize=(90, 90)
        )

        if len(faces) > 0:
            face_found = True
            self.missed_faces = 0

            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])

            if self.smoothed_face is None:
                self.smoothed_face = [x, y, w, h]
            else:
                alpha = 0.20
                self.smoothed_face[0] = (1 - alpha) * self.smoothed_face[0] + alpha * x
                self.smoothed_face[1] = (1 - alpha) * self.smoothed_face[1] + alpha * y
                self.smoothed_face[2] = (1 - alpha) * self.smoothed_face[2] + alpha * w
                self.smoothed_face[3] = (1 - alpha) * self.smoothed_face[3] + alpha * h

            sx, sy, sw, sh = [int(v) for v in self.smoothed_face]
            self.last_valid_box = (sx, sy, sw, sh)

        else:
            self.missed_faces += 1

            if self.missed_faces > 8:
                self.smoothed_face = None
                self.last_valid_box = None

        display_frame = raw_frame.copy()

        if self.last_valid_box is not None:
            sx, sy, sw, sh = self.last_valid_box

            cv2.rectangle(display_frame, (sx, sy), (sx + sw, sy + sh), (255, 180, 0), 2)

            rois = self._extract_face_rois(raw_frame, sx, sy, sw, sh)
            self._draw_rois(display_frame, rois)

            roi_results = self._extract_multi_roi_data(rois)

            if self.frame_counter % 30 == 0 and roi_results is not None:
                short_log = []

                for item in roi_results:
                    short_log.append(
                        f"{item['name']}:rgb={item['rgb']},"
                        f"q={item['quality']:.1f},"
                        f"n={item['valid_pixels']}"
                    )

                print("[VIDEO] " + " | ".join(short_log))

        frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        h_img, w_img, ch = frame_rgb.shape
        bytes_per_line = ch * w_img

        image = QImage(
            frame_rgb.data,
            w_img,
            h_img,
            bytes_per_line,
            QImage.Format_RGB888
        )

        pixmap = QPixmap.fromImage(image).scaled(
            self.video_window.width(),
            self.video_window.height(),
            Qt.KeepAspectRatio
        )

        self.video_window.setPixmap(pixmap)

        return roi_results, display_frame, face_found