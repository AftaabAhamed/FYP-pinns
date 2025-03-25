import streamlit as st
import requests
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Database setup
conn = sqlite3.connect('data.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS measurements (
    timestamp TEXT,
    model TEXT,
    height REAL,
    time REAL
)
''')
conn.commit()

# API endpoint configuration (replace with your actual server URL)
API_URL = "http://localhost:8000"

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
        st.error(f"API Connection Failed: {e}", icon="⚠️")
        return None

# Function to fetch data from FastAPI server periodically and store in database
def fetch_and_store_data():
    models = {
        "ODE": "ODE/data",
        "Real System": "real/data",
        "Transfer Function Model": "tfm/data"
    }
    for model_name, endpoint in models.items():
        data = send_api_request(endpoint, method="get")  # Fetch data from the respective endpoint
        if data:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            height = data.get('height', 0.0)
            time = data.get('time', 0.0)
            
            cursor.execute('INSERT INTO measurements (timestamp, model, height, time) VALUES (?, ?, ?, ?)',
                           (timestamp, model_name, height, time))
            conn.commit()

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
            send_api_request("ODE/", {})
            send_api_request("real/", {"setpoint": float(setpoint)})
            send_api_request("tfm/", {"setpoint": float(setpoint)})
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

# Right column for real-time plots (7/10 of the screen)
with right_col:
    # Retrieve stored data from SQL database for plotting
    df = pd.read_sql_query('SELECT * FROM measurements ORDER BY timestamp ASC', conn)

    # Height vs Time plot
    fig1, ax1 = plt.subplots(figsize=(12, 4))  # Extend graph horizontally
    if not df.empty:
        if first_principle_plot:
            fp_data = df[df['model'] == "ODE"]
            ax1.plot(pd.to_datetime(fp_data['timestamp']), fp_data['height'], marker='o', linestyle='-', color='blue', label="First Principle Model")
        if real_system_plot:
            rs_data = df[df['model'] == "Real System"]
            ax1.plot(pd.to_datetime(rs_data['timestamp']), rs_data['height'], marker='x', linestyle='-', color='orange', label="Real System")
        if tf_model_plot:
            tf_data = df[df['model'] == "Transfer Function Model"]
            ax1.plot(pd.to_datetime(tf_data['timestamp']), tf_data['height'], marker='s', linestyle='-', color='green', label="Transfer Function Model")
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Height (m)')
        ax1.set_title('Height (m) vs Time')
        ax1.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
    else:
        ax1.set_title('Height (m) vs Time')
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Height (m)')
    
    st.pyplot(fig1)

    # Time vs Time plot
    fig2, ax2 = plt.subplots(figsize=(12, 4))  # Extend graph horizontally
    if not df.empty:
        if first_principle_plot:
            fp_data = df[df['model'] == "ODE"]
            ax2.plot(pd.to_datetime(fp_data['timestamp']), fp_data['time'], marker='o', linestyle='-', color='blue', label="First Principle Model")
        if real_system_plot:
            rs_data = df[df['model'] == "Real System"]
            ax2.plot(pd.to_datetime(rs_data['timestamp']), rs_data['time'], marker='x', linestyle='-', color='orange', label="Real System")
        if tf_model_plot:
            tf_data = df[df['model'] == "Transfer Function Model"]
            ax2.plot(pd.to_datetime(tf_data['timestamp']), tf_data['time'], marker='s', linestyle='-', color='green', label="Transfer Function Model")
        ax2.set_xlabel('Time')
        ax2.set_ylabel('Time (s)')
        ax2.set_title('Time (s) vs Time')
        ax2.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
    else:
        ax2.set_title('Time (s) vs Time')
        ax2.set_xlabel('Time')
        ax2.set_ylabel('Time (s)')
    
    st.pyplot(fig2)

# Button to manually fetch new data
if left_col.button("Fetch Latest Data"):
    fetch_and_store_data()

# Footer with copyright information at the bottom of the page
st.markdown(
    """
    ---
    
    © IIoT liked Digital Twin process model controller developed in National Institute of Technology Calicut.
    
"""
)