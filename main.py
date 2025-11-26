"""
LED Noodle Controller for Raspberry Pi Pico 2 W
Controls 4 LED noodles with PWM dimming and fade effects

FEATURES:
- Individual LED control with brightness (0-100%)
- Smooth fade transitions for each LED
- Multiple display modes (ON, OFF, BLINK, PULSE, WAVE, CHASE, INDIVIDUAL)
- Web interface for remote control
- Loop-friendly LED control interface

USAGE EXAMPLES:

1. Set individual LED brightness:
   set_led(0, 75)  # Set LED 0 to 75%
   set_brightness(1, 100)  # Set LED 1 to 100%

2. Fade individual LEDs:
   fade_led(0, 100, duration=2.0)  # Fade LED 0 to 100% over 2 seconds
   fade_led(1, 0, duration=1.0, steps=30)  # Fade LED 1 to 0% with 30 steps

3. Control all LEDs:
   set_all(50)  # Set all LEDs to 50%
   fade_all(100, duration=1.5)  # Fade all LEDs to 100%

4. Loop-friendly control using LEDLoop context manager:
   with LEDLoop(delay=0.1) as loop:
       for i in range(4):
           loop.set(i, 100)
           loop.wait()  # Wait for default delay
       for i in range(4):
           loop.fade(i, 0, duration=0.5)

5. Custom patterns in run_light_show():
   # Example: Sequential fade
   for i in range(4):
       fade_led(i, 100, duration=0.5)
       fade_led(i, 0, duration=0.5)
"""

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
# Modes: "OFF", "ON", "BLINK", "PULSE", "WAVE", "CHASE", "INDIVIDUAL"
current_mode = "OFF"

# Individual LED brightness values (0-100) for INDIVIDUAL mode
individual_brightness = [0, 0, 0, 0]

# Current brightness tracking for fade operations
current_brightness = [0.0, 0.0, 0.0, 0.0]

# --- HELPER FUNCTIONS ---

def set_brightness(noodle_index, percent):
    """Set brightness of a specific LED (0-100%)"""
    if percent < 0: percent = 0
    if percent > 100: percent = 100
    duty = int((percent / 100)**2 * 65535) # Gamma corrected
    noodles[noodle_index].duty_u16(duty)
    current_brightness[noodle_index] = float(percent)

def set_led(index, brightness):
    """Alias for set_brightness for cleaner loop code"""
    set_brightness(index, brightness)

def set_all(brightness):
    """Set all LEDs to the same brightness"""
    for i in range(len(noodles)):
        set_brightness(i, brightness)

def all_off():
    for i in range(len(noodles)):
        set_brightness(i, 0)

def fade_led(noodle_index, target_percent, duration=1.0, steps=50):
    """
    Smoothly fade a single LED from current brightness to target.

    Args:
        noodle_index: Which LED to fade (0-3)
        target_percent: Target brightness (0-100)
        duration: How long the fade should take in seconds
        steps: Number of steps in the fade (higher = smoother)

    Returns:
        True if fade completed, False if mode changed
    """
    if target_percent < 0: target_percent = 0
    if target_percent > 100: target_percent = 100

    start_brightness = current_brightness[noodle_index]
    step_delay = duration / steps

    for i in range(steps + 1):
        # Check if mode changed
        if current_mode != "WAVE" and current_mode != "CHASE" and current_mode != "INDIVIDUAL":
            # Allow fade operations in certain modes only
            pass

        progress = i / steps
        brightness = start_brightness + (target_percent - start_brightness) * progress
        set_brightness(noodle_index, brightness)
        time.sleep(step_delay)

    return True

def fade_all(target_percent, duration=1.0, steps=50):
    """Fade all LEDs to the same brightness"""
    if target_percent < 0: target_percent = 0
    if target_percent > 100: target_percent = 100

    start_values = list(current_brightness)
    step_delay = duration / steps

    for i in range(steps + 1):
        progress = i / steps
        for n in range(len(noodles)):
            brightness = start_values[n] + (target_percent - start_values[n]) * progress
            set_brightness(n, brightness)
        time.sleep(step_delay)

    return True

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

