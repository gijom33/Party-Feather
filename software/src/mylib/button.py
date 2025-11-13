# Button handling with press durations and visual progress bar feedback
import time
import math
try:
    import digitalio  # pyright: ignore[reportMissingImports]
except ImportError:
    digitalio = None

class button_handler:
    # Press duration thresholds (seconds)
    SHORT_MAX = 0.5
    MEDIUM_MAX = 1.5
    LONG_MIN = 1.5

    def __init__(self, button, show):
        self.button = button
        self.show = show
        
        # Interrupt-based state tracking
        self.press_start_time = None
        self.is_pressed = False
        self.last_button_state = button.value if hasattr(button, 'value') else True
        self.wake_mode = False  # Special mode for long-press wake-up
        self.debounce_time = 0
        # Save state before shutdown for wake-up restoration
        self.saved_mode = 0
        self.saved_set_idx = 0
        
        # Try to use keypad module for better interrupt-like behavior
        self.use_keypad = False
        try:
            import keypad  # pyright: ignore[reportMissingImports]
            # Check if button pin supports keypad
            if hasattr(button, 'pin') or (hasattr(button, 'value') and hasattr(button, 'direction')):
                # For now, we'll use efficient polling that behaves like interrupts
                self.use_keypad = False  # Keep using digitalio for compatibility
        except ImportError:
            pass

    def _check_button_state(self):
        """Check button state changes (interrupt-like behavior)"""
        if not hasattr(self.button, 'value'):
            return False
        
        current_state = self.button.value
        now = time.monotonic()
        
        # Debounce check
        if now - self.debounce_time < 0.02:
            return False
        
        # Detect falling edge (button press)
        if not current_state and self.last_button_state and not self.is_pressed:
            # Button just pressed
            self.debounce_time = now
            self.press_start_time = now
            self.is_pressed = True
            self.last_button_state = current_state
            return True
        
        # Detect rising edge (button release)
        if current_state and not self.last_button_state and self.is_pressed:
            # Button just released
            self.debounce_time = now
            self.is_pressed = False
            self.last_button_state = current_state
            return True
        
        self.last_button_state = current_state
        return False

    def _show_press_feedback(self, duration):
        """Show visual progress bar feedback based on press duration"""
        # Calculate progress through each stage
        if duration < self.SHORT_MAX:
            # Short press: blue progress bar
            progress = duration / self.SHORT_MAX
            color = (0, 0, 64)  # dim blue
        elif duration < self.MEDIUM_MAX:
            # Medium press: yellow progress bar
            progress = (duration - self.SHORT_MAX) / (self.MEDIUM_MAX - self.SHORT_MAX)
            color = (64, 64, 0)  # dim yellow
        else:
            # Long press: red bar fills immediately
            progress = 1.0
            color = (64, 0, 0)  # dim red
            
        # Calculate how many LEDs to light based on progress
        num_pixels = len(self.show.pixel32)
        lit_pixels = int(num_pixels * progress)
        
        # Fill the progress bar
        for i in range(num_pixels):
            if i < lit_pixels:
                self.show.pixel32[i] = color
            else:
                self.show.pixel32[i] = (0, 0, 0)
        self.show.pixel32.show()
        
        # Show current stage color on the single pixel
        if self.show.pixel:
            self.show.pixel[0] = color
            self.show.pixel.show()

    def is_showing_feedback(self):
        """Returns True if button feedback is currently being displayed"""
        return (self.is_pressed and self.press_start_time is not None) or self.wake_mode

    def update(self):
        """Update button state - call this from main loop (interrupt-driven)"""
        # Don't check normal button state if we're in wake mode
        if not self.wake_mode:
            # Check for button state changes (interrupt-like detection)
            state_changed = self._check_button_state()
            
            # If button was just released, handle it
            if state_changed and not self.is_pressed and self.press_start_time is not None:
                duration = time.monotonic() - self.press_start_time
                
                # Clear feedback
                self.show.pixel32.fill((0, 0, 0))
                self.show.pixel32.show()
                if self.show.pixel:
                    self.show.pixel[0] = (0, 0, 0)
                    self.show.pixel.show()
                
                # Handle the press
                self.handle_press(duration)
                self.press_start_time = None
                return
        
        # Update visual feedback if button is currently pressed (and not in wake mode)
        if self.is_pressed and self.press_start_time is not None and not self.wake_mode:
            duration = time.monotonic() - self.press_start_time
            self._show_press_feedback(duration)
        
        # Handle wake mode (waiting for long press to wake up)
        if self.wake_mode:
            # Check for button state changes in wake mode using edge detection
            if hasattr(self.button, 'value'):
                current_state = self.button.value
                now = time.monotonic()
                
                # Wake mode state machine: wait for release, then detect new press
                if not self.is_pressed and self.press_start_time is None:
                    # Not currently tracking a press
                    state_changed = (self.last_button_state != current_state)
                    
                    if not current_state:
                        # Button is currently pressed
                        if state_changed and self.last_button_state:
                            # Falling edge detected: button was released, now pressed - start wake timer
                            if now - self.debounce_time >= 0.02:
                                self.debounce_time = now
                                self.press_start_time = now
                                self.is_pressed = True
                                self.last_button_state = current_state
                        # Update state if it changed
                        if state_changed:
                            self.last_button_state = current_state
                        return  # Button is pressed, wait for release
                    else:
                        # Button is currently released
                        # Update state
                        if state_changed:
                            self.last_button_state = current_state
                        # Button is released - continue to check for visual feedback
                
                # Update visual feedback while button is held in wake mode
                if self.is_pressed and self.press_start_time is not None:
                    held = time.monotonic() - self.press_start_time
                    
                    # Calculate wake progress (0 to 1.0)
                    wake_progress = min(held / self.LONG_MIN, 1.0)
                    
                    # Map progress to colors (fade from dim blue to bright white)
                    if wake_progress < 0.5:
                        # First half: blue filling up
                        intensity = int(32 * (wake_progress * 2))  # 0 to 32
                        color = (0, 0, intensity)
                    else:
                        # Second half: add white to make it brighter
                        white = int(64 * ((wake_progress - 0.5) * 2))  # 0 to 64
                        color = (white, white, 64)  # keeps blue component bright
                    
                    # Update progress bar
                    num_pixels = len(self.show.pixel32)
                    lit_pixels = int(num_pixels * wake_progress)
                    
                    # Fill the bar
                    for i in range(num_pixels):
                        if i < lit_pixels:
                            self.show.pixel32[i] = color
                        else:
                            self.show.pixel32[i] = (0, 0, 0)
                    self.show.pixel32.show()
                    
                    # Update onboard pixel
                    if self.show.pixel:
                        self.show.pixel[0] = color if lit_pixels > 0 else (0, 0, 0)
                        self.show.pixel.show()
                
                # Detect rising edge (button release) in wake mode
                if current_state and not self.last_button_state and self.is_pressed and self.press_start_time is not None:
                    # Button just released - check if it was held long enough
                    if now - self.debounce_time >= 0.02:
                        self.debounce_time = now
                        held = time.monotonic() - self.press_start_time
                        self.is_pressed = False
                        
                        # Clear feedback
                        self.show.pixel32.fill((0, 0, 0))
                        self.show.pixel32.show()
                        if self.show.pixel:
                            self.show.pixel[0] = (0, 0, 0)
                            self.show.pixel.show()
                        
                        if held >= self.LONG_MIN:
                            # Restore previous state
                            self.show.active = True
                            self.show.mode = self.saved_mode
                            self.show.set_idx = self.saved_set_idx
                            self.show.palette_pos = 0
                            self.show.rotate_pos = 0
                            print(f"Wake: mode {self.show.mode}, set {self.show.set_idx}")
                            self.show.flash_feedback(0.12)
                            self.show.last_palette_change = time.monotonic()
                            self.wake_mode = False
                        
                        self.press_start_time = None
                        self.last_button_state = current_state  # Update state after release handling
                
                # State is already updated in the state machine above
                # No need for additional state updates here

    def handle_press(self, duration):
        """Handle a button press of the given duration"""
        if duration < self.SHORT_MAX:
            # short press: next set (palette)
            old_set = self.show.set_idx
            # Use sets_per_mode to determine the max sets for current mode
            max_sets = self.show.sets_per_mode[self.show.mode]
            self.show.set_idx = (self.show.set_idx + 1) % max_sets
            self.show.palette_pos = 0
            print(f"Set: {self.show.set_idx}")
            
            # Show set number (skip in brightness mode)
            if self.show.mode != 3:  # Not in brightness mode
                self.show.show_set_number(self.show.set_idx, color=(0, 0, 64))  # dim blue
                # Show first color of new set
                self.show.show_palette_color(self.show.sets[self.show.set_idx][0])

        elif duration < self.MEDIUM_MAX:
            # medium press: next mode
            old_mode = self.show.mode
            # Save current set for the old mode
            self.show.mode_sets[old_mode] = self.show.set_idx
            
            # Switch to next mode
            self.show.mode = (self.show.mode + 1) % self.show.mode_count
            # Restore the saved set for the new mode
            self.show.set_idx = self.show.mode_sets[self.show.mode]
            self.show.palette_pos = 0
            self.show.rotate_pos = 0
            
            print(f"Mode: {self.show.mode}, Set: {self.show.set_idx}")
            # Show mode number on the grid
            self.show.show_number(self.show.mode, color=(64, 64, 0))  # yellow number
            # Show current set number for this mode (skip in brightness mode)
            if self.show.mode != 3:  # Not in brightness mode
                time.sleep(0.3)  # Brief pause between mode and set display
                self.show.show_set_number(self.show.set_idx, color=(0, 0, 64))  # dim blue
            self.show.last_palette_change = 0

        else:
            # long press: toggle active state
            # Save current state before shutting down
            self.saved_mode = self.show.mode
            self.saved_set_idx = self.show.set_idx
            self.show.active = False
            print("Off")
            self.show.show_off()
            self.wake_mode = True
            self.press_start_time = None
            # Reset button state tracking to ensure clean wake detection
            self.is_pressed = False
            if hasattr(self.button, 'value'):
                self.last_button_state = self.button.value