import csv
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QLabel, QWidget, QGridLayout, QCheckBox, QMessageBox
)
from PyQt5.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from controller_sim import DifferentialEqnThread, RealSystemThread, PINNModelThread
from simple_pid import PID
import subprocess

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PID Fluid Level Control")
        
        # Set window size directly
        self.setGeometry(100, 100, 1200, 800)  # Increased window size

        # Main Layout
        self.main_widget = QWidget()
        self.layout = QGridLayout(self.main_widget)

        # Top Left: Controls (Reduced size)
        self.controls_layout = QVBoxLayout()
        
        # Setpoint Height
        self.setpoint_label = QLabel("Set Point Height (m):")
        self.controls_layout.addWidget(self.setpoint_label)

        self.setpoint_input = QLineEdit("0.1")
        self.setpoint_input.setAlignment(Qt.AlignCenter)
        self.controls_layout.addWidget(self.setpoint_input)

        # PID Parameters: kp, ki, kd
        self.kp_label = QLabel("Proportional Gain (Kp):")
        self.controls_layout.addWidget(self.kp_label)

        self.kp_input = QLineEdit("30.0")
        self.kp_input.setAlignment(Qt.AlignCenter)
        self.controls_layout.addWidget(self.kp_input)

        self.ki_label = QLabel("Integral Gain (Ki):")
        self.controls_layout.addWidget(self.ki_label)

        self.ki_input = QLineEdit("1.0")
        self.ki_input.setAlignment(Qt.AlignCenter)
        self.controls_layout.addWidget(self.ki_input)

        self.kd_label = QLabel("Derivative Gain (Kd):")
        self.controls_layout.addWidget(self.kd_label)

        self.kd_input = QLineEdit("0.0")
        self.kd_input.setAlignment(Qt.AlignCenter)
        self.controls_layout.addWidget(self.kd_input)

        self.enter_button = QPushButton("Enter")
        self.enter_button.clicked.connect(self.update_parameters)
        self.controls_layout.addWidget(self.enter_button)

        self.start_button = QPushButton("Start All Models")
        self.start_button.clicked.connect(self.start_threads)
        self.controls_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop All Models")
        self.stop_button.clicked.connect(self.stop_threads)
        self.stop_button.setEnabled(False)
        self.controls_layout.addWidget(self.stop_button)

        controls_widget = QWidget()
        controls_widget.setLayout(self.controls_layout)
        self.layout.addWidget(controls_widget, 0, 0, 1, 1)  # Reduced size, change 1x1 span

        # Top Right: Graph 1 (Height vs Time)
        self.figure1, self.ax1 = plt.subplots(figsize=(8, 6))  # Increased figure size
        self.canvas1 = FigureCanvas(self.figure1)
        self.layout.addWidget(self.canvas1, 0, 1, 1, 1)  # This quadrant retains size, 1x1 span

        # Bottom Right: Graph 2 (Voltage vs Time)
        self.figure2, self.ax2 = plt.subplots(figsize=(8, 6))  # Increased figure size
        self.canvas2 = FigureCanvas(self.figure2)
        self.layout.addWidget(self.canvas2, 1, 1, 1, 1)  # This quadrant retains size, 1x1 span

        self.height_data = {"Differential": [], "Real System": [], "PINN": []}
        self.voltage_data = {"Differential": [], "Real System": [], "PINN": []}
        self.time_data = {"Differential": [], "Real System": [], "PINN": []}

        # Bottom Left: Checkboxes and Watermark
        self.bottom_left_widget = QWidget()
        self.bottom_left_layout = QVBoxLayout()

        # Checkboxes for plot visibility
        self.checkbox_diff_eqn = QCheckBox("Show Differential Eqn Plot")
        self.checkbox_diff_eqn.setChecked(True)
        self.bottom_left_layout.addWidget(self.checkbox_diff_eqn)

        self.checkbox_real_system = QCheckBox("Show Real System Plot")
        self.checkbox_real_system.setChecked(True)
        self.bottom_left_layout.addWidget(self.checkbox_real_system)

        self.checkbox_pinn = QCheckBox("Show PINN Model Plot")
        self.checkbox_pinn.setChecked(True)
        self.bottom_left_layout.addWidget(self.checkbox_pinn)

        self.bottom_left_layout.addSpacing(200)

        # Add Watermark to the Bottom Left Panel
        self.watermark_label = QLabel("Project: Physics-Informed Neural Networks\n"
                                      "Team: Shibin Fazil, Aftaab Ahamed, Karthik Manoranjan\n"
                                      "Faculty In Charge: Dr. Chandrashekhar Bestha")
        self.watermark_label.setAlignment(Qt.AlignCenter)
        self.watermark_label.setStyleSheet("color: gray; font-size: 13px; font-style: italic;")
        self.bottom_left_layout.addWidget(self.watermark_label)

        self.bottom_left_widget.setLayout(self.bottom_left_layout)
        self.layout.addWidget(self.bottom_left_widget, 1, 0, 1, 1)  # Occupies bottom-left quadrant

        # Set the layout
        self.main_widget.setLayout(self.layout)
        self.setCentralWidget(self.main_widget)

        # Initialize Threads
        self.diff_eqn_thread = DifferentialEqnThread(set_point_height=0.1, kp=30.0, ki=1.0, kd=0.0)
        self.real_system_thread = RealSystemThread(set_point_height=0.1, kp=30.0, ki=1.0, kd=0.0)
        self.pinn_thread = PINNModelThread(set_point_height=0.1, kp=30.0, ki=1.0, kd=0.0)

        # Connect Signals
        self.diff_eqn_thread.update_height.connect(lambda v, h, t: self.update_plot(v, h, t, "Differential"))
        self.real_system_thread.update_height.connect(lambda v, h, t: self.update_plot(v, h, t, "Real System"))
        self.pinn_thread.update_height.connect(lambda v, h, t: self.update_plot(v, h, t, "PINN"))

        # Connect error signals
        self.diff_eqn_thread.error_signal.connect(self.show_error_message)
        self.real_system_thread.error_signal.connect(self.show_error_message)
        self.pinn_thread.error_signal.connect(self.show_error_message)

    def show_error_message(self, error_message):
        """ Show the error message. """
        error_box = QMessageBox()
        error_box.setIcon(QMessageBox.Critical)
        error_box.setWindowTitle("Error")
        error_box.setText(error_message)
        error_box.setStandardButtons(QMessageBox.Ok)  # You can also add 'Retry' or other buttons if necessary
        error_box.exec_()  # Show the error box in a non-blocking way (does not block the execution)

    def update_parameters(self):
        """ Update both the setpoint and PID values after the Enter button is clicked. """
        try:
            # Retrieve the input values
            set_point_height = float(self.setpoint_input.text())
            kp = float(self.kp_input.text())
            ki = float(self.ki_input.text())
            kd = float(self.kd_input.text())
        except ValueError:
            # Show an error message box if input is invalid
            error_message = QMessageBox()
            error_message.setIcon(QMessageBox.Critical)
            error_message.setWindowTitle("Invalid Input")
            error_message.setText("Please enter valid numerical values for all fields.")
            error_message.exec_()  # Show the message box
            return  # Return to prevent further execution

        # Update set point height in all threads
        self.diff_eqn_thread.set_point_height = set_point_height
        self.real_system_thread.set_point_height = set_point_height
        self.pinn_thread.set_point_height = set_point_height

        # Update PID values in each thread
        self.diff_eqn_thread.pid.tunings = (kp, ki, kd)  # Update PID gains
        self.real_system_thread.pid.tunings = (kp, ki, kd)
        self.pinn_thread.pid.tunings = (kp, ki, kd)

        # Update setpoint for all threads' PID controllers
        self.diff_eqn_thread.pid.setpoint = set_point_height
        self.real_system_thread.pid.setpoint = set_point_height
        self.pinn_thread.pid.setpoint = set_point_height

    def start_threads(self):
        self.diff_eqn_thread.start()
        self.real_system_thread.start()
        self.pinn_thread.start()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_threads(self):
        self.diff_eqn_thread.stop()
        self.real_system_thread.stop()
        self.pinn_thread.stop()
        self.diff_eqn_thread.wait()
        self.real_system_thread.wait()
        self.pinn_thread.wait()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def update_plot(self, voltage, height, time_str, model_type):
        """ Update the plots with new data and write to CSV files. """
        self.height_data[model_type].append(height)
        self.voltage_data[model_type].append(voltage)
        self.time_data[model_type].append(time_str)

        # Save data to CSV
        self.save_data_to_csv(model_type)

        # Update Graph 1 (Height vs Time)
        self.ax1.clear()
        model = list(self.height_data.keys())
        # print(model)
        if self.checkbox_diff_eqn.isChecked():
            self.ax1.plot(self.time_data[model[0]], self.height_data[model[0]], label=f"{model[0]} Model", color="blue")
        if self.checkbox_real_system.isChecked():
            self.ax1.plot(self.time_data[model[1]], self.height_data[model[1]], label=f"{model[1]} Model", color="orange")
        if self.checkbox_pinn.isChecked():
            self.ax1.plot(self.time_data[model[2]], self.height_data[model[2]], label=f"{model[2]} Model", color="green")
        # for model in self.height_data.keys():
            # self.ax1.plot(self.time_data[model], self.height_data[model], label=f"{model} Model")

        # Configure X-axis
        self.configure_x_axis(self.ax1, self.time_data)
        self.ax1.set_xlabel("Time")
        self.ax1.set_ylabel("Height (m)")
        self.ax1.set_title("Fluid Level vs Time")
        self.ax1.legend()
        self.figure1.tight_layout()  # Adjust layout to prevent clipping
        self.canvas1.draw()

        # Update Graph 2 (Voltage vs Time)
        self.ax2.clear()
        if self.checkbox_diff_eqn.isChecked():
            self.ax2.plot(self.time_data[model[0]], self.voltage_data[model[0]], label=f"{model[0]} Model", color="blue")
        if self.checkbox_real_system.isChecked():
            self.ax2.plot(self.time_data[model[1]], self.voltage_data[model[1]], label=f"{model[1]} Model", color="orange")
        if self.checkbox_pinn.isChecked():
            self.ax2.plot(self.time_data[model[2]], self.voltage_data[model[2]], label=f"{model[2]} Model", color="green")
        # for model in self.voltage_data.keys():
        #     self.ax2.plot(self.time_data[model], self.voltage_data[model], label=f"{model} Model")

        # Configure X-axis
        self.configure_x_axis(self.ax2, self.time_data)
        self.ax2.set_xlabel("Time")
        self.ax2.set_ylabel("Voltage (V)")
        self.ax2.set_title("Voltage vs Time")
        self.ax2.legend()
        self.figure2.tight_layout()  # Adjust layout to prevent clipping
        self.canvas2.draw()

    def configure_x_axis(self, ax, time_data):
        """ Configures the X-axis to avoid overcrowding and keeps labels slanted. """
        max_ticks = 10  # Limit the number of ticks
        for model, time_values in time_data.items():
            if len(time_values) > max_ticks:
                displayed_ticks = time_values[::len(time_values) // max_ticks]
            else:
                displayed_ticks = time_values
        ax.set_xticks(displayed_ticks)
        ax.set_xticklabels(displayed_ticks, rotation=45, fontsize=8)

    def save_data_to_csv(self, model_type):
        """ Save data to separate CSV files for each model. """
        with open(f"{model_type}_data.csv", mode="a", newline='') as file:
            writer = csv.writer(file)
            # Write header if the file is empty
            if file.tell() == 0:
                writer.writerow(["Time", "Height (m)", "Voltage (V)"])

            writer.writerow([self.time_data[model_type][-1], self.height_data[model_type][-1], self.voltage_data[model_type][-1]])


# Main execution
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    script_path = "digital_model.py"
    # subprocess.Popen(
    #     [sys.executable, script_path],  # Launches the script with the same Python interpreter
    #     creationflags=subprocess.CREATE_NEW_CONSOLE  # Creates a new terminal window
    # )
    sys.exit(app.exec_())
