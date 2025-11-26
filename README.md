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
2. Configure WiFi credentials if needed
3. Run the script - it will start the web server automatically
4. Access the web interface to control your LEDs