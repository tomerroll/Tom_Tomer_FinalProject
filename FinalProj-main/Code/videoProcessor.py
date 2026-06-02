import cv2
import numpy as np
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt

try:
    import mediapipe as mp
    from mediapipe.python.solutions import face_mesh as mp_face_mesh
    MEDIAPIPE_AVAILABLE = True
except (ImportError, AttributeError):
    MEDIAPIPE_AVAILABLE = False
    print("[VIDEO] MediaPipe not fully compatible with this Python version. Falling back to Haar Cascades.")


class VideoProcessor:
    def __init__(self, capture, video_window, is_webcam=False):
        self.capture = capture
        self.video_window = video_window
        self.is_webcam = is_webcam
        self.frame_counter = 0

        if MEDIAPIPE_AVAILABLE:
            self.face_mesh = mp_face_mesh.FaceMesh(
                static_image_mode=False,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5
            )
        else:
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )

    def _extract_face_rois_mp(self, frame, landmarks):
        h, w, _ = frame.shape

        center = landmarks[10]
        cx, cy = int(center.x * w), int(center.y * h)

        face_width = abs((landmarks[338].x - landmarks[109].x) * w)
        roi_size = int(face_width * 0.30)
        roi_size = max(25, min(roi_size, min(w, h) // 3))

        # Forehead ROI: slightly above landmark 10, without writing text over the box.
        sx = int(cx - roi_size // 2)
        sy = int(cy - roi_size * 0.75)

        sx = max(0, min(sx, w - 1))
        sy = max(0, min(sy, h - 1))
        ex = max(sx + 1, min(w, sx + roi_size))
        ey = max(sy + 1, min(h, sy + roi_size))

        roi_img = frame[sy:ey, sx:ex]
        box_w = ex - sx
        box_h = ey - sy

        return [("forehead", roi_img, (sx, sy, box_w, box_h))]


    def _extract_face_rois_haar(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)

        if len(faces) == 0:
            return None

        x, y, w, h = faces[0]

        fx = x + int(w * 0.3)
        fy = y + int(h * 0.1)
        fw = int(w * 0.4)
        fh = int(h * 0.15)

        roi_img = frame[fy:fy + fh, fx:fx + fw]

        return [("forehead", roi_img, (fx, fy, fw, fh))]

    def update_video_feed(self):
        ret, frame = self.capture.read()

        if not ret or frame is None:
            return None, None, False

        self.frame_counter += 1

        display_frame = frame.copy()
        roi_results = None
        face_found = False

        if MEDIAPIPE_AVAILABLE:
            rgb_input = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(rgb_input)

            if results.multi_face_landmarks:
                face_found = True
                rois = self._extract_face_rois_mp(
                    frame,
                    results.multi_face_landmarks[0].landmark
                )

                roi_results = []

                for name, img, box in rois:
                    x, y, w, h = box

                    roi_data = self._extract_single_roi_rgb(name, img)
                    roi_results.append(roi_data)

                    cv2.rectangle(
                        display_frame,
                        (x, y),
                        (x + w, y + h),
                        (0, 255, 0),
                        2
                    )


        else:
            rois = self._extract_face_rois_haar(frame)

            if rois:
                face_found = True
                roi_results = []

                for name, img, box in rois:
                    x, y, w, h = box

                    roi_data = self._extract_single_roi_rgb(name, img)
                    roi_results.append(roi_data)

                    cv2.rectangle(
                        display_frame,
                        (x, y),
                        (x + w, y + h),
                        (0, 255, 0),
                        2
                    )


        rgb_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        rgb_frame = np.ascontiguousarray(rgb_frame)
        h, w, ch = rgb_frame.shape

        qimg = QImage(
            rgb_frame.data,
            w,
            h,
            ch * w,
            QImage.Format_RGB888
        ).copy()

        self.video_window.setPixmap(
            QPixmap.fromImage(qimg).scaled(
                self.video_window.width(),
                self.video_window.height(),
                Qt.KeepAspectRatio
            )
        )

        return roi_results, display_frame, face_found

    def _extract_single_roi_rgb(self, name, roi):
        if roi is None or roi.size == 0:
            print(f"[VIDEO] {name}: no valid ROI pixels")

            return {
                "name": name,
                "rgb": None,
                "quality": 0.0,
                "pixels": 0,
                "sampling_score": 0.0
            }

        roi_height = roi.shape[0]
        roi_width = roi.shape[1]
        num_pixels = roi_height * roi_width

        sampling_score = min(100.0, (num_pixels / 5000.0) * 100.0)

        avg_rgb = np.mean(roi, axis=(0, 1))

        print(
            f"[VIDEO] {name}: "
            f"pixels={num_pixels}, "
            f"sampling_score={sampling_score:.1f}/100, "
            f"roi_size={roi_width}x{roi_height}, "
            f"rgb=({avg_rgb[2]:.1f}, {avg_rgb[1]:.1f}, {avg_rgb[0]:.1f})"
        )

        return {
            "name": name,
            "rgb": (avg_rgb[2], avg_rgb[1], avg_rgb[0]),
            "quality": 100.0,
            "pixels": num_pixels,
            "sampling_score": sampling_score
        }