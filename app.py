# app.py
import streamlit as st
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI instance
app = FastAPI()

# Data validation model
class SensorData(BaseModel):
    flowRate: float
    totalLitres: float
    relayState: bool

# Global state initialization
if "relay_command" not in st.session_state:
    st.session_state.relay_command = None
if "esp_data" not in st.session_state:
    st.session_state.esp_data = {}
if "last_update" not in st.session_state:
    st.session_state.last_update = None

# Endpoint untuk menerima data dari ESP32
@app.post("/receive-data")
async def receive_data(data: SensorData):
    try:
        logger.info(f"Received data from ESP32: {data.dict()}")
        st.session_state.esp_data = data.dict()
        st.session_state.last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return {"status": "success", "data_received": data.dict()}
    except Exception as e:
        logger.error(f"Error processing data: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# Endpoint untuk menerima permintaan kontrol dari ESP32
@app.get("/receive-command")
def receive_command():
    command = st.session_state.relay_command
    logger.info(f"Sending command to ESP32: {command}")
    if command:
        st.session_state.relay_command = None
        return command
    return "NO_COMMAND"

# Streamlit UI
st.title("ESP32 Water Flow Monitoring & Control System")

# Sidebar status
st.sidebar.subheader("Connection Status")
if st.session_state.esp_data:
    st.sidebar.success("✅ ESP32 Connected")
    st.sidebar.text(f"Last update: {st.session_state.last_update}")
else:
    st.sidebar.error("❌ ESP32 Not Connected")

# Main content
col1, col2 = st.columns(2)

with col1:
    st.subheader("Sensor Data")
    if st.session_state.esp_data:
        st.metric("Flow Rate", f"{st.session_state.esp_data.get('flowRate', 0):.2f} L/min")
        st.metric("Total Volume", f"{st.session_state.esp_data.get('totalLitres', 0):.2f} L")
    else:
        st.info("Waiting for data from ESP32...")

with col2:
    st.subheader("Relay Control")
    relay_status = "ON" if st.session_state.esp_data.get('relayState', False) else "OFF"
    st.metric("Current Relay Status", relay_status)
    
    col3, col4 = st.columns(2)
    with col3:
        if st.button("Turn ON", type="primary"):
            st.session_state.relay_command = "ON"
            st.success("Command sent: Turn ON")
    with col4:
        if st.button("Turn OFF", type="secondary"):
            st.session_state.relay_command = "OFF"
            st.success("Command sent: Turn OFF")

# Error log section
st.subheader("System Log")
if st.checkbox("Show Debug Logs"):
    with st.expander("Debug Information"):
        st.json(st.session_state.esp_data)
        st.text(f"Last Command: {st.session_state.relay_command}")
