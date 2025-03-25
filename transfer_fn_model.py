import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
import csv
import time

class TransferFnModel:
    def __init__(self, initial_height=0.025, voltage_input1=5, voltage_input2=10, dt=1, total_time=100, step_time=50):
        self.num = [0.011]
        self.den = [380, 0.9]
        self.sys_tf = signal.TransferFunction(self.num, self.den)
        self.A, self.B, self.C, self.D = signal.tf2ss(self.num, self.den)
        
        self.initial_height = initial_height
        self.voltage_input1 = voltage_input1
        self.voltage_input2 = voltage_input2
        self.dt = dt
        self.total_time = total_time
        self.step_time = step_time  # Time at which the step change occurs
        self.time_vals = np.arange(0, total_time, dt)
        
        # Create the step input signal
        self.u = np.ones_like(self.time_vals) * voltage_input1
        self.u[self.time_vals >= step_time] = voltage_input2  # Change voltage at step_time
        
        # Compute the correct initial state (x0) for the given height
        self.x0 = np.linalg.inv(self.C) @ np.array([initial_height])
        
    def simulate(self):
        t_response, y_response, x_out = signal.lsim(
            (self.A, self.B, self.C, self.D), U=self.u, T=self.time_vals, X0=self.x0
        )
        return t_response, y_response
    
    def plot_response(self):
        t_response, y_response = self.simulate()
        plt.plot(t_response, y_response, label="Height (cm)")
        plt.xlabel("Time (s)")
        plt.ylabel("Height (cm)")
        plt.title(f"Step Response with Step Change at {self.step_time}s")
        plt.legend()
        plt.grid(True)
        plt.show()
        print(f"Last y_response value: {y_response[-1]:.4f}")

    def log_to_csv(self, filename=r"transfer_fn\transfer_fn.csv"):
        t_response, y_response = self.simulate()
        print("1:", self.voltage_input1, "2:", self.voltage_input2)
        # Writing data to CSV file
        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Time (s)", "Height (cm)"])  # Header
            for t, y in zip(t_response, y_response):
                writer.writerow([t, y])  # Data rows
        print(f"Data successfully logged to {filename}")

# Example usage
# tank = TransferFnModel(initial_height=0.025, voltage_input1=0, voltage_input2=0, total_time=1000, step_time=0)
# tank.plot_response()
# print(tank.simulate())
# for i in range(1, 10000):
#     tank.total_time = i
#     tank.time_vals = np.arange(0, i, tank.dt)
#     tank.u = np.ones_like(tank.time_vals) * tank.voltage_input1
#     tank.u[tank.time_vals >= tank.step_time] = tank.voltage_input2  # Step change

#     _, y_output = tank.simulate()
#     print(i)
#     print(y_output)
#     time.sleep(0.5)
