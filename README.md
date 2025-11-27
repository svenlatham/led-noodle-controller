# LED Noodle Controller

Advanced Raspberry Pi Pico 2 W controller for 4 LED noodles with individual control and smooth fade effects.

## Hardware Requirements

- Raspberry Pi Pico 2 W
- 4 LED noodles connected to GPIO pins 16, 17, 19, 18

## Features

### Display Modes
- **OFF** - All LEDs off
- **ON** - All LEDs at full brightness
- **BLINK** - Sequential blinking pattern
- **PULSE** - Smooth breathing effect on all LEDs
- **WAVE** - Wave effect with individual LED fades
- **CHASE** - Chasing pattern with overlapping fades
- **WARP ENGINE** - Star Trek TNG warp nacelle effect with power-up sequence and steady pulse
- **INDIVIDUAL** - Manual control of each LED via web interface

### LED Control API

#### Individual LED Control
```python
set_led(index, brightness)        # Set LED brightness (0-100%)
set_brightness(index, brightness)  # Same as set_led
set_all(brightness)               # Set all LEDs to same brightness
all_off()                         # Turn off all LEDs
```

#### Fade Functions
```python
fade_led(index, target, duration=1.0, steps=50)  # Fade single LED
fade_all(target, duration=1.0, steps=50)         # Fade all LEDs
```

#### Loop-Friendly Interface
```python
with LEDLoop(delay=0.1) as loop:
    for i in range(4):
        loop.set(i, 100)
        loop.wait()
    for i in range(4):
        loop.fade(i, 0, duration=0.5)
```

## Web Interface

Access the web interface by connecting to the Pico's IP address. Features include:
- Mode selection buttons
- Individual LED brightness sliders
- Real-time control of all 4 LEDs

## Usage Examples

### Set Individual LEDs
```python
set_led(0, 75)   # Set LED 0 to 75%
set_led(1, 100)  # Set LED 1 to 100%
```

### Fade Individual LEDs
```python
fade_led(0, 100, duration=2.0)              # Fade LED 0 to 100% over 2 seconds
fade_led(1, 0, duration=1.0, steps=30)      # Fade LED 1 off with 30 steps
```

### Create Custom Patterns
```python
# Sequential fade pattern
for i in range(4):
    fade_led(i, 100, duration=0.5)
    fade_led(i, 0, duration=0.5)

# Overlapping waves
for i in range(4):
    fade_led(i, 100, duration=0.3)
    if i > 0:
        fade_led(i-1, 0, duration=0.3)
```

### Using LEDLoop for Clean Code
```python
with LEDLoop(delay=0.2) as loop:
    for brightness in range(0, 101, 10):
        for led in range(4):
            loop.set(led, brightness)
        loop.wait()
```

## Installation

1. Upload `main.py` to your Pico 2 W
2. Configure WiFi credentials:
   - Copy `wifi_config.example.py` to `wifi_config.py`
   - Edit `wifi_config.py` and add your WiFi network name and password
   - Optionally adjust retry interval and timeout settings
3. Upload `wifi_config.py` to your Pico 2 W
4. Run the script - it will automatically:
   - Connect to your WiFi network
   - Monitor the connection and retry every 30 seconds if disconnected
   - Start the web server
5. Find your Pico's IP address in the console output
6. Access the web interface at `http://<pico-ip-address>` to control your LEDs

## WiFi Configuration

The WiFi credentials are stored in `wifi_config.py`, which is not tracked by git for security. This file contains:

- `WIFI_SSID`: Your WiFi network name
- `WIFI_PASSWORD`: Your WiFi password
- `WIFI_RETRY_INTERVAL`: Seconds between reconnection attempts (default: 30)
- `WIFI_CONNECT_TIMEOUT`: Seconds to wait for initial connection (default: 10)

The controller will automatically attempt to reconnect if the WiFi connection is lost, checking every `WIFI_RETRY_INTERVAL` seconds.

### WiFi Status LED Indicators

The LEDs provide visual feedback for WiFi connection status:
- **Connecting**: LED noodle 0 flashes on/off while attempting to connect
- **Connected**: All 4 LED noodles flash together 3 times to indicate successful connection
- **Reconnected**: All 4 LED noodles flash together 2 times when reconnection succeeds
- **Failed**: LED noodle 0 turns off if connection fails