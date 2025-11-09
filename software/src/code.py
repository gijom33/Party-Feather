"""
Main program for LED light show with button control
"""
import time
import board # pyright: ignore[reportMissingImports]
import digitalio # pyright: ignore[reportMissingImports]
import neopixel # pyright: ignore[reportMissingImports]
import pio_i2s # pyright: ignore[reportMissingImports]

from mylib.hardware import init_hardware, have_hardware
from mylib.lightshow import LightShow
from mylib.button import ButtonHandler

def main():
    # Initialize all hardware (with fallbacks if missing)
    led, button, pixel, pixel32, mic = init_hardware()
    
    # Create light show controller
    show = LightShow(led, pixel, pixel32)
    
    # Create button handler
    handler = ButtonHandler(button, show)
    
    print("Starting main loop. Short/medium/long button presses will be handled.")
    print("- Short press: change color set")
    print("- Medium press: change mode (flags/explosions/glitter/brightness)")
    print("- Long press: turn off/on")
    
    while True:
        # Update animation
        show.animate_step()
        
        # Check for button presses
        handler.check_press()
        
        # Keep CPU friendly
        time.sleep(0.01)

if __name__ == "__main__":
    main()

# Safe hardware setup: handle missing pins gracefully so code runs on different boards

# Feather onboard LED (fallback: create a dummy with .value)
try:
    led = digitalio.DigitalInOut(board.LED)
    led.direction = digitalio.Direction.OUTPUT
except Exception:
    class _LedStub:
        def __init__(self):
            self.value = False
    led = _LedStub()

# Pixel stub (used when a real NeoPixel string isn't present). Implements the
# minimal API used below: fill(), show(), __setitem__(), __len__().
class PixelStub:
    def __init__(self, n):
        self._n = n
        self.data = [(0, 0, 0)] * n
    def fill(self, color):
        for i in range(self._n):
            self.data[i] = color
    def show(self):
        # no-op for stub
        pass
    def __setitem__(self, idx, val):
        if 0 <= idx < self._n:
            self.data[idx] = val
    def __len__(self):
        return self._n

# Feather single NeoPixel (optional)
pixel = None
if have_hardware:
    try:
        np_pin = getattr(board, "NEOPIXEL", None)
        if np_pin is not None:
            pixel = neopixel.NeoPixel(np_pin, 1, brightness=0.01, auto_write=False)
            print("Single NeoPixel initialized on", np_pin)
        else:
            print("No NEOPIXEL pin found")
            pixel = PixelStub(1)
    except Exception as e:
        print("NeoPixel init failed:", e)
        pixel = PixelStub(1)
else:
    pixel = PixelStub(1)

# FeatherWing 32-LED strip (try D6 first, then other common pins)
if have_hardware:
    try:
        # Try a few common pins for the FeatherWing
        fw_pin = None
        for pin_name in ('D6', 'D5', 'D9', 'D10'):
            if hasattr(board, pin_name):
                fw_pin = getattr(board, pin_name)
                try:
                    pixel32 = neopixel.NeoPixel(fw_pin, 32, brightness=0.04, auto_write=False)
                    print("FeatherWing initialized on", pin_name)
                    break
                except Exception:
                    continue
        if fw_pin is None:
            print("No valid FeatherWing pin found")
            pixel32 = PixelStub(32)
    except Exception as e:
        print("FeatherWing init failed:", e)
        pixel32 = PixelStub(32)
else:
    pixel32 = PixelStub(32)

# Breakaway microphone (optional)
mic = None
if have_hardware:
    try:
        mic = pio_i2s.I2S(
            data_in=getattr(board, 'D10', None),
            bit_clock=getattr(board, 'D11', None),
            # word_select=board.D12,
            channel_count=1,
            sample_rate=48000,
            bits_per_sample=16,
            samples_signed=True,
            buffer_size=4096,
            peripheral=False,
        )
        print("Microphone initialized")
    except Exception as e:
        print("Microphone init failed:", e)
        mic = None

# Feather button (try board.BUTTON then a few fallbacks)
button = None
button_pin = getattr(board, 'BUTTON', None)
if button_pin is None:
    for name in ('D9', 'D5', 'SW1', 'BTN', 'BOOT'):
        button_pin = getattr(board, name, None)
        if button_pin is not None:
            break
if button_pin is not None:
    try:
        button = digitalio.DigitalInOut(button_pin)
        button.direction = digitalio.Direction.INPUT
        button.pull = digitalio.Pull.UP
    except Exception:
        button = None
if button is None:
    # create a fake button that is never pressed (value True == not pressed)
    class _ButtonStub:
        def __init__(self):
            self.value = True
    button = _ButtonStub()

