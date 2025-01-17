# app.py
import streamlit as st 
import paho.mqtt.client as mqtt
import json
from datetime import datetime
import ssl
import os

# MQTT Configuration
MQTT_BROKER = os.getenv('MQTT_BROKER', '1feb698b048a450ea46a18947fa65a1d.s1.eu.hivemq.cloud')
MQTT_PORT = 8883
MQTT_USER = os.getenv('MQTT_USER', 'innovillage')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', 'Inn12345')
TOPIC_DATA = "waterflow/data"
TOPIC_COMMAND = "waterflow/command"

# Initialize session state
if "mqtt_client" not in st.session_state:
    st.session_state.mqtt_client = None
if "sensor_data" not in st.session_state:
    st.session_state.sensor_data = {}
if "last_update" not in st.session_state:
    st.session_state.last_update = None
if "connection_status" not in st.session_state:
    st.session_state.connection_status = False

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        st.session_state.connection_status = True
        print("Connected to MQTT Broker!")
        client.subscribe(TOPIC_DATA)
    else:
        st.session_state.connection_status = False
        print(f"Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        st.session_state.sensor_data = payload
        st.session_state.last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        print(f"Error processing message: {e}")

def init_mqtt():
    client = mqtt.Client()
    
    # Set username and password
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    
    # Enable TLS
    client.tls_set(tls_version=ssl.PROTOCOL_TLS)
    client.tls_insecure_set(True)
    
    # Set callbacks
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        return client
    except Exception as e:
        print(f"Error connecting to MQTT broker: {e}")
        return None

# Streamlit UI
st.set_page_config(
    page_title="Water Flow Monitoring System",
    page_icon="💧",
    layout="wide"
)

st.title("💧 Water Flow Monitoring System")

# Initialize MQTT client if not exists
if st.session_state.mqtt_client is None:
    st.session_state.mqtt_client = init_mqtt()

# Connection status in sidebar
st.sidebar.subheader("Connection Status")
if st.session_state.connection_status:
    st.sidebar.success("✅ MQTT Connected")
    st.sidebar.text(f"Broker: {MQTT_BROKER}")
    if st.session_state.last_update:
        st.sidebar.text(f"Last update: {st.session_state.last_update}")
else:
    st.sidebar.error("❌ MQTT Disconnected")

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📊 Real-time Data")
    if st.session_state.sensor_data:
        col3, col4 = st.columns(2)
        with col3:
            st.metric(
                "Flow Rate", 
                f"{st.session_state.sensor_data.get('flowRate', 0):.2f} L/min",
                delta=None
            )
        with col4:
            st.metric(
                "Total Volume", 
                f"{st.session_state.sensor_data.get('totalLitres', 0):.2f} L",
                delta=None
            )
        
        # Add a simple chart
        if 'history' not in st.session_state:
            st.session_state.history = []
        
        # Keep last 50 readings
        if len(st.session_state.history) > 50:
            st.session_state.history.pop(0)
        
        st.session_state.history.append({
            'time': datetime.now().strftime("%H:%M:%S"),
            'flow_rate': st.session_state.sensor_data.get('flowRate', 0)
        })
        
        # Display chart
        chart_data = {
            'time': [h['time'] for h in st.session_state.history],
            'flow_rate': [h['flow_rate'] for h in st.session_state.history]
        }
        st.line_chart(chart_data, x='time', y='flow_rate')
    else:
        st.info("Waiting for data from ESP32...")

with col2:
    st.subheader("🎛️ Control Panel")
    relay_status = "ON" if st.session_state.sensor_data.get('relayState', False) else "OFF"
    
    st.metric(
        "Relay Status",
        relay_status,
        delta=None
    )
    
    col5, col6 = st.columns(2)
    with col5:
        if st.button("Turn ON", type="primary", use_container_width=True):
            if st.session_state.mqtt_client:
                st.session_state.mqtt_client.publish(TOPIC_COMMAND, "ON")
                st.success("Command sent: Turn ON")
            else:
                st.error("MQTT not connected!")
    
    with col6:
        if st.button("Turn OFF", type="secondary", use_container_width=True):
            if st.session_state.mqtt_client:
                st.session_state.mqtt_client.publish(TOPIC_COMMAND, "OFF")
                st.success("Command sent: Turn OFF")
            else:
                st.error("MQTT not connected!")

# Debug section
with st.expander("Debug Information", expanded=False):
    st.subheader("📝 Debug Log")
    st.json(st.session_state.sensor_data)
    if st.button("Clear History"):
        st.session_state.history = []
        st.success("History cleared!")
