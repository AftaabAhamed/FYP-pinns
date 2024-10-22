
import math as m
import time 
import numpy as np 
from scipy.integrate import odeint 
import matplotlib.pyplot as plt 
from simple_pid import PID


class Controller:
    def __init__(self,):
        self.stop_sim = False
        self.set_point_height = 0.0
        pass
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
                # pid.setpoint = self.set_point_height
                t_now     = time.time()
                t         = np.asarray([0.0, t_now])
                v         = pid(h_current)
                print(f"height : {h_current} , voltage : {v} ")
                h         = odeint(fp_model, h_init, t, (v,))
                h_current = h[-1]
                st = t_now
        pass
    def real_pcs(self):
        pass
    def pinn_sim(self):
        pass

print("hi")
ctrlr = Controller()
ctrlr.set_point_height = 0.10
ctrlr.fp_model_sim()