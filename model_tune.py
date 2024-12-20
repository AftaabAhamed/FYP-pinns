import math as m
import time
import numpy as np
from scipy.integrate import odeint
from PyQt5.QtCore import pyqtSignal, QThread
from simple_pid import PID
import serial
import queue
import csv
from datetime import datetime as dt

q_deq = queue.Queue()
q_real = queue.Queue()
q_pinn = queue.Queue()

class DifferentialEqnThread(QThread):
    update_height = pyqtSignal(float)

    def __init__(self, set_point_height=0.025):
        super().__init__()
        self.stop_sim = False
        self.set_point_height = set_point_height
        self.hist = []


    def run(self):
    #     def fp_model(h, t, v):
    #         fmin = 0.022
    #         fmax = 0.033
    #         f = (2.042*(v - 2.866))/100000
    #         if f < 0:
    #             f = 0
    #         PI = m.pi
    #         d = 0.008
    #         r = 0.185
    #         h0 = 0.04       
    #         dhdt = (f - (0.3 * (PI * pow(d, 2)) * m.sqrt(2 * 9.81 * (h - h0)))) / (PI * (2 * r * h - pow(h, 2)))
    #         return dhdt
        
    #     h_current = 0.04

        t_start =  time.time()
        while not self.stop_sim:
            time.sleep(1)
            v = self.set_point_height
            t = [0.0, 1.0]
            # h = odeint(fp_model, h_current, t, args=(v,))
            h = 0
            h_current = h
            
            t_hist = time.time()-t_start
            
            self.update_height.emit(v*10)

            self.hist.append([v,t_hist,h_current])

            q_deq.put(h_current)
            # print(self.set_point_height)

    def stop(self):
        self.stop_sim = True
        fields = ['voltage','time','height']
        rows = self.hist
        with open(f"dataset-folder/deq_data{dt.isoformat(dt.now())[:-10]}.csv",'w') as f:
            write = csv.writer(f)
            write.writerow(fields)
            write.writerows(rows)

class RealSystemThread(QThread):
    update_height = pyqtSignal(float)

    def __init__(self, set_point_height=0.025):
        super().__init__()
        self.stop_sim = False
        self.set_point_height = set_point_height

        self.hist = []
        self.mode = "1"

    def run(self):
        SERIAL_PORT = '/dev/ttyACM0'
        BAUD_RATE = 9600
        self.arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        def read_from_arduino():
            if self.arduino.in_waiting > 0:
                line = self.arduino.readline().decode('utf-8').strip()
                return line
            return None

        pid = PID(20.0, 1, 0, setpoint=self.set_point_height)
        pid.output_limits = (0, 12)

        t_start = time.time()
        h = 0.0401
        hprev = h

        while not self.stop_sim:
            time.sleep(1)
            data = read_from_arduino()
            
            if data :
                height = data.split()[-1] 
                try:
                    op = self.set_point_height
                    h = 0.178 - float(height)/100
                    if abs(h - hprev) > 0.02:
                        h = hprev


                    q_real.put(h)
                    t_hist = time.time()-t_start
                    self.hist.append([op,t_hist,h])
                    self.update_height.emit((h-0.036)*100/(.17 - .036))

                    if int(self.mode) == 2:
                        h = q_deq.get()
                    
                    
                    
                    if self.arduino.is_open:
                        pwm = int(255*(op+3)/12)
                        print(pwm,h)
                        self.arduino.write(f"{pwm}\n".encode())
                    hprev = h
                    

                except Exception as e:
                    print(f"Invalid data from Arduino{e}")


    def stop(self):
        self.stop_sim = True
        fields = ['voltage','time','height']
        rows = self.hist
        with open(f"dataset-folder/real_data{dt.isoformat(dt.now())[:-10]}.csv",'w+') as f:
            write = csv.writer(f)
            write.writerow(fields)
            write.writerows(rows)



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
