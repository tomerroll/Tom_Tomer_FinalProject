import unittest
from unittest.mock import MagicMock
from PyQt5.QtWidgets import QApplication
from specificPatientScreen import SpecificPatientScreen


# Test the specific patient screen
class TestSpecificPatientScreenFirst(unittest.TestCase):
    def setUp(self):
        self.app = QApplication([])
        self.client_mock = MagicMock()
        self.patient_mock = MagicMock()
        self.specific_patient_screen = SpecificPatientScreen(self.app, self.client_mock, self.patient_mock)

    def test_start_clicked(self):
        # Call the method start clicked
        self.specific_patient_screen.start_clicked()
        # Assertions to check the behavior of the buttons and combo box after start clicked
        self.assertFalse(self.specific_patient_screen.start_button.isEnabled())
        self.assertFalse(self.specific_patient_screen.video_combo_box.isEnabled())
        self.assertFalse(self.specific_patient_screen.open_button.isEnabled())
        self.assertFalse(self.specific_patient_screen.back_button.isEnabled())
        self.assertTrue(self.specific_patient_screen.stop_button.isEnabled())

    def tearDown(self):
        self.app.quit()


if __name__ == '__main__':
    unittest.main()
