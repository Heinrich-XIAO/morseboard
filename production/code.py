import time
import board
import digitalio
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.consumer_control_code import ConsumerControlCode
import adafruit_matrixkeypad
import supervisor

import adafruit_fancyled.adafruit_fancyled as fancy
import neopixel

# rotary encoder (A = D3, B = D4)
encoder_pin_a = digitalio.DigitalInOut(board.MOSI)
encoder_pin_a.direction = digitalio.Direction.INPUT
encoder_pin_a.pull = digitalio.Pull.UP

encoder_pin_b = digitalio.DigitalInOut(board.MISO)
encoder_pin_b.direction = digitalio.Direction.INPUT
encoder_pin_b.pull = digitalio.Pull.UP

last_encoder_state = (encoder_pin_a.value, encoder_pin_b.value)


rows = [
    digitalio.DigitalInOut(board.SCK),
    digitalio.DigitalInOut(board.RX),
]
cols = [
    digitalio.DigitalInOut(board.A1),
    digitalio.DigitalInOut(board.A2),
    digitalio.DigitalInOut(board.A3),
]
keymap = [
    [Keycode.A, Keycode.B, Keycode.C],
    [Keycode.D, Keycode.E, Keycode.F]
]
kpad = adafruit_matrixkeypad.Matrix_Keypad(rows, cols, keymap)

kbd = Keyboard(usb_hid.devices)

# positions [0][0] -> [1][0] used for morse code
SYMBOL_KEYS = [Keycode.A, Keycode.B, Keycode.C, Keycode.E]
key_indices = {k: i for i, k in enumerate(SYMBOL_KEYS)}
DOT_THRESHOLD = 0.3

# morse code to keycode
MORSE_MAP = {
    ".-  ": Keycode.A,
    "-...": Keycode.B,
    "-.-.": Keycode.C,
    "-.. ": Keycode.D,
    ".   ": Keycode.E,
    "..-.": Keycode.F,
    "--. ": Keycode.G,
    "....": Keycode.H,
    "..  ": Keycode.I,
    ".---": Keycode.J,
    "-.- ": Keycode.K,
    ".-..": Keycode.L,
    "--  ": Keycode.M,
    "-.  ": Keycode.N,
    "--- ": Keycode.O,
    ".--.": Keycode.P,
    "--.-": Keycode.Q,
    ".-. ": Keycode.R,
    "... ": Keycode.S,
    "-   ": Keycode.T,
    "..- ": Keycode.U,
    "...-": Keycode.V,
    ".-- ": Keycode.W,
    "-..-": Keycode.X,
    "-.--": Keycode.Y,
    "--..": Keycode.Z,
    "  . ": Keycode.SPACE,
    "   .": Keycode.BACKSPACE
}

press_times = {}
pressed_last = set()
symbol_sequence = [' ', ' ', ' ', ' ']

def decode_and_send():
    if not symbol_sequence or symbol_sequence == [' ', ' ', ' ', ' ']:
        return
    print(symbol_sequence)
    code = "".join(symbol_sequence)
    print(f"Sequence complete: {code}")
    if code in MORSE_MAP:
        kbd.send(MORSE_MAP[code])
        print(f"Sent: {MORSE_MAP[code]}")
    else:
        print("Unknown Morse:", code)





# Configuration
NUM_PIXELS = 6
PIXEL_PIN = board.A0
BRIGHTNESS = 0.1  # Max brightness (0.0 - 1.0) for the breathing effect
BREATH_SPEED = 0.01  # Adjust this value for faster/slower breathing

# Initialize NeoPixel strip
pixels = neopixel.NeoPixel(PIXEL_PIN, NUM_PIXELS, brightness=BRIGHTNESS, auto_write=False)

# Define the light blue color
# You can adjust these R, G, B values for different shades of light blue
LIGHT_BLUE = fancy.CRGB(0, 191, 255)  # A nice bright light blue

RED = fancy.CRGB(255, 0, 0)

GREEN = fancy.CRGB(0, 255, 0)


# Variable to control the brightness level for the breathing effect
# We'll use a sine wave to make it smoothly go up and down
brightness_level = 0.0
direction = -1  # 1 for increasing brightness, -1 for decreasing


count = 0
# polling is great
while True:
    now = time.monotonic()
    currently_pressed = set(kpad.pressed_keys)

    # track press start times
    for key in currently_pressed - pressed_last:
        if key in SYMBOL_KEYS:
            press_times[key] = now
            

    # track releases
    for key in pressed_last - currently_pressed:
        if key in press_times and key in SYMBOL_KEYS:
            held_time = now - press_times[key]
            symbol = "." if held_time < DOT_THRESHOLD else "-"
            index = key_indices[key]
            # Ensure in-order input (ignore future keys if previous not pressed)
            symbol_sequence[index] = symbol
            del press_times[key]
        elif key not in SYMBOL_KEYS:
            kbd.send(key)

    if not currently_pressed and symbol_sequence:
        decode_and_send()
        symbol_sequence = [' ', ' ', ' ', ' ']

    pressed_last = currently_pressed

    current_state = (encoder_pin_a.value, encoder_pin_b.value)

    if current_state != last_encoder_state:
        if last_encoder_state == (1, 1):
            if current_state == (0, 1):
                kbd.send(ConsumerControlCode.VOLUME_INCREMENT)
                print("Volume up")
            elif current_state == (1, 0):
                kbd.send(ConsumerControlCode.VOLUME_DECREMENT)
                print("Volume down")

        last_encoder_state = current_state
    
    if count % 1 == 0:
        # Update brightness_level based on direction and speed
        brightness_level += direction * BREATH_SPEED

        # Reverse direction when limits are reached
        if brightness_level >= 0.95:
            brightness_level = 0.9
            direction = -1
        elif brightness_level <= 0.05:
            brightness_level = 0.05
            direction = 1

        # Apply the current brightness_level to the light blue color
        # and then pack it for the NeoPixel
        scaled_color = fancy.gamma_adjust(LIGHT_BLUE, brightness_level)

        # Set all pixels to the calculated color
        for i in range(NUM_PIXELS):
            if i>4 or not SYMBOL_KEYS[i-1] in currently_pressed:
                pixels[i] = scaled_color.pack()
    
        pixels.show()
    
    for key in currently_pressed:
        if key in SYMBOL_KEYS:
            held_time = now - press_times[key]
            if press_times[key]:
                if now - press_times[key] < DOT_THRESHOLD:
                    pixels[SYMBOL_KEYS.index(key)+1] = RED.pack()
                else:
                    pixels[SYMBOL_KEYS.index(key)+1] = GREEN.pack()
                
    
    pixels.show()
    
    time.sleep(0.01)
    count += 1
