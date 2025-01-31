from collections import deque
import numpy as np
from keras import models
import time
import joblib

# Load the trained model
model = models.load_model("trained_model.h5")
scaler = joblib.load("scaler.pkl")

# Create a rolling buffer to hold the latest `sequence_length` data points
sequence_length = 30
input_buffer = deque(maxlen=sequence_length)  # Holds the last 30 time steps

# Initialize the buffer with zeros or dummy values (shape: (sequence_length, 2))
for _ in range(sequence_length):
    input_buffer.append([0, 0])  # [voltage, height]


def preprocess_input(input_buffer, scaler):
    # Convert buffer to a NumPy array and scale the data
    data = np.array(input_buffer)
    scaled_data = scaler.transform(data)
    return scaled_data.reshape(1, sequence_length, 2)  # Reshape for LSTM input


# Set the constant voltage for the open-loop control
constant_voltage = 5  # Example constant voltage input
predicted_height = 0  # Initialize the predicted height

time_step = 0  # To track time steps
while True:
    # Simulated input: constant voltage and last predicted height
    new_voltage = constant_voltage
    new_height = predicted_height if len(input_buffer) == sequence_length else 0

    # Append the new data to the buffer
    input_buffer.append([new_voltage, new_height])

    # If the buffer is full (at least `sequence_length` points), make a prediction
    if len(input_buffer) == sequence_length:
        # Preprocess the input
        input_sequence = preprocess_input(input_buffer, scaler)

        # Make a prediction
        predicted_scaled_height = model.predict(input_sequence)[0][0]

        # Inverse transform the predicted height
        scaled_prediction = np.zeros((1, 2))  # Shape: (1, 2) for inverse transform
        scaled_prediction[0, 1] = predicted_scaled_height
        predicted_height = scaler.inverse_transform(scaled_prediction)[0, 1]

        # Display the predicted height
        print(f"Time Step: {time_step}, Voltage: {new_voltage:.2f}, "
              f"Predicted Height: {predicted_height:.5f}")

    # Increment time for simulation
    time_step += 1

    # Add a delay for real-time simulation (e.g., 1 second for 1Hz update)
    time.sleep(1)