class LEDLoop:
    """Context manager for easier LED control in loops"""
    def __init__(self, delay=0.1):
        self.delay = delay
        self.active = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.active = False
        return False

    def set(self, index, brightness):
        """Set LED brightness"""
        if self.active:
            set_brightness(index, brightness)

    def fade(self, index, target, duration=0.5):
        """Fade LED to target brightness"""
        if self.active:
            fade_led(index, target, duration)

    def wait(self, duration=None):
        """Wait for specified duration or default delay"""
        if duration is None:
            duration = self.delay
        time.sleep(duration)
        return self.active

# --- LIGHT SHOW LOGIC (Thread 1) ---

def run_light_show():
    global current_mode, individual_brightness
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
            # Blink Sequence - individual LEDs
            for i in range(4):
                if current_mode != "BLINK": break
                all_off()
                set_brightness(i, 100)
                if not smart_sleep(0.5, "BLINK"): break

        elif current_mode == "PULSE":
            # Pulse In
            for b in range(0, 101, 2):
                if current_mode != "PULSE": break
                for n in range(4): set_brightness(n, b)
                time.sleep(0.02)

            # Pulse Out
            for b in range(100, -1, -2):
                if current_mode != "PULSE": break
                for n in range(4): set_brightness(n, b)
                time.sleep(0.02)

        elif current_mode == "WAVE":
            # Wave effect - each LED fades in and out in sequence
            for i in range(4):
                if current_mode != "WAVE": break
                # Fade in this LED while fading out the others
                fade_led(i, 100, duration=0.4, steps=20)
                if current_mode != "WAVE": break
                fade_led(i, 0, duration=0.4, steps=20)

        elif current_mode == "CHASE":
            # Chase effect - LEDs light up in sequence with overlapping fades
            all_off()
            for i in range(4):
                if current_mode != "CHASE": break
                # Fade in current LED
                fade_led(i, 100, duration=0.3, steps=15)
                # Fade out previous LED
                if i > 0:
                    fade_led(i - 1, 0, duration=0.3, steps=15)
                elif i == 0:
                    # Fade out last LED on first iteration
                    fade_led(3, 0, duration=0.3, steps=15)
            # Clean up - fade out last LED
            if current_mode == "CHASE":
                fade_led(3, 0, duration=0.3, steps=15)

        elif current_mode == "INDIVIDUAL":
            # Individual control mode - set each LED to its individual brightness
            for i in range(4):
                set_brightness(i, individual_brightness[i])
            time.sleep(0.1)

# --- WIFI & WEB SERVER (Thread 2) ---


