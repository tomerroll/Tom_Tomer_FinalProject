import numpy as np


# This Class is responsible for calculating the Heart Rate
class ExtractHeartRate:
    def __init__(self, green_channel):
        self.green_channel = green_channel
        self.heart_rate = 0
        self.frequency = 0

    def calc_hr_process(self, padded_list, sampling_rate, bin_plotter, counter):
        if self.green_channel is None:
            return 0, 0, "Face did not detected"

        # take interval of new values only
        new_list = list(padded_list[counter - 600:counter])

        # Calculate the average
        average_value = sum(new_list) / len(new_list)

        # Subtract average_value from each element in new_list using a loop
        for i in range(len(new_list)):
            new_list[i] -= average_value

        fourier = np.fft.fft(new_list)
        fourier_abs_values = np.absolute(fourier)
        bin_plotter.update_bin_plot(fourier_abs_values)
        length_of_padded_list = 600

        start_max_value = float('-inf')
        start_max_index = -1
        start_range = self.calculate_start_range(sampling_rate, length_of_padded_list)
        end_range = self.calculate_end_range(sampling_rate, length_of_padded_list)
        # Loop through the first half of the array to find max index of the max value
        for i in range(start_range, end_range):
            current_value = fourier_abs_values[i]
            # Update max_value and max_index if a greater value is found
            if current_value > start_max_value:
                start_max_value = current_value
                start_max_index = i
        self.frequency = (sampling_rate * start_max_index) / length_of_padded_list
        self.heart_rate = self.frequency * 60
        return self.heart_rate, self.frequency, None

    def calculate_start_range(self, sampling_rate, length_of_padded_list):
        freq = 60 / 60
        start_index = freq * length_of_padded_list / sampling_rate
        return round(start_index)

    def calculate_end_range(self, sampling_rate, length_of_padded_list):
        freq = 140 / 60
        end_index = freq * length_of_padded_list / sampling_rate
        return round(end_index)
