from PyQt5.QtWidgets import QLabel, QWidget, QPushButton, QLineEdit
from PyQt5.QtCore import QFile, QTextStream, QSize, Qt
from PyQt5.QtGui import QPixmap
import json
import os


# This Class is responsible for the Signup Screen and its functionality
class SignupScreen(QWidget):
    def __init__(self, app, client):
        super().__init__()
        self.app = app
        self.client = client
        self.window_menu_screen = None
        self.label_of_image = None
        self.setWindowTitle('Monitoring Heart Rate Application')
        self.resize(1500, 800)  # Set the window size

        # Load and apply the CSS styles from the style.css file
        style_file = QFile('style.css')
        if style_file.open(QFile.ReadOnly | QFile.Text):
            style_stream = QTextStream(style_file)
            app.setStyleSheet(style_stream.readAll())

        # Add title label
        title_label = QLabel('Sign Up', self)
        title_label.move(630, 0)  # x,y coordinates value from top-left corner
        title_label.setObjectName('title_label')  # set object name for using it in the css file

        # ID label
        id_label = QLabel('ID:', self)
        id_label.move(520, 200)  # x,y coordinates value from top-left corner
        id_label.setObjectName('id_label')  # set object name for using it in the css file
        # ID input
        self.id_input = QLineEdit(self)
        self.id_input.move(640, 200)  # x,y coordinates value from top-left corner
        self.id_input.setObjectName('id_input')  # set object name for using it in the css file
        self.id_input.setFixedWidth(200)  # Decrease the width to 200 pixels

        # First Name label
        first_name_label = QLabel('First Name:', self)
        first_name_label.move(520, 300)  # x,y coordinates value from top-left corner
        first_name_label.setObjectName('first_name_label')  # set object name for using it in the css file
        # First Name input
        self.firstName_input = QLineEdit(self)
        self.firstName_input.move(640, 300)  # x,y coordinates value from top-left corner
        self.firstName_input.setObjectName('firstName_input')  # set object name for using it in the css file
        self.firstName_input.setFixedWidth(200)  # Decrease the width to 200 pixels

        # Last Name label
        last_name_label = QLabel('Last Name:', self)
        last_name_label.move(520, 400)  # x,y coordinates value from top-left corner
        last_name_label.setObjectName('last_name_label')  # set object name for using it in the css file
        # Last Name input
        self.lastName_input = QLineEdit(self)
        self.lastName_input.move(640, 400)  # x,y coordinates value from top-left corner
        self.lastName_input.setObjectName('lastName_input')  # set object name for using it in the css file
        self.lastName_input.setFixedWidth(200)  # Decrease the width to 200 pixels

        # Add patient Button
        add_button = QPushButton('Add patient', self)
        add_button.move(630, 500)  # x,y coordinates value from top-left corner
        add_button.clicked.connect(self.add_clicked)

        # Back button
        back_button = QPushButton('Back', self)
        back_button.move(10, 10)  # Adjust the position of the back button
        back_button.clicked.connect(self.back_clicked)  # Connect the button's clicked signal to the go_back method
        back_button.setObjectName('back_button')  # set object name for using it in the css file

        # Error label
        self.error_label = QLabel('', self)
        self.error_label.move(590, 580)  # x,y coordinates value from top-left corner
        self.error_label.setObjectName('error_label')  # set object name for using it in the css file
        self.error_label.setFixedSize(400, 40)  # Adjust width and height accordingly

        # Function that displaying image on the signup screen
        self.load_pic()

    # Go back to the previous window
    def back_clicked(self):
        from menuScreen import MenuScreen
        self.window_menu_screen = MenuScreen(self.app, self.client)
        self.window_menu_screen.show()
        self.hide()

    # Triggered when add patient button clicked
    def add_clicked(self):
        # Save the inserted data by the user
        entered_id = self.id_input.text()
        entered_first_name = self.firstName_input.text()
        entered_last_name = self.lastName_input.text()

        # Check if one of the fields are empty
        if entered_id == "" or entered_first_name == "" or entered_last_name == "":
            self.error_label.setText('At least one of the fields are empty')
            self.error_label.show()
            return

        # Hide the previous error label
        self.error_label.hide()

        # Prepare the patient data to be sent to the server
        patient_data = {
            "id": entered_id,
            "firstName": entered_first_name,
            "lastName": entered_last_name
        }

        # Send a 'add patient request' to the server
        self.client.send('ADD_PATIENT_REQUEST'.encode("utf-8"))

        # Send the patient data to the server
        self.client.send(json.dumps(patient_data).encode("utf-8"))

        # Receive the login result from the server
        id_already_exist_in_db = self.client.recv(1024).decode("utf-8")

        # Added new patient failed because id already exist
        if id_already_exist_in_db == "True":
            self.error_label.setText('The id already exist in the system')
            self.error_label.show()
        # Added new patient succeed
        else:
            self.error_label.setText('Added new patient!')
            self.error_label.show()

    # Function that displaying image on the signup screen
    def load_pic(self):
        image_name = "sign_up_image.png"
        image_path = os.path.join(os.path.dirname(__file__), '..', 'server', 'pics', image_name)

        # Create a QLabel to display the image
        self.label_of_image = QLabel(self)

        # Load the image using QPixmap
        original_pixmap = QPixmap(image_path)

        # Resize the image
        target_size = QSize(200, 200)  # Set your desired size
        pixmap = original_pixmap.scaled(target_size, aspectRatioMode=Qt.KeepAspectRatio)

        # Set the pixmap to the QLabel
        self.label_of_image.setPixmap(pixmap)

        # Set the fixed size of the QLabel to match the size of the image
        self.label_of_image.setFixedSize(pixmap.size())

        # Set the initial position of the QLabel
        self.label_of_image.move(1050, 250)
