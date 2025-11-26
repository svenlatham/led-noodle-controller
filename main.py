import machine
import network
import socket
import _thread
import time


# Pins
pins = [16, 17, 19, 18] 
noodles = [machine.PWM(machine.Pin(p)) for p in pins]
for n in noodles:
    n.freq(1000)

# Global Variable to control state (Shared between Web and Lights)
# Modes: "OFF", "ON", "BLINK", "PULSE"
current_mode = "OFF"

# --- HELPER FUNCTIONS ---

def set_brightness(noodle_index, percent):
    if percent < 0: percent = 0
    if percent > 100: percent = 100
    duty = int((percent / 100)**2 * 65535) # Gamma corrected
    noodles[noodle_index].duty_u16(duty)

def all_off():
    for i in range(len(noodles)):
        set_brightness(i, 0)

def smart_sleep(duration, mode_check_val):
    """
    Sleeps for 'duration' seconds, but checks frequently if the 
    user changed the mode. Returns False if mode changed (abort!)
    """
    steps = int(duration * 20) # Check 20 times per second
    for _ in range(steps):
        if current_mode != mode_check_val:
            return False # ABORT
        time.sleep(0.05)
    return True # Sleep completed successfully

# --- LIGHT SHOW LOGIC (Thread 1) ---

def run_light_show():
    global current_mode
    print("Light thread started.")
    
    while True:
        if current_mode == "OFF":
            all_off()
            time.sleep(0.2)
            
        elif current_mode == "ON":
            for i in range(4):
                set_brightness(i, 100)
            time.sleep(0.2)

        elif current_mode == "BLINK":
            # Blink Sequence
            for i in range(4):
                if current_mode != "BLINK": break
                all_off()
                set_brightness(i, 100)
                # Use smart_sleep to keep it responsive
                if not smart_sleep(0.5, "BLINK"): break

        elif current_mode == "PULSE":
            # Pulse In
            for b in range(0, 101, 2):
                if current_mode != "PULSE": break
                for n in range(4): set_brightness(n, b)
                time.sleep(0.02) # Short sleep, no need for smart_sleep
            
            # Pulse Out
            for b in range(100, -1, -2):
                if current_mode != "PULSE": break
                for n in range(4): set_brightness(n, b)
                time.sleep(0.02)

# --- WIFI & WEB SERVER (Thread 2) ---


def web_page():
    # Simple HTML with buttons
    html = """<html>
    <head> <title>Noodle Control</title> 
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
    body{font-family:sans-serif; text-align:center; margin-top:50px; background:#222; color:#fff;}
    button{width:150px; height:60px; font-size:20px; margin:10px; border-radius:10px; border:none; cursor:pointer;}
    .on{background:#4CAF50; color:white;}
    .off{background:#f44336; color:white;}
    .eff{background:#2196F3; color:white;}
    </style>
    </head>
    <body> <h1>Noodle Command</h1> 
    <a href="/?mode=ON"><button class="on">ALL ON</button></a><br>
    <a href="/?mode=OFF"><button class="off">ALL OFF</button></a><br>
    <a href="/?mode=BLINK"><button class="eff">BLINK</button></a><br>
    <a href="/?mode=PULSE"><button class="eff">PULSE</button></a>
    </body></html>"""
    return html

def start_server():
    global current_mode
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    print('Listening on', addr)

    while True:
        try:
            cl, addr = s.accept()
            request = cl.recv(1024)
            request = str(request)
            
            # Parse the URL (Very basic parsing)
            if 'mode=ON' in request:
                current_mode = "ON"
            if 'mode=OFF' in request:
                current_mode = "OFF"
            if 'mode=BLINK' in request:
                current_mode = "BLINK"
            if 'mode=PULSE' in request:
                current_mode = "PULSE"
            
            response = web_page()
            cl.send('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n')
            cl.send(response)
            cl.close()
        except OSError as e:
            cl.close()
            print('Connection closed')

# --- MAIN EXECUTION ---


# Start the Light Show in a separate thread
_thread.start_new_thread(run_light_show, ())

# Start the Web Server in the main thread
start_server()
