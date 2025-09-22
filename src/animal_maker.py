"""
Animal Maker - Main application class that orchestrates all components
"""

import pygame
import sys
import time
import numpy as np
from typing import Optional, Tuple
from enum import Enum

from drawing_canvas import DrawingCanvas
from ocr_recognition import OCRRecognizer
from animal_image_manager import AnimalImageManager
from animation_system import AnimationManager, AnimationType

class AppState(Enum):
    DRAWING = "drawing"
    PROCESSING = "processing"
    ANIMATING = "animating"
    DISPLAYING = "displaying"

class AnimalMaker:
    """Main application class for the Animal Maker project"""
    
    def __init__(self, width: int = 1200, height: int = 800):
        pygame.init()

        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Animal Maker - Draw an animal name!")

        self.canvas = DrawingCanvas(width, height)
        self.ocr = OCRRecognizer()
        self.image_manager = AnimalImageManager()
        self.animator = AnimationManager()

        self.state = AppState.DRAWING
        self.clock = pygame.time.Clock()
        self.running = True

        self.current_animal = None
        self.current_animal_image = None
        self.animal_image_rect = None
        
        # UI elements
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # Colors
        self.bg_color = (240, 240, 245)
        self.text_color = (50, 50, 50)
        self.hint_color = (120, 120, 120)
        
        # Animation settings
        self.animation_types = list(AnimationType)
        self.current_animation_index = 3  # Default to WAVE_TRANSFORM
        
        print("Animal Maker initialized successfully!")
        print("Draw an animal name and wait 3 seconds to see the magic!")
        
    def handle_events(self) -> None:
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE and self.state in [AppState.DISPLAYING, AppState.DRAWING]:
                    # Reset to drawing state
                    self.reset_to_drawing()
                elif event.key == pygame.K_c and self.state == AppState.DRAWING:
                    # Clear canvas
                    self.canvas.clear_canvas()
                elif event.key == pygame.K_TAB:
                    # Cycle through animation types
                    self.current_animation_index = (self.current_animation_index + 1) % len(self.animation_types)
                    print(f"Animation type: {self.animation_types[self.current_animation_index].value}")
                    
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    if self.state == AppState.DRAWING:
                        self.canvas.start_drawing(event.pos)
                elif event.button == 3:  # Right click
                    if self.state == AppState.DRAWING:
                        self.canvas.clear_canvas()
                    elif self.state in [AppState.DISPLAYING, AppState.ANIMATING]:
                        self.reset_to_drawing()
                        
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and self.state == AppState.DRAWING:
                    self.canvas.stop_drawing()
                    
            elif event.type == pygame.MOUSEMOTION:
                if self.state == AppState.DRAWING and pygame.mouse.get_pressed()[0]:
                    self.canvas.continue_drawing(event.pos)
                    
    def update(self) -> None:
        """Update application logic"""
        dt = self.clock.tick(60) / 1000.0  # Delta time in seconds
        
        if self.state == AppState.DRAWING:
            # Check if user has been idle and there's something to process
            if self.canvas.has_drawing() and self.canvas.has_been_idle(3000):
                self.start_processing()
                
        elif self.state == AppState.PROCESSING:
            # OCR processing happens in start_processing()
            pass
            
        elif self.state == AppState.ANIMATING:
            self.animator.update(dt)
            if self.animator.is_finished():
                self.state = AppState.DISPLAYING
                
    def start_processing(self) -> None:
        """Start OCR processing of the drawn content"""
        self.state = AppState.PROCESSING
        print("Processing handwriting...")
        
        # Get the drawing surface
        drawing_surface = self.canvas.get_drawing_surface()
        if not drawing_surface:
            print("No drawing found")
            self.state = AppState.DRAWING
            return
            
        # Recognize animal name
        animal_name = self.ocr.recognize_animal_name(drawing_surface)
        
        if animal_name:
            print(f"Recognized animal: {animal_name}")
            self.current_animal = animal_name
            
            # Get animal image
            self.current_animal_image = self.image_manager.get_animal_image(animal_name)
            
            # Calculate positioning for animal image
            canvas_bounds = self.canvas.get_drawing_bounds()
            if canvas_bounds:
                # Position animal image near the drawing
                img_width, img_height = self.current_animal_image.get_size()
                center_x = (canvas_bounds[0] + canvas_bounds[2]) // 2
                center_y = (canvas_bounds[1] + canvas_bounds[3]) // 2
                
                self.animal_image_rect = pygame.Rect(
                    center_x - img_width // 2,
                    center_y - img_height // 2,
                    img_width,
                    img_height
                )
                
                # Start animation
                self.start_animation()
            else:
                self.state = AppState.DRAWING
        else:
            print("Could not recognize any animal name")
            self.state = AppState.DRAWING
            
    def start_animation(self) -> None:
        """Start the transformation animation"""
        if not self.current_animal_image or not self.animal_image_rect:
            self.state = AppState.DRAWING
            return
            
        self.state = AppState.ANIMATING
        
        # Get drawing surface and bounds
        drawing_surface = self.canvas.get_drawing_surface()
        drawing_bounds = self.canvas.get_drawing_bounds()
        
        if drawing_surface and drawing_bounds:
            # Calculate offsets
            source_offset = (drawing_bounds[0], drawing_bounds[1])
            target_offset = (self.animal_image_rect.x, self.animal_image_rect.y)
            
            # Prepare a silhouette target surface from the animal image so particles form a silhouette
            anim_img = self.current_animal_image.copy()

            # Resize target image to fit drawing bounds while preserving aspect ratio
            draw_w = drawing_bounds[2] - drawing_bounds[0]
            draw_h = drawing_bounds[3] - drawing_bounds[1]
            
            if draw_w > 0 and draw_h > 0:
                # Get original image dimensions
                orig_w, orig_h = anim_img.get_size()
                
                # Calculate scale factor to fit within drawing bounds while preserving aspect ratio
                scale_x = draw_w / orig_w
                scale_y = draw_h / orig_h
                scale = min(scale_x, scale_y)  # Use smaller scale to fit within bounds
                
                # Calculate new dimensions
                new_w = int(orig_w * scale)
                new_h = int(orig_h * scale)
                
                # Scale the image
                anim_img = pygame.transform.smoothscale(anim_img, (new_w, new_h))
                
                # Center the image within the drawing bounds
                center_x = drawing_bounds[0] + draw_w // 2
                center_y = drawing_bounds[1] + draw_h // 2
                target_offset = (center_x - new_w // 2, center_y - new_h // 2)

            # Option 3: Floyd-Steinberg Dithering for high quality black and white
            try:
                from PIL import Image
                # Convert pygame surface to PIL Image
                w, h = anim_img.get_size()
                raw = pygame.image.tostring(anim_img, 'RGB')
                pil_img = Image.frombytes('RGB', (w, h), raw)

                # Convert to grayscale first, then to black and white with dithering
                gray = pil_img.convert('L')
                bw_img = gray.convert('1', dither=Image.FLOYDSTEINBERG)

                # Convert back to RGB format for pygame
                bw_rgb = bw_img.convert('RGB')
                bw_data = bw_rgb.tobytes()
                target_surface = pygame.image.frombuffer(bw_data, (w, h), 'RGB').convert()
                print("Created black and white silhouette with Floyd-Steinberg dithering")

            except Exception as e:
                print(f"Floyd-Steinberg dithering failed: {e}")
                # Fallback: just use the original image
                target_surface = anim_img.copy()
                print("Using original image as fallback")            # Store the silhouette as the final display image - NEVER show the color reference photo
            self.current_animal_image = target_surface  # Use the black/white silhouette, not the color image
            self.animal_image_rect = pygame.Rect(target_offset[0], target_offset[1], target_surface.get_width(), target_surface.get_height())

            # Start the animation using the drawing surface as source and silhouette as target
            animation_type = self.animation_types[self.current_animation_index]
            self.animator.start_animation(
                drawing_surface,
                target_surface,
                source_offset,
                target_offset,
                animation_type
            )
            
            print(f"Starting {animation_type.value} animation...")
        else:
            self.state = AppState.DRAWING
            
    def reset_to_drawing(self) -> None:
        """Reset application to drawing state"""
        self.state = AppState.DRAWING
        self.canvas.clear_canvas()
        self.current_animal = None
        self.current_animal_image = None
        self.animal_image_rect = None
        print("Ready to draw a new animal!")
        
    def draw_ui(self) -> None:
        """Draw user interface elements"""
        # Draw title
        title_text = self.font.render("Animal Maker", True, self.text_color)
        self.screen.blit(title_text, (20, 20))
        
        # Draw instructions based on state
        if self.state == AppState.DRAWING:
            if self.canvas.has_drawing():
                if self.canvas.has_been_idle(1000):  # Show countdown
                    remaining = 3 - (pygame.time.get_ticks() - self.canvas.last_draw_time) // 1000
                    if remaining > 0:
                        instruction = f"Processing in {remaining}..."
                    else:
                        instruction = "Processing..."
                else:
                    instruction = "Keep drawing or wait 3 seconds..."
            else:
                instruction = "Draw an animal name with your mouse"
        elif self.state == AppState.PROCESSING:
            instruction = "Recognizing your handwriting..."
        elif self.state == AppState.ANIMATING:
            progress = int(self.animator.get_progress() * 100)
            instruction = f"Creating {self.current_animal}... {progress}%"
        elif self.state == AppState.DISPLAYING:
            instruction = f"Here's your {self.current_animal}! Press SPACE to draw again"
            
        instruction_text = self.small_font.render(instruction, True, self.hint_color)
        self.screen.blit(instruction_text, (20, 60))
        
        # Draw controls
        controls = [
            "Left click: Draw",
            "Right click: Clear/Reset", 
            "C: Clear canvas",
            "TAB: Change animation",
            "SPACE: Reset",
            "ESC: Exit"
        ]
        
        for i, control in enumerate(controls):
            text = self.small_font.render(control, True, self.hint_color)
            self.screen.blit(text, (self.width - 200, 20 + i * 25))
            
        # Show current animation type
        anim_type = self.animation_types[self.current_animation_index].value.replace('_', ' ').title()
        anim_text = self.small_font.render(f"Animation: {anim_type}", True, self.text_color)
        self.screen.blit(anim_text, (20, self.height - 30))
        
    def draw(self) -> None:
        """Render the current frame"""
        # Clear screen
        self.screen.fill(self.bg_color)
        
        # Draw canvas
        if self.state in [AppState.DRAWING, AppState.PROCESSING]:
            self.canvas.draw(self.screen)
        elif self.state == AppState.ANIMATING:
            # Draw animation particles
            self.animator.draw(self.screen)
            
            # Draw progressive animal image based on animation progress
            if self.current_animal_image and self.animal_image_rect:
                progress = self.animator.get_progress()
                
                # Only start revealing the silhouette after particles have had time to move
                if progress > 0.3:  # Start revealing after 30% of animation
                    # Adjust progress for smoother reveal (slower at start, faster at end)
                    reveal_progress = (progress - 0.3) / 0.7  # Map 0.3-1.0 to 0.0-1.0
                    reveal_progress = reveal_progress * reveal_progress  # Quadratic for smooth acceleration
                    
                    # Create a surface for the progressive reveal
                    reveal_surface = pygame.Surface(self.current_animal_image.get_size(), pygame.SRCALPHA)
                    reveal_surface.fill((0, 0, 0, 0))  # Transparent
                    
                    # Get particles and reveal pixels based on their proximity to targets
                    particles = self.animator.particles
                    img_width, img_height = self.current_animal_image.get_size()
                    
                    # Create a set of revealed pixel positions
                    revealed_pixels = set()
                    
                    for particle in particles:
                        # Calculate how close this particle is to its target
                        dx = particle.target_x - particle.current_x
                        dy = particle.target_y - particle.current_y
                        distance_to_target = (dx*dx + dy*dy) ** 0.5
                        
                        # Only reveal pixels for particles that are close to their targets
                        max_reveal_distance = 50 * (1 - reveal_progress)  # Shrink reveal distance over time
                        if distance_to_target < max_reveal_distance:
                            # Calculate particle position relative to the animal image
                            particle_x = int(particle.current_x - self.animal_image_rect.x)
                            particle_y = int(particle.current_y - self.animal_image_rect.y)
                            
                            # Reveal pixels in a small radius around particles close to targets
                            reveal_radius = max(1, int(2 + 3 * reveal_progress))  # Grow reveal radius over time
                            
                            for dy in range(-reveal_radius, reveal_radius + 1):
                                for dx in range(-reveal_radius, reveal_radius + 1):
                                    reveal_x = particle_x + dx
                                    reveal_y = particle_y + dy
                                    
                                    # Check if pixel is within image bounds
                                    if 0 <= reveal_x < img_width and 0 <= reveal_y < img_height:
                                        # Check if within circular radius
                                        if dx*dx + dy*dy <= reveal_radius*reveal_radius:
                                            revealed_pixels.add((reveal_x, reveal_y))
                    
                    # Reveal pixels with progressive alpha for smoother appearance
                    for pixel_x, pixel_y in revealed_pixels:
                        pixel_color = self.current_animal_image.get_at((pixel_x, pixel_y))
                        # Apply alpha based on reveal progress for smoother fade-in
                        alpha = min(255, int(255 * reveal_progress))
                        if len(pixel_color) >= 4:
                            pixel_color = (pixel_color[0], pixel_color[1], pixel_color[2], alpha)
                        else:
                            pixel_color = (pixel_color[0], pixel_color[1], pixel_color[2], alpha)
                        reveal_surface.set_at((pixel_x, pixel_y), pixel_color)
                    
                    # Blit the progressive reveal
                    self.screen.blit(reveal_surface, self.animal_image_rect)
        elif self.state == AppState.DISPLAYING:
            # Draw final animal image
            if self.current_animal_image and self.animal_image_rect:
                self.screen.blit(self.current_animal_image, self.animal_image_rect)
                
        # Draw UI
        self.draw_ui()
        
        # Update display
        pygame.display.flip()
        
    def run(self) -> None:
        """Main application loop"""
        print("Starting Animal Maker...")
        
        try:
            while self.running:
                self.handle_events()
                self.update()
                self.draw()
                
        except KeyboardInterrupt:
            print("\\nApplication interrupted by user")
        except Exception as e:
            print(f"Error in main loop: {e}")
            raise
        finally:
            pygame.quit()
            print("Animal Maker closed successfully!")
            
if __name__ == "__main__":
    app = AnimalMaker()
    app.run()