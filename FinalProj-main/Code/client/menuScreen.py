from PyQt5.QtWidgets import QLabel, QWidget, QPushButton, QMessageBox
from PyQt5.QtCore import QFile, QTextStream
from signupScreen import SignupScreen
from manageUsersScreen import ManageUsersScreen
from panelScreen import PanelScreen


# This Class is responsible for the Menu Screen and its functionality
class MenuScreen(QWidget):
    def __init__(self, app, client):
        super().__init__()
        self.app = app
        self.client = client
        self.window_signup_screen = None
        self.window_manage_users_screen = None
        self.window_panel_screen = None
        self.setWindowTitle('Monitoring Heart Rate Application')
        self.resize(1500, 800)  # Set the window size

        # Load and apply the CSS styles from the style.css file
        style_file = QFile('style.css')
        if style_file.open(QFile.ReadOnly | QFile.Text):
            style_stream = QTextStream(style_file)
            app.setStyleSheet(style_stream.readAll())

        # Add title label
        title_label = QLabel('Menu', self)
        title_label.move(660, 0)  # x,y coordinates value from top-left corner
        title_label.setObjectName('title_label')  # set object name for using it in the css file

        # Sign Up Button
        signup_button = QPushButton('Sign up', self)
        signup_button.move(640, 200)  # x,y coordinates value from top-left corner
        signup_button.clicked.connect(self.signup_clicked)

        # Manage users Button
        manage_users_button = QPushButton('Manage users', self)
        manage_users_button.move(640, 300)  # x,y coordinates value from top-left corner
        manage_users_button.clicked.connect(self.manage_users_clicked)

        # Patient Control Panel Button
        panel_button = QPushButton('Patient control panel', self)
        panel_button.move(640, 400)  # x,y coordinates value from top-left corner
        panel_button.clicked.connect(self.panel_clicked)

        # Logout Button
        logout_button = QPushButton('Logout', self)
        logout_button.move(640, 500)  # x,y coordinates value from top-left corner
        logout_button.clicked.connect(self.logout_clicked)

    # Triggered when signup button pressed
    def signup_clicked(self):
        self.window_signup_screen = SignupScreen(self.app, self.client)
        self.window_signup_screen.show()
        self.hide()

    # Triggered when signup button pressed
    def manage_users_clicked(self):
        self.window_manage_users_screen = ManageUsersScreen(self.app, self.client)
        self.window_manage_users_screen.show()
        self.hide()

    # Triggered when patient control panel button pressed
    def panel_clicked(self):
        # Send a request to the server to enter the panel screen
        self.client.send('ENTER_PANEL_SCREEN'.encode("utf-8"))
        response = self.client.recv(1024).decode("utf-8")
        # Entry is allowed, navigate to the PanelScreen page
        if response == 'ENTRY_ALLOWED':
            self.window_panel_screen = PanelScreen(self.app, self.client)
            self.window_panel_screen.show()
            self.hide()
        else:
            # Entry is denied, display an error message or handle it accordingly
            QMessageBox.warning(self, "Entry Denied", "Only one client can enter the PanelScreen page.")

    # Triggered when logout button pressed
    def logout_clicked(self):
        self.close()
