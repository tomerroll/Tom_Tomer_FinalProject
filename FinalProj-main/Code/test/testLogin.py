import unittest
from unittest.mock import MagicMock
from PyQt5.QtWidgets import QApplication
from loginScreen import LoginScreen
from menuScreen import MenuScreen


#Test the login screen
class TestLoginScreen(unittest.TestCase):
    def setUp(self):
        self.app = QApplication([])
        self.client_mock = MagicMock()
        self.login_screen = LoginScreen(self.app, self.client_mock)

    def test_login_successful(self):
        # Set up your test data
        self.login_screen.username_input.setText("valid_username")
        self.login_screen.password_input.setText("valid_password")

        # Mock the client's behavior
        self.client_mock.recv.return_value = b"True"  # Use bytes instead of a string

        # Trigger the login_clicked method
        self.login_screen.login_clicked()

        # The test asserts that the window_menu_screen is an instance of MenuScreen,
        # indicating that the login was successful.
        self.assertIsInstance(self.login_screen.window_menu_screen, MenuScreen)
        # It also asserts that the window_menu_screen is visible.
        self.assertTrue(self.login_screen.window_menu_screen.isVisible())

    def test_login_failed_already_logged_in(self):
        # Set up your test data
        self.login_screen.username_input.setText("valid_username")
        self.login_screen.password_input.setText("valid_password")

        # Mock the client's behavior
        self.client_mock.recv.return_value = b"alreadyLoggedIn"  # Use bytes instead of a string

        # Trigger the login_clicked method
        self.login_screen.login_clicked()

        # Assert that the error label = The user already logged in
        self.assertEqual(self.login_screen.error_label.text(), 'The user already logged in')

    def test_login_failed_empty_field(self):
        # Set up your test data
        self.login_screen.username_input.setText("")
        self.login_screen.password_input.setText("valid_password")

        # Trigger the login_clicked method
        self.login_screen.login_clicked()

        # Assert that the error label = At least one of the fields are empty
        self.assertEqual(self.login_screen.error_label.text(), 'At least one of the fields are empty')

    def test_login_failed_invalid_credentials(self):
        # Set up your test data
        self.login_screen.username_input.setText("invalid_username")
        self.login_screen.password_input.setText("invalid_password")

        # Mock the client's behavior
        self.client_mock.recv.return_value = b"False"  # Use bytes instead of a string

        # Trigger the login_clicked method
        self.login_screen.login_clicked()

        # Assert that the error label = invalid username or password
        self.assertEqual(self.login_screen.error_label.text(), 'Invalid username or password')

    def tearDown(self):
        self.app.quit()


if __name__ == '__main__':
    unittest.main()