# sets = palettes (user short-press cycles sets)
sets = [
    # French flag-ish set (blue, white, red)
    [(0, 0, 255), (255, 255, 255), (255, 0, 0)],
    # Warm set
    [(255, 16, 0), (255, 64, 0), (255, 128, 32)],
    # Cool set
    [(0, 32, 255), (0, 128, 255), (32, 255, 200)],
]

# modes: 0 = palette cycle, 1 = solid (current palette index), 2 = moving gradient
mode_count = 3
mode = 0
set_idx = 0

active = True  # when False, LEDs are shut off

# press duration thresholds (seconds)
SHORT_MAX = 0.5
MEDIUM_MAX = 1.5
LONG_MIN = 1.5

# animation state
last_step = time.monotonic()
last_palette_change = time.monotonic()  # moved from function attribute to global
palette_pos = 0
rotate_pos = 0

def flash_feedback(duration=0.08):
    led.value = True
    if pixel:
        pixel[0] = (255, 255, 255)
        pixel.show()
    time.sleep(duration)
    led.value = False
    if pixel:
        pixel[0] = (0, 0, 0)
        pixel.show()

def show_palette_color(color):
    pixel32.fill(color)
    pixel32.show()
    if pixel:
        pixel[0] = color
        pixel.show()

def show_off():
    pixel32.fill((0, 0, 0))
    pixel32.show()
    if pixel:
        pixel[0] = (0, 0, 0)
        pixel.show()
    led.value = False

def animate_step():
    global last_step, last_palette_change, palette_pos, rotate_pos
    now = time.monotonic()
    dt = now - last_step
    # small-step-driven animation (updates at ~50Hz)
    if dt < 0.02:
        return
    last_step = now

    if not active:
        return

    palette = sets[set_idx]
    if mode == 0:
        # palette cycle: change whole strip to next palette color every 0.6s
        if now - last_palette_change >= 0.6:
            c = palette[palette_pos % len(palette)]
            show_palette_color(c)
            palette_pos += 1
            last_palette_change = now
    elif mode == 1:
        # solid: show the selected color index in the palette (palette_pos used as index)
        idx = palette_pos % len(palette)
        show_palette_color(palette[idx])
    elif mode == 2:
        # moving gradient: rotate palette across the strip
        for i in range(len(pixel32)):
            # pick color from palette based on position + rotate_pos
            p = (i + rotate_pos) % len(palette)
            pixel32[i] = palette[p]
        pixel32.show()
        rotate_pos = (rotate_pos + 1) % len(palette)

# initialize palette change time
last_palette_change = time.monotonic()

def handle_press(duration):
    global set_idx, mode, active, palette_pos, last_palette_change
    print("Button press duration:", duration)  # Debug print
    
    if duration < SHORT_MAX:
        # short press: next set (palette)
        set_idx = (set_idx + 1) % len(sets)
        palette_pos = 0
        print("Short press: set ->", set_idx)
        flash_feedback(0.06)
        # show first color briefly
        show_palette_color(sets[set_idx][0])
        time.sleep(0.18)
    elif duration < MEDIUM_MAX:
        # medium press: next mode
        mode = (mode + 1) % mode_count
        palette_pos = 0
        rotate_pos = 0  # Reset position for moving gradient
        print("Medium press: mode ->", mode, "Modes: 0=cycle, 1=solid, 2=gradient")
        flash_feedback(0.12)
        # immediate update
        last_palette_change = 0
    else:
        # long press: shutoff / toggle active
        active = False
        print("Long press: shutting off LEDs")
        show_off()
        # Wait for a long-press to wake (press and hold LONG_MIN seconds)
        while True:
            # wait for button down
            while button.value:
                time.sleep(0.02)
            t0 = time.monotonic()
            # wait until release or threshold reached
            while not button.value:
                time.sleep(0.02)
            held = time.monotonic() - t0
            if held >= LONG_MIN:
                active = True
                print("Waking from shutoff")
                flash_feedback(0.12)
                # reset animation timers so we don't jump
                global last_palette_change
                last_palette_change = time.monotonic()
                break
            # otherwise ignore short taps while off

# main loop
print("Starting main loop. Short/medium/long button presses will be handled.")

while True:
    
    animate_step()

    # poll button for presses (blocking while pressed; small, acceptable)
    if not button.value:  # pressed (active-low)
        # debounce: confirm still pressed
        time.sleep(0.02)
        if button.value:
            continue
        t_start = time.monotonic()
        # wait for release
        while not button.value:
            time.sleep(0.01)
        duration = time.monotonic() - t_start
        # handle according to duration
        handle_press(duration)

    # keep CPU friendly
    time.sleep(0.01)