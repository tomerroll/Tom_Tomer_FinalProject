from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt


# This Class is responsible for creating the plotter of Heart Rate data
class HRPlotter:
    def __init__(self, hr_window, layout_hr_window):
        self.hr_window = hr_window
        self.layout_hr_window = layout_hr_window
        self.time_interval = 3
        self.total_time = 60
        self.num_updates = int(self.total_time / self.time_interval)
        self.heart_rate_values = []
        self.time_axis = []
        self.len_of_hr_values = 0
        self.elapsed_time = 0

        # Create Matplotlib figure and canvas
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setParent(self.hr_window)
        # Add canvas to the layout only once
        self.layout_hr_window.addWidget(self.canvas)
        self.hr_window.setLayout(self.layout_hr_window)

    def update_hr_plot(self, heart_rate):
        if heart_rate != 0:
            # Replace this with your actual heart rate variable or function to get heart rate
            current_heart_rate = heart_rate
            # Update data
            self.heart_rate_values.append(current_heart_rate)
            self.time_axis.append(self.elapsed_time)

            # Plot the data
            self.ax.clear()
            self.ax.plot(self.time_axis, self.heart_rate_values)
            self.ax.set_title('Heart Rate Monitor')
            # Redraw the canvas
            self.canvas.draw()

        self.elapsed_time += 3  # Because heart rate updating every 3 seconds
