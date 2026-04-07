from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt


# This Class is responsible for creating the plotter of FFT data
class BINPlotter:
    def __init__(self, bin_window, layout_bin_window):
        self.bin_window = bin_window
        self.layout_bin_window = layout_bin_window

        # Create Matplotlib figure and canvas
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setParent(self.bin_window)
        # Add canvas to the layout only once
        self.layout_bin_window.addWidget(self.canvas)
        self.bin_window.setLayout(self.layout_bin_window)

    def update_bin_plot(self, image_vector):
        # Plot the data
        self.ax.clear()
        self.ax.plot(range(len(image_vector)-1), image_vector[1:len(image_vector)+1])
        self.ax.set_title('FFT Bin')
        # Redraw the canvas
        self.canvas.draw()
