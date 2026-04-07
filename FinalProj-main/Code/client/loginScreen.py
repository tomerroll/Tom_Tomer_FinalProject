from PyQt5.QtWidgets import QLabel, QWidget, QLineEdit, QPushButton
from PyQt5.QtCore import QFile, QTextStream, QSize
from PyQt5.QtGui import QPixmap
from menuScreen import MenuScreen
import json
import os


# This Class is responsible for the Login Screen and its functionality
class LoginScreen(QWidget):
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
        title_label = QLabel('Heart Rate Monitoring Application', self)
        title_label.move(300, 0)  # x,y coordinates value from top-left corner
        title_label.setObjectName('title_label')  # set object name for using it in the css file

        # Username label
        username_label = QLabel('Username:', self)
        username_label.move(520, 200)  # x,y coordinates value from top-left corner
        username_label.setObjectName('username_label')  # set object name for using it in the css file
        # Username input
        self.username_input = QLineEdit(self)
        self.username_input.move(640, 200)  # x,y coordinates value from top-left corner
        self.username_input.setObjectName('username_input')  # set object name for using it in the css file
        self.username_input.setFixedWidth(200)  # Decrease the width to 200 pixels

        # Password label
        password_label = QLabel('Password:', self)
        password_label.move(520, 300)  # x,y coordinates value from top-left corner
        password_label.setObjectName('password_label')  # set object name for using it in the css file
        # Password input
        self.password_input = QLineEdit(self)
        self.password_input.move(640, 300)  # x,y coordinates value from top-left corner
        self.password_input.setObjectName('password_input')  # set object name for using it in the css file
        self.password_input.setFixedWidth(200)  # Decrease the width to 200 pixels
        self.password_input.setEchoMode(QLineEdit.Password)  # Hide password characters

        # Login Button
        login_button = QPushButton('Login', self)
        login_button.move(620, 400)  # x,y coordinates value from top-left corner
        login_button.clicked.connect(self.login_clicked)
        login_button.setObjectName('login_button')  # set object name for using it in the css file

        # Error label
        self.error_label = QLabel('', self)
        self.error_label.move(580, 480)  # x,y coordinates value from top-left corner
        self.error_label.setObjectName('error_label')  # set object name for using it in the css file

        # Function that displaying image on the login screen
        self.load_pic()

    # Triggered when login button pressed
    def login_clicked(self):
        # Save the inserted data by the user
        entered_username = self.username_input.text()
        entered_password = self.password_input.text()

        # Hide the previous error label
        self.error_label.hide()

        # Prepare the login data to be sent to the server
        login_data = {
            "username": entered_username,
            "password": entered_password
        }

        # Send a login request to the server
        self.client.send('LOGIN_REQUEST'.encode("utf-8"))

        # Send the login data to the server
        self.client.send(json.dumps(login_data).encode("utf-8"))

        # Receive the login result from the server
        login_result = self.client.recv(1024).decode("utf-8")

        # Successful login, proceed to the menu screen
        if login_result == "True":
            self.window_menu_screen = MenuScreen(self.app, self.client)
            self.window_menu_screen.show()
            self.hide()
        # Login failed, display an error message
        elif login_result == "alreadyLoggedIn":
            self.error_label.setText('The user already logged in')
            self.error_label.show()
        elif entered_username == "" or entered_password == "":
            self.error_label.setText('At least one of the fields are empty')
            self.error_label.show()
        else:
            self.error_label.setText('Invalid username or password')
            self.error_label.show()

    # Function that displaying image on the login screen
    def load_pic(self):
        image_name = "hr_image.png"
        image_path = os.path.join(os.path.dirname(__file__), '..', 'server', 'pics', image_name)

        # Create a QLabel to display the image
        self.label_of_image = QLabel(self)

        # Load the image using QPixmap
        pixmap = QPixmap(image_path)

        # Set the pixmap to the QLabel
        self.label_of_image.setPixmap(pixmap)

        # Set the initial position of the QLabel
        self.label_of_image.move(480, 500)

        # Set the size of the QLabel
        new_size = QSize(450, 300)
        self.label_of_image.resize(new_size)
