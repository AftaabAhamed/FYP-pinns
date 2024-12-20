import numpy as np
from scipy.integrate import odeint
from scipy.optimize import minimize
import matplotlib.pyplot as plt
import math as m
import pandas as pd

# Define the differential equation
def fp_model(h, t, v, a, b, c, cf, d):
    f = a * v**2 + b * v + c  # Quadratic function of v
    PI = m.pi
    diameter = 0.008  # m
    r = 0.185  # m
    h0 = 0.025  # m (constant)
    dhdt = (f - (cf * (PI * pow(diameter, 2)) * m.sqrt(2 * 9.81 * (h - h0)))) / (PI * (2 * r * h - pow(h, 2))) + d
    return dhdt

# Define the cost function for optimization
def cost_function(params, t_data, h_data, v_data):
    a, b, c, cf, d = params  # Coefficients for f, cf, and additional term d

    # Solve the differential equation with the current parameters
    h_model = odeint(lambda h, t: fp_model(h, t, v_data[int(t)], a, b, c, cf, d), 0.025, t_data).flatten()

    # Compute the mean squared error
    mse = np.mean((h_model - h_data)**2)
    return mse

# Load experimental data from CSV
# The CSV should have columns: "v", "height", "time"
data = pd.read_csv("/home/aftaab/Documents/fyp_working/dataset-folder/openloop-data3000s.csv")
v_data = data["voltage"].values
h_data = data["height"].values
t_data = data["time"].values

# Initial guess for the parameters
initial_guess = [0.01, 0.01, 0.01, 0.6, 0.0]  # [a, b, c, cf, d]

# Perform the optimization
result = minimize(cost_function, initial_guess, args=(t_data, h_data, v_data), method='Nelder-Mead')

# Extract the fitted parameters
a_fit, b_fit, c_fit, cf_fit, d_fit = result.x
print(f"Fitted parameters:\n a = {a_fit}\n b = {b_fit}\n c = {c_fit}\n cf = {cf_fit}\n d = {d_fit}")

# Solve the differential equation with the fitted parameters
h_fitted = odeint(lambda h, t: fp_model(h, t, v_data[int(t)], a_fit, b_fit, c_fit, cf_fit, d_fit), 0.025, t_data).flatten()

# Plot the experimental data and the fitted curve
plt.figure(figsize=(8, 6))
plt.scatter(t_data, h_data, label="Experimental Data", color="red", s=10)
plt.plot(t_data, h_fitted, label="Fitted Model", color="blue")
plt.xlabel("Time (s)")
plt.ylabel("Height (m)")
plt.legend()
plt.title("Fitting Differential Equation to Data")
plt.grid()
plt.show()
