import unittest
from unittest.mock import MagicMock
from PyQt5.QtWidgets import QApplication
from signupScreen import SignupScreen


# Test the signup screen
class TestSignupScreen(unittest.TestCase):
    def setUp(self):
        self.app = QApplication([])
        self.client_mock = MagicMock()
        self.signup_screen = SignupScreen(self.app, self.client_mock)

    def test_add_clicked_empty_fields(self):
        # Trigger the add_clicked method with empty fields
        self.signup_screen.add_clicked()
        self.signup_screen.id_input.setText("")
        # Assert that the error label is set to the correct message and is visible
        self.assertEqual(self.signup_screen.error_label.text(), 'At least one of the fields are empty')

    def test_add_clicked_id_exists(self):
        # Set up your test data
        self.signup_screen.id_input.setText("existing_id")
        self.signup_screen.firstName_input.setText("John")
        self.signup_screen.lastName_input.setText("Doe")
        # Mock the client's behavior
        self.client_mock.recv.return_value = b"True"  # Use bytes instead of a string
        # Trigger the add_clicked method
        self.signup_screen.add_clicked()
        # Assert that the error label is set to the correct message and is visible
        self.assertEqual(self.signup_screen.error_label.text(), 'The id already exist in the system')

    def test_add_clicked_success(self):
        # Set up your test data
        self.signup_screen.id_input.setText("new_id")
        self.signup_screen.firstName_input.setText("Jane")
        self.signup_screen.lastName_input.setText("Doe")
        # Mock the client's behavior
        self.client_mock.recv.return_value = b"False"  # Use bytes instead of a string
        # Trigger the add_clicked method
        self.signup_screen.add_clicked()
        # Assert that the error label is set to the correct message and is visible
        self.assertEqual(self.signup_screen.error_label.text(), 'Added new patient!')

    def tearDown(self):
        self.app.quit()


if __name__ == '__main__':
    unittest.main()
