from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class BINPlotter:
    def __init__(self, parent, layout):
        self.fig = Figure(figsize=(5, 3))
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title("FFT Bins")
        self.ax.set_xlabel("Bin")
        self.ax.set_ylabel("Amplitude")
        layout.addWidget(self.canvas)

    def update_bin_plot(self, bins):
        self.ax.clear()
        self.ax.set_title("FFT Bins")
        self.ax.set_xlabel("Bin")
        self.ax.set_ylabel("Amplitude")
        self.ax.plot(bins)
        self.canvas.draw_idle()
