from PyQt5.QtCore import pyqtSignal, QThread
from PyQt5.QtWidgets import QMessageBox
import torch
import torch.nn as nn
from transfer_fn_model import TransferFnModel
import time
import math as m
from scipy.integrate import odeint
from simple_pid import PID
import serial
import serial.tools.list_ports
from keras import models
import numpy as np                 
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import joblib
from collections import deque
import control as ctl


class DifferentialEqnThread(QThread):
    update_height = pyqtSignal(float, float, float)  # Emit voltage, height, and time
    error_signal = pyqtSignal(str)  # Signal to pass the error message


    def __init__(self, set_point_height=0.025, kp=30.0, ki=1.0, kd=0.0, open_loop=False):
        super().__init__()
        self.stop_sim = False
        self.set_point_height = set_point_height
        self.pid = PID(kp, ki, kd, setpoint=self.set_point_height)
        self.pid.output_limits = (0, 12)  # Constrained PID output to 0-12 volts
        self.open_loop = open_loop

    def run(self):
        try:
            # def fp_model(h, t, v):
            #     fmin = 0.022
            #     fmax = 0.033
            #     f = fmax * v / 1023
            #     PI = m.pi
            #     d = 0.008
            #     r = 0.185
            #     h0 = 0.025        
            #     dhdt = (f - (0.6 * (PI * pow(d, 2)) * m.sqrt(2 * 9.81 * (h - h0)))) / (PI * (2 * r * h - pow(h, 2)))
            #     return dhdt
            def fp_model(h, t, v):
                """
                Tank flow process model.
                
                Parameters:
                h (float): Current height of the tank liquid (m).
                t (float): Current time (s).
                v_func (function): Interpolated voltage function.
                
                Returns:
                float: Rate of change of liquid height (dh/dt).
                """
                # Constants

                PI = m.pi
                d = 0.008  # Orifice diameter (m)
                r = 0.185  # Tank radius (m)
                h0 = 0.025  # Reference height (m)
                cf = 0.335 # Discharge coefficient

                # Interpolated voltage at time t
                
                # v = 12 * v / 1023

                # Flowrate calculation
                f = (4.042 * v - 2.866) / 1000000

                # Prevent negative or zero height difference
                h_effective = max(h - h0, 0)

                # Avoid division by zero in tank geometry calculation
                area = PI * (2 * r * h - h**2)
                if area <= 0:
                    return 0  # No change if area is invalid

                # Differential equation for height change
                dhdt = (f - (cf * (PI * d**2)/4 * m.sqrt(2 * 9.81 * h_effective))) / area
                return dhdt            

            h_current = 0.025

            while not self.stop_sim:
                st_time =time.time()
                time.sleep(1)
                if not self.open_loop:
                    self.pid.setpoint = self.set_point_height
                    v = self.pid(h_current)
                    del_t = time.time()-st_time
                    t = [0.0, del_t]
                    h = odeint(fp_model, h_current, t, args=(v,))
                    h_current = h[-1][0]

                else:
                    del_t = time.time()-st_time
                    v = self.set_point_height
                    t = [0.0, del_t]
                    h = odeint(fp_model, h_current, t, args=(v,))
                    h_current = h[-1][0]
                current_time = time.time()
                self.update_height.emit(v, h_current, current_time)  # Emit voltage, height, and time
        except Exception as e:
            print(f"Error in DifferentialEqnThread: {e}")
            # Emit error message to the main thread
            self.error_signal.emit(str(e))

    def stop(self):
        self.stop_sim = True


class RealSystemThread(QThread):
    update_height = pyqtSignal(float, float, float)  # Emit voltage, height, and time
    error_signal = pyqtSignal(str)  # Signal to pass the error message


    def __init__(self, set_point_height=0.025, kp=30.0, ki=1.0, kd=0.0, open_loop=False):
        super().__init__()
        self.stop_sim = False
        self.set_point_height = set_point_height
        self.pid = PID(kp, ki, kd, setpoint=self.set_point_height)
        self.pid.output_limits = (0, 12)  # Constrained PID output to 0-12 volts
        self.open_loop = open_loop


    def findSerialPort(self):
        """
        Find the serial port for an ESP32 device.
        Scans available serial ports and returns the device path for an ESP32 board,
        which typically uses Silicon Labs CP210x or CH340 USB-to-Serial converters.
        Returns:
            str: Device path of the ESP32 serial port if found, None otherwise
        """
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if 'Silicon Labs' in port.manufacturer or 'CP210x' in port.description:
                return port.device
            if 'CH340' in port.description:
                return port.device
            return None

    def run(self):
        try:
            SERIAL_PORT = self.findSerialPort()
            BAUD_RATE = 9600
            arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

            def read_from_arduino():
                if arduino.in_waiting > 0:
                    line = arduino.readline().decode('utf-8').strip()
                    return line
                return None

            while not self.stop_sim:
                time.sleep(1)
                data = read_from_arduino()
                if data:
                    try:
                        dt = data.split()[-1]
                        h = 0.1374 + 0.025  - float(dt)/100
                        
                        if not self.open_loop:
                            voltage = self.pid(h)
                        else:
                            voltage = self.set_point_height
                        if arduino.is_open:
                            # current_time = time.strftime("%H:%M:%S")
                            current_time = time.time()
                            pwm = int((voltage+3)*255/12)
                            arduino.write(f"{pwm}\n".encode())  # Send voltage to Arduino
                            self.update_height.emit(voltage, h, current_time)  # Emit voltage, height, and time
                    except Exception as e:
                        print(f"Invalid data from Arduino{e}")
        except Exception as e:
            print(f"Error in RealSystemThread: {e}")
            # Emit error message to the main thread
            self.error_signal.emit(str(e))

    def stop(self):
        self.stop_sim = True

