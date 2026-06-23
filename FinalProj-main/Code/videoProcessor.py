import cv2
import numpy as np
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt


class VideoProcessor:
    """
    Handles frame-by-frame extraction of facial Regions of Interest (ROI) using 
    OpenCV Haar Cascades for real-time face detection and bounding box estimation.
    """
    def __init__(self, capture, video_window, is_webcam=False):
        """
        Initializes the VideoProcessor and configures the Haar Cascade face detector backbone.

        :param capture: The cv2.VideoCapture object.
        :param video_window: The PyQt QLabel where the output frames will be rendered.
        :param is_webcam: Boolean indicating if the source is live.
        """
        self.capture = capture
        self.video_window = video_window
        self.is_webcam = is_webcam
        self.frame_counter = 0

        # Initialize OpenCV Haar Cascade Classifier for face detection
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )

    def _extract_face_rois_haar(self, frame):
        """
        Utilizes Haar Cascades to detect the primary face boundary and dynamically 
        estimates the forehead location using deterministic pixel offsets.

        :param frame: The full BGR video frame.
        :return: A list of tuples containing (ROI name, cropped image array, bounding box) 
                 or None if no face is detected.
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)

        if len(faces) == 0:
            return None

        # Process the primary detected face
        x, y, w, h = faces[0]

        # Calculate localized offsets specific to the forehead region
        fx = x + int(w * 0.3)
        fy = y + int(h * 0.1)
        fw = int(w * 0.4)
        fh = int(h * 0.15)

        roi_img = frame[fy:fy + fh, fx:fx + fw]

        return [("forehead", roi_img, (fx, fy, fw, fh))]

    def update_video_feed(self):
        """
        Executes a single frame processing cycle: reads a frame, invokes the Haar Cascade 
        vision backend, extracts the target ROI, draws bounding boxes, formats the image 
        for PyQt UI rendering, and calculates RGB spatial averages.

        :return: Tuple containing (list of dictionaries with ROI statistics, raw frame, face_found boolean).
        """
        ret, frame = self.capture.read()

        if not ret or frame is None:
            return None, None, False

        self.frame_counter += 1

        display_frame = frame.copy()
        roi_results = None
        face_found = False

        # Extract target facial regions using Haar Cascade classifier
        rois = self._extract_face_rois_haar(frame)

        if rois:
            face_found = True
            roi_results = []

            for name, img, box in rois:
                x, y, w, h = box

                # Process color metrics for the extracted region
                roi_data = self._extract_single_roi_rgb(name, img)
                roi_results.append(roi_data)

                # Render geometric bounding box on the display frame
                cv2.rectangle(
                    display_frame,
                    (x, y),
                    (x + w, y + h),
                    (0, 255, 0),
                    2
                )

        # Convert image format to fit PyQt layout constraints
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
        """
        Computes the spatial pixel average for Red, Green, and Blue channels over the isolated ROI.

        :param name: The anatomical string identifier of the ROI (e.g., "forehead").
        :param roi: The cropped numpy image array of the region.
        :return: A dictionary mapping the statistical data (pixel count, sampling score, avg RGB tuple).
        """
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

        # Evaluate pixel density score relative to baseline requirements
        sampling_score = min(100.0, (num_pixels / 5000.0) * 100.0)

        # Compute mean intensity across spatial coordinates (OpenCV uses BGR layout)
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