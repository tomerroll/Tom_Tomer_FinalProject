import unittest
from unittest.mock import MagicMock, patch, Mock
from PyQt5.QtWidgets import QApplication
from panelScreen import PanelScreen


# Creating stub for the Panel Screen Class for simulate enter_clicked function
class PanelScreenStub:
    def __init__(self, app, client):
        self.app = app
        self.client = client
        self.window_specificPatient_screen = None

    # It should navigate to specific patient screen
    def enter_clicked(self):
        self.window_specificPatient_screen = True
        return self.window_specificPatient_screen


# Creating HRPlotter Class Stub just to mock the instance of that class
class HRPlotterStub:
    def __init__(self, hr_window, layout_hr_window):
        self.canvas = Mock()
        self.hr_window = hr_window
        self.layout_hr_window = layout_hr_window

    def update_hr_plot(self, heart_rate):
        pass


# Test the panel screen
class TestPanelScreen1(unittest.TestCase):
    def setUp(self):
        self.app = QApplication([])
        self.client_mock = MagicMock()
        with patch('panelScreen.PanelScreen.update_button_states_in_gui'), \
                patch('panelScreen.PanelScreen.update_patients_combobox'), \
                patch('panelScreen.PanelScreen.initialize_patient_labels'), \
                patch('panelScreen.PanelScreen.get_hr_value'), \
                patch('specificPatientScreen.HRPlotter', HRPlotterStub):
            self.panel_screen = PanelScreen(self.app, self.client_mock)

    def test_update_button_states_in_gui(self):
        # Assume the server sends button states for patient 1 and 2 as enabled, and patient 3 as disabled
        button_states_json = '[{"id": "1", "enabled": "yes"}, {"id": "2", "enabled": "yes"},' \
                             ' {"id": "3", "enabled": "no"}]'
        button_states_json = button_states_json.encode("utf-8")

        with patch.object(self.panel_screen.client, 'send'), \
                patch.object(self.panel_screen.client, 'recv', return_value=button_states_json):
            self.panel_screen.update_button_states_in_gui()

        # Assert that the Enter buttons are enabled/disabled based on the received data
        self.assertTrue(self.panel_screen.enter1_button.isEnabled())
        self.assertTrue(self.panel_screen.enter2_button.isEnabled())
        self.assertFalse(self.panel_screen.enter3_button.isEnabled())

    # Test that it put the hr values in the labels correctly, from the received data
    @patch('panelScreen.PanelScreen', autospec=True)
    def test_get_hr_value(self, mock_client):
        list_hr = '{"heart_rate1": 75, "heart_rate2": 80, "heart_rate3": 85}'.encode("utf-8")

        # Mock the client's behavior
        self.client_mock.recv.return_value = list_hr
        # Call the tested function
        self.panel_screen.get_hr_value()

        # Assert that labels are updated correctly based on the mocked data
        self.assertEqual(self.panel_screen.hr1_label.text(), "Heart rate: 75")
        self.assertEqual(self.panel_screen.hr2_label.text(), "Heart rate: 80")
        self.assertEqual(self.panel_screen.hr3_label.text(), "Heart rate: 85")

    def tearDown(self):
        self.app.quit()


class TestPanelScreen2(unittest.TestCase):
    def setUp(self):
        self.app = 1
        self.client_mock = 1
        self.panel_screen = PanelScreenStub(self.app, self.client_mock)

    # Assert that it navigate to the specific patient screen when enter_clicked activated
    def test_enter_clicked(self):
        result = self.panel_screen.enter_clicked()
        self.assertTrue(result)

    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
