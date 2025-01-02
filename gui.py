import csv
import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QLabel, QWidget, QGridLayout, QCheckBox, QMessageBox, QComboBox,
    QTableWidget, QTableWidgetItem
)
from PyQt5.QtCore import Qt, QThread
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from controller_sim import DifferentialEqnThread, RealSystemThread, PINNModelThread
from simple_pid import PID
import subprocess
from datetime import datetime
from block_diagram import ImageWithTextOverlay
from pid_tuning import PIDController
from model_params import ModelParameterCalculator

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Digital Twin Modelling")
        
        # Set window size directly
        self.setGeometry(100, 100, 1200, 800)  # Increased window size
        self.showMaximized()

        # Main Layout
        self.main_widget = QWidget()
        self.layout = QGridLayout(self.main_widget)

        # Sidebar Layout
        self.sidebar_layout = QVBoxLayout()

        # PID params
        self.kp = 30
        self.ki = 1
        self.kd = 0
        self.set_point_height = 0

        # Model Calculation Class init
        self.model_param = ModelParameterCalculator()

        # PID calculator init
        self.pid_calculator = PIDController()

        # Example Sidebar Components
        self.sidebar_label = QLabel("Navigation")
        self.sidebar_label.setAlignment(Qt.AlignCenter)
        self.sidebar_layout.addWidget(self.sidebar_label)

        self.sidebar_button1 = QPushButton("Open-loop")
        self.sidebar_layout.addWidget(self.sidebar_button1)
        self.sidebar_button1.clicked.connect(self.update_open_loop)

        self.sidebar_button2 = QPushButton("Model Select")
        self.sidebar_layout.addWidget(self.sidebar_button2)
        self.sidebar_button2.clicked.connect(self.model_select_push)
        self.sidebar_button2.setEnabled(False)

        self.sidebar_button3 = QPushButton("Controller Tuning")
        self.sidebar_layout.addWidget(self.sidebar_button3)
        self.sidebar_button3.clicked.connect(self.control_tune)
        self.sidebar_button3.setEnabled(False)

        self.sidebar_button4 = QPushButton("Close-loop")
        self.sidebar_layout.addWidget(self.sidebar_button4)
        self.sidebar_button4.clicked.connect(self.update_close_loop)
        self.sidebar_button4.setEnabled(False)

        # Add spacing to the bottom of the sidebar
        self.sidebar_layout.addStretch()

        self.sidebar_widget = QWidget()
        self.sidebar_widget.setLayout(self.sidebar_layout)
        self.sidebar_widget.setFixedWidth(250)

        # Add Sidebar to the layout
        self.layout.addWidget(self.sidebar_widget, 0, 0, 2, 1)  # Occupies the left-most column

        # Adjusted the remaining widgets to fit the grid
        # Top Left: Controls (Reduced size)
        self.controls_layout = QVBoxLayout()

        # Setpoint Height
        self.setpoint_label = QLabel("Set Voltage (V):")
        self.controls_layout.addWidget(self.setpoint_label)

        self.setpoint_input = QLineEdit("0")
        self.setpoint_input.setAlignment(Qt.AlignCenter)
        self.controls_layout.addWidget(self.setpoint_input)

        # PID Parameters: kp, ki, kd
        self.kp_label = QLabel("Proportional Gain (Kp):")
        self.controls_layout.addWidget(self.kp_label)

        self.kp_input = QLineEdit(f"{self.kp}")
        self.kp_input.setAlignment(Qt.AlignCenter)
        self.controls_layout.addWidget(self.kp_input)

        self.ki_label = QLabel("Integral Gain (Ki):")
        self.controls_layout.addWidget(self.ki_label)

        self.ki_input = QLineEdit(f"{self.ki}")
        self.ki_input.setAlignment(Qt.AlignCenter)
        self.controls_layout.addWidget(self.ki_input)

        self.kd_label = QLabel("Derivative Gain (Kd):")
        self.controls_layout.addWidget(self.kd_label)

        self.kd_input = QLineEdit(f"{self.kd}")
        self.kd_input.setAlignment(Qt.AlignCenter)
        self.controls_layout.addWidget(self.kd_input)

        self.kp_label.hide()
        self.kp_input.hide()
        self.ki_label.hide()
        self.ki_input.hide()
        self.kd_label.hide()
        self.kd_input.hide()

        self.enter_button = QPushButton("Enter")
        self.enter_button.clicked.connect(self.update_parameters)
        self.controls_layout.addWidget(self.enter_button)

        # self.controls_layout.addSpacing(150)

        self.start_button = QPushButton("Start All Models")
        self.start_button.clicked.connect(self.start_threads)
        self.controls_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop All Models")
        self.stop_button.clicked.connect(self.stop_threads)
        self.stop_button.setEnabled(False)
        self.controls_layout.addWidget(self.stop_button)

        self.select_model = QComboBox()
        self.select_model.addItem("Differential Model")
        self.select_model.addItem("Real System Model")
        self.select_model.addItem("PINN Model")
        self.controls_layout.addWidget(self.select_model)
        self.select_model.hide()

        self.select_model_confirm = QPushButton("Enter")
        self.select_model_confirm.clicked.connect(self.confirm_model)
        self.controls_layout.addWidget(self.select_model_confirm)
        self.select_model_confirm.hide()

        self.tableLable = QLabel("Model Parameters")
        self.controls_layout.addWidget(self.tableLable)
        self.tableWidget = QTableWidget()
        self.tableWidget.setRowCount(3)
        self.tableWidget.setColumnCount(2)
        self.tableWidget.setHorizontalHeaderItem(0,QTableWidgetItem("Params"))
        self.tableWidget.setHorizontalHeaderItem(1,QTableWidgetItem("Value"))
        self.tableWidget.setItem(0,0,QTableWidgetItem("kp"))
        self.tableWidget.setItem(0,1,QTableWidgetItem("0"))
        self.tableWidget.setItem(1,0,QTableWidgetItem("tau"))
        self.tableWidget.setItem(1,1,QTableWidgetItem("0"))
        self.tableWidget.setItem(2,0,QTableWidgetItem("theta"))
        self.tableWidget.setItem(2,1,QTableWidgetItem("0"))
        self.controls_layout.addWidget(self.tableWidget)
        self.tableLable.hide()
        self.tableWidget.hide()

        self.tune_label = QLabel("Select Tuning Method")
        self.controls_layout.addWidget(self.tune_label)
        self.tune_label.hide()
        self.select_tuning = QComboBox()
        self.select_tuning.addItem("Fine Tune")
        self.select_tuning.addItem("Detune")
        self.select_tuning.currentTextChanged.connect(self.tuning_param_change)
        self.controls_layout.addWidget(self.select_tuning)
        self.select_tuning.hide()

        self.tuning_param_label = QLabel("Input alpha value")
        self.tuning_param_input = QLineEdit("0")
        self.controls_layout.addWidget(self.tuning_param_label)
        self.controls_layout.addWidget(self.tuning_param_input)
        self.tuning_param_input.hide()
        self.tuning_param_label.hide()

        self.confirm_tuning_param = QPushButton("Enter")
        self.confirm_tuning_param.clicked.connect(self.confirm_tuning)
        self.controls_layout.addWidget(self.confirm_tuning_param)
        self.confirm_tuning_param.hide()

        self.tuningTableLable = QLabel("Tuning Params")
        self.controls_layout.addWidget(self.tuningTableLable)
        self.tuningTableWidget = QTableWidget()
        self.tuningTableWidget.setRowCount(3)
        self.tuningTableWidget.setColumnCount(2)
        self.tuningTableWidget.setHorizontalHeaderItem(0,QTableWidgetItem("Params"))
        self.tuningTableWidget.setHorizontalHeaderItem(1,QTableWidgetItem("Value"))
        self.tuningTableWidget.setItem(0,0,QTableWidgetItem("kc"))
        self.tuningTableWidget.setItem(0,1,QTableWidgetItem("0"))
        self.tuningTableWidget.setItem(1,0,QTableWidgetItem("ki"))
        self.tuningTableWidget.setItem(1,1,QTableWidgetItem("0"))
        self.tuningTableWidget.setItem(2,0,QTableWidgetItem("kd"))
        self.tuningTableWidget.setItem(2,1,QTableWidgetItem("0"))
        self.controls_layout.addWidget(self.tuningTableWidget)
        self.tuningTableLable.hide()
        self.tuningTableWidget.hide()

        self.controls_layout.addStretch()
        controls_widget = QWidget()
        controls_widget.setLayout(self.controls_layout)
        self.layout.addWidget(controls_widget, 0, 1, 1, 1)  # Reduced size, change 1x1 span

        # Top Right: Graph 1 (Height vs Time)
        self.figure1, self.ax1 = plt.subplots(figsize=(8, 6))  # Increased figure size
        self.canvas1 = FigureCanvas(self.figure1)
        self.layout.addWidget(self.canvas1, 0, 2, 1, 1)  # This quadrant retains size, 1x1 span

        # Bottom Right: Graph 2 (Voltage vs Time)
        self.figure2, self.ax2 = plt.subplots(figsize=(8, 6))  # Increased figure size
        self.canvas2 = FigureCanvas(self.figure2)
        self.layout.addWidget(self.canvas2, 1, 2, 1, 1)  # This quadrant retains size, 1x1 span

        self.height_data = {"Differential": [], "Real System": [], "PINN": []}
        self.voltage_data = {"Differential": [], "Real System": [], "PINN": []}
        self.time_data = {"Differential": [], "Real System": [], "PINN": []}

        # Bottom Left: Checkboxes and Watermark
        self.bottom_left_widget = QWidget()
        self.bottom_left_layout = QVBoxLayout()

        # self.bottom_left_layout.addSpacing(100)

        # Checkboxes for plot visibility
        self.checkbox_diff_eqn = QCheckBox("Differential Eqn Plot")
        self.checkbox_diff_eqn.setChecked(True)
        self.sidebar_layout.addWidget(self.checkbox_diff_eqn)

        self.checkbox_real_system = QCheckBox("Real System Plot")
        self.checkbox_real_system.setChecked(True)
        self.sidebar_layout.addWidget(self.checkbox_real_system)

        self.checkbox_pinn = QCheckBox("PINN Model Plot")
        self.checkbox_pinn.setChecked(True)
        self.sidebar_layout.addWidget(self.checkbox_pinn)

        # self.bottom_left_layout.addSpacing(100)

        # self.bottom_left_layout.addStretch()

        self.bottom_left_widget.setLayout(self.bottom_left_layout)
        self.layout.addWidget(self.bottom_left_widget, 1, 1, 1, 1)  # Occupies bottom-left quadrant

        # Set the layout
        self.main_widget.setLayout(self.layout)
        self.setCentralWidget(self.main_widget)

        # Block Diagram
        self.image_path = "image_ol.png"  # Replace with your image path
        self.text_data_OL = {
            "height": (f"y: {1}", (630, 280)),
            "voltage": (f"u: {self.set_point_height}", (210, 305)),
            "flow_rate": ("Qin: 13.5", (405, 280))
        }

        self.text_data_CL = {
            "kp": (f"Kp: {self.kp}", (325, 225)),
            "ki": (f"Ki: {self.ki}", (325, 255)),
            "kd": (f"Kd: {self.kd}", (325, 285)),
            "set_point": (f"SP: {self.set_point_height}", (163, 240)),
            "error": ("Error: 0.5", (245, 185)),
            "height": ("y: 2.0", (630, 180)),
            "voltage": ("u: 5.0", (383, 210)),
            "flow_rate": ("Qin: 13.5", (445, 170))
        }

        self.block_diagram = ImageWithTextOverlay(self.image_path, self.text_data_OL)
        self.bottom_left_layout.addWidget(self.block_diagram)

        # # Add Watermark to the Bottom Left Panel
        # self.watermark_label = QLabel("Project: Physics-Informed Neural Networks\n"
        #                               "Team: Shibin Fazil, Aftaab Ahamed, Karthik Manoranjan\n"
        #                               "Faculty In Charge: Dr. Chandrashekhar Bestha")
        # self.watermark_label.setAlignment(Qt.AlignCenter)
        # self.watermark_label.setStyleSheet("color: gray; font-size: 13px; font-style: italic;")
        # self.bottom_left_layout.addWidget(self.watermark_label)

        # Initialize Threads
        self.diff_eqn_thread = DifferentialEqnThread(set_point_height=0.0, kp=30.0, ki=1.0, kd=0.0, open_loop=True)
        self.real_system_thread = RealSystemThread(set_point_height=0.0, kp=30.0, ki=1.0, kd=0.0, open_loop=True)
        self.pinn_thread = PINNModelThread(set_point_height=0.0, kp=30.0, ki=1.0, kd=0.0, open_loop=True)

        # Connect Signals
        self.diff_eqn_thread.update_height.connect(lambda v, h, t: self.update_plot(v, h, t, "Differential"))
        self.real_system_thread.update_height.connect(lambda v, h, t: self.update_plot(v, h, t, "Real System"))
        self.pinn_thread.update_height.connect(lambda v, h, t: self.update_plot(v, h, t, "PINN"))

        # Connect error signals
        self.diff_eqn_thread.error_signal.connect(self.show_error_message)
        self.real_system_thread.error_signal.connect(self.show_error_message)
        self.pinn_thread.error_signal.connect(self.show_error_message)

        # Variable to check open or close loop for file saving
        self.curr_loop = "OL"
        self.save_time = None
        self.modelCheck = False

    def control_tune(self):
        self.setpoint_label.hide()
        self.select_model.hide()
        self.select_tuning.show()
        self.tune_label.show()
        self.tuning_param_label.show()
        self.tuning_param_input.show()
        self.confirm_tuning_param.show()
        self.select_model_confirm.hide()
        self.tableLable.hide()
        self.tableWidget.hide()

    def tuning_param_change(self):
        if self.select_tuning.currentText() == "Fine Tune":
            self.tuning_param_label.setText("Input alpha value")
        else:
            self.tuning_param_label.setText("Input F value")
        
    def confirm_tuning(self):
        self.pid_calculator.calculate(method=self.select_tuning.currentText(), val=self.tuning_param_input.text())
        self.tuningTableLable.show()
        self.tuningTableWidget.show()
        kc, ki, kd = self.pid_calculator.kc, self.pid_calculator.ki, self.pid_calculator.kd
        self.tuningTableWidget.setItem(0,1,QTableWidgetItem(f"{kc}"))
        self.tuningTableWidget.setItem(1,1,QTableWidgetItem(f"{ki}"))
        self.tuningTableWidget.setItem(2,1,QTableWidgetItem(f"{kd}"))
        self.kp_input.setText(f"{kc}")
        self.ki_input.setText(f"{ki}")
        self.kd_input.setText(f"{kd}")
        self.sidebar_button3.setEnabled(False)
        self.sidebar_button4.setEnabled(True)

    def model_select_push(self):
        self.setpoint_label.setText("Select the Model")
        self.setpoint_input.hide()
        self.start_button.hide()
        self.stop_button.hide()
        self.enter_button.hide()
        self.sidebar_button1.setEnabled(False)
        self.checkbox_diff_eqn.hide()
        self.checkbox_real_system.hide()
        self.checkbox_pinn.hide()
        self.select_model.show()
        self.select_model_confirm.show()
        self.block_diagram.hide()

    def confirm_model(self):
        keys = ["Differential_data", "Real System_data", "PINN_data"]
        if self.select_model.currentText() == "Differential Model":
            path = f"{keys[0]}_OL_{self.save_time}.csv"
        elif self.select_model.currentText() == "Real System Model":
            path = f"{keys[1]}_OL_{self.save_time}.csv"
        else:
            path = f"{keys[2]}_OL_{self.save_time}.csv"

        self.model_param.load_csv(path)
        self.model_param.calculate_parameters()
        kp, tau, theta = self.model_param.get_parameters()
        self.tableLable.show()
        self.tableWidget.show()
        self.tableWidget.setItem(0,1,QTableWidgetItem(f"{kp}"))
        self.tableWidget.setItem(1,1,QTableWidgetItem(f"{tau}"))
        self.tableWidget.setItem(2,1,QTableWidgetItem(f"{theta}"))
        self.pid_calculator.set_parameters(kp, tau, theta)
        self.sidebar_button3.setEnabled(True)
        self.sidebar_button2.setEnabled(False)

    def update_open_loop(self):
        """Update mode to Open-loop."""
        self.setpoint_label.setText("Set Voltage (V):")
        self.kp_label.hide()
        self.kp_input.hide()
        self.ki_label.hide()
        self.ki_input.hide()
        self.kd_label.hide()
        self.kd_input.hide()
        self.diff_eqn_thread.open_loop = True
        self.real_system_thread.open_loop = True
        self.pinn_thread.open_loop = True
        self.modelCheck = False
        self.block_diagram.image_path = "image_ol.png"
        self.block_diagram.text_data = self.text_data_OL
        self.block_diagram.update_image()

    def update_close_loop(self):
        """Update mode to Close-loop"""
        self.setpoint_label.show()
        self.setpoint_label.setText("Set Point Height (m):")
        self.setpoint_input.show()
        self.start_button.show()
        self.stop_button.show()
        self.enter_button.show()
        self.kp_label.show()
        self.kp_input.show()
        self.ki_label.show()
        self.ki_input.show()
        self.kd_label.show()
        self.kd_input.show()
        self.select_tuning.hide()
        self.tune_label.hide()
        self.confirm_tuning_param.hide()
        self.tuning_param_label.hide()
        self.tuning_param_input.hide()
        self.tuningTableLable.hide()
        self.tuningTableWidget.hide()
        self.checkbox_diff_eqn.show()
        self.checkbox_real_system.show()
        self.checkbox_pinn.show()
        self.diff_eqn_thread.open_loop = False
        self.real_system_thread.open_loop = False
        self.pinn_thread.open_loop = False

        self.block_diagram.image_path = "image.png"
        kc, ki, kd = self.pid_calculator.kc, self.pid_calculator.ki, self.pid_calculator.kd
        self.text_data_CL["set_point"] = (f"SP: {self.setpoint_input.text()}", (163, 240))
        self.text_data_CL["kp"] = (f"Kp: {kc}", (325, 225))
        self.text_data_CL["ki"] = (f"Ki: {ki}", (325, 255))
        self.text_data_CL["kd"] = (f"Kd: {kd}", (325, 285))
        self.block_diagram.text_data = self.text_data_CL

        self.block_diagram.update_image()
        self.block_diagram.show()

        self.curr_loop = "CL"
        self.modelCheck = True

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
            self.kp = float(self.kp_input.text())
            self.ki = float(self.ki_input.text())
            self.kd = float(self.kd_input.text())
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
        self.text_data_OL["voltage"] = (f"u: {set_point_height}", (210, 305))
        self.text_data_CL["set_point"] = (f"SP: {set_point_height}", (163, 240))

        # Update PID values in each thread
        self.diff_eqn_thread.pid.tunings = (self.kp, self.ki, self.kd)  # Update PID gains
        self.real_system_thread.pid.tunings = (self.kp, self.ki, self.kd)
        self.pinn_thread.pid.tunings = (self.kp, self.ki, self.kd)

        self.text_data_CL["kp"] = (f"Kp: {self.kp}", (325, 225))
        self.text_data_CL["ki"] = (f"Ki: {self.ki}", (325, 255))
        self.text_data_CL["kd"] = (f"Kd: {self.kd}", (325, 285))

        # Update setpoint for all threads' PID controllers
        self.diff_eqn_thread.pid.setpoint = set_point_height
        self.real_system_thread.pid.setpoint = set_point_height
        self.pinn_thread.pid.setpoint = set_point_height

        if self.curr_loop == "OL":
            self.block_diagram.params(self.text_data_OL)
        elif self.curr_loop == "CL":
            self.block_diagram.params(self.text_data_CL)

    def start_threads(self):
        self.height_data = {"Differential": [], "Real System": [], "PINN": []}
        self.voltage_data = {"Differential": [], "Real System": [], "PINN": []}
        self.time_data = {"Differential": [], "Real System": [], "PINN": []}
        self.ax1.clear()
        self.ax2.clear()

        # Connect signals and slots
        self.diff_eqn_thread.start()
        self.real_system_thread.start()
        self.pinn_thread.start()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_threads(self):
        self.diff_eqn_thread.terminate()
        self.real_system_thread.terminate()
        self.pinn_thread.terminate()
        self.diff_eqn_thread.wait()
        self.real_system_thread.wait()
        self.pinn_thread.wait()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

        if not self.modelCheck:
            self.sidebar_button2.setEnabled(True)
            self.sidebar_button1.setEnabled(False)
        else:
            self.sidebar_button1.setEnabled(True)
            self.sidebar_button4.setEnabled(False)

        keys = ["Differential_data", "Real System_data", "PINN_data"]
        now = datetime.now()
        self.save_time = now.strftime("%H-%M-%S")
        
        for key in keys:
            try:
                os.rename(f"{key}.csv", f"{key}_{self.curr_loop}_{self.save_time}.csv")
            except Exception as e:
                print(e)

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
        self.ax1.set_ylabel("y")
        self.ax1.set_title("Height (m) vs Time")
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

        # Update the block diagram live
        if self.curr_loop == "CL":
            self.text_data_CL["height"] = (f"y: {round(height,2)}", (630, 180))
            self.text_data_CL["volatge"] = (f"u: {round(voltage,2)}", (383, 210))
            self.text_data_CL["error"] = (f"Error: {round(float(self.setpoint_input.text())-height,2)}", (245, 185))
            self.text_data_CL["flow_rate"] = (f"Qin: {round(height*10,2)}", (445, 170))
            self.block_diagram.params(self.text_data_CL)
        else:
            self.text_data_OL["height"] = (f"y: {round(height,2)}", (630, 280))
            self.text_data_OL["voltage"] = (f"u: {self.setpoint_input.text()}", (210, 305))
            self.text_data_OL["flow_rate"] = (f"Qin: {round(height*10,2)}", (405, 280))
            self.block_diagram.params(self.text_data_OL)

        self.configure_x_axis(self.ax2, self.time_data)
        self.ax2.set_xlabel("Time")
        self.ax2.set_ylabel("u")
        self.ax2.set_title("Voltage (V) vs Time")
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
