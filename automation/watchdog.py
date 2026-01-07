"""Minimal Watchdog - Auto-restart backend"""
import time
import subprocess
import requests
from pathlib import Path

PYTHON_EXE = r"C:\Kiosk\.venv\Scripts\python.exe"
APP_PATH = r"C:\Kiosk\app.py"
PROJECT_DIR = r"C:\Kiosk"
SERVER_URL = "http://localhost:5000"

backend_process = None

def start_backend():
    global backend_process
    try:
        backend_process = subprocess.Popen(
            [PYTHON_EXE, "app.py"],
            cwd=PROJECT_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True
    except:
        return False

def is_healthy():
    try:
        r = requests.get(f"{SERVER_URL}/api/health", timeout=3)
        return r.status_code == 200
    except:
        return False

start_backend()
time.sleep(5)

while True:
    if backend_process.poll() is not None:
        time.sleep(5)
        start_backend()
    elif not is_healthy():
        if backend_process:
            backend_process.terminate()
            time.sleep(2)
            backend_process.kill()
        time.sleep(5)
        start_backend()
    
    time.sleep(10)
