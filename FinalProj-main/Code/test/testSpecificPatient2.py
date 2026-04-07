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

    def test_video_feed_handling(self):
        # Test when displaying video feed from webcam
        self.specific_patient_screen.display_video_feed()
        self.assertTrue(self.specific_patient_screen.timer_for_update_video_feed.isActive())

        # Test when displaying video feed from a recorded video
        self.specific_patient_screen.display_video_feed("path/to/video/file.mp4")
        self.assertTrue(self.specific_patient_screen.timer_for_update_video_feed.isActive())

    def tearDown(self):
        self.app.quit()


class TestSpecificPatientScreenSecond(unittest.TestCase):
    def setUp(self):
        self.app = QApplication([])
        self.client_mock = MagicMock()
        self.patient_mock = MagicMock()
        self.specific_patient_screen = SpecificPatientScreen(self.app, self.client_mock, self.patient_mock)

    def test_combobox_changed(self):
        # Test behavior of buttons when "Video" is selected
        self.specific_patient_screen.combo_box_changed(0)
        self.assertTrue(self.specific_patient_screen.open_button.isEnabled())
        self.assertFalse(self.specific_patient_screen.start_button.isEnabled())
        # Test behavior of buttons when "Webcam" is selected
        self.specific_patient_screen.combo_box_changed(1)
        self.assertFalse(self.specific_patient_screen.open_button.isEnabled())
        self.assertTrue(self.specific_patient_screen.start_button.isEnabled())

    def tearDown(self):
        self.app.quit()


if __name__ == '__main__':
    unittest.main()
