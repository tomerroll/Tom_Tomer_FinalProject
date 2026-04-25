import cv2
import json
import os
import time
import numpy as np
from collections import deque

from PyQt5.QtWidgets import (
    QLabel, QWidget, QPushButton, QComboBox, QFileDialog,
    QVBoxLayout, QHBoxLayout, QGridLayout
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont
from PIL import Image

from hr_plotter import HRPlotter
from bin_plotter import BINPlotter
from videoProcessor import VideoProcessor
from extractHeartRate import ExtractHeartRate


class SpecificPatientScreen(QWidget):
    def __init__(self, app, client, patient, main_window=None):
        super().__init__()
        self.app = app
        self.client = client
        self.patient = patient
        self.main_window = main_window
        self.capture = None
        self.picture_captured = False

        self.setWindowTitle(f'VitalSign Monitoring - Patient {self.patient}')
        self.resize(1400, 800)

        self.apply_modern_style()
        self.setup_ui()
        self.init_variables()
        self.setup_timers()

    def apply_modern_style(self):
        style = """
        QWidget {
            background-color: #1e1e2e;
            color: #cdd6f4;
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        QLabel {
            font-size: 14px;
        }
        QPushButton {
            background-color: #89b4fa;
            color: #11111b;
            border-radius: 8px;
            font-weight: bold;
            font-size: 13px;
        }
        QPushButton:hover {
            background-color: #b4befe;
        }
        QPushButton:disabled {
            background-color: #45475a;
            color: #a6adc8;
        }
        QComboBox {
            background-color: #313244;
            color: #cdd6f4;
            border: 1px solid #585b70;
            border-radius: 6px;
            padding: 5px;
            font-size: 13px;
        }
        QComboBox::drop-down {
            border: none;
        }
        QLabel#video_frame {
            border: 2px solid #89b4fa;
            border-radius: 12px;
            background-color: #181825;
        }
        QLabel#highlight_label {
            color: #a6e3a1;
            font-weight: bold;
            font-size: 18px;
        }
        QLabel#error_label {
            color: #f38ba8;
            font-weight: bold;
        }
        """
        self.setStyleSheet(style)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        top_bar_layout = QHBoxLayout()

        self.back_button = QPushButton('⬅ Back')
        self.back_button.setFixedSize(90, 35)
        self.back_button.clicked.connect(self.back_clicked)

        title_label = QLabel(f"Live Vitals Monitoring - Patient {self.patient}")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)

        top_bar_layout.addWidget(self.back_button)
        top_bar_layout.addWidget(title_label, 1)
        main_layout.addLayout(top_bar_layout)

        grid_layout = QGridLayout()
        grid_layout.setSpacing(20)

        left_panel = QVBoxLayout()

        self.video_window = QLabel(self)
        self.video_window.setMinimumSize(500, 400)
        self.video_window.setAlignment(Qt.AlignCenter)
        self.video_window.setObjectName("video_frame")
        self.video_window.setText("Waiting for Video Feed...")
        left_panel.addWidget(self.video_window)

        controls_layout = QHBoxLayout()

        self.video_combo_box = QComboBox(self)
        self.video_combo_box.addItems(["Video File", "Live Webcam"])
        self.video_combo_box.setFixedSize(120, 35)
        self.video_combo_box.currentIndexChanged.connect(self.combo_box_changed)

        self.open_button = self.create_button('📂 Open', self.open_clicked)
        self.start_button = self.create_button('▶ Start', self.start_clicked, False)
        self.stop_button = self.create_button('⏹ Stop', self.stop_clicked, False)

        controls_layout.addWidget(self.video_combo_box)
        controls_layout.addWidget(self.open_button)
        controls_layout.addWidget(self.start_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addStretch()

        left_panel.addLayout(controls_layout)

        status_layout = QHBoxLayout()
        self.timer_label = QLabel('Time: 0s')
        self.face_detect_error_label = QLabel('')
        self.face_detect_error_label.setObjectName("error_label")

        status_layout.addWidget(self.timer_label)
        status_layout.addWidget(self.face_detect_error_label)
        status_layout.addStretch()
        left_panel.addLayout(status_layout)

        grid_layout.addLayout(left_panel, 0, 0, 2, 1)

        right_top_panel = QVBoxLayout()

        stats_layout = QHBoxLayout()
        self.hr_label = QLabel('Heart rate: --')
        self.hr_label.setObjectName("highlight_label")
        self.freq_label = QLabel('Frequency: --')
        self.avg_hr_label = QLabel('Final Avg HR: --')

        stats_layout.addWidget(self.hr_label)
        stats_layout.addWidget(self.freq_label)
        stats_layout.addWidget(self.avg_hr_label)
        right_top_panel.addLayout(stats_layout)

        self.hr_window = QWidget()
        self.hr_window.setMinimumHeight(250)
        self.layout_hr = QVBoxLayout(self.hr_window)
        self.hr_plotter = HRPlotter(self.hr_window, self.layout_hr)
        right_top_panel.addWidget(self.hr_window)

        grid_layout.addLayout(right_top_panel, 0, 1)

        self.bin_window = QWidget()
        self.bin_window.setMinimumHeight(350)
        self.layout_bin = QVBoxLayout(self.bin_window)
        self.bin_plotter = BINPlotter(self.bin_window, self.layout_bin)
        grid_layout.addWidget(self.bin_window, 1, 1)

        grid_layout.setColumnStretch(0, 1)
        grid_layout.setColumnStretch(1, 1)

        main_layout.addLayout(grid_layout)

    def create_button(self, text, slot, enabled=True):
        btn = QPushButton(text, self)
        btn.setFixedSize(90, 35)
        btn.setEnabled(enabled)
        btn.clicked.connect(slot)
        return btn

    def init_variables(self):
        self.min_hr_window_seconds = 10.0
        self.max_hr_window_seconds = 20.0
        self.pos_window_seconds = 1.6

        self.list_rgb_means = deque()
        self.hr_history = []
        self.frames_processed = 0
        self.video_ended = False

        self.nominal_capture_fps = 30.0
        self.sampling_rate = 30.0

        self.face_detected_latest = None
        self.video_processor = None
        self.hr_extractor = ExtractHeartRate(
            min_signal_seconds=self.min_hr_window_seconds,
            pos_window_seconds=self.pos_window_seconds
        )
        self.last_frame = None
        self.no_face_counter = 0

        self.last_wall_time = None
        self.last_video_pos_msec = None
        self.fps_history = deque(maxlen=90)
        self.source_is_webcam = False

    def setup_timers(self):
        self.hr_update_timer = QTimer(self)
        self.hr_update_timer.timeout.connect(self.update_heart_rate)

        self.video_timer = QTimer(self)
        self.video_timer.timeout.connect(self.update_video_feed)

    def reset_runtime_state(self):
        self.list_rgb_means.clear()
        self.hr_history = []
        self.frames_processed = 0
        self.video_ended = False
        self.picture_captured = False
        self.face_detected_latest = None
        self.last_frame = None
        self.no_face_counter = 0
        self.last_wall_time = None
        self.last_video_pos_msec = None
        self.fps_history.clear()

        self.hr_extractor = ExtractHeartRate(
            min_signal_seconds=self.min_hr_window_seconds,
            pos_window_seconds=self.pos_window_seconds
        )

        self.hr_label.setText('Heart rate: --')
        self.freq_label.setText('Frequency: --')
        self.avg_hr_label.setText('Final Avg HR: --')
        self.face_detect_error_label.setText('')
        self.timer_label.setText('Time: 0s')

    def _get_effective_buffer_size(self):
        fps = max(float(self.sampling_rate), 1.0)
        return int(np.ceil(self.max_hr_window_seconds * fps))

    def _get_min_frames_for_hr(self):
        fps = max(float(self.sampling_rate), 1.0)
        return int(np.ceil(self.min_hr_window_seconds * fps))

    def _trim_rgb_buffer(self):
        max_frames = max(self._get_effective_buffer_size(), 1)
        while len(self.list_rgb_means) > max_frames:
            self.list_rgb_means.popleft()

    def _update_sampling_rate(self):
        measured_fps = None

        if self.source_is_webcam:
            now = time.perf_counter()
            if self.last_wall_time is not None:
                dt = now - self.last_wall_time
                if 0.001 < dt < 1.0:
                    measured_fps = 1.0 / dt
            self.last_wall_time = now
        else:
            pos_msec = float(self.capture.get(cv2.CAP_PROP_POS_MSEC)) if self.capture else 0.0
            if pos_msec > 0:
                if self.last_video_pos_msec is not None:
                    dt_msec = pos_msec - self.last_video_pos_msec
                    if 1.0 <= dt_msec <= 1000.0:
                        measured_fps = 1000.0 / dt_msec
                self.last_video_pos_msec = pos_msec

        if measured_fps is not None and np.isfinite(measured_fps):
            measured_fps = float(np.clip(measured_fps, 5.0, 120.0))
            self.fps_history.append(measured_fps)

        if len(self.fps_history) > 0:
            smooth_fps = float(np.median(self.fps_history))
            if self.sampling_rate <= 0:
                self.sampling_rate = smooth_fps
            else:
                alpha = 0.15
                self.sampling_rate = (1.0 - alpha) * self.sampling_rate + alpha * smooth_fps
        else:
            self.sampling_rate = self.nominal_capture_fps

    def display_video_feed(self, file_path=None):
        if self.capture:
            self.capture.release()
            self.capture = None

        self.video_processor = None
        self.reset_runtime_state()

        if file_path is None:
            self.capture = cv2.VideoCapture(0)
            is_webcam = True
        else:
            self.capture = cv2.VideoCapture(file_path)
            is_webcam = False

        if not self.capture or not self.capture.isOpened():
            self.video_window.setText("Failed to open video source")
            return

        self.source_is_webcam = is_webcam

        self.video_processor = VideoProcessor(
            self.capture,
            self.video_window,
            is_webcam=is_webcam
        )

        self.nominal_capture_fps = float(self.capture.get(cv2.CAP_PROP_FPS))
        if self.nominal_capture_fps <= 0 or np.isnan(self.nominal_capture_fps):
            self.nominal_capture_fps = 30.0

        self.sampling_rate = self.nominal_capture_fps

        delay = max(1, int(1000 / self.nominal_capture_fps))
        self.video_timer.start(delay)

    def update_video_feed(self):
        if not self.capture or not self.capture.isOpened():
            return

        if self.video_combo_box.currentIndex() == 0:
            current_frame_idx = int(self.capture.get(cv2.CAP_PROP_POS_FRAMES))
            total_frames = int(self.capture.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames > 0 and current_frame_idx >= total_frames - 5:
                self.handle_video_end()
                return

        if self.video_processor is None:
            return

        roi_results, current_frame, face_found = self.video_processor.update_video_feed()

        if current_frame is not None:
            self.last_frame = current_frame.copy()

        self._update_sampling_rate()

        if face_found:
            self.no_face_counter = 0
            self.face_detected_latest = True
        else:
            self.no_face_counter += 1
            if self.no_face_counter > 10:
                self.face_detected_latest = None

        if roi_results is not None and len(roi_results) > 0:
            self.list_rgb_means.append(roi_results)
            self._trim_rgb_buffer()
            self.frames_processed += 1

            elapsed_seconds = len(self.list_rgb_means) / max(self.sampling_rate, 1.0)
            self.timer_label.setText(f'⏱ Time: {int(elapsed_seconds)}s | FPS: {self.sampling_rate:.1f}')

            if not self.picture_captured:
                self.capture_picture()

    def update_heart_rate(self):
        if self.video_ended:
            return

        if len(self.list_rgb_means) < self._get_min_frames_for_hr():
            return

        self.hr_extractor.face_detected = self.face_detected_latest

        hr, freq, err = self.hr_extractor.calc_hr_process(
            list(self.list_rgb_means),
            self.sampling_rate,
            self.bin_plotter
        )

        if hr is None or freq is None:
            self.face_detect_error_label.setText("⚠ No valid RGB data")
            return

        if err:
            self.face_detect_error_label.setText(f"⚠ {err}")
            if hr and 40 <= hr <= 180:
                self.hr_label.setText(f"❤ HR: {round(hr, 1)} BPM")
                self.freq_label.setText(f"🌊 Freq: {round(freq, 2)} Hz")
            return

        self.face_detect_error_label.setText('')
        self.hr_label.setText(f"❤ HR: {round(hr, 1)} BPM")
        self.freq_label.setText(f"🌊 Freq: {round(freq, 2)} Hz")
        self.hr_plotter.update_hr_plot(hr)

        if 40 <= hr <= 180:
            self.hr_history.append(hr)

        self.send_hr_to_server(hr)

    def handle_video_end(self):
        if self.video_ended:
            return

        self.video_ended = True
        self.video_timer.stop()
        self.hr_update_timer.stop()

        if self.hr_history:
            avg = round(sum(self.hr_history) / len(self.hr_history), 1)
            self.avg_hr_label.setText(f"📊 Final Avg HR: {avg} BPM")

        self.stop_button.setEnabled(False)
        self.start_button.setEnabled(True)

    def start_clicked(self):
        self.video_ended = False
        self.reset_runtime_state()

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        self.hr_update_timer.start(1000)

    def stop_clicked(self):
        self.handle_video_end()

        if self.capture:
            self.capture.release()
            self.capture = None

        self.video_processor = None
        self.video_window.clear()
        self.video_window.setText("Video Stopped")

    def back_clicked(self):
        self.stop_clicked()
        self.hide()

        if self.main_window:
            self.main_window.show()

    def delete_patient_image(self):
        pics_folder = os.path.join(
            os.path.dirname(__file__),
            '..',
            'server',
            'pics'
        )
        image_path = os.path.join(
            pics_folder,
            f"patient_{self.patient}_image.jpg"
        )

        if os.path.exists(image_path):
            os.remove(image_path)

    def open_clicked(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Video",
            "",
            "Videos (*.mp4 *.avi)"
        )

        if path:
            self.display_video_feed(path)
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)

    def combo_box_changed(self, idx):
        self.video_timer.stop()
        self.hr_update_timer.stop()

        if self.capture:
            self.capture.release()
            self.capture = None

        self.video_processor = None
        self.reset_runtime_state()

        self.video_window.clear()
        self.video_window.setText("Loading Feed...")

        if idx == 1:
            self.open_button.setEnabled(False)
            self.display_video_feed()
            self.start_button.setEnabled(True)
        else:
            self.open_button.setEnabled(True)
            self.start_button.setEnabled(False)

        self.stop_button.setEnabled(False)

    def send_hr_to_server(self, hr):
        data = json.dumps({"heart_rate": hr, "num": self.patient})
        try:
            self.client.send('HEART_RATE_UPDATE'.encode("utf-8"))
            self.client.send(data.encode("utf-8"))
        except Exception:
            pass

    def capture_picture(self):
        if self.face_detected_latest and self.last_frame is not None:
            pics_folder = os.path.join(
                os.path.dirname(__file__),
                '..',
                'server',
                'pics'
            )
            os.makedirs(pics_folder, exist_ok=True)

            image_path = os.path.join(
                pics_folder,
                f"patient_{self.patient}_image.jpg"
            )

            image = Image.fromarray(
                cv2.cvtColor(self.last_frame, cv2.COLOR_BGR2RGB)
            )
            image.save(image_path, format="JPEG")
            self.picture_captured = True