import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import time
from collections import defaultdict, deque

# API endpoint configuration (replace with your actual FastAPI server URL)
API_URL = "http://127.0.0.1:8000"

# Function to send data to server via API with basic error handling
def send_api_request(endpoint, payload=None, method="post"):
    try:
        if method == "post":
            response = requests.post(f"{API_URL}/{endpoint}", json=payload)
        elif method == "get":
            response = requests.get(f"{API_URL}/{endpoint}", params=payload)
        else:
            raise ValueError("Unsupported HTTP method")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Connection Failed: {e}")
        return None

def fetch_data(model):
    """
    Fetch historical data (time, height, voltage) from the FastAPI server for a given model.

    Args:
        model (str): The name of the model (e.g., "ODE", "Real System", "Transfer Function Model").

    Returns:
        list: A list of dictionaries containing the historical data, or None if an error occurs.
    """
    # Map model names to API-compatible model names
    endpoint_map = {
        "ODE": "ODEsim",
        "Real System": "RealSystem",
        "Transfer Function Model": "TransferFunctionModel"
    }
    model_name = endpoint_map.get(model)
    if not model_name:
        return None

    try:
        # Make a GET request to the /history/<model_name> endpoint
        response = requests.get(f"{API_URL}/history/{model_name}")
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
        return data.get("data", [])  # Return the "data" field from the response
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {model}: {e}")
        return None

# Layout setup using Streamlit columns
st.set_page_config(layout="wide")  # Set wide layout for better visualization

# Title section aligned in the top blank area with blue background
st.markdown(
    """
    <style>
    .title-container {
        background-color: #1E90FF; /* Blue background */
        padding: 15px;
        text-align: center;
        color: white;
        font-size: 24px;
        font-weight: bold;
    }
    </style>
    <div class="title-container">
        IIoT based Digital Twin process model controller
    </div>
    """,
    unsafe_allow_html=True,
)

# Divide the screen into 10 vertical parts: 3 for control panel, 7 for graphs
left_col, right_col = st.columns([3, 7])

# Left column for control panel (3/10 of the screen)
with left_col:
    st.sidebar.header("Navigation")
    if st.sidebar.button("Open Loop Control"):
        send_api_request("ODE/is_openloop", {"is_openloop": True})
    if st.sidebar.button("Closed Loop Control"):
        send_api_request("ODE/is_openloop", {"is_openloop": False})

    # Parameter input fields
    st.subheader("Set Controller Parameters")
    setpoint = st.text_input("Set Point Height (m):", value="0.08")
    kp = st.text_input("Proportional Gain (Kp):", value="27")
    ki = st.text_input("Integral Gain (Ki):", value="0.9")
    kd = st.text_input("Derivative Gain (Kd):", value="0.05")

    if st.button("Enter"):
        payload = {
            "setpoint": float(setpoint),
            "Kp": float(kp),
            "Ki": float(ki),
            "Kd": float(kd)
        }
        send_api_request("ODE/update_setpoint", {"setpoint": payload["setpoint"]})
        send_api_request("ODE/update_ctrlr", payload)

    # Buttons for model control
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Start All Models"):
            send_api_request("ODE/", method="get")  # Use GET method for ODE
            send_api_request("real/", {"setpoint": float(setpoint)})  # POST method for real
            send_api_request("tfm/", {"setpoint": float(setpoint)})  # POST method for tfm
    with col2:
        if st.button("Stop All Models"):
            send_api_request("ODE/stop", {})
            send_api_request("real/stop", {})
            send_api_request("tfm/stop", {})

    # Checkboxes for model plots
    st.subheader("Select your Model")
    first_principle_plot = st.checkbox("First Principle Model")
    real_system_plot = st.checkbox("Real System Only")
    tf_model_plot = st.checkbox("Transfer Function")

# Initialize data history for each model
data_history = defaultdict(lambda: deque(maxlen=1000))  # Store up to 1000 points for each model

# Right column for real-time plots (7/10 of the screen)
with right_col:
    # Create an empty container for the plot
    plot_container = st.empty()

    # Continuously update the plot
    while True:
        # Fetch data for each selected model
        if first_principle_plot:
            ode_data = fetch_data("ODE")
            if ode_data:
                data_history["ODE"] = [(entry["time"], entry["height"]) for entry in ode_data]  # Replace with full history
        if real_system_plot:
            real_data = fetch_data("Real System")
            if real_data:
                data_history["Real System"] = [(entry["time"], entry["height"]) for entry in real_data]  # Replace with full history
        if tf_model_plot:
            tfm_data = fetch_data("Transfer Function Model")
            if tfm_data:
                data_history["Transfer Function Model"] = [(entry["time"], entry["height"]) for entry in tfm_data]  # Replace with full history

        # Create a new plot
        fig1, ax1 = plt.subplots(figsize=(12, 4))  # Extend graph horizontally

        # Plot data for each selected model
        if first_principle_plot and "ODE" in data_history:
            times, heights = zip(*data_history["ODE"])
            ax1.plot(times, heights, marker='o', linestyle='-', color='blue', label="First Principle Model")
        if real_system_plot and "Real System" in data_history:
            times, heights = zip(*data_history["Real System"])
            ax1.plot(times, heights, marker='x', linestyle='-', color='orange', label="Real System")
        if tf_model_plot and "Transfer Function Model" in data_history:
            times, heights = zip(*data_history["Transfer Function Model"])
            ax1.plot(times, heights, marker='s', linestyle='-', color='green', label="Transfer Function Model")

        # Set plot labels and title
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Height (m)')
        ax1.set_title('Height (m) vs Time')
        ax1.legend()
        plt.tight_layout()

        # Update the plot in the container
        plot_container.pyplot(fig1)

        # Add a delay to avoid overwhelming the backend
        time.sleep(1)