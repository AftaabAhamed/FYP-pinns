# main_gui.py
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QPushButton,
                             QWidget, QLineEdit, QLabel)
from PyQt5.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from frst_principles_model import Controller  # Import the Controller class

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PID Fluid Level Control")
        self.setGeometry(100, 100, 800, 600)  # Ensure the GUI is visible with a set size

        # Set up Controller with an initial setpoint of 0.1 (this can be updated via GUI)
        self.controller_thread = None
        self.set_point_height = 0.1  # Default

        # Main Layout
        self.main_widget = QWidget()
        self.layout = QVBoxLayout(self.main_widget)

        # Set point input
        self.setpoint_label = QLabel("Set Point Height (m):")
        self.layout.addWidget(self.setpoint_label)

        self.setpoint_input = QLineEdit(str(self.set_point_height))
        self.setpoint_input.setAlignment(Qt.AlignCenter)  # Center align the input
        self.layout.addWidget(self.setpoint_input)

        # Start and Stop buttons
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_process)
        self.layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_process)
        self.stop_button.setEnabled(False)
        self.layout.addWidget(self.stop_button)

        # Plotting Area
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)
        self.height_data = []  # For graphing purposes

        # Configure the main window layout
        self.main_widget.setLayout(self.layout)
        self.setCentralWidget(self.main_widget)

    def start_process(self):
        """Start the controller simulation and update the graph."""
        try:
            self.set_point_height = float(self.setpoint_input.text())
        except ValueError:
            self.set_point_height = 0.1  # Fallback to default if input is invalid
            self.setpoint_input.setText("0.1")

        # Initialize and start the Controller thread
        self.controller_thread = Controller(set_point_height=self.set_point_height)
        self.controller_thread.update_height.connect(self.update_plot)
        self.controller_thread.start()

        # Enable Stop button and disable Start button
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_process(self):
        """Stop the controller simulation."""
        if self.controller_thread:
            self.controller_thread.stop()
            self.controller_thread.wait()  # Ensure the thread has finished
            self.controller_thread = None

        # Enable Start button and disable Stop button
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def update_plot(self, height):
        """Update the plot with the latest height data."""
        self.height_data.append(height)
        self.ax.clear()  # Clear previous plot
        self.ax.plot(self.height_data, label="FP Model")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Height (m)")
        self.ax.legend()
        self.canvas.draw()  # Update the canvas


# Main execution
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
