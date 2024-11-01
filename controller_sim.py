import math as m
import time
import numpy as np
from scipy.integrate import odeint
from PyQt5.QtCore import pyqtSignal, QThread
from simple_pid import PID
import serial

class DifferentialEqnThread(QThread):
    update_height = pyqtSignal(float)

    def __init__(self, set_point_height=0.025):
        super().__init__()
        self.stop_sim = False
        self.set_point_height = set_point_height


    def run(self):
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
        pid = PID(30.0, 1, 0, setpoint=self.set_point_height)
        pid.output_limits = (0, 6)

        while not self.stop_sim:
            time.sleep(1)
            pid.setpoint = self.set_point_height
            v = pid(h_current)
            t = [0.0, 1.0]
            h = odeint(fp_model, h_current, t, args=(v,))
            h_current = h[-1][0]
            self.update_height.emit(h_current)
            print(self.set_point_height)

    def stop(self):
        self.stop_sim = True


class RealSystemThread(QThread):
    update_height = pyqtSignal(float)

    def __init__(self, set_point_height=0.025):
        super().__init__()
        self.stop_sim = False
        self.set_point_height = set_point_height

    def run(self):
        SERIAL_PORT = '/dev/ttyUSB0'
        BAUD_RATE = 9600
        arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

        def read_from_arduino():
            if arduino.in_waiting > 0:
                line = arduino.readline().decode('utf-8').strip()
                return line
            return None

        pid = PID(30.0, 1, 0, setpoint=self.set_point_height)
        pid.output_limits = (0, 6)

        while not self.stop_sim:
            time.sleep(1)
            data = read_from_arduino()
            if data:
                try:
                    h = 0.18 - float(data)
                    self.update_height.emit(h)
                    op = pid(h)
                    if arduino.is_open:
                        arduino.write(f"{op}\n".encode())
                except ValueError:
                    print("Invalid data from Arduino")

    def stop(self):
        self.stop_sim = True


class PINNModelThread(QThread):
    update_height = pyqtSignal(float)

    def __init__(self, set_point_height=0.025):
        super().__init__()
        self.stop_sim = False
        self.set_point_height = set_point_height

    def run(self):
        # Replace with PINN model code for prediction
        h_current = 0.025  # Example initial height

        while not self.stop_sim:
            time.sleep(1)
            # Calculate the new height using PINN
            # Example: h_current = pinn_predict()
            self.update_height.emit(h_current)

    def stop(self):
        self.stop_sim = True
