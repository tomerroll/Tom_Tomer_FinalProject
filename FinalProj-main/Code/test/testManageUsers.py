import unittest
from unittest.mock import MagicMock, patch
from PyQt5.QtWidgets import QApplication
from manageUsersScreen import ManageUsersScreen


# Test the manage users screen
class TestManageUsers(unittest.TestCase):
    def setUp(self):
        self.app = QApplication([])
        self.client_mock = MagicMock()
        with patch('manageUsersScreen.ManageUsersScreen.receive_and_display_patients_data'):
            self.manage_users_screen = ManageUsersScreen(self.app, self.client_mock)

    def test_successful_save_clicked(self):
        # Set up the necessary mock values and behaviors
        self.manage_users_screen.patients_data = [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}]
        # Call the method we test
        self.manage_users_screen.save_clicked()
        # Assert the label text
        self.assertEqual(self.manage_users_screen.error_label.text(), 'Changes have been saved')

    def test_empty_field_save_clicked(self):
        # Set up the necessary mock values and behaviors
        self.manage_users_screen.patients_data = [{"id": 1, "name": ""}, {"id": 2, "name": "Jane"}]
        # Call the method we test
        self.manage_users_screen.save_clicked()
        # Assert the label text
        self.assertEqual(self.manage_users_screen.error_label.text(), 'At least one of the fields are empty')

    def test_id_exist_save_clicked(self):
        # Set up the necessary mock values and behaviors
        self.manage_users_screen.patients_data = [{"id": 1, "name": "John"}, {"id": 1, "name": "Jane"}]
        # Call the method we test
        self.manage_users_screen.save_clicked()
        # Assert the label text
        self.assertEqual(self.manage_users_screen.error_label.text(), 'At least one element has an ID that '
                                                                      'already exists')

    def tearDown(self):
        self.app.quit()


if __name__ == '__main__':
    unittest.main()
