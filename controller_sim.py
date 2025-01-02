from PyQt5.QtCore import pyqtSignal, QThread
from PyQt5.QtWidgets import QMessageBox
import time
import math as m
from scipy.integrate import odeint
from simple_pid import PID
import serial


class DifferentialEqnThread(QThread):
    update_height = pyqtSignal(float, float, str)  # Emit voltage, height, and time
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
            def fp_model(h, t, v):
                fmin = 0.022
                fmax = 0.033
                f = fmax * v / 1023
                PI = m.pi
                d = 0.008
                r = 0.185
                h0 = 0.025        
                dhdt = (f - (0.6 * (PI * pow(d, 2)) * m.sqrt(2 * 9.81 * (h - h0)))) / (PI * (2 * r * h - pow(h, 2)))
                return dhdt

            h_current = 0.025

            while not self.stop_sim:
                time.sleep(1)
                if not self.open_loop:
                    self.pid.setpoint = self.set_point_height
                    v = self.pid(h_current)
                    t = [0.0, 1.0]
                    h = odeint(fp_model, h_current, t, args=(v,))
                    h_current = h[-1][0]
                else:
                    h = odeint(fp_model, h_current, t, args=(self.set_point_height,))
                    h_current = h[-1][0]
                    v = self.set_point_height
                current_time = time.strftime("%H:%M:%S")
                self.update_height.emit(v, h_current, current_time)  # Emit voltage, height, and time
        except Exception as e:
            print(f"Error in DifferentialEqnThread: {e}")
            # Emit error message to the main thread
            self.error_signal.emit(str(e))

    def stop(self):
        self.stop_sim = True


class RealSystemThread(QThread):
    update_height = pyqtSignal(float, float, str)  # Emit voltage, height, and time
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
            SERIAL_PORT = '/dev/ttyUSB0'
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
                        h = 0.18 - float(data)
                        current_time = time.strftime("%H:%M:%S")
                        if not self.open_loop:
                            voltage = self.pid(h)
                        else:
                            voltage = self.set_point_height
                        if arduino.is_open:
                            arduino.write(f"{voltage}\n".encode())  # Send voltage to Arduino
                        self.update_height.emit(voltage, h, current_time)  # Emit voltage, height, and time
                    except ValueError:
                        print("Invalid data from Arduino")
        except Exception as e:
            print(f"Error in RealSystemThread: {e}")
            # Emit error message to the main thread
            self.error_signal.emit(str(e))

    def stop(self):
        self.stop_sim = True


class PINNModelThread(QThread):
    update_height = pyqtSignal(float, float, str)  # Emit voltage, height, and time
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
            h_current = 0.025  # Example initial height

            while not self.stop_sim:
                time.sleep(1)
                current_time = time.strftime("%H:%M:%S")
                if not self.open_loop:
                    voltage = self.pid(h_current)  # PID output (voltage)
                else:
                    voltage = self.set_point_height
                self.update_height.emit(voltage, h_current, current_time)  # Emit voltage, height, and time
        except Exception as e:
            print(f"Error in PINNModelThread: {e}")
            # Emit error message to the main thread
            self.error_signal.emit(str(e))

    def stop(self):
        self.stop_sim = True
