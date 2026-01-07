import threading
import time
import serial
import serial.tools.list_ports
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
import sys
import io

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Minimal logging - max 5MB, 2 backups
import os
os.makedirs('logs', exist_ok=True)
log_handler = RotatingFileHandler('logs/kiosk.log', maxBytes=5*1024*1024, backupCount=2, encoding='utf-8')
log_handler.setLevel(logging.ERROR)
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[log_handler]
)

# Global state
SYSTEM_STATE = {
    "card_inserted": False,
    "arduino_connected": False
}

def read_from_serial_robust():
    """Arduino connection thread"""
    global SYSTEM_STATE
    
    while True:
        arduino_port = None
        ports = serial.tools.list_ports.comports()
        
        for port in ports:
            if any(kw in port.description for kw in ["USB", "Arduino", "CH340", "CP210"]):
                arduino_port = port.device
                break
        
        if arduino_port:
            try:
                with serial.Serial(arduino_port, 9600, timeout=1) as ser:
                    SYSTEM_STATE["arduino_connected"] = True
                    time.sleep(2)
                    ser.reset_input_buffer()
                    
                    while True:
                        if ser.in_waiting > 0:
                            line = ser.readline().decode('utf-8', errors='ignore').strip()
                            
                            if line == '1' and not SYSTEM_STATE["card_inserted"]:
                                SYSTEM_STATE["card_inserted"] = True
                            elif line == '0' and SYSTEM_STATE["card_inserted"]:
                                SYSTEM_STATE["card_inserted"] = False
                        
                        time.sleep(0.05)
                        
            except Exception as e:
                logging.error(f"Arduino error: {e}")
                SYSTEM_STATE["arduino_connected"] = False
                SYSTEM_STATE["card_inserted"] = False
                time.sleep(2)
        else:
            SYSTEM_STATE["arduino_connected"] = False
            time.sleep(2)

serial_thread = threading.Thread(target=read_from_serial_robust, daemon=True)
serial_thread.start()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/status", methods=["GET"])
def get_status():
    return jsonify(SYSTEM_STATE)

@app.route("/api/scan", methods=["POST"])
def scan_barcode():
    try:
        data = request.json
        barcode = data.get("barcode", "").strip()
        
        if not barcode or not SYSTEM_STATE["card_inserted"]:
            return jsonify({"error": "Invalid scan"}), 403
        
        return jsonify({"status": "success", "barcode": barcode}), 200
        
    except Exception as e:
        logging.error(f"Scan error: {e}")
        return jsonify({"error": "Server error"}), 500

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False, threaded=True)
