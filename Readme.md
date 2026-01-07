# 🚀 **Complete A-Z Kiosk Setup Guide (Fresh PC)**

***

## 📋 **Pre-Setup Checklist**

Before starting, gather these:

- [ ] **New PC** (Windows 10/11)
- [ ] **Monitor** + cables
- [ ] **Arduino** with card sensor
- [ ] **Barcode scanner** (USB)
- [ ] **Internet connection** (for initial setup only)
- [ ] **USB flash drive** (to transfer files)
- [ ] **Admin password** (you'll create this)

***

## 🔧 **Phase 1: Windows Setup (20 minutes)**

### **Step 1: Install/Configure Windows**

```
1. Boot PC with Windows installation media
2. Install Windows 10/11 (Home edition is fine)
3. During setup:
   - Create username: "kiosk" (or any name you prefer)
   - Set a SIMPLE password: "kiosk123" (you'll auto-login anyway)
   - Skip Microsoft account (use Local account)
   - Disable all privacy options
4. Wait for Windows to complete setup
5. Connect to internet (WiFi or Ethernet)
```

### **Step 2: Update Windows (Important!)**

```batch
REM Open Settings → Windows Update → Check for updates
REM Install ALL updates and restart
REM Repeat until no more updates available
```

**Why?** Prevents forced updates during your event.

***

### **Step 3: Install Chrome Browser**

```
1. Open Edge browser (pre-installed)
2. Go to: https://www.google.com/chrome/
3. Download and install Chrome
4. Make Chrome the default browser
5. Close Chrome
```

***

## 🐍 **Phase 2: Install Python (10 minutes)**

### **Step 4: Download Python**

```
1. Go to: https://www.python.org/downloads/
2. Download: Python 3.11 or 3.12 (64-bit)
3. Run installer
```

### **Step 5: Install Python (CRITICAL SETTINGS)**

```
IMPORTANT - Check these boxes during installation:
✅ Add Python to PATH
✅ Install pip
✅ Install for all users (optional)

Then click: "Install Now"

After installation:
Click "Disable path length limit" (if prompted)
```

### **Step 6: Verify Python Installation**

```batch
REM Open Command Prompt (Press Win+R, type cmd, press Enter)
python --version
REM Should show: Python 3.11.x or 3.12.x

pip --version
REM Should show: pip 23.x.x or higher
```

***

## 📁 **Phase 3: Project Setup (15 minutes)**

### **Step 7: Create Project Folder**

```batch
REM Open Command Prompt as Administrator
REM (Right-click Start → Command Prompt (Admin))

cd C:\
mkdir Kiosk
cd Kiosk
```

**Your project will be at: `C:\Kiosk\`**

***

### **Step 8: Copy Your Project Files**

**Using USB Flash Drive:**

```
1. Copy these folders from your USB to C:\Kiosk\:
   ├── templates\
   │   └── index.html
   ├── static\
   │   ├── butterfly.png
   │   ├── insert.mp3
   │   ├── check.mp3
   │   ├── analyze.mp3
   │   ├── success.mp3
   │   └── error.mp3

2. DO NOT copy app.py yet (we'll create it fresh)
```

***

### **Step 9: Create Virtual Environment**

```batch
REM In Command Prompt (still in C:\Kiosk\)

python -m venv .venv

REM Verify it was created
dir .venv
REM You should see: Include, Lib, Scripts folders
```

***

### **Step 10: Install Python Packages**

```batch
REM Activate virtual environment
.venv\Scripts\activate.bat

REM Your prompt should now show: (.venv) C:\Kiosk>

REM Install packages
pip install flask flask-cors pyserial requests

REM Verify installation
pip list
REM Should show: Flask, flask-cors, pyserial, requests

REM Deactivate for now
deactivate
```

***

### **Step 11: Create `app.py`**

**Create file: `C:\Kiosk\app.py`**

```batch
REM In Command Prompt
notepad app.py
```

**Paste this code:**

```python
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
```

**Save and close Notepad.**

***

### **Step 12: Test Backend Manually**

```batch
REM In Command Prompt at C:\Kiosk\

REM Activate venv
.venv\Scripts\activate.bat

REM Run app
python app.py

REM You should see:
REM  * Running on http://0.0.0.0:5000
```

**Open Chrome, go to: `http://localhost:5000`**

- Should see your kiosk interface
- Press `Ctrl+C` in Command Prompt to stop

```batch
deactivate
```

***

## 🤖 **Phase 4: Create Automation Scripts (10 minutes)**

### **Step 13: Create Automation Folder**

```batch
mkdir C:\Kiosk\automation
mkdir C:\Kiosk\logs
```

***

### **Step 14: Create `watchdog.py`**

```batch
notepad automation\watchdog.py
```

**Paste this:**

```python
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
```

**Save and close.**

***

### **Step 15: Create `start_kiosk.bat`**

```batch
notepad automation\start_kiosk.bat
```

**Paste this:**

```batch
@echo off
REM Kiosk Auto-Launcher

cd /d C:\Kiosk

REM Cleanup old processes
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM chrome.exe >nul 2>&1
timeout /t 2 /nobreak >nul

REM Start watchdog (which starts backend)
start /min "" .venv\Scripts\python.exe automation\watchdog.py

REM Wait for backend to be ready
timeout /t 5 /nobreak >nul

:WAIT
curl -s http://localhost:5000/api/health >nul 2>&1
if errorlevel 1 (
    timeout /t 2 /nobreak >nul
    goto WAIT
)

REM Launch browser in kiosk mode
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --kiosk http://localhost:5000 --start-fullscreen --autoplay-policy=no-user-gesture-required --disable-infobars --no-first-run

exit
```

**Save and close.**

***

### **Step 16: Test Automation Manually**

```batch
REM In Command Prompt
cd C:\Kiosk\automation
start_kiosk.bat
```

**Expected result:**
- Backend starts in background
- After 5-10 seconds, Chrome opens fullscreen
- You see the kiosk interface

**Press F11 to exit fullscreen, close Chrome**

***

## 🔌 **Phase 5: Arduino Setup (5 minutes)**

### **Step 17: Install Arduino Drivers**

```
1. Plug in Arduino to USB
2. Windows should auto-install drivers
3. If not, download from: https://www.arduino.cc/en/software
4. Install Arduino IDE (includes drivers)
```

### **Step 18: Verify Arduino Connection**

```batch
REM Open Device Manager (Win+X → Device Manager)
REM Expand "Ports (COM & LPT)"
REM You should see: "Arduino Uno (COM3)" or similar
```

***

## ⚙️ **Phase 6: Auto-Start Configuration (10 minutes)**

### **Step 19: Configure Auto-Login**

```
1. Press Win+R
2. Type: netplwiz
3. Press Enter
4. Uncheck: "Users must enter a username and password to use this computer"
5. Click OK
6. Enter your password twice
7. Click OK
```

***

### **Step 20: Create Auto-Start Task**

**Create file: `C:\Kiosk\automation\enable_autostart.bat`**

```batch
notepad automation\enable_autostart.bat
```

**Paste this:**

```batch
@echo off
REM Run this as Administrator

REM Create scheduled task
schtasks /create /tn "Kiosk" /tr "C:\Kiosk\automation\start_kiosk.bat" /sc onlogon /rl highest /f

REM Disable sleep/screensaver
powercfg /change monitor-timeout-ac 0
powercfg /change standby-timeout-ac 0
powercfg /change hibernate-timeout-ac 0
reg add "HKCU\Control Panel\Desktop" /v ScreenSaveActive /t REG_SZ /d 0 /f

REM Set high performance power plan
powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c

echo Auto-start enabled!
echo Power settings configured!
echo Restart computer to test.
pause
```

**Save and close.**

***

### **Step 21: Enable Auto-Start**

```batch
REM Right-click on: C:\Kiosk\automation\enable_autostart.bat
REM Select: "Run as administrator"
REM Click Yes to UAC prompt
REM Wait for "Press any key to continue..."
REM Press any key
```

***

## 🧪 **Phase 7: Final Testing (15 minutes)**

### **Step 22: Test Full Boot Sequence**

```batch
REM In Command Prompt (as Admin)
shutdown /r /t 10
```

**Wait 10 seconds, computer will restart.**

***

### **Step 23: Monitor Boot Process**

**Watch for these stages:**

```
00:00 - Computer boots (BIOS screen)
00:30 - Windows loading screen
00:40 - Auto-login happens (no password prompt)
00:45 - Desktop appears
00:50 - Kiosk starts automatically (background)
01:00 - Chrome opens fullscreen
01:05 - Kiosk interface appears
01:10 - READY FOR USE ✅
```

***

### **Step 24: Verify Everything Works**

**Test 1: Check Backend**
```batch
REM Press Ctrl+Shift+Esc (Task Manager)
REM Look for: python.exe (should see 2 instances)
```

**Test 2: Check Arduino**
```batch
REM Press F11 to exit fullscreen
REM Open: C:\Kiosk\logs\kiosk.log
REM Should be empty (only errors logged)
REM If Arduino connected, no errors
```

**Test 3: Card Detection**
```
1. Press F11 to go back to fullscreen
2. Insert card into Arduino sensor
3. Should see "Card Inserted" animation
4. Remove card
5. Should return to idle
```

**Test 4: Barcode Scanning**
```
1. Insert card
2. Scan a barcode
3. Should see: Checking → Analyzing → Building → Result
4. Remove card
5. Should see thank you message
```

***

## 🔧 **Phase 8: Optional Hardening (10 minutes)**

### **Step 25: Disable Windows Updates (For Event Duration)**

**Create: `C:\Kiosk\automation\disable_updates.bat`**

```batch
@echo off
REM Run as Administrator before event

REM Pause updates for 7 days
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" /v NoAutoUpdate /t REG_DWORD /d 1 /f

echo Windows Updates paused for 7 days
pause
```

**Run as Administrator before your event.**

**After event, re-enable:**

```batch
@echo off
REM Run as Administrator after event

reg delete "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" /v NoAutoUpdate /f

echo Windows Updates re-enabled
pause
```

***

### **Step 26: Disable Chrome Auto-Update**

```batch
REM Run as Administrator

reg add "HKLM\SOFTWARE\Policies\Google\Update" /v AutoUpdateCheckPeriodMinutes /t REG_DWORD /d 0 /f
reg add "HKLM\SOFTWARE\Policies\Google\Update" /v UpdateDefault /t REG_DWORD /d 0 /f

echo Chrome auto-update disabled
```

***

## 📊 **Complete File Structure (Final)**

```
C:\Kiosk\
├── .venv\                          # Virtual environment
│   ├── Lib\
│   ├── Scripts\
│   │   └── python.exe
│   └── ...
├── templates\
│   └── index.html                  # Your frontend
├── static\
│   ├── butterfly.png
│   ├── insert.mp3
│   ├── check.mp3
│   ├── analyze.mp3
│   ├── success.mp3
│   └── error.mp3
├── automation\
│   ├── watchdog.py                 # Auto-restart monitor
│   ├── start_kiosk.bat             # Main launcher
│   ├── enable_autostart.bat        # Setup script
│   ├── disable_updates.bat         # Optional
│   └── enable_updates.bat          # Optional
├── logs\
│   └── kiosk.log                   # Error logs only
└── app.py                          # Flask backend
```

***

## ✅ **Final Validation Checklist**

### **Before Event Day:**

- [ ] PC boots to kiosk automatically (no login screen)
- [ ] Backend starts within 60 seconds of boot
- [ ] Browser opens in fullscreen automatically
- [ ] Arduino connected (check logs for errors)
- [ ] Barcode scanner working
- [ ] Card detection working
- [ ] Scan workflow complete (Checking → Analyzing → Result)
- [ ] Thank you popup appears on card removal
- [ ] Timeout error appears after 20 min (optional test)
- [ ] Windows updates disabled
- [ ] Power settings configured (never sleep)
- [ ] Task Manager shows 2 python.exe processes
- [ ] Chrome in kiosk mode (no address bar)

***

## 🚨 **Troubleshooting Quick Reference**

### **Problem: Backend won't start**

```batch
REM Check logs
type C:\Kiosk\logs\kiosk.log

REM Test manually
cd C:\Kiosk
.venv\Scripts\activate.bat
python app.py

REM Look for errors
```

### **Problem: Arduino not detected**

```batch
REM Check Device Manager
devmgmt.msc

REM Look under "Ports (COM & LPT)"
REM If missing, reinstall Arduino IDE
```

### **Problem: Browser doesn't open**

```batch
REM Check Chrome path
dir "C:\Program Files\Google\Chrome\Application\chrome.exe"

REM If different path, update start_kiosk.bat
```

### **Problem: Auto-start doesn't work**

```batch
REM Check scheduled task
schtasks /query /tn "Kiosk"

REM If missing, re-run enable_autostart.bat as Admin
```

### **Problem: Python not found**

```batch
REM Check Python installation
python --version

REM If error, reinstall Python with "Add to PATH" checked
```

***

## 🎯 **Quick Commands Reference**

```batch
REM Manual start kiosk
C:\Kiosk\automation\start_kiosk.bat

REM Stop all kiosk processes
taskkill /F /IM python.exe
taskkill /F /IM chrome.exe

REM View logs
notepad C:\Kiosk\logs\kiosk.log

REM Test backend manually
cd C:\Kiosk
.venv\Scripts\activate.bat
python app.py

REM Check scheduled task
schtasks /query /tn "Kiosk"

REM Remove auto-start
schtasks /delete /tn "Kiosk" /f

REM Restart computer
shutdown /r /t 0
```

***

## 📅 **Day-of-Event Workflow**

### **Setup Evening (5 minutes):**

```
1. Turn on PC
2. Wait for kiosk to auto-start
3. Verify card detection works
4. Scan test barcode
5. Verify internet URLs work (leaderboard/results)
6. Shut down: shutdown /s /t 0
```

### **Event Morning (2 minutes):**

```
1. Turn on PC
2. Wait 90 seconds
3. System is READY ✅
4. Walk away - zero intervention needed
```

### **During Event (Zero intervention):**

```
System handles:
✅ Card insertions/removals
✅ Barcode scans
✅ Result displays
✅ Backend crashes (auto-restart)
✅ Network errors (auto-retry)
✅ Process freezes (auto-recover)
```

### **Event Evening:**

```
1. Shut down PC: shutdown /s /t 0
2. (Optional) Re-enable Windows updates
```

***

## 🎉 **You're Done!**

**Total Setup Time: ~90 minutes**

Your kiosk is now:
- ✅ Fully automated
- ✅ Auto-recovering
- ✅ Production-ready
- ✅ Zero daily intervention required

**Next Steps:**
1. Test with full reboot (Step 22)
2. Run for 24 hours to verify stability
3. Deploy on event day

**If you encounter any issues during setup, check the Troubleshooting section above or view the logs at `C:\Kiosk\logs\kiosk.log`**

Good luck with your event! 🚀

[1](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/92022686/951f8809-2ce1-48af-8e46-0b2697e66d94/image.jpg)
[2](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/92022686/81e1cc4f-1798-43e8-958f-5ad0db2f6484/logo-land-1.jpg)
[3](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/92022686/330b7df8-73be-481e-9e25-7887bfff4105/She-Fest-2025-26-Logo-Brochure_page-0001.jpg)
[4](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/92022686/2fef68a2-49ef-45c8-8c07-b5f0af7b44da/She-Fest-2025-26-Logo-Brochure-1.jpg)
[5](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/92022686/7ed0300b-b9e1-43bb-a61b-6ac9ecd01a59/image.jpg)
[6](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/92022686/514c9787-92b5-4494-abf3-2de745e38142/She-Fest-2025-26-Logo-Brochure-1.jpg)
[7](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/92022686/d0c4ef1b-cdd7-4ee6-b10c-2fa94a4f642c/Untitled-design.jpg)