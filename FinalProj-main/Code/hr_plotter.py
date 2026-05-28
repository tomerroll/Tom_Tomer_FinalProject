from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class HRPlotter:
    def __init__(self, parent, layout):
        self.hr_values = []
        self.fig = Figure(figsize=(5, 3))
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title("Heart Rate")
        self.ax.set_xlabel("Update")
        self.ax.set_ylabel("BPM")
        layout.addWidget(self.canvas)

    def update_hr_plot(self, hr):
        self.hr_values.append(float(hr))
        self.ax.clear()
        self.ax.set_title("Heart Rate")
        self.ax.set_xlabel("Update")
        self.ax.set_ylabel("BPM")
        self.ax.plot(self.hr_values)
        self.canvas.draw_idle()
