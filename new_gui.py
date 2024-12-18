# main_gui.py

import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QPushButton,
                             QWidget, QLineEdit, QLabel)
from PyQt5.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from controller_sim import DifferentialEqnThread, RealSystemThread, PINNModelThread  # Import all three thread classes

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PID Fluid Level Control")
        self.setGeometry(100, 100, 800, 600)  # Set a fixed size for better visibility

        # Main Layout
        self.main_widget = QWidget()
        self.layout = QVBoxLayout(self.main_widget)

        # Set Point Input
        self.setpoint_label = QLabel("Set Point Height (m):")
        self.layout.addWidget(self.setpoint_label)

        self.setpoint_input = QLineEdit("0.1")  # Default setpoint height
        self.setpoint_input.setAlignment(Qt.AlignCenter)
        self.setpoint_input.textChanged.connect(self.update_setpoint)  # Connect input change to update setpoint
        self.layout.addWidget(self.setpoint_input)

        # Start and Stop Buttons
        self.start_button = QPushButton("Start All Models")
        self.start_button.clicked.connect(self.start_threads)
        self.layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop All Models")
        self.stop_button.clicked.connect(self.stop_threads)
        self.stop_button.setEnabled(False)  # Disable stop button initially
        self.layout.addWidget(self.stop_button)

        # Plotting Area
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)
        self.height_data = {"Differential": [], "Real System": [], "PINN": []}  # Store data for plotting

        # Configure the main window layout
        self.main_widget.setLayout(self.layout)
        self.setCentralWidget(self.main_widget)

        # Initialize Threads
        self.diff_eqn_thread = DifferentialEqnThread(set_point_height=0.1)
        self.real_system_thread = RealSystemThread(set_point_height=0.1)
        self.pinn_thread = PINNModelThread(set_point_height=0.1)
        # mode = input("input 0 for direct and 1 for model")
        
        # Connect Signals to Update Plot
        self.diff_eqn_thread.update_height.connect(lambda h: self.update_plot(h, "Differential"))
        self.real_system_thread.update_height.connect(lambda h: self.update_plot(h, "Real System"))
        self.pinn_thread.update_height.connect(lambda h: self.update_plot(h, "PINN"))

    def update_setpoint(self):
        """Update the setpoint in each thread based on GUI input."""
        try:
            set_point_height = float(self.setpoint_input.text())
        except ValueError:
            return  # Ignore invalid input

        # Update setpoint in each thread
        self.diff_eqn_thread.set_point_height = set_point_height
        self.real_system_thread.set_point_height = set_point_height
        self.pinn_thread.set_point_height = set_point_height

    def start_threads(self):
        """Start all model threads."""
        # Start all threads
        self.diff_eqn_thread.start()
        self.real_system_thread.start()
        self.pinn_thread.start()

        # Enable Stop button and disable Start button
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_threads(self):
        """Stop all model threads."""
        self.diff_eqn_thread.stop()
        self.real_system_thread.stop()
        self.pinn_thread.stop()

        # Wait for threads to finish
        self.diff_eqn_thread.wait()
        self.real_system_thread.wait()
        self.pinn_thread.wait()

        # Enable Start button and disable Stop button
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def update_plot(self, height, model_type):
        """Update the plot with the latest height data from each model type."""
        self.height_data[model_type].append(height)
        self.ax.clear()  # Clear previous plot

        # Plot data from each model with labels
        for model, data in self.height_data.items():
            self.ax.plot(data, label=f"{model} Model")

        self.ax.set_xlabel("Time Step")
        self.ax.set_ylabel("Height (m)")
        self.ax.legend()
        self.canvas.draw()  # Update the canvas with the new plot

# Main execution
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
