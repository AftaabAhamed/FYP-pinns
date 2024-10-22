import streamlit as st
import serial
import time
import pandas as pd
import plotly.express as px

# from plotly.graph_objects import Figure as figure
# import matplotlib.pyplot as plt

# Replace with your Arduino serial port and baud rate
SERIAL_PORT = '/dev/ttyUSB0'  # Update to your serial port
BAUD_RATE = 9600

try :
    df = pd.read_csv('cache.csv')
except:
    df = pd.DataFrame(columns=["Time", "flow_rate","height"])

# Initialize the serial connection
try:
    arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)  # Wait for connection to establish
    st.write(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud rate.")
except Exception as e:
    st.write(f"Error connecting to {SERIAL_PORT}: {e}")

# Function to read data from Arduino
def read_from_arduino():
    if arduino.in_waiting > 0:
        line = arduino.readline().decode('utf-8').strip()
        return line
    return None

# Create a Streamlit slider to control the Arduino


# if arduino.is_open:
#     arduino.write(f"{slider_val}\n".encode())  # Send the slider value to Arduino

# DataFrame to store the incoming data


# Streamlit app title
st.title("Real-Time Data Plot")
slider_val = st.slider("Send value to Arduino", 0, 1024, 0)
# Continuously read from Arduino and update plot
col1 , col2 = st.columns(2)
with col1:
    plot_placeholder = st.empty()
with col2:
    plot_placeholder2 = st.empty()

while True:
    data = read_from_arduino()
    if data:
        try:
            if arduino.is_open:
                arduino.write(f"{slider_val}\n".encode())
            t ,flow_rate ,height = data.split()  
            t = float(t)/100
            flow_rate = float(flow_rate)
            height = 17.00-float(height)
            # current_time = time.time()
            new_row = {"Time": t, "flow_rate": ((sum(df['flow_rate'][-5:-1])+flow_rate)/5), "height": ((sum(df['height'][-5:-1])+height)/5)}
            # new_row = {"Time": t, "flow_rate": flow_rate, "height": height}

            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv('cache.csv')
            # Plotting the data
            
            # if df.shape[0] is not None and df.shape[0]>10:df = df.iloc[1:]
            fig = px.line(df, x='Time', y='height', title="tank height data",range_y=[0,20])            
            fig2 = px.line(df, x='Time', y='flow_rate', title="flow rate data",range_y=[0,20])            
            plot_placeholder.plotly_chart(fig, use_container_width=True)
            plot_placeholder2.plotly_chart(fig2, use_container_width=True)
        except ValueError:
            st.write("Received non-numeric data from Arduino:", data)

    time.sleep(0.1)  # Adjust the sleep duration as needed
