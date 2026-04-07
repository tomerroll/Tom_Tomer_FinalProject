import cv2
import json
import os
from PyQt5.QtWidgets import QLabel, QWidget, QPushButton, QComboBox, QFileDialog, QMessageBox, QVBoxLayout
from PyQt5.QtCore import QFile, QTextStream, QTimer
from PIL import Image
from hr_plotter import HRPlotter
from bin_plotter import BINPlotter
import numpy as np


# This Class is responsible for the Specific Patient Screen and its functionality
class SpecificPatientScreen(QWidget):
    def __init__(self, app, client, patient):
        super().__init__()
        self.app = app
        self.client = client
        self.patient = patient
        self.capture = None  # Initialize self.capture as None
        self.window_panel_screen = None
        self.setWindowTitle('Monitoring Heart Rate Application')
        self.resize(1500, 800)  # Set the window size
        self.picture_captured = False  # Initialize the flag to False - it didn't capture pic yet

        # Load and apply the CSS styles from the style.css file
        style_file = QFile('style.css')
        if style_file.open(QFile.ReadOnly | QFile.Text):
            style_stream = QTextStream(style_file)
            app.setStyleSheet(style_stream.readAll())

        # Frequency of Patient label
        self.freq_label = QLabel('Frequency:', self)
        self.freq_label.move(1200, 100)  # x,y coordinates value from top-left corner
        self.freq_label.setObjectName('freq_label')  # set object name for using it in the css file
        self.freq_label.setFixedSize(400, 40)  # Adjust width and height accordingly

        # Heart rate of Patient label
        self.hr_label = QLabel('Heart rate:', self)
        self.hr_label.move(1200, 200)  # x,y coordinates value from top-left corner
        self.hr_label.setObjectName('hr_label')  # set object name for using it in the css file
        self.hr_label.setFixedSize(400, 40)  # Adjust width and height accordingly

        # Error of face detection label
        self.face_detect_error_label = QLabel('', self)
        self.face_detect_error_label.move(140, 450)  # x,y coordinates value from top-left corner
        self.face_detect_error_label.setObjectName('face_detect_error_label')  # set object name for using it in css
        self.face_detect_error_label.setFixedSize(400, 40)  # Adjust width and height accordingly

        # Combo box for choosing Live or captured video
        self.video_combo_box = QComboBox(self)
        self.video_combo_box.addItem("Video")
        self.video_combo_box.addItem("Webcam")
        self.video_combo_box.move(150, 500)

        # Open button to upload video from DB or local memory
        self.open_button = QPushButton('Open', self)
        self.open_button.move(320, 500)  # x,y coordinates value from top-left corner
        self.open_button.clicked.connect(self.open_clicked)
        self.open_button.setObjectName('smaller_button')  # set object name for using it in the css file

        # Start button to start extracting the HR
        self.start_button = QPushButton('Start', self)
        self.start_button.move(450, 500)  # x,y coordinates value from top-left corner
        self.start_button.clicked.connect(self.start_clicked)
        self.start_button.setObjectName('smaller_button')  # set object name for using it in the css file
        self.start_button.setDisabled(True)  # Disable the start button

        # Stop button to stop extracting the HR
        self.stop_button = QPushButton('Stop', self)
        self.stop_button.move(580, 500)  # x,y coordinates value from top-left corner
        self.stop_button.clicked.connect(self.stop_clicked)
        self.stop_button.setObjectName('smaller_button')  # set object name for using it in the css file
        self.stop_button.setEnabled(False)  # Disable the stop button

        # Back button
        self.back_button = QPushButton('Back', self)
        self.back_button.move(10, 10)  # Adjust the position of the back button
        self.back_button.clicked.connect(self.back_clicked)  # Connect the button's clicked signal to the go_back method
        self.back_button.setObjectName('back_button')  # set object name for using it in the css file

        # Create a window to display the HR
        self.hr_window = QWidget(self)
        self.hr_window.setGeometry(850, 10, 300, 230)
        self.hr_window.setStyleSheet("border: 2px solid black;")
        self.layout_hr_window = QVBoxLayout(self.hr_window)

        # Create a window to display the FFT Signals
        self.bin_window = QWidget(self)
        self.bin_window.setGeometry(750, 300, 700, 400)
        self.bin_window.setStyleSheet("border: 2px solid black;")
        self.layout_bin_window = QVBoxLayout(self.bin_window)

        # Create a window to display the video
        self.video_window = QLabel(self)
        self.video_window.setGeometry(140, 50, 500, 400)
        self.video_window.setStyleSheet("border: 2px solid black;")

        # Heart rate calculation variables
        self.green_channel = None
        self.list_green_channel_avg = []
        self.previous_list_counter = 0
        self.counter_for_list = 0
        self.heart_rate = 0
        self.frequency = 0
        self.sampling_rate = 0
        # Timer to update heart rate label and db every second (set the interval when start the timer)
        self.update_heart_rate_label_and_db_timer = QTimer(self)
        self.update_heart_rate_label_and_db_timer.timeout.connect(self.update_heart_rate)
        # Create a QTimer to continuously update the video feed
        self.timer_for_update_video_feed = QTimer(self)
        self.timer_for_update_video_feed.timeout.connect(self.update_video_feed)

        # Triggered when combo box changed
        self.video_combo_box.currentIndexChanged.connect(self.combo_box_changed)
        # Set fixed size based on the button size hint
        self.video_combo_box.setFixedSize(self.open_button.sizeHint())

        # Create an instance of HRPlotter
        self.hr_plotter = HRPlotter(self.hr_window, self.layout_hr_window)
        # Create an instance of BINPlotter
        self.bin_plotter = BINPlotter(self.bin_window, self.layout_bin_window)
        self.flag_for_file_path = False

    # Go back to the previous window
    def back_clicked(self):
        if self.capture is not None:
            self.timer_for_update_video_feed.stop()  # Stop calling update_video_feed()
            self.video_window.clear()  # Clear the window that contain the frames

        # Send a request to the server to enter the panel screen
        self.client.send('ENTER_PANEL_SCREEN'.encode("utf-8"))
        response = self.client.recv(1024).decode("utf-8")
        # Entry is allowed, navigate to the PanelScreen page
        if response == 'ENTRY_ALLOWED':
            if self.patient == '1':
                self.update_button_state_in_db('1', "yes")
            elif self.patient == '2':
                self.update_button_state_in_db('2', "yes")
            elif self.patient == '3':
                self.update_button_state_in_db('3', "yes")
            from panelScreen import PanelScreen
            self.window_panel_screen = PanelScreen(self.app, self.client)
            self.window_panel_screen.show()
            self.hide()
        else:  # Entry is denied, display an error message or handle it accordingly
            QMessageBox.warning(self, "Entry Denied", "Only one client can enter the PanelScreen page.")

    # Handle combo box selection change
    def combo_box_changed(self, index):
        if index == 0:  # Captured video selected
            self.timer_for_update_video_feed.stop()  # Stop calling update_video_feed()
            self.video_window.clear()  # Clear the window that containing the frames
            self.open_button.setEnabled(True)  # Enable the open button
            self.start_button.setDisabled(True)  # Disable the start button
        if index == 1:  # Webcam option selected
            self.timer_for_update_video_feed.stop()  # Stop calling update_video_feed()
            self.video_window.clear()  # Clear the window that containing the frames
            self.open_button.setEnabled(False)  # Disable the open button for recorded video
            self.display_video_feed()  # Begin to display the video feed
            self.start_button.setEnabled(True)  # Enable the start button
            self.flag_for_file_path = False

    # Start video feed (webcam or captured video)
    def display_video_feed(self, file_path=None):
        if file_path is None:  # If there is no file, so it means its webcam
            self.capture = cv2.VideoCapture(0)
        else:
            self.capture = cv2.VideoCapture(file_path)

        self.sampling_rate = self.capture.get(cv2.CAP_PROP_FPS)
        # Activate update_video_feed() every 100 Millisecond
        self.timer_for_update_video_feed.start(100)

    # Update the video feed
    def update_video_feed(self):
        from videoProcessor import VideoProcessor
        # Create new instance of the video processor class
        video_processor_instance = VideoProcessor(self.capture, self.video_window, self.flag_for_file_path)
        # Call the update_video_feed method to process the frames from the video and detect the forehead
        video_processor_instance.update_video_feed()
        # Get the green channel values in order to extract the hr later
        self.green_channel = video_processor_instance.get_green_channel()
        # Check if self.green_channel is not None before using it
        if self.green_channel is not None:
            # Convert the matrix to a NumPy array
            matrix_array = np.array(self.green_channel)
            np.set_printoptions(threshold=np.inf)
            # Calculate the median along a specific axis (axis= None calculates the overall median)
            median_value = np.median(matrix_array, axis=None)
            self.list_green_channel_avg.append(float(median_value))
            self.counter_for_list += 1
        else:
            # Handle the case when self.green_channel is None
            print("Face did not detected")

    # Open button clicked for recorded video
    def open_clicked(self):
        # Getting the path of the video file
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", "Video Files (*.mp4 *.avi *.mov)",
                                                   options=options)
        if file_path:
            self.flag_for_file_path = True
            self.display_video_feed(file_path)  # Displaying the video feed of this recorded video
            self.start_button.setEnabled(True)  # Enable the start button

    def start_clicked(self):
        self.start_button.setEnabled(False)  # Disable the start button
        self.video_combo_box.setEnabled(False)  # Disable the combo box
        self.open_button.setEnabled(False)  # Disable the open button
        self.back_button.setEnabled(False)  # Disable the back button
        self.stop_button.setEnabled(True)  # Enable the stop button

        # Capture the picture of the patient and store it in the server
        if not self.picture_captured:
            self.capture_picture()
            self.picture_captured = True  # After capturing the first pic, it will not take pic again

        if self.green_channel is not None:
            # Update heart rate every 1 second - Activate update_heart_rate() function
            self.update_heart_rate_label_and_db_timer.start(1000)

    # Stop button clicked
    def stop_clicked(self):
        self.update_heart_rate_label_and_db_timer.stop()  # Stop calling update_heart_rate()
        self.timer_for_update_video_feed.stop()  # Stop calling update_video_feed()
        self.start_button.setEnabled(True)  # Enable the start button
        self.video_combo_box.setEnabled(True)  # Enable the combo box
        self.open_button.setEnabled(True)  # Enable the open button
        self.back_button.setEnabled(True)  # Enable the back button
        self.delete_patient_image()  # Delete the pic of the patient from the pics file (in the server side)
        self.capture.release()  # Object is used to capture video frames, so release it for memory
        self.capture = None  # Set this object as None
        self.video_window.clear()  # Clear the window that contain the frames
        self.picture_captured = False  # After delete image, if start again it will take pic patient again
        self.hr_label.setText("Heart rate: " + str(0))  # Display the label of the hr as 0
        self.stop_button.setEnabled(False)  # Disable the stop button
        self.start_button.setEnabled(False)  # Disable the start button
        self.open_button.setEnabled(False)  # Disable the open button
        # Update the hr in the DB to 0 because stop button pressed
        data = {
            "heart_rate": 0,
            "num": self.patient
        }
        json_data = json.dumps(data)
        self.client.send('HEART_RATE_UPDATE'.encode("utf-8"))
        self.client.send(json_data.encode("utf-8"))

    # Update the heart rate label
    def update_heart_rate(self):
        if self.counter_for_list >= 600:
            hr_result, freq_result = self.calculate_heart_rate()  # Receive hr & freq from instance of ExtractHeartRate
            self.hr_label.setText("Heart rate: " + str(hr_result))  # Display the hr in the label
            self.freq_label.setText("Frequency: " + str(freq_result))  # Display the frequency in the label
            # Update the dynamic HR signal plot using HRPlotter
            self.hr_plotter.update_hr_plot(hr_result)

            # Send the updated heart rate to the server side
            data = {
                "heart_rate": hr_result,
                "num": self.patient
            }
            json_data = json.dumps(data)
            self.client.send('HEART_RATE_UPDATE'.encode("utf-8"))
            self.client.send(json_data.encode("utf-8"))

    # Calculate the heart rate based on the green channel
    def calculate_heart_rate(self):
        from extractHeartRate import ExtractHeartRate
        copied_list = list(self.list_green_channel_avg)
        extract_hr_instance = ExtractHeartRate(self.green_channel)
        self.heart_rate, self.frequency, error_label = extract_hr_instance.calc_hr_process(copied_list,
                                                                                           30,
                                                                                           self.bin_plotter,
                                                                                           self.counter_for_list)
        if error_label is not None:  # The face is too close to the camera / far from the camera
            self.face_detect_error_label.setText(str(error_label))  # Display the error label
        else:
            self.face_detect_error_label.setText('')  # There is no error so delete it
        return self.heart_rate, self.frequency  # Return the results of the calculated hr and frequency

    # Update button state in JSON data base
    def update_button_state_in_db(self, patient_id, enabled):
        # Prepare the patient data to be sent to the server
        patient_data = {
            "enabled": enabled,
            "id": patient_id
        }
        # Send a 'UPDATE_BUTTON_STATES' request to the server
        self.client.send('UPDATE_BUTTON_STATES'.encode("utf-8"))
        # Send the patient data to the server
        self.client.send(json.dumps(patient_data).encode("utf-8"))

    # Capture the picture of the patient
    def capture_picture(self):
        if self.green_channel is not None:
            # Get the original frame from the capture
            ret, frame = self.capture.read()

            if ret:
                # Save the frame to the "pics" folder
                pics_folder = os.path.join(os.path.dirname(__file__), '..', 'server', 'pics')
                os.makedirs(pics_folder, exist_ok=True)  # Create the "pics" folder if it doesn't exist
                image_name = "patient_" + self.patient + "_image.jpg"
                image_path = os.path.join(pics_folder, image_name)
                # Convert the frame to RGB format
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # Convert the RGB frame to a PIL Image
                image = Image.fromarray(frame_rgb)
                # Save the image
                image.save(image_path, format="JPEG")

    # Method to delete the patient's image
    def delete_patient_image(self):
        pics_folder = os.path.join(os.path.dirname(__file__), '..', 'server', 'pics')
        image_name = "patient_" + self.patient + "_image.jpg"
        image_path = os.path.join(pics_folder, image_name)
        if os.path.exists(image_path):
            os.remove(image_path)
