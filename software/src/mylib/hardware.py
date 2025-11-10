# Hardware initialization and stubs
import time
import board # pyright: ignore[reportMissingImports]
import digitalio # pyright: ignore[reportMissingImports]
import neopixel # pyright: ignore[reportMissingImports]

# Track if we have real hardware or are using stubs
have_hardware = False

# Stub classes for graceful fallback
class led_stub:
    def __init__(self):
        self.value = False

class pixel_stub:
    def __init__(self, n):
        self._n = n
        self.data = [(0, 0, 0)] * n
    def fill(self, color):
        for i in range(self._n):
            self.data[i] = color
    def show(self):
        pass
    def __setitem__(self, idx, val):
        if 0 <= idx < self._n:
            self.data[idx] = val
    def __len__(self):
        return self._n

class button_stub:
    def __init__(self):
        self.value = True

def init_hardware():
    """Initialize all hardware with fallbacks"""
    led = None
    button = None
    pixel = None
    pixel32 = None
    mic = None
    
    try:
        # CircuitPython boards have these by default
        global have_hardware
        have_hardware = True
        print("o Successfully imported hardware libraries")
    except ImportError as e:
        print(f"o Import error: {e}")
        print("o Failed to import hardware libraries - running in stub mode")
        return led_stub(), button_stub(), pixel_stub(1), pixel_stub(32), None
    
    # LED init
    try:
        led = digitalio.DigitalInOut(board.LED)
        led.direction = digitalio.Direction.OUTPUT
    except Exception:
        led = led_stub()

    # Single NeoPixel
    try:
        np_pin = getattr(board, "NEOPIXEL", None)
        if np_pin is not None:
            pixel = neopixel.NeoPixel(np_pin, 1, brightness=0.01, auto_write=False)
            print("Single NeoPixel initialized on", np_pin)
        else:
            print("No NEOPIXEL pin found")
            pixel = pixel_stub(1)
    except Exception as e:
        print("NeoPixel init failed:", e)
        pixel = pixel_stub(1)

    # LED init
    try:
        led = digitalio.DigitalInOut(board.LED)
        led.direction = digitalio.Direction.OUTPUT
    except Exception:
        led = led_stub()

    # Single NeoPixel
    try:
        np_pin = getattr(board, "NEOPIXEL", None)
        if np_pin is not None:
            pixel = neopixel.NeoPixel(np_pin, 1, brightness=0.01, auto_write=False)
            print("o Single NeoPixel initialized on", np_pin)
        else:
            print("o No NEOPIXEL pin found")
            pixel = pixel_stub(1)
    except Exception as e:
        print("o NeoPixel init failed:", e)
        pixel = pixel_stub(1)

    # FeatherWing 32-LED strip
    try:
        fw_pin = None
        for pin_name in ('D6', 'D5', 'D9', 'D10'):
            if hasattr(board, pin_name):
                fw_pin = getattr(board, pin_name)
                try:
                    pixel32 = neopixel.NeoPixel(fw_pin, 32, brightness=0.04, auto_write=False)
                    print("o FeatherWing initialized on", fw_pin)
                    break
                except Exception:
                    continue
        if fw_pin is None:
            print("o No valid FeatherWing pin found")
            pixel32 = pixel_stub(32)
    except Exception as e:
        print("o FeatherWing init failed:", e)
        pixel32 = pixel_stub(32)

    # Button
    if have_hardware:
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
                print("o Button initialized on", button_pin)
            except Exception as e:
                print("o Button init failed:", e)
                button = button_stub()
        else:
            print("o No button pin found")
            button = button_stub()
    else:
        button = button_stub()

    # Microphone (optional)
    try:
        import pio_i2s # pyright: ignore[reportMissingImports] # tpe: ignore
        mic = pio_i2s.I2S(
            data_in=getattr(board, 'D10', None),
            bit_clock=getattr(board, 'D11', None),
            channel_count=1,
            sample_rate=48000,
            bits_per_sample=16,
            samples_signed=True,
            buffer_size=4096,
            peripheral=False,
        )
        print("o Microphone initialized")
    except Exception as e:
        print("o Microphone init failed:", e)
        mic = None

    return led, button, pixel, pixel32, mic