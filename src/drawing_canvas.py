"""
Drawing Canvas - Handles mouse input and drawing functionality
"""

import pygame
import numpy as np
from typing import List, Tuple, Optional

class DrawingCanvas:
    """Manages the drawing canvas where users write animal names"""
    
    def __init__(self, width: int = 1200, height: int = 800):
        self.width = width
        self.height = height
        self.canvas = pygame.Surface((width, height))
        self.canvas.fill((255, 255, 255))  # White background
        
        # Drawing state
        self.is_drawing = False
        self.last_pos = None
        self.drawing_color = (0, 0, 0)  # Black
        self.brush_size = 5
        
        # Store drawing points for OCR processing
        self.drawing_points: List[Tuple[int, int]] = []
        self.stroke_groups: List[List[Tuple[int, int]]] = []
        self.current_stroke: List[Tuple[int, int]] = []
        
        # Timing for pause detection
        self.last_draw_time = 0
        
    def start_drawing(self, pos: Tuple[int, int]) -> None:
        """Start a new drawing stroke"""
        self.is_drawing = True
        self.last_pos = pos
        self.current_stroke = [pos]
        self.drawing_points.append(pos)
        self.last_draw_time = pygame.time.get_ticks()
        
    def continue_drawing(self, pos: Tuple[int, int]) -> None:
        """Continue drawing from last position to current position"""
        if self.is_drawing and self.last_pos:
            # Draw line on canvas
            pygame.draw.line(self.canvas, self.drawing_color, self.last_pos, pos, self.brush_size)
            
            # Store points for OCR
            self.current_stroke.append(pos)
            self.drawing_points.append(pos)
            
            self.last_pos = pos
            self.last_draw_time = pygame.time.get_ticks()
            
    def stop_drawing(self) -> None:
        """Stop current drawing stroke"""
        if self.is_drawing and self.current_stroke:
            self.stroke_groups.append(self.current_stroke.copy())
            self.current_stroke = []
        
        self.is_drawing = False
        self.last_pos = None
        
    def clear_canvas(self) -> None:
        """Clear the entire canvas"""
        self.canvas.fill((255, 255, 255))
        self.drawing_points.clear()
        self.stroke_groups.clear()
        self.current_stroke.clear()
        
    def get_drawing_bounds(self) -> Optional[Tuple[int, int, int, int]]:
        """Get bounding rectangle of all drawn content"""
        if not self.drawing_points:
            return None
            
        min_x = min(point[0] for point in self.drawing_points)
        max_x = max(point[0] for point in self.drawing_points)
        min_y = min(point[1] for point in self.drawing_points)
        max_y = max(point[1] for point in self.drawing_points)
        
        # Add some padding
        padding = 20
        return (
            max(0, min_x - padding),
            max(0, min_y - padding),
            min(self.width, max_x + padding),
            min(self.height, max_y + padding)
        )
        
    def get_drawing_surface(self) -> Optional[pygame.Surface]:
        """Extract the drawn area as a surface for OCR processing"""
        bounds = self.get_drawing_bounds()
        if not bounds:
            return None
            
        x, y, right, bottom = bounds
        width = right - x
        height = bottom - y
        
        if width <= 0 or height <= 0:
            return None
            
        # Create subsurface of the drawing area
        drawing_surface = pygame.Surface((width, height))
        drawing_surface.fill((255, 255, 255))
        drawing_surface.blit(self.canvas, (0, 0), (x, y, width, height))
        
        return drawing_surface
        
    def has_been_idle(self, idle_duration_ms: int = 3000) -> bool:
        """Check if user has been idle for specified duration"""
        if not self.drawing_points:
            return False
            
        current_time = pygame.time.get_ticks()
        return current_time - self.last_draw_time > idle_duration_ms
        
    def get_pixels_array(self) -> np.ndarray:
        """Get the canvas as a numpy array for processing"""
        return pygame.surfarray.array3d(self.canvas)
        
    def has_drawing(self) -> bool:
        """Check if there's any drawing on the canvas"""
        return len(self.drawing_points) > 0
        
    def draw(self, screen: pygame.Surface, offset: Tuple[int, int] = (0, 0)) -> None:
        """Draw the canvas to the screen"""
        screen.blit(self.canvas, offset)