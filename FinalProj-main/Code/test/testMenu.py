import unittest
from unittest.mock import MagicMock, patch
from PyQt5.QtWidgets import QApplication
from menuScreen import MenuScreen
from signupScreen import SignupScreen
from manageUsersScreen import ManageUsersScreen


# Test the menu screen
class TestMenuScreen1(unittest.TestCase):
    def setUp(self):
        self.app = QApplication([])
        self.client_mock = MagicMock()
        self.menu_screen = MenuScreen(self.app, self.client_mock)

    def test_signup_clicked(self):
        # Trigger the signup_clicked method
        self.menu_screen.signup_clicked()
        # The test asserts that the window_signup_screen is an instance of SignupScreen
        self.assertIsInstance(self.menu_screen.window_signup_screen, SignupScreen)
        # It also asserts that the window_signup_screen is visible.
        self.assertTrue(self.menu_screen.window_signup_screen.isVisible())

    def test_panel_clicked_entry_denied(self):
        # Mock the client's behavior
        self.client_mock.recv.return_value = b"ENTRY_DENIED"  # Use bytes instead of a string
        # Trigger the panel_clicked method
        self.menu_screen.panel_clicked()
        # The test asserts that the window_panel_screen is not created
        self.assertIsNone(self.menu_screen.window_panel_screen)

    def tearDown(self):
        self.app.quit()


class TestMenuScreen2(unittest.TestCase):
    def setUp(self):
        self.app = QApplication([])
        self.client_mock = MagicMock()
        self.menu_screen = MenuScreen(self.app, self.client_mock)

    def test_panel_clicked_entry_allowed(self):
        with patch('panelScreen.PanelScreen.update_patients_combobox', return_value='mocked_result'), \
             patch('panelScreen.PanelScreen.initialize_patient_labels', return_value='mocked_result'), \
             patch('panelScreen.PanelScreen.update_button_states_in_gui', return_value='mocked_result'):
            self.client_mock.recv.return_value = b"ENTRY_ALLOWED"  # Use bytes instead of a string
            # Trigger the panel_clicked method
            self.menu_screen.panel_clicked()
            # The test asserts that the window_panel_screen is not created
            self.assertIsNotNone(self.menu_screen.window_panel_screen)

    def test_manage_users_clicked(self):
        # Mocking the behavior of receive_and_display_patients_data() inside manageUsersScreen.py
        with patch('manageUsersScreen.ManageUsersScreen.receive_and_display_patients_data',
                   return_value='mocked_result'):
            self.menu_screen.manage_users_clicked()
        # The test asserts that the window_manage_users_screen is an instance of SignupScreen
        self.assertIsInstance(self.menu_screen.window_manage_users_screen, ManageUsersScreen)
        # It also asserts that the window_manage_users_screen is visible.
        self.assertTrue(self.menu_screen.window_manage_users_screen.isVisible())

    def tearDown(self):
        self.app.quit()


if __name__ == '__main__':
    unittest.main()
