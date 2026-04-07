import unittest
from unittest.mock import MagicMock
from extractHeartRate import ExtractHeartRate
import numpy as np


# Test the extract heart rate screen
class TestExtractHeartRate(unittest.TestCase):
    def setUp(self):
        self.green_channel_mock = MagicMock()
        self.extract_heart_rate = ExtractHeartRate(self.green_channel_mock)

    def test_calc_hr_process_no_face_detected(self):
        # Test when green_channel is None
        self.extract_heart_rate.green_channel = None
        padded_list = np.zeros(600)
        result = self.extract_heart_rate.calc_hr_process(padded_list, 30, 600, 600)
        self.assertEqual(result, (0, 0, "Face did not detected"))

    def test_calc_hr_process_valid_case(self):
        # Test a valid case with non-empty sample data
        padded_list = np.random.rand(600)
        counter = 600
        result = self.extract_heart_rate.calc_hr_process(padded_list, 30, MagicMock(), 600)
        self.assertIsInstance(result[0], float)
        self.assertIsInstance(result[1], float)
        self.assertIsNone(result[2])

    def test_calculate_start_range(self):
        # Test the calculate_start_range method
        result = self.extract_heart_rate.calculate_start_range(30, 600)
        self.assertIsInstance(result, int)

    def test_calculate_end_range(self):
        # Test the calculate_end_range method
        result = self.extract_heart_rate.calculate_end_range(30, 600)
        self.assertIsInstance(result, int)

    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
