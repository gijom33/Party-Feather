# Button handling with press durations and visual progress bar feedback
import time
import math

class ButtonHandler:
    # Press duration thresholds (seconds)
    SHORT_MAX = 0.5
    MEDIUM_MAX = 1.5
    LONG_MIN = 1.5

    def __init__(self, button, show):
        self.button = button
        self.show = show

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

    def check_press(self):
        """Check for button press and handle appropriately"""
        if not self.button.value:  # pressed
            # debounce
            time.sleep(0.02)
            if self.button.value:  # button released during debounce
                return
            print("Button pressed!")

            t_start = time.monotonic()
            # wait for release, showing feedback while pressed
            print("Waiting for button release...")
            while not self.button.value:  # while pressed
                duration = time.monotonic() - t_start
                self._show_press_feedback(duration)
                time.sleep(0.01)
            
            # Clear feedback
            self.show.pixel32.fill((0, 0, 0))
            self.show.pixel32.show()
            if self.show.pixel:
                self.show.pixel[0] = (0, 0, 0)
                self.show.pixel.show()
            
            duration = time.monotonic() - t_start
            print("Button press duration:", duration)
            self.handle_press(duration)

    def handle_press(self, duration):
        """Handle a button press of the given duration"""
        if duration < self.SHORT_MAX:
            # short press: next set (palette)
            old_set = self.show.set_idx
            # Use sets_per_mode to determine the max sets for current mode
            max_sets = self.show.sets_per_mode[self.show.mode]
            self.show.set_idx = (self.show.set_idx + 1) % max_sets
            self.show.palette_pos = 0
            print(f"Short press: set {old_set} -> {self.show.set_idx}")
            
            # Show set number
            self.show.show_set_number(self.show.set_idx, color=(0, 0, 64))  # dim blue
            
            # Show first color of new set (only in non-brightness modes)
            if self.show.mode != 3:  # Not in brightness mode
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
            
            print(f"Medium press: mode {old_mode} -> {self.show.mode} (set {self.show.set_idx})")
            # Show mode number on the grid
            self.show.show_number(self.show.mode, color=(64, 64, 0))  # yellow number
            # Show current set number for this mode
            time.sleep(0.3)  # Brief pause between mode and set display
            self.show.show_set_number(self.show.set_idx, color=(0, 0, 64))  # dim blue
            self.show.last_palette_change = 0

        else:
            # long press: toggle active state
            self.show.active = False
            print("Long press: shutting off LEDs")
            self.show.show_off()

            # Wait for wake-up long press
            while True:
                while self.button.value:
                    time.sleep(0.02)
                t0 = time.monotonic()
                
                # Show feedback while waiting for long-press to wake
                while not self.button.value:
                    held = time.monotonic() - t0
                    
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
                    
                    time.sleep(0.02)
                
                # Make sure we clear the strip after release
                self.show.pixel32.fill((0, 0, 0))
                self.show.pixel32.show()
                if self.show.pixel:
                    self.show.pixel[0] = (0, 0, 0)
                    self.show.pixel.show()
                held = time.monotonic() - t0
                
                # Clear feedback
                self.show.show_off()
                
                if held >= self.LONG_MIN:
                    # Reset to initial state
                    self.show.active = True
                    self.show.mode = 0  # First mode (cycle)
                    # Reset all mode-specific sets
                    self.show.mode_sets = [0] * self.show.mode_count
                    self.show.set_idx = 0  # First color set
                    self.show.palette_pos = 0
                    self.show.rotate_pos = 0
                    print("Waking from shutoff - reset to initial mode and set")
                    self.show.flash_feedback(0.12)
                    self.show.last_palette_change = time.monotonic()
                    break