def web_page():
    global individual_brightness
    # Enhanced HTML with buttons and individual LED controls
    html = """<html>
    <head> <title>Noodle Control</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
    body{font-family:sans-serif; text-align:center; margin-top:20px; background:#222; color:#fff;}
    button{width:150px; height:50px; font-size:18px; margin:5px; border-radius:10px; border:none; cursor:pointer;}
    .on{background:#4CAF50; color:white;}
    .off{background:#f44336; color:white;}
    .eff{background:#2196F3; color:white;}
    .ind{background:#FF9800; color:white;}
    .led-control{background:#333; padding:15px; margin:20px auto; width:90%; max-width:400px; border-radius:10px;}
    .slider{width:80%; margin:10px auto;}
    input[type=range]{width:100%; height:8px; border-radius:5px; background:#555; outline:none;}
    input[type=range]::-webkit-slider-thumb{appearance:none; width:20px; height:20px; border-radius:50%; background:#4CAF50; cursor:pointer;}
    input[type=range]::-moz-range-thumb{width:20px; height:20px; border-radius:50%; background:#4CAF50; cursor:pointer;}
    .led-label{font-size:16px; margin:5px 0;}
    h2{margin:10px; font-size:20px;}
    </style>
    </head>
    <body>
    <h1>Noodle Command</h1>
    <div>
    <a href="/?mode=ON"><button class="on">ALL ON</button></a>
    <a href="/?mode=OFF"><button class="off">ALL OFF</button></a><br>
    <a href="/?mode=BLINK"><button class="eff">BLINK</button></a>
    <a href="/?mode=PULSE"><button class="eff">PULSE</button></a><br>
    <a href="/?mode=WAVE"><button class="eff">WAVE</button></a>
    <a href="/?mode=CHASE"><button class="eff">CHASE</button></a><br>
    <a href="/?mode=INDIVIDUAL"><button class="ind">INDIVIDUAL</button></a>
    </div>
    <div class="led-control">
    <h2>Individual LED Control</h2>
    <form action="/" method="get">
    <input type="hidden" name="mode" value="INDIVIDUAL">
    <div class="led-label">LED 1: <span id="val0">""" + str(individual_brightness[0]) + """</span>%</div>
    <input type="range" name="led0" min="0" max="100" value='""" + str(individual_brightness[0]) + """' class="slider" oninput="this.previousElementSibling.querySelector('span').innerText=this.value"><br>
    <div class="led-label">LED 2: <span id="val1">""" + str(individual_brightness[1]) + """</span>%</div>
    <input type="range" name="led1" min="0" max="100" value='""" + str(individual_brightness[1]) + """' class="slider" oninput="this.previousElementSibling.querySelector('span').innerText=this.value"><br>
    <div class="led-label">LED 3: <span id="val2">""" + str(individual_brightness[2]) + """</span>%</div>
    <input type="range" name="led2" min="0" max="100" value='""" + str(individual_brightness[2]) + """' class="slider" oninput="this.previousElementSibling.querySelector('span').innerText=this.value"><br>
    <div class="led-label">LED 4: <span id="val3">""" + str(individual_brightness[3]) + """</span>%</div>
    <input type="range" name="led3" min="0" max="100" value='""" + str(individual_brightness[3]) + """' class="slider" oninput="this.previousElementSibling.querySelector('span').innerText=this.value"><br>
    <button type="submit" class="ind" style="margin-top:15px;">Apply</button>
    </form>
    </div>
    </body></html>"""
    return html

def parse_query_param(request, param):
    """Extract a query parameter value from the request"""
    try:
        start = request.find(param + '=')
        if start == -1:
            return None
        start += len(param) + 1

        # Find the end of the value - look for &, space, or line endings
        end = request.find('&', start)
        if end == -1:
            end = request.find(' ', start)
        if end == -1:
            end = request.find('\r', start)
        if end == -1:
            end = request.find('\n', start)
        if end == -1:
            end = len(request)

        value = request[start:end]
        return value.strip()
    except:
        return None

def start_server():
    global current_mode, individual_brightness
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    print('Listening on', addr)

    while True:
        try:
            cl, addr = s.accept()
            request = cl.recv(1024)
            request = request.decode('utf-8')

            # Parse the URL (Very basic parsing)
            if 'mode=ON' in request:
                current_mode = "ON"
            elif 'mode=OFF' in request:
                current_mode = "OFF"
            elif 'mode=BLINK' in request:
                current_mode = "BLINK"
            elif 'mode=PULSE' in request:
                current_mode = "PULSE"
            elif 'mode=WAVE' in request:
                current_mode = "WAVE"
            elif 'mode=CHASE' in request:
                current_mode = "CHASE"
            elif 'mode=INDIVIDUAL' in request:
                current_mode = "INDIVIDUAL"
                # Parse individual LED brightness values
                for i in range(4):
                    param_name = 'led' + str(i)
                    value = parse_query_param(request, param_name)
                    if value is not None:
                        try:
                            brightness = int(value)
                            if 0 <= brightness <= 100:
                                individual_brightness[i] = brightness
                        except:
                            pass

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
