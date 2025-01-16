import streamlit as st
from fastapi import FastAPI, Request
from starlette.middleware.wsgi import WSGIMiddleware

# FastAPI instance
app = FastAPI()

# Global variables
if "relay_command" not in st.session_state:
    st.session_state.relay_command = None
if "esp_data" not in st.session_state:
    st.session_state.esp_data = {}

# Endpoint untuk menerima data dari ESP32
@app.post("/receive-data")
async def receive_data(request: Request):
    data = await request.json()
    st.session_state.esp_data = data
    return {"status": "success", "data_received": data}

# Endpoint untuk menerima permintaan kontrol dari ESP32
@app.get("/receive-command")
def receive_command():
    # Kirim perintah relay saat diminta ESP32
    if st.session_state.relay_command:
        command = st.session_state.relay_command
        st.session_state.relay_command = None  # Reset perintah setelah dikirim
        return command
    return "NO_COMMAND"

# Integrasi FastAPI ke Streamlit
st_app = WSGIMiddleware(app)

# Streamlit UI
st.title("ESP32 Data Monitoring & Relay Control")

# Tampilkan data dari ESP32
if st.session_state.esp_data:
    st.subheader("Data ESP32:")
    st.json(st.session_state.esp_data)
else:
    st.info("Belum ada data yang diterima dari ESP32.")

# Kontrol relay
st.subheader("Kontrol Relay:")
if st.button("Hidupkan Relay"):
    st.session_state.relay_command = "ON"
    st.success("Perintah untuk menghidupkan relay dikirim.")
elif st.button("Matikan Relay"):
    st.session_state.relay_command = "OFF"
    st.success("Perintah untuk mematikan relay dikirim.")
