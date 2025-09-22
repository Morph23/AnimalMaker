"""
Animation System - Handles pixel transformation animations
"""

import pygame
import numpy as np
import math
import random
from typing import List, Tuple, Optional
from enum import Enum

class AnimationType(Enum):
    SAND_FALL = "sand_fall"
    PARTICLE_SWIRL = "particle_swirl"
    PIXEL_MORPH = "pixel_morph"
    WAVE_TRANSFORM = "wave_transform"

class Particle:
    """Represents a single particle in the animation"""
    
    def __init__(self, start_pos: Tuple[float, float], target_pos: Tuple[float, float], 
                 source_color: Tuple[int, int, int], target_color: Tuple[int, int, int], size: int = 2):
        # positions
        self.start_x, self.start_y = start_pos
        self.target_x, self.target_y = target_pos
        self.current_x = float(self.start_x)
        self.current_y = float(self.start_y)

        # Colors
        self.source_color = tuple(int(c) for c in source_color)
        self.target_color = tuple(int(c) for c in target_color)
        self.color = self.source_color
        self.size = size

        # Physics / animation properties
        # Start with an initial scatter velocity so pixels appear to break away
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(40.0, 80.0)  # Reduced speed for smoother motion
        self.velocity_x = math.cos(angle) * speed
        self.velocity_y = math.sin(angle) * speed * 0.4  # Less vertical scatter

        self.gravity = 150.0  # Reduced gravity for smoother fall
        self.friction = 0.95  # Increased friction for smoother deceleration
        self.life = 1.0
        self.age = 0.0

        # Random properties for variety
        self.wobble_frequency = random.uniform(0.5, 1.5)  # Slower wobble
        self.wobble_amplitude = random.uniform(2, 8)  # Smaller wobble
        # Delay before a particle starts being pulled toward the target (staggered arrival)
        self.fall_delay = random.uniform(0.0, 0.4)  # Shorter delays for faster convergence
        
    def update_sand_fall(self, progress: float, dt: float) -> None:
        """Update particle for sand falling animation with stronger, progressive attraction.

        Behavior:
        - Particles start with an outward scatter velocity.
        - Gravity and wobble apply while particles are in the "air".
        - After each particle's fall_delay, a pull toward its target grows with progress,
          pulling particles into the silhouette.
        - Color blends from source_color to target_color as the particle approaches its target.
        """
        # If overall progress hasn't reached this particle's delay, let it scatter/fall
        if progress < self.fall_delay:
            # still scattering, apply gravity and friction
            self.velocity_y += self.gravity * dt
            self.velocity_x *= self.friction

            # wobble adds organic motion
            wobble = math.sin(self.age * self.wobble_frequency) * self.wobble_amplitude
            self.velocity_x += wobble * dt

            # integrate
            self.current_x += self.velocity_x * dt
            self.current_y += self.velocity_y * dt
        else:
            # compute adjusted progress for this particle (0..1)
            adjusted_progress = (progress - self.fall_delay) / max(1e-6, (1.0 - self.fall_delay))

            # still apply a reduced gravity so particles settle smoothly
            self.velocity_y += (self.gravity * 0.35) * dt
            self.velocity_x *= max(0.6, self.friction)
            
            self.current_x += self.velocity_x * dt
            self.current_y += self.velocity_y * dt

            # target attraction: grows smoothly so particles gradually move into place
            attraction_strength = min(4.0, (adjusted_progress ** 1.5) * 3.0)  # Smoother, less aggressive attraction
            self.current_x = self.current_x * (1 - attraction_strength * dt) + self.target_x * (attraction_strength * dt)
            self.current_y = self.current_y * (1 - attraction_strength * dt) + self.target_y * (attraction_strength * dt)

            # Blend color toward target based on adjusted_progress
            t = min(1.0, max(0.0, adjusted_progress))
            blended = (
                int(self.source_color[0] * (1 - t) + self.target_color[0] * t),
                int(self.source_color[1] * (1 - t) + self.target_color[1] * t),
                int(self.source_color[2] * (1 - t) + self.target_color[2] * t),
            )
            self.color = blended

        self.age += dt
        
    def update_particle_swirl(self, progress: float, dt: float, center: Tuple[float, float]) -> None:
        """Update particle for swirling animation"""
        center_x, center_y = center
        
        # Create spiral motion towards target
        angle = self.age * 2.0 + progress * math.pi * 4
        radius = 50 * (1 - progress)
        
        spiral_x = center_x + math.cos(angle) * radius
        spiral_y = center_y + math.sin(angle) * radius
        
        # Interpolate between spiral and target
        self.current_x = spiral_x * (1 - progress) + self.target_x * progress
        self.current_y = spiral_y * (1 - progress) + self.target_y * progress
        
        self.age += dt
        
    def update_pixel_morph(self, progress: float, dt: float) -> None:
        """Update particle for direct morphing animation"""
        # Simple eased interpolation
        eased_progress = 1 - (1 - progress) * (1 - progress)  # Ease out
        
        self.current_x = self.start_x * (1 - eased_progress) + self.target_x * eased_progress
        self.current_y = self.start_y * (1 - eased_progress) + self.target_y * eased_progress
        
        self.age += dt
        
    def update_wave_transform(self, progress: float, dt: float) -> None:
        """Update particle for wave-based transformation"""
        # Create wave motion
        wave_offset = math.sin(progress * math.pi * 2 + self.start_x * 0.1) * 20 * (1 - progress)
        
        eased_progress = progress * progress * (3 - 2 * progress)  # Smooth step
        
        self.current_x = self.start_x * (1 - eased_progress) + self.target_x * eased_progress
        self.current_y = self.start_y * (1 - eased_progress) + self.target_y * eased_progress + wave_offset
        
        self.age += dt
        
    def draw(self, surface: pygame.Surface) -> None:
        """Draw the particle"""
        x, y = int(self.current_x), int(self.current_y)
        if 0 <= x < surface.get_width() and 0 <= y < surface.get_height():
            # draw with alpha based on proximity to target (so the silhouette appears smoothly)
            # estimate distance to target
            dx = self.target_x - self.current_x
            dy = self.target_y - self.current_y
            dist = math.hypot(dx, dy)
            # closer particles are more opaque
            alpha = int(max(40, min(255, 255 - dist * 0.8)))

            # create a temporary surface for alpha circle drawing
            if self.size <= 2:
                # small pixel-level draw
                col = (self.color[0], self.color[1], self.color[2])
                surface.set_at((x, y), col)
            else:
                s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (self.color[0], self.color[1], self.color[2], alpha), (self.size, self.size), self.size)
                surface.blit(s, (x - self.size, y - self.size))

