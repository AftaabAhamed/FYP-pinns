import threading
from collections import deque

import time
import math as m
import csv

from scipy.integrate import odeint
from simple_pid import PID
import serial.tools.list_ports
import serial
from datetime import datetime 
import sqlite3
from transfer_fn_model import TransferFnModel
import numpy as np





# Database Manager Class
class DatabaseManager:
    def __init__(self, db_name="history.db"):
        self.db_name = db_name
        self.create_tables()

    def create_tables(self):
        # Create tables using a temporary connection
        with sqlite3.connect(self.db_name) as connection:
            cursor = connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ODEsim (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    time REAL,
                    height REAL,
                    voltage REAL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS RealSystem (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    time REAL,
                    height REAL,
                    voltage REAL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS TransferFunctionModel (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    time REAL,
                    height REAL,
                    voltage REAL
                )
            """)
            connection.commit()

    def insert_record(self, table, time, height, voltage):
        # Create a new connection for each thread
        with sqlite3.connect(self.db_name) as connection:
            cursor = connection.cursor()
            cursor.execute(f"""
                INSERT INTO {table} (time, height, voltage)
                VALUES (?, ?, ?)
            """, (time, height, voltage))
            connection.commit()










class ODEsim():
    def __init__(self, ode_height,stop_sim,setpoint):

        # self.con = sqlite3.connect('ODE.db')
        self.db_manager = DatabaseManager()

        self.ode_height = ode_height
        self.stop_sim = stop_sim
        self.thread = threading.Thread(target=self.ODE)
        
        self.setpoint = setpoint
        self.vin = 0.0

        self.Kp = 10.0
        self.Ki = 1
        self.Kd = 0

        self.schedule = []
        self.use_scheduler = False

        self.is_openloop = False
        self.start_time_stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        

    

    def ODE(self):

        def setpoint_scheduler():
            if self.schedule[0][-1] > datetime.now().timestamp():
                self.setpoint = self.scheduler[0][0]
                self.schedule.pop(0)

        # Define the differential equation for the tank system
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
            cf = 0.375 # Discharge coefficient

            # Interpolated voltage at time t
            

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

        h_current = 0.04
        pid = PID(self.Kp, self.Ki, self.Kd)
        pid.output_limits = (0, 12)
        start_time = time.time()
        prev_time = start_time


        while not self.stop_sim:
            time.sleep(1)
            del_t = prev_time-time .time()


            if self.is_openloop:
                v = self.vin
            else:
                if self.use_scheduler:
                    setpoint_scheduler()    
                pid.setpoint = self.setpoint
                v = pid(h_current)
                self.vin = v

            t = [0.0, del_t]

            h = odeint(fp_model, h_current, t, args=(v,))
            h_current = h[-1][0]

            elapsed_time = time.time() - start_time
            prev_time = time.time()
            self.ode_height.append((h_current, elapsed_time))
  
            with open(f'data_ODE_{self.start_time_stamp}.csv', 'a') as f:
                csvwriter = csv.writer(f)
                csvwriter.writerow([v,h_current, elapsed_time]) 
                self.db_manager.insert_record("ODEsim", elapsed_time, h_current, v)

            if len(self.ode_height) > 50:
                self.ode_height.popleft()


    def start(self):
        self.stop_sim = False
        self.thread.start()
        return "started"

    def stop(self):
        self.stop_sim = True

    def update_setpoint(self,setpoint):
        self.setpoint = setpoint

    def update_ctrlr(self,Kp,Ki,Kd):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd


class RealSystem():

    def __init__(self, real_height,stop_sim,setpoint):
        self.real_height = real_height
        self.stop_sim = stop_sim
        self.is_openloop = False
        self.setpoint = setpoint
        self.thread = threading.Thread(target=self.RealSystem)

        self.db_manager = DatabaseManager()
        
        self.vin = 0.0        
        
        self.Kp = 20.0
        self.Ki = 1
        self.Kd = 0
        
        self.start_time_stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        

        def find_esp32_port():
            ports = serial.tools.list_ports.comports()
            for port in ports:
                if 'USB' in port.description or 'UART' in port.description:
                    return port.device
            raise Exception("ESP32 not found")

        try:
            SERIAL_PORT = find_esp32_port()
        except Exception as e:
            print(e)
          
        
        BAUD_RATE = 9600
        self.arduino = serial.Serial()
        self.arduino.port = SERIAL_PORT
        self.arduino.baudrate = BAUD_RATE
        self.arduino.open()
        # self.arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=10)


    def RealSystem(self):

        pid = PID(20.0, 1, 0)
        pid.output_limits = (0, 12)
        start_time = time.time()
        h = 0.0401

        def read_from_arduino():
            if self.arduino.in_waiting > 0:
                line = self.arduino.readline().decode('utf-8').strip()
                return line
            return None
        while not self.stop_sim:
            time.sleep(1)
            data = read_from_arduino()
            pid.setpoint = self.setpoint

            if data:
                try:
                    dt = data.split()[-1]
                    h = 0.1374 + 0.025  - float(dt)/100

                    if self.is_openloop:
                        v = self.vin
                    else:
                        pid.setpoint = self.setpoint
                        v = pid(h)
                        self.vin = v

                    elapsed_time = time.time() - start_time
                    self.real_height.append((h, elapsed_time))

                    current_time = time.time()
                    pwm = int((v+3)*255/12)
                    self.arduino.write(f"{pwm}\n".encode())


                    with open(f'data_real_{self.start_time_stamp}.csv', 'a') as f:
                        csvwriter = csv.writer(f)
                        csvwriter.writerow([v,h, elapsed_time]) 
                        self.db_manager.insert_record("RealSystem", elapsed_time, h, v)
                except Exception as e:
                        print(f"Invalid data from Arduino: {e}")    


            if len(self.real_height) > 50:
                self.real_height.popleft()

    def start(self):
        self.stop_sim = False
        self.thread.start()
        return "started"

    def stop(self):        
        self.stop_sim = True

    def update_setpoint(self,setpoint):
        self.setpoint = setpoint

    def update_ctrlr(self,Kp,Ki,Kd):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd    




class TransferFunctionModel():
    
    def __init__(self, height_queue, stop_sim, setpoint, kp=30.0, ki=1.0, kd=0.0, open_loop=False):
        self.height_queue = height_queue
        self.stop_sim = stop_sim
        self.setpoint = setpoint
        self.thread = threading.Thread(target=self.run)
        self.open_loop = open_loop
        self.start_time_stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        self.pid = PID(kp, ki, kd, setpoint=self.setpoint)
        self.pid.output_limits = (0, 12)  # Constrain PID output to 0-12 volts

        self.db_manager = DatabaseManager()

        self.time_step = 1
        self.tf_model = TransferFnModel(
            initial_height=0.025,
            voltage_input1=0,
            voltage_input2=0,
            total_time=1,
            step_time=0,
        )

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
                    self.tf_model.u[self.tf_model.time_vals >= self.tf_model.step_time] = self.tf_model.voltage_input2

                    _, y_out = self.tf_model.simulate()
                    h_current = y_out if y_out.size == 1 else y_out[-1]
                    prev_voltage = voltage
                    self.time_step += 1

                else:
                    if self.time_step == 1:
                        self.tf_model.initial_height = h_current
                    voltage = self.setpoint
                    self.tf_model.total_time = self.time_step
                    self.tf_model.x0 = np.linalg.inv(self.tf_model.C) @ np.array([self.tf_model.initial_height])
                    self.tf_model.time_vals = np.arange(0, self.time_step, self.tf_model.dt)
                    self.tf_model.u = np.ones_like(self.tf_model.time_vals) * self.tf_model.voltage_input1
                    self.tf_model.u[self.tf_model.time_vals >= self.tf_model.step_time] = self.tf_model.voltage_input2

                    _, y_out = self.tf_model.simulate()
                    h_current = y_out if y_out.size == 1 else y_out[-1]
                    self.time_step += 1

                self.height_queue.append((voltage, h_current, current_time))
                if len(self.height_queue) > 50:
                    self.height_queue.popleft()
                with open(f'data_tf_{self.start_time_stamp}.csv', 'a') as f:
                    csvwriter = csv.writer(f)
                    csvwriter.writerow([voltage, h_current, current_time])
                    self.db_manager.insert_record("TransferFunctionModel", current_time, h_current, voltage)

        except Exception as e:
            print(f"Error in TransferFunctionModel: {e}")

    def start(self):
        self.stop_sim = False
        self.thread.start()
        return "started"

    def stop(self):
        self.stop_sim = True

    def update_setpoint(self, setpoint):
        self.setpoint = setpoint

    def update_ctrlr(self, kp, ki, kd):
        self.pid.Kp = kp
        self.pid.Ki = ki
        self.pid.Kd = kd

"""   ......................................................................................................................   """



# if __name__ == "__main__":

#     # Create shared deques for height data
#     ode_height = deque(maxlen=50)
#     real_height = deque(maxlen=50)
#     tf_height = deque(maxlen=50)

#     # Initialize stop_sim flags
#     stop_sim_ode = False
#     stop_sim_real = False
#     stop_sim_tf = False

#     # Set initial setpoints
#     setpoint_ode = 0.05
#     setpoint_real = 0.05
#     setpoint_tf = 0.05

#     # Create instances of the classes
#     ode_sim = ODEsim(ode_height, stop_sim_ode, setpoint_ode)
#     real_system = RealSystem(real_height, stop_sim_real, setpoint_real)
#     tf_model = TransferFunctionModel(tf_height, stop_sim_tf, setpoint_tf)

#     # Start the simulations
#     ode_sim.start()
#     real_system.start()
#     tf_model.start()

#     print("All simulations started.")
