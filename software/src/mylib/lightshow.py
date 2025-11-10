# Animation patterns and utilities
import time

class light_show:
    def __init__(self, led, pixel, pixel32):
        self.led = led
        self.pixel = pixel
        self.pixel32 = pixel32
        
        # French flag colors (blue, white, red)
        self.sets = [
            [(0, 0, 255), (255, 255, 255), (255, 0, 0)],      # Set 0 - France (blue, white, red)
            [(255, 255, 255), (0, 0, 255), (255, 0, 0), (255, 200, 0)],  # Set 1 - Philippines (white, blue, red, yellow)
            [(255, 0, 0), (255, 255, 255), (255, 0, 0)],      # Set 2 - Canada (red, white, red)
            [(0, 0, 255), (255, 0, 0), (255, 255, 255)],      # Set 3 - USA (blue, red, white)
            [(0, 51, 153), (255, 255, 0), (0, 51, 153)]       # Set 4 - EU (blue, yellow, blue)
        ]
        
        # Brightness settings for mode 3
        self.brightness_levels = [
            0.04,  # Set 0: Ultra low brightness (4%)
            0.12,  # Set 1: Very low brightness (12%)
            0.25,  # Set 2: Low brightness (25%)
            0.50,  # Set 3: Medium brightness (50%)
            0.75,  # Set 4: High brightness (75%)
            1.00   # Set 5: Full brightness (100%)
        ]
        self.current_brightness = 0.25  # Start at low brightness
        
        # State
        self.mode = 0  # 0=cycle, 1=solid, 2=gradient, 3=settings
        self.mode_count = 4  # Added settings mode
        self.mode_sets = [0] * self.mode_count  # Remember set for each mode
        # Number of sets available in each mode
        self.sets_per_mode = [
            5,  # Mode 0 (flags): 5 sets (0-4)
            5,  # Mode 1 (explosion): 5 sets (0-4)
            5,  # Mode 2 (gradient): 5 sets (0-4)
            6   # Mode 3 (settings): 6 brightness levels (0-5)
        ]
        self.set_idx = 0
        self.active = True
        self.palette_pos = 0
        self.rotate_pos = 0
        self.last_step = time.monotonic()
        self.last_palette_change = time.monotonic()

    def flash_feedback(self, duration=0.08):
        self.led.value = True
        if self.pixel:
            self.pixel[0] = (255, 255, 255)
            self.pixel.show()
        time.sleep(duration)
        self.led.value = False
        if self.pixel:
            self.pixel[0] = (0, 0, 0)
            self.pixel.show()

    def show_palette_color(self, color):
        self.pixel32.fill(color)
        self.pixel32.show()
        if self.pixel:
            self.pixel[0] = color
            self.pixel.show()

    def show_off(self):
        self.pixel32.fill((0, 0, 0))
        self.pixel32.show()
        if self.pixel:
            self.pixel[0] = (0, 0, 0)
            self.pixel.show()
        self.led.value = False

    def show_set_number(self, number, color=(0, 0, 64), duration=0.4):  # dim blue for sets
        """Display a set number (S0-S2) on the 4x8 LED grid"""
        # Use your existing pixel font but with S prefix
        patterns = [
            # Set 0 - "S0"
            [
                1, 1, 1, 1, 0, 0, 1, 0,  # Row 0: S    0
                1, 1, 0, 0, 0, 1, 0, 1,  # Row 1: S    0
                0, 0, 1, 1, 0, 1, 0, 1,  # Row 2: S    0
                1, 1, 1, 1, 0, 0, 1, 0   # Row 3: S    0
            ],
            # Set 1 - "S1"
            [
                1, 1, 1, 1, 0, 0, 1, 0,  # Row 0: S    1
                1, 1, 0, 0, 0, 1, 1, 0,  # Row 1: S    1
                0, 0, 1, 1, 0, 0, 1, 0,  # Row 2: S    1
                1, 1, 1, 1, 0, 1, 1, 1   # Row 3: S    1
            ],
            # Set 2 - "S2"
            [
                1, 1, 1, 1, 0, 1, 1, 0,  # Row 0: S    2
                1, 1, 0, 0, 0, 0, 0, 1,  # Row 1: S    2
                0, 0, 1, 0, 0, 1, 1, 0,  # Row 2: S    2
                1, 1, 1, 1, 0, 1, 1, 1   # Row 3: S    2
            ],
            # Set 3 - "S3"
            [
                1, 1, 1, 1, 0, 1, 1, 1,  # Row 0: S    3
                1, 1, 0, 0, 0, 0, 1, 1,  # Row 1: S    3
                0, 0, 1, 1, 0, 0, 0, 1,  # Row 2: S    3
                1, 1, 1, 1, 0, 1, 1, 1   # Row 3: S    3
            ],
            # Set 4 - "S4"
            [
                1, 1, 1, 1, 0, 0, 0, 1,  # Row 0: S    4
                1, 1, 0, 0, 0, 0, 1, 1,  # Row 1: S    4
                0, 0, 1, 1, 0, 1, 1, 1,  # Row 2: S    4
                1, 1, 1, 1, 0, 0, 0, 1   # Row 3: S    4
            ],
            # Set 5 - "S5"
            [
                1, 1, 1, 1, 0, 1, 1, 1,  # Row 0: S    5
                1, 1, 0, 0, 0, 1, 1, 0,  # Row 1: S    5
                0, 0, 1, 1, 0, 0, 0, 1,  # Row 2: S    5
                1, 1, 1, 1, 0, 1, 1, 0   # Row 3: S    5
            ]
        ]
        
        # Only clamp if not in brightness mode (mode 3)
        if self.mode != 3:
            number = max(0, min(len(patterns) - 1, number))
        pattern = patterns[number]
        
        # Clear display
        self.pixel32.fill((0, 0, 0))
        
        # Display pattern
        for row in range(4):
            for col in range(8):
                pattern_idx = row * 8 + col
                if pattern[pattern_idx]:
                    self.pixel32[pattern_idx] = color
        
        self.pixel32.show()
        time.sleep(duration)

    def show_number(self, number, color=(64, 64, 0), duration=0.4):
        """Display a mode number (M0-M2) on the 4x8 LED grid
        Modes: 0=cycle, 1=solid, 2=gradient
        Layout is 4 rows × 8 columns, indexed like:
         0  1  2  3  4  5  6  7
         8  9 10 11 12 13 14 15
        16 17 18 19 20 21 22 23
        24 25 26 27 28 29 30 31
        """
        print(f"show_number: input number = {number}")
        
        # Define patterns for a 4×8 grid (4 rows × 8 columns)
        patterns = [
            # Mode 0 (flags) - "m0"
            [
                1, 0, 0, 1, 0, 0, 1, 0,  # Row 0: m    0
                1, 1, 1, 1, 0, 1, 0, 1,  # Row 1: m    0
                1, 0, 1, 1, 0, 1, 0, 1,  # Row 2: m    0
                1, 0, 0, 1, 0, 0, 1, 0   # Row 3: m    0
            ],
            # Mode 1 (explosions) - "m1"
            [
                1, 0, 0, 1, 0, 0, 1, 0,  # Row 0: m    1
                1, 1, 1, 1, 0, 1, 1, 0,  # Row 1: m    1
                1, 0, 1, 1, 0, 0, 1, 0,  # Row 2: m    1
                1, 0, 0, 1, 0, 1, 1, 1   # Row 3: m    1
            ],
            # Mode 2 (gradient) - "m2"
            [
                1, 0, 0, 1, 0, 1, 1, 0,  # Row 0: m    2
                1, 1, 1, 1, 0, 0, 0, 1,  # Row 1: m    2
                1, 0, 1, 1, 0, 1, 1, 0,  # Row 2: m    2
                1, 0, 0, 1, 0, 1, 1, 1   # Row 3: m    2
            ],
            # Mode 3 (settings) - "m3"
            [
                1, 0, 0, 1, 0, 1, 1, 1,  # Row 0: m    3
                1, 1, 1, 1, 0, 0, 1, 1,  # Row 1: m    3
                1, 0, 1, 1, 0, 0, 0, 1,  # Row 2: m    3
                1, 0, 0, 1, 0, 1, 1, 1   # Row 3: m    3
            ]
        ]

        # Ensure number is in valid range
        number = max(0, min(len(patterns) - 1, number))  # Clamp to valid index
        pattern = patterns[number]
        
        # Ensure number is valid
        if number < 0 or number >= len(patterns):
            print(f"Invalid number {number}, patterns length = {len(patterns)}")
            return
            
        pattern = patterns[number]
        print(f"Pattern length = {len(pattern)}")
        
        # Clear display
        self.pixel32.fill((0, 0, 0))
        
        # Clear display
        self.pixel32.fill((0, 0, 0))
        
        # Display 4×8 pattern (4 rows, 8 columns per row)
        for row in range(4):  # 4 rows
            for col in range(8):  # 8 columns per row
                pattern_idx = row * 8 + col  # Index into the pattern array
                pixel_idx = pattern_idx  # Direct mapping - pattern matches LED layout
                
                print(f"r{row} c{col}: pattern[{pattern_idx}] -> pixel[{pixel_idx}]")
                
                if pattern[pattern_idx]:
                    self.pixel32[pixel_idx] = color
        
        self.pixel32.show()
        time.sleep(duration)

    def animate_step(self):
        now = time.monotonic()
        dt = now - self.last_step
        if dt < 0.02:  # ~50Hz update
            return
        self.last_step = now

        if not self.active:
            return

        # Don't fetch palette in brightness mode
        if self.mode == 3:
            palette = [(64, 64, 64)]  # Just need a single color for brightness bar
        else:
            palette = self.sets[self.set_idx]
            
        if self.mode == 0:
            # flag display mode
            self.pixel32.fill((0, 0, 0))  # Clear first
            
            if self.set_idx == 0:  # France - vertical stripes
                for row in range(4):
                    # Left stripe (blue) - 3 pixels
                    for col in range(3):
                        self.pixel32[row * 8 + col] = palette[0]
                    # Middle stripe (white) - 2 pixels
                    for col in range(3, 5):
                        self.pixel32[row * 8 + col] = palette[1]
                    # Right stripe (red) - 3 pixels
                    for col in range(5, 8):
                        self.pixel32[row * 8 + col] = palette[2]

            elif self.set_idx == 1:  # Philippines - white triangle pointing right, blue top, red bottom
                # First set the blue top and red bottom
                for row in range(4):
                    for col in range(8):
                        if row < 2:
                            self.pixel32[row * 8 + col] = palette[1]  # Blue top half
                        else:
                            self.pixel32[row * 8 + col] = palette[2]  # Red bottom half
                
                # Create white triangle pointing right
                # All 4 pixels in leftmost column
                for row in range(4):
                    self.pixel32[row * 8] = palette[0]
                # 3 pixels in second column
                for row in range(0, 3):
                    self.pixel32[row * 8 + 1] = palette[0]
                # 2 pixels in third column
                for row in range(1, 3):
                    self.pixel32[row * 8 + 2] = palette[0]
                # 1 pixel in fourth column
                self.pixel32[1 * 8 + 3] = palette[0]  # Middle point of triangle
                
                # Define the pattern points for blue and red sections
                pattern_points = [
                    (0, 5), (0, 6),  # Two dots in first row
                    (1, 5), (1, 7)   # Two dots with gap in second row
                ]
                
                # Apply pattern to both blue and red sections
                for row, col in pattern_points:
                    # Blue dots in top half
                    self.pixel32[row * 8 + col] = palette[1]  # Blue
                    # Red dots in bottom half (mirror)
                    mirror_row = row + 2  # Offset by 2 rows for bottom half
                    self.pixel32[mirror_row * 8 + col] = palette[2]  # Red
                
                # Yellow sun dot in white triangle area
                self.pixel32[1 * 8 + 2] = palette[3]  # Yellow dot in second row

            elif self.set_idx == 2:  # Canada
                # First fill everything with white
                for row in range(4):
                    for col in range(8):
                        self.pixel32[row * 8 + col] = palette[1]  # White background

                # Two-pixel wide red bars on sides
                for row in range(4):
                    # Left red stripe
                    self.pixel32[row * 8] = palette[0]     # Leftmost column
                    self.pixel32[row * 8 + 1] = palette[0] # Second column
                    # Right red stripe
                    self.pixel32[row * 8 + 6] = palette[0] # Second-to-last column
                    self.pixel32[row * 8 + 7] = palette[0] # Rightmost column

                # Simple red maple leaf (2x2 square in center)
                self.pixel32[1 * 8 + 3] = palette[0]  # Top left
                self.pixel32[1 * 8 + 4] = palette[0]  # Top right
                self.pixel32[2 * 8 + 3] = palette[0]  # Bottom left
                self.pixel32[2 * 8 + 4] = palette[0]  # Bottom right

            elif self.set_idx == 3:  # USA
                # Blue canton (top left)
                for row in range(2):
                    for col in range(3):
                        self.pixel32[row * 8 + col] = palette[0]
                # Red and white stripes
                stripe_colors = [palette[1], palette[2]] * 2  # Red, white pattern
                for row in range(4):
                    color = stripe_colors[row]
                    # Skip canton area for first two rows
                    start_col = 3 if row < 2 else 0
                    for col in range(start_col, 8):
                        self.pixel32[row * 8 + col] = color

            elif self.set_idx == 4:  # European Union
                # Blue background
                self.pixel32.fill(palette[0])
                # Yellow star circle (8 dots in a circle pattern)
                star_pixels = [
                    1 * 8 + 2, 1 * 8 + 5,    # Left and right on row 1
                    2 * 8 + 2, 2 * 8 + 5,    # Left and right on row 2
                    0 * 8 + 3, 0 * 8 + 4,    # Top two dots
                    3 * 8 + 3, 3 * 8 + 4     # Bottom two dots
                ]
                for pixel_idx in star_pixels:
                    self.pixel32[pixel_idx] = palette[1]

            else:  # Russia - horizontal stripes
                stripe_height = 4 // len(palette)
                for color_idx, color in enumerate(palette):
                    start_row = color_idx * stripe_height
                    end_row = start_row + stripe_height
                    for row in range(start_row, end_row):
                        for col in range(8):
                            self.pixel32[row * 8 + col] = color
            
            self.pixel32.show()
        elif self.mode == 1:
            # explosion pattern using flag colors
            self.pixel32.fill((0, 0, 0))  # Clear first
            
            # Calculate phases for firework effect
            launch_phase = (self.palette_pos // 2) % 8  # More phases for launch and explosion
            spark_phase = self.palette_pos % 4  # For twinkling sparks
            fade_factor = max(0, 7 - launch_phase) / 7  # For color fading
            
            # Use colors based on current set with transitions
            if self.set_idx == 0:  # France
                colors = [(0, 0, 255), (255, 255, 255), (255, 0, 0)]
                sparks = [(192, 192, 255), (255, 255, 255), (255, 192, 192)]
            elif self.set_idx == 1:  # Philippines
                colors = [(255, 255, 255), (0, 0, 255), (255, 0, 0), (255, 200, 0)]
                sparks = [(255, 255, 220), (192, 192, 255), (255, 192, 192), (255, 220, 160)]
            elif self.set_idx == 2:  # Canada
                colors = [(255, 0, 0), (255, 255, 255)]
                sparks = [(255, 160, 160), (255, 255, 220)]
            elif self.set_idx == 3:  # USA
                colors = [(0, 0, 255), (255, 0, 0), (255, 255, 255)]
                sparks = [(160, 160, 255), (255, 160, 160), (255, 255, 220)]
            else:  # EU
                colors = [(0, 51, 153), (255, 255, 0)]
                sparks = [(160, 180, 255), (255, 255, 160)]
            
            # Color transitions
            color_idx = (self.palette_pos // 4) % len(colors)
            next_idx = (color_idx + 1) % len(colors)
            blend = (self.palette_pos % 4) / 4.0
            
            # Blend between current and next color
            c1 = colors[color_idx]
            c2 = colors[next_idx]
            color = (
                int(c1[0] * (1 - blend) + c2[0] * blend),
                int(c1[1] * (1 - blend) + c2[1] * blend),
                int(c1[2] * (1 - blend) + c2[2] * blend)
            )
            
            # Get spark color with similar blending
            s1 = sparks[color_idx]
            s2 = sparks[next_idx]
            spark = (
                int(s1[0] * (1 - blend) + s2[0] * blend),
                int(s1[1] * (1 - blend) + s2[1] * blend),
                int(s1[2] * (1 - blend) + s2[2] * blend)
            )
            
            # Apply fade factor for trail effect
            def fade_color(c):
                return (
                    int(c[0] * fade_factor),
                    int(c[1] * fade_factor),
                    int(c[2] * fade_factor)
                )
            
            rotation = (self.palette_pos % 4)  # Smoother rotation
            
            if launch_phase < 4:  # Extended launch sequence
                # Single pixel moving up the center
                pos = launch_phase
                launch_col = 3  # Center column (0-7)
                
                # Calculate current position and trail
                for row in range(4):  # For each row
                    idx = row * 8 + launch_col
                    if row == (3 - pos):  # Current position (moving up)
                        self.pixel32[idx] = color  # Bright leading pixel
                    elif row > (3 - pos):  # Trail below
                        fade = (row - (3 - pos)) / 3.0  # Fade based on distance
                        trail_color = (
                            int(color[0] * (1 - fade) * 0.7),
                            int(color[1] * (1 - fade) * 0.7),
                            int(color[2] * (1 - fade) * 0.7)
                        )
                        self.pixel32[idx] = trail_color
                
            elif launch_phase < 6:  # Initial burst from last launch position
                # Calculate burst center (where launch ended - top center)
                center_row = 0
                center_col = 3
                
                # Define burst pattern radiating from center
                burst_pattern = [
                    (0, 0),    # Center
                    (-1, 0),   # Up
                    (1, 0),    # Down
                    (0, -1),   # Left
                    (0, 1),    # Right
                    (-1, -1),  # Diagonal up-left
                    (-1, 1),   # Diagonal up-right
                    (1, -1),   # Diagonal down-left
                    (1, 1),    # Diagonal down-right
                ]
                
                # Add all burst points based on pattern
                for dr, dc in burst_pattern:
                    new_row = center_row + dr
                    new_col = center_col + dc
                    if 0 <= new_row < 4 and 0 <= new_col < 8:  # Check bounds
                        idx = new_row * 8 + new_col
                        if spark_phase % 2 == 0:
                            self.pixel32[idx] = color
                        else:
                            self.pixel32[idx] = spark
                
            elif launch_phase < 7:  # Expanding burst
                # Define expanding pattern from center
                center_row = 0
                center_col = 3
                
                # Create expanding ring pattern
                burst_pixels = []
                radius = 2  # Larger radius for this phase
                for row in range(4):
                    for col in range(8):
                        # Calculate distance from burst center
                        dr = row - center_row
                        dc = col - center_col
                        distance = abs(dr) + abs(dc)  # Manhattan distance
                        if distance <= radius:
                            burst_pixels.append(row * 8 + col)
                for idx in burst_pixels:
                    if (idx + spark_phase) % 3 == 0:
                        self.pixel32[idx] = spark
                    else:
                        self.pixel32[idx] = color
                
            else:  # Final sparkle and fade
                sparkle_pixels = [
                    0 * 8 + 1, 0 * 8 + 6,  # Corner sparkles
                    3 * 8 + 1, 3 * 8 + 6,
                    1 * 8 + 0, 1 * 8 + 7,
                    2 * 8 + 0, 2 * 8 + 7
                ]
                for idx in sparkle_pixels:
                    if (idx + spark_phase) % 2 == 0:
                        self.pixel32[idx] = fade_color(spark)
                    else:
                        self.pixel32[idx] = fade_color(color)
            
            if now - self.last_palette_change >= 0.08:  # Even faster for smooth fireworks
                self.palette_pos += 1
                self.last_palette_change = now
            
            self.pixel32.show()
        elif self.mode == 2:
            # Spectacular gradient with sparkles and waves
            time_phase = (self.rotate_pos // 2) % 4  # Slower core animation
            sparkle_phase = self.rotate_pos % 3      # Fast sparkle effect
            wave_pos = self.rotate_pos % 8           # Wave position
            
            # Create smooth transitions between colors
            color_idx = (self.rotate_pos // 4) % len(palette)
            next_idx = (color_idx + 1) % len(palette)
            blend = (self.rotate_pos % 4) / 4.0
            
            c1 = palette[color_idx]
            c2 = palette[next_idx]
            mid_color = (
                int(c1[0] * (1 - blend) + c2[0] * blend),
                int(c1[1] * (1 - blend) + c2[1] * blend),
                int(c1[2] * (1 - blend) + c2[2] * blend)
            )
            
            # Calculate bright version for sparkles
            bright_color = (
                min(255, int(mid_color[0] * 1.5)),
                min(255, int(mid_color[1] * 1.5)),
                min(255, int(mid_color[2] * 1.5))
            )
            
            # Fill with base pattern
            for row in range(4):
                for col in range(8):
                    idx = row * 8 + col
                    
                    # Wave effect
                    wave_offset = (col + wave_pos) % 8
                    intensity = abs(4 - wave_offset) / 4.0  # Creates a peak in the middle
                    
                    # Combine with time-based patterns
                    if time_phase == 0:  # Horizontal bands
                        pattern_value = (row + self.rotate_pos) % 4
                    elif time_phase == 1:  # Vertical bands
                        pattern_value = (col + self.rotate_pos) % 8
                    elif time_phase == 2:  # Diagonal pattern
                        pattern_value = ((row + col + self.rotate_pos) % 4)
                    else:  # Circular pattern
                        dist_from_center = abs(row - 1.5) + abs(col - 3.5)
                        pattern_value = (int(dist_from_center + self.rotate_pos)) % 4
                    
                    # Combine pattern and wave
                    factor = (pattern_value / 4.0 + intensity) / 2
                    
                    # Calculate base color with pattern
                    pixel_color = (
                        int(mid_color[0] * factor),
                        int(mid_color[1] * factor),
                        int(mid_color[2] * factor)
                    )
                    
                    # Add sparkles based on position and phase
                    if ((row + col + sparkle_phase) % 3 == 0 and 
                        (abs(4 - wave_offset) < 2)):  # More sparkles near wave peak
                        self.pixel32[idx] = bright_color
                    else:
                        self.pixel32[idx] = pixel_color
            
            self.pixel32.show()
            self.rotate_pos = (self.rotate_pos + 1) % (len(palette) * 4)
        elif self.mode == 3:
            # Settings mode - show brightness level
            # We now use set_idx directly since sets_per_mode handles the range
            new_brightness = self.brightness_levels[self.set_idx]
            if new_brightness != self.current_brightness:
                self.current_brightness = new_brightness
                self.pixel32.brightness = self.current_brightness
            
            # Show brightness bar
            self.pixel32.fill((0, 0, 0))
            bar_length = int(32 * self.current_brightness)
            for i in range(bar_length):
                self.pixel32[i] = (64, 64, 64)  # Dim white for brightness indicator
            self.pixel32.show()