class PINNModelThread(QThread):
    update_height = pyqtSignal(float, float, float)  # Emit voltage, height, and time
    error_signal = pyqtSignal(str)  # Signal to pass the error message

    def __init__(self, set_point_height=0.025, kp=30.0, ki=1.0, kd=0.0, open_loop=False):
        super().__init__()
        self.stop_sim = False
        self.set_point_height = set_point_height
        self.pid = PID(kp, ki, kd, setpoint=self.set_point_height)
        self.pid.output_limits = (0, 12)  # Constrain PID output to 0-12 volts
        self.open_loop = open_loop
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = self.load_pinn_model()
        self.sequence_length = 10
        self.input_buffer = deque(maxlen=self.sequence_length)
        self.model.to(self.device)
        
        # Initialize buffer with zeros
        for _ in range(self.sequence_length):
            self.input_buffer.append([0.025, 0.0])  # [height, voltage]

    def load_pinn_model(self):
        class PINN(nn.Module):
            def __init__(self):
                super(PINN, self).__init__()
                self.net = nn.Sequential(
                    nn.Linear(2, 64),
                    nn.Tanh(),
                    nn.Linear(64, 64),
                    nn.Tanh(),
                    nn.Linear(64, 1)
                )
            def forward(self, h_prev, u_current):
                inputs = torch.cat((h_prev, u_current), dim=1)
                return self.net(inputs)
        
        model = PINN()
        model.load_state_dict(torch.load("pinn_model.pth", map_location=self.device))
        model.eval()
        return model

    def preprocess_input(self, input_buffer):
        data = np.array(input_buffer, dtype=np.float32)
        return torch.tensor(data, device=self.device).unsqueeze(0)

    def run(self):
        try:
            predicted_height = 0.025  # Initial height
            while not self.stop_sim:
                time.sleep(1)
                current_time = time.time()
                
                if not self.open_loop:
                    new_voltage = self.pid(predicted_height)
                else:
                    new_voltage = self.set_point_height
                
                self.input_buffer.append([predicted_height, new_voltage])
                
                if len(self.input_buffer) == self.sequence_length:
                    input_sequence = self.preprocess_input(self.input_buffer)
                    h_prev = input_sequence[:, -1, 0].unsqueeze(-1)  # Take last height in sequence
                    u_current = input_sequence[:, -1, 1].unsqueeze(-1)  # Take last voltage in sequence
                    
                    with torch.no_grad():
                        predicted_scaled_height = self.model(h_prev, u_current).item()
                    predicted_height = max(0.0, predicted_scaled_height)  # Ensure non-negative height
                
                self.update_height.emit(new_voltage, predicted_height, current_time)
        except Exception as e:
            self.error_signal.emit(str(e))

    def stop(self):
        self.stop_sim = True



class TransferFunctionModelThread(QThread):
    update_height = pyqtSignal(float, float, float)  # Emit voltage, height, and time
    error_signal = pyqtSignal(str)  # Signal to pass the error message

    def __init__(self, set_point_height=0.025, kp=30.0, ki=1.0, kd=0.0, open_loop=False):
        super().__init__()
        self.stop_sim = False
        self.set_point_height = set_point_height
        self.pid = PID(kp, ki, kd, setpoint=self.set_point_height)
        self.pid.output_limits = (0, 12)  # Constrained PID output to 0-12 volts
        self.open_loop = open_loop

        # Define the tf model
        self.time_step = 1
        self.tf_model = TransferFnModel(initial_height=0.025, 
                                        voltage_input1=0, 
                                        voltage_input2=0, 
                                        total_time=1, 
                                        step_time=0,)

    def run(self):
        try:
            h_current = 0.025  # Example initial height
            prev_voltage = 0.0

            while not self.stop_sim:
                time.sleep(1)
                current_time = time.time()
                
                if not self.open_loop:
                    self.tf_model.initial_height = h_current                    
                    voltage = self.pid(h_current)  # PID output (voltage)
                    self.tf_model.total_time = self.time_step
                    self.tf_model.x0 = np.linalg.inv(self.tf_model.C) @ np.array([self.tf_model.initial_height])

                    self.tf_model.voltage_input2 = prev_voltage
                    self.tf_model.voltage_input1 = voltage

                    self.tf_model.time_vals = np.arange(0, self.time_step, self.tf_model.dt)
                    self.tf_model.u = np.ones_like(self.tf_model.time_vals) * self.tf_model.voltage_input1
                    self.tf_model.u[self.tf_model.time_vals >= self.tf_model.step_time] = self.tf_model.voltage_input2  # Step change

                    _, y_out = self.tf_model.simulate()
                    h_current = y_out if y_out.size == 1 else y_out[-1]
                    prev_voltage = voltage
                    self.time_step += 1

                else:
                    if self.time_step == 1:
                        self.tf_model.initial_height = h_current                    
                    voltage = self.set_point_height
                    self.tf_model.total_time = self.time_step
                    self.tf_model.x0 = np.linalg.inv(self.tf_model.C) @ np.array([self.tf_model.initial_height])
                    self.tf_model.time_vals = np.arange(0, self.time_step, self.tf_model.dt)
                    self.tf_model.u = np.ones_like(self.tf_model.time_vals) * self.tf_model.voltage_input1
                    self.tf_model.u[self.tf_model.time_vals >= self.tf_model.step_time] = self.tf_model.voltage_input2  # Step change

                    _, y_out = self.tf_model.simulate()
                    h_current = y_out if y_out.size == 1 else y_out[-1]
                    self.time_step += 1
                
                self.update_height.emit(voltage, h_current, current_time)  # Emit voltage, height, and time
        except Exception as e:
            print(f"Error in TransferFunctionModelThread: {e}")
            # Emit error message to the main thread
            self.error_signal.emit(str(e))

    def stop(self):
        self.stop_sim = True


