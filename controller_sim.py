
import math as m
import time 
import numpy as np 
from scipy.integrate import odeint 
import matplotlib.pyplot as plt 
from simple_pid import PID
from threading import Thread


class Controller:
    def __init__(self,):
        self.stop_sim = False
        self.set_point_height = 0.025
        self.fp_sim_hist = []
        self.real_pcs_hist = []

        pass
    
    def run_fp_model_sim_async(self,):
        fpsim_thread = Thread(target = self.fp_model_sim)
        fpsim_thread.start()
        fpsim_thread.join()
    def run_real_pcs_async(self,):
        real_pcs_thread = Thread(target = self.real_pcs)
        real_pcs_thread.start()
        real_pcs_thread.join()



    def fp_model_sim(self):
        st = time.time()

        def fp_model(h,t,v):
            fmin = 0.022#L/s
            fmax = 0.033#L/s
            f    = fmax*v/1023 #l/s
            PI   = m.pi
            d    = 0.008 #m
            r    = 0.185 #m
            h0   = 0.025 #m        
            dhdt = (f-(0.6*(PI*pow(d,2))*m.sqrt(2*9.81*(h-h0))))/(PI*(2*r*h - pow(h,2)))
            return dhdt   

        h_init = 0.025 #m
        h_max  = 0.18  #m 
        pid = PID(30.0, 1, 0, setpoint=self.set_point_height)
        pid.output_limits = (0,6)
        h_current = h_init

        while not self.stop_sim:
            if time.time() - st > 1:
                pid.setpoint = self.set_point_height
                t_now     = time.time()
                t         = np.asarray([0.0, t_now])
                v         = pid(h_current)
                print(f"height : {h_current} , voltage : {v} ")
                h         = odeint(fp_model, h_init, t, (v,))
                h_current = h[-1]
                st = t_now
                self.fp_sim_hist.append((t_now,h_current))

        pass
    def real_pcs(self):
        SERIAL_PORT = '/dev/ttyUSB0'  # Update to your serial port
        BAUD_RATE = 9600
        arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

        def read_from_arduino():
            if arduino.in_waiting > 0:
                line = arduino.readline().decode('utf-8').strip()
                return line
        
        pid = PID(30.0, 1, 0, setpoint=self.set_point_height)
        pid.output_limits = (0,6)   

        st = time.time() 
        while not self.stop_sim:
            if time.time() - st > 1:
                pid.setpoint = self.set_point_height
                data = read_from_arduino()
                
                t_now     = time.time()
                h = 0.18 - data[-1]
                op = pid(h)
                if arduino.is_open:
                    arduino.write(f"{op}\n".encode())
                st = t_now
                self.real_pcs_hist.append((t_now,h_current))
        pass
    def pinn_sim(self):
        pass

print("hi")
ctrlr = Controller()
ctrlr.set_point_height = 0.10
ctrlr.run_fp_model_sim_async()