class AnimationManager:
    """Manages the transformation animation from handwriting to animal image"""
    
    def __init__(self):
        self.particles: List[Particle] = []
        self.animation_type = AnimationType.WAVE_TRANSFORM  # Default to wave transform
        self.progress = 0.0
        self.duration = 25.0  # seconds - even longer for ultra-smooth, gradual appearance
        self.is_animating = False
        self.center_point = (0, 0)
        
    def start_animation(self, source_surface: pygame.Surface, target_surface: pygame.Surface,
                       source_offset: Tuple[int, int] = (0, 0),
                       target_offset: Tuple[int, int] = (0, 0),
                       animation_type: AnimationType = AnimationType.SAND_FALL) -> None:
        """Start the transformation animation"""
        self.particles.clear()
        self.animation_type = animation_type
        self.progress = 0.0
        self.is_animating = True
        
        # Calculate center point for swirl animations
        src_width, src_height = source_surface.get_size()
        self.center_point = (
            source_offset[0] + src_width // 2,
            source_offset[1] + src_height // 2
        )
        
        # Extract pixels from source (handwriting)
        source_pixels = self.extract_non_white_pixels(source_surface, source_offset)
        
        # Extract pixels from target (animal image)
        target_pixels = self.extract_pixels_for_shape(target_surface, target_offset, len(source_pixels))
        
        # Create particles
        self.create_particles(source_pixels, target_pixels)
        
        print(f"Animation started with {len(self.particles)} particles")
        
    def extract_non_white_pixels(self, surface: pygame.Surface, offset: Tuple[int, int]) -> List[Tuple[Tuple[int, int], Tuple[int, int, int]]]:
        """Extract non-white pixels from surface with their positions and colors"""
        pixels = []
        width, height = surface.get_size()
        
        # Sample pixels to avoid too many particles
        step = max(1, min(width, height) // 100)  # Adaptive sampling
        
        for y in range(0, height, step):
            for x in range(0, width, step):
                try:
                    color = surface.get_at((x, y))[:3]  # RGB only
                    # Check if pixel is not white-ish
                    if sum(color) < 700:  # Not pure white
                        world_pos = (offset[0] + x, offset[1] + y)
                        pixels.append((world_pos, color))
                except:
                    continue
                    
        return pixels
        
    def extract_pixels_for_shape(self, surface: pygame.Surface, offset: Tuple[int, int], 
                                num_pixels: int) -> List[Tuple[Tuple[int, int], Tuple[int, int, int]]]:
        """Extract pixels from target image to form the animal shape"""
        pixels = []
        width, height = surface.get_size()
        
        # Get all non-transparent pixels
        all_pixels = []
        for y in range(height):
            for x in range(width):
                try:
                    color = surface.get_at((x, y))
                    if len(color) > 3 and color[3] > 128:  # Check alpha
                        world_pos = (offset[0] + x, offset[1] + y)
                        all_pixels.append((world_pos, color[:3]))
                    elif len(color) == 3:  # No alpha channel
                        if sum(color) < 700:  # Not white
                            world_pos = (offset[0] + x, offset[1] + y)
                            all_pixels.append((world_pos, color))
                except:
                    continue
                    
        # Sample pixels to match source count
        if len(all_pixels) > num_pixels:
            step = len(all_pixels) // num_pixels
            pixels = all_pixels[::step][:num_pixels]
        else:
            pixels = all_pixels
            
        # Fill remaining pixels if needed
        while len(pixels) < num_pixels and all_pixels:
            pixels.append(random.choice(all_pixels))
            
        return pixels
        
    def create_particles(self, source_pixels: List[Tuple[Tuple[int, int], Tuple[int, int, int]]],
                        target_pixels: List[Tuple[Tuple[int, int], Tuple[int, int, int]]]) -> None:
        """Create particles with optimal source->target assignment (simplified Hungarian algorithm)"""
        # Ensure we have pixels to work with
        if not source_pixels or not target_pixels:
            return
            
        # For better visual effect, ensure source particles map to nearby target pixels
        # This creates a more convincing transformation
        
        # Sort target pixels by position for consistent assignment
        target_pixels_sorted = sorted(target_pixels, key=lambda p: (p[0][1], p[0][0]))  # Sort by y, then x
        
        # If we have more source than target, truncate source
        # If we have more target than source, repeat source pixels
        if len(source_pixels) > len(target_pixels_sorted):
            source_pixels = source_pixels[:len(target_pixels_sorted)]
        else:
            # Repeat source pixels to match target count
            while len(source_pixels) < len(target_pixels_sorted):
                source_pixels.extend(source_pixels[:len(target_pixels_sorted) - len(source_pixels)])
        
        # Simple assignment: for each source pixel, find a nearby target pixel
        used_targets = set()
        assignments = []
        
        for source_pos, source_color in source_pixels:
            best_target = None
            best_distance = float('inf')
            
            # Find the closest unused target pixel
            for i, (target_pos, target_color) in enumerate(target_pixels_sorted):
                if i in used_targets:
                    continue
                    
                # Calculate distance
                dx = source_pos[0] - target_pos[0]
                dy = source_pos[1] - target_pos[1]
                distance = dx*dx + dy*dy
                
                if distance < best_distance:
                    best_distance = distance
                    best_target = (i, target_pos, target_color)
            
            if best_target:
                target_idx, target_pos, target_color = best_target
                used_targets.add(target_idx)
                assignments.append((source_pos, source_color, target_pos, target_color))
            else:
                # Fallback: use any available target
                for i, (target_pos, target_color) in enumerate(target_pixels_sorted):
                    if i not in used_targets:
                        used_targets.add(i)
                        assignments.append((source_pos, source_color, target_pos, target_color))
                        break
        
        # Create particles from assignments
        for source_pos, source_color, target_pos, target_color in assignments:
            # Add jitter to start positions to avoid exact overlap
            jitter_x = random.uniform(-2, 2)
            jitter_y = random.uniform(-2, 2)
            start = (source_pos[0] + jitter_x, source_pos[1] + jitter_y)

            # Vary particle sizes slightly
            size = 2 if random.random() < 0.8 else random.randint(3, 5)

            particle = Particle(start, target_pos, source_color, target_color, size=size)
            self.particles.append(particle)
            
    def update(self, dt: float) -> None:
        """Update animation"""
        if not self.is_animating:
            return
            
        self.progress += dt / self.duration
        
        if self.progress >= 1.0:
            self.progress = 1.0
            self.is_animating = False
            
        # Update all particles based on animation type
        for particle in self.particles:
            if self.animation_type == AnimationType.SAND_FALL:
                particle.update_sand_fall(self.progress, dt)
            elif self.animation_type == AnimationType.PARTICLE_SWIRL:
                particle.update_particle_swirl(self.progress, dt, self.center_point)
            elif self.animation_type == AnimationType.PIXEL_MORPH:
                particle.update_pixel_morph(self.progress, dt)
            elif self.animation_type == AnimationType.WAVE_TRANSFORM:
                particle.update_wave_transform(self.progress, dt)
            
            # Ensure color blends toward target in all animation types
            # compute a global blend factor based on progress
            blend_factor = min(1.0, max(0.0, (self.progress - particle.fall_delay) / max(1e-6, (1.0 - particle.fall_delay)))) if hasattr(particle, 'fall_delay') else self.progress
            if blend_factor > 0:
                bf = max(0.0, min(1.0, blend_factor))
                particle.color = (
                    int(particle.source_color[0] * (1 - bf) + particle.target_color[0] * bf),
                    int(particle.source_color[1] * (1 - bf) + particle.target_color[1] * bf),
                    int(particle.source_color[2] * (1 - bf) + particle.target_color[2] * bf),
                )
                
    def draw(self, surface: pygame.Surface) -> None:
        """Draw all particles"""
        for particle in self.particles:
            particle.draw(surface)
            
    def is_finished(self) -> bool:
        """Check if animation is complete"""
        return not self.is_animating
        
    def get_progress(self) -> float:
        """Get animation progress (0.0 to 1.0)"""
        return self.progress
        
    def set_animation_type(self, animation_type: AnimationType) -> None:
        """Set the animation type"""
        self.animation_type = animation_type
        
    def set_duration(self, duration: float) -> None:
        """Set animation duration in seconds"""
        self.duration = duration