class DataDrivenModelThread(QThread):
    update_height = pyqtSignal(float, float, float)  # Emit voltage, height, and time
    error_signal = pyqtSignal(str)  # Signal to pass the error message

    def __init__(self, set_point_height=0.025, kp=30.0, ki=1.0, kd=0.0, open_loop=False):
        super().__init__()
        self.stop_sim = False
        self.set_point_height = set_point_height
        self.pid = PID(kp, ki, kd, setpoint=self.set_point_height)
        self.pid.output_limits = (0, 12)  # Constrain PID output to 0-12 volts
        self.open_loop = open_loop
        self.model = models.load_model("trained_model.h5")  # Load trained model
        self.scaler = joblib.load("scaler.pkl")  # Load the fitted scaler
        self.sequence_length = 30
        self.input_buffer = deque(maxlen=self.sequence_length) # Sequence to hold 30 timesteps

        for _ in range(self.sequence_length):
            self.input_buffer.append([0.025, 0.0])  # [voltage, height]

    def preprocess_input(self, input_buffer, scaler):
        # Convert buffer to a NumPy array and scale the data
        data = np.array(input_buffer)
        scaled_data = scaler.transform(data)
        return scaled_data.reshape(1, self.sequence_length, 2)  # Reshape for LSTM input

    def run(self):
        try:
            predicted_height = 0.025  # Starting height
            initial_voltage = 0.0  # Starting voltage

            self.input_buffer = deque(maxlen=self.sequence_length) # Sequence to hold 30 timesteps
            for _ in range(self.sequence_length):
                self.input_buffer.append([0.025, 0.0])  # [voltage, height]

            while not self.stop_sim:
                time.sleep(1)
                current_time = time.time()

                if not self.open_loop:
                    new_voltage = self.pid(predicted_height) if len(self.input_buffer) == self.sequence_length else 0
                    new_height = predicted_height if len(self.input_buffer) == self.sequence_length else 0.025

                    self.input_buffer.append([new_voltage, new_height])

                    if len(self.input_buffer) == self.sequence_length:
                        # Preprocess the input
                        input_sequence = self.preprocess_input(self.input_buffer, self.scaler)

                        # Make a prediction
                        predicted_scaled_height = self.model.predict(input_sequence)[0][0]

                        # Inverse transform the predicted height
                        scaled_prediction = np.zeros((1, 2))  # Shape: (1, 2) for inverse transform
                        scaled_prediction[0, 1] = predicted_scaled_height
                        predicted_height = self.scaler.inverse_transform(scaled_prediction)[0, 1]

                else:
                    new_voltage = self.set_point_height
                    new_height = predicted_height if len(self.input_buffer) == self.sequence_length else 0.025

                    self.input_buffer.append([new_voltage, new_height])

                    if len(self.input_buffer) == self.sequence_length:
                        # Preprocess the input
                        input_sequence = self.preprocess_input(self.input_buffer, self.scaler)

                        # Make a prediction
                        predicted_scaled_height = self.model.predict(input_sequence)[0][0]

                        # Inverse transform the predicted height
                        scaled_prediction = np.zeros((1, 2))  # Shape: (1, 2) for inverse transform
                        scaled_prediction[0, 1] = predicted_scaled_height
                        predicted_height = self.scaler.inverse_transform(scaled_prediction)[0, 1]

                # Emit the updated values
                self.update_height.emit(new_voltage, predicted_height, current_time)
        except Exception as e:
            print(f"Error in DataDrivenModelThread: {e}")
            self.error_signal.emit(str(e))

    def stop(self):
        self.stop_sim = True