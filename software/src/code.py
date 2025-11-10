"""
Main program for LED light show with button control
"""
import time
from mylib.hardware import init_hardware
from mylib.lightshow import light_show
from mylib.button import button_handler

def main():
    # Initialize all hardware (with fallbacks if missing)
    led, button, pixel, pixel32, mic = init_hardware()
    
    # Create light show controller
    show = light_show(led, pixel, pixel32)
    
    # Create button handler
    handler = button_handler(button, show)
    
    print("\nStarting main loop. Short/medium/long button presses will be handled.")
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