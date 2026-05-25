import cv2
import numpy as np
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt

# Try to import mediapipe with a workaround for Python 3.13
try:
    import mediapipe as mp
    from mediapipe.python.solutions import face_mesh as mp_face_mesh
    from mediapipe.python.solutions import drawing_utils as mp_drawing
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
            # Fallback to Haar Cascade logic
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    def _extract_face_rois_mp(self, frame, landmarks):
        """Extracts ROI using MediaPipe Landmarks (Landmark 10 for forehead)"""
        h, w, _ = frame.shape
        center = landmarks[10]
        cx, cy = int(center.x * w), int(center.y * h)
        
        # Estimate size based on temple distance (landmarks 109 and 338)
        fw = (landmarks[338].x - landmarks[109].x) * w
        roi_size = int(fw * 0.25)
        
        if roi_size <= 0:
            return None

        sx, sy = max(0, cx - roi_size//2), max(0, cy - roi_size//2)
        ex, ey = min(w, sx + roi_size), min(h, sy + roi_size)
        
        roi_img = frame[sy:ey, sx:ex]
        return [("forehead", roi_img, (sx, sy, ex - sx, ey - sy))]

    def _extract_face_rois_haar(self, frame):
        """Original Haar Cascade fallback"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        if len(faces) == 0: 
            return None
        
        x, y, w, h = faces[0]
        # Forehead estimate
        fx, fy, fw, fh = x + int(w*0.3), y + int(h*0.1), int(w*0.4), int(h*0.15)
        
        h_img, w_img, _ = frame.shape
        ex, ey = min(w_img, fx + fw), min(h_img, fy + fh)
        
        roi_img = frame[fy:ey, fx:ex]
        return [("forehead", roi_img, (fx, fy, ex - fx, ey - fy))]

    def update_video_feed(self):
        ret, frame = self.capture.read()
        if not ret or frame is None: 
            return None, None, False

        self.frame_counter += 1
        display_frame = frame.copy()
        roi_results = None
        face_found = False

        if MEDIAPIPE_AVAILABLE:
            results = self.face_mesh.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            if results.multi_face_landmarks:
                rois = self._extract_face_rois_mp(frame, results.multi_face_landmarks[0].landmark)
                if rois:
                    face_found = True
                    for name, img, box in rois:
                        cv2.rectangle(display_frame, (box[0], box[1]), (box[0]+box[2], box[1]+box[3]), (0, 255, 0), 2)
                        single_roi_data = self._extract_single_roi_rgb(name, img)
                        if single_roi_data["rgb"] is not None:
                            roi_results = [single_roi_data]
        else:
            rois = self._extract_face_rois_haar(frame)
            if rois:
                face_found = True
                for name, img, box in rois:
                    cv2.rectangle(display_frame, (box[0], box[1]), (box[0]+box[2], box[1]+box[3]), (0, 255, 0), 2)
                    single_roi_data = self._extract_single_roi_rgb(name, img)
                    if single_roi_data["rgb"] is not None:
                        roi_results = [single_roi_data]

        # Rendering logic to update PyQt interface window layout
        rgb_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        qimg = QImage(rgb_frame.data, w, h, ch * w, QImage.Format_RGB888)
        
        # Check window dimension boundaries before layout calculation to prevent stretch exceptions
        win_w = max(self.video_window.width(), 100)
        win_h = max(self.video_window.height(), 100)
        
        self.video_window.setPixmap(QPixmap.fromImage(qimg).scaled(
            win_w, win_h, Qt.KeepAspectRatio))

        return roi_results, display_frame, face_found

    def _extract_single_roi_rgb(self, name, roi):
        if roi is None or roi.size == 0 or roi.shape[0] == 0 or roi.shape[1] == 0: 
            return {"name": name, "rgb": None, "quality": 0.0}
        
        avg_bgr = np.mean(roi, axis=(0, 1))
        # Safely convert to float list to ensure downstream numpy arrays build correctly
        return {
            "name": name, 
            "rgb": [float(avg_bgr[2]), float(avg_bgr[1]), float(avg_bgr[0])], 
            "quality": 100.0
        }