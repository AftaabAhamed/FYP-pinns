# Import required libraries
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.integrate import odeint



import os

# Constants
Cf = 0.375  # Coefficient for outflow
d = 0.008  # Diameter of the outlet
r = 0.185  # Radius of the tank
g = 9.81  # Acceleration due to gravity
h0 = 0.025  # Initial height of the tank

# Define the inflow rate as a function of voltage
def Q_in(voltage):
    return 0.0000040423 * voltage - 0.0000028661

# Define the ODE for the tank height with safe handling of edge cases
def single_tank_ode(h, t, voltage):
    Q_v = Q_in(voltage)  # Inflow rate for given voltage
    h_diff = h - h0  # Difference from reference height

    # Ensure no negative square root calculations
    if h_diff <= 0:
        outflow = 0  # No outflow if height difference is zero or negative
    else:
        outflow = Cf * (np.pi / 4) * d**2 * np.sqrt(2 * g * h_diff)

    # Prevent division by zero in the tank volume change denominator
    denominator = np.pi * (2 * r * h - h**2)
    if denominator <= 0:
        denominator = np.finfo(float).eps  # Small positive number to avoid division by zero

    # ODE computation
    dh_dt = (Q_v - outflow) / denominator
    return dh_dt

# Simulation parameters
voltage_start = 3
voltage_end = 8
voltage_step = 0.2
steady_state_time = 4500  # Time to reach steady state

# Initialize results
time_points = []
height_results = []
voltage_results = []

# Loop through voltage steps (3 to 8)
voltage = voltage_start
h_current = h0
while voltage <= voltage_end:
    # Time points for the current step
    t = np.linspace(0, steady_state_time, steady_state_time)
    
    # Solve the ODE for the current voltage
    h_solution = odeint(single_tank_ode, h_current, t, args=(voltage,)).flatten()
    h_current = h_solution[-1]  # Update the current height to the last value of the solution
    
    # Store the results
    time_points.extend(t + (time_points[-1] if time_points else 0))  # Offset time points
    height_results.extend(h_solution)
    voltage_results.extend([voltage] * len(t))
    
    # Increment voltage
    voltage += voltage_step

# Loop through voltage steps (8 to 3)
voltage = voltage_end
while voltage >= voltage_start:
    # Time points for the current step
    t = np.linspace(0, steady_state_time, steady_state_time)
    
    # Solve the ODE for the current voltage
    h_solution = odeint(single_tank_ode, h_current, t, args=(voltage,)).flatten()
    h_current = h_solution[-1]  # Update the current height to the last value of the solution
    
    # Store the results
    time_points.extend(t + time_points[-1])  # Offset time points
    height_results.extend(h_solution)
    voltage_results.extend([voltage] * len(t))
    
    # Decrement voltage
    voltage -= voltage_step

# Create a DataFrame for the data
data = pd.DataFrame({
    "Voltage": voltage_results,
    "Time": time_points,
    "Height": height_results
})

# Save to CSV


# Plot Height vs. Time
plt.figure(figsize=(10, 6))
plt.plot(time_points, height_results, label="Height (h) vs Time", color="blue")
plt.title("Height vs Time for Step Voltage Input (3 to 8 and back to 3)")
plt.xlabel("Time (s)")
plt.ylabel("Height (m)")
plt.grid(True)
plt.legend()
plt.show()
csv_file_path = os.path.expanduser("~/Downloads/ode_step_data.csv")
data.to_csv(csv_file_path, index=False)