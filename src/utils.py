"""
Utility functions for the Animal Maker application
"""

import pygame
import math
from typing import Tuple, List, Optional

def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between min and max"""
    return max(min_val, min(value, max_val))

def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between a and b"""
    return a + (b - a) * t

def ease_in_out(t: float) -> float:
    """Smooth ease in-out function"""
    return t * t * (3.0 - 2.0 * t)

def distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Calculate distance between two points"""
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

def normalize_vector(vector: Tuple[float, float]) -> Tuple[float, float]:
    """Normalize a 2D vector"""
    length = math.sqrt(vector[0] ** 2 + vector[1] ** 2)
    if length == 0:
        return (0, 0)
    return (vector[0] / length, vector[1] / length)

def create_gradient_surface(size: Tuple[int, int], color1: Tuple[int, int, int], 
                          color2: Tuple[int, int, int], vertical: bool = True) -> pygame.Surface:
    """Create a gradient surface"""
    surface = pygame.Surface(size)
    width, height = size
    
    if vertical:
        for y in range(height):
            ratio = y / height
            color = (
                int(color1[0] * (1 - ratio) + color2[0] * ratio),
                int(color1[1] * (1 - ratio) + color2[1] * ratio),
                int(color1[2] * (1 - ratio) + color2[2] * ratio)
            )
            pygame.draw.line(surface, color, (0, y), (width, y))
    else:
        for x in range(width):
            ratio = x / width
            color = (
                int(color1[0] * (1 - ratio) + color2[0] * ratio),
                int(color1[1] * (1 - ratio) + color2[1] * ratio),
                int(color1[2] * (1 - ratio) + color2[2] * ratio)
            )
            pygame.draw.line(surface, color, (x, 0), (x, height))
    
    return surface

def draw_text_with_outline(surface: pygame.Surface, text: str, font: pygame.font.Font,
                          pos: Tuple[int, int], text_color: Tuple[int, int, int],
                          outline_color: Tuple[int, int, int], outline_width: int = 1) -> None:
    """Draw text with an outline"""
    # Draw outline
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx != 0 or dy != 0:
                outline_surf = font.render(text, True, outline_color)
                surface.blit(outline_surf, (pos[0] + dx, pos[1] + dy))
    
    # Draw main text
    text_surf = font.render(text, True, text_color)
    surface.blit(text_surf, pos)

def scale_image_to_fit(image: pygame.Surface, target_size: Tuple[int, int], 
                      maintain_aspect: bool = True) -> pygame.Surface:
    """Scale an image to fit within target size"""
    img_width, img_height = image.get_size()
    target_width, target_height = target_size
    
    if maintain_aspect:
        # Calculate scale factor to fit while maintaining aspect ratio
        scale_x = target_width / img_width
        scale_y = target_height / img_height
        scale = min(scale_x, scale_y)
        
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
    else:
        new_width, new_height = target_size
    
    return pygame.transform.scale(image, (new_width, new_height))

def get_text_size(text: str, font: pygame.font.Font) -> Tuple[int, int]:
    """Get the size of rendered text"""
    return font.size(text)

def center_rect_in_rect(inner_size: Tuple[int, int], outer_rect: pygame.Rect) -> pygame.Rect:
    """Center a rectangle of inner_size within outer_rect"""
    inner_width, inner_height = inner_size
    return pygame.Rect(
        outer_rect.centerx - inner_width // 2,
        outer_rect.centery - inner_height // 2,
        inner_width,
        inner_height
    )

def color_blend(color1: Tuple[int, int, int], color2: Tuple[int, int, int], ratio: float) -> Tuple[int, int, int]:
    """Blend two colors"""
    ratio = clamp(ratio, 0.0, 1.0)
    return (
        int(color1[0] * (1 - ratio) + color2[0] * ratio),
        int(color1[1] * (1 - ratio) + color2[1] * ratio),
        int(color1[2] * (1 - ratio) + color2[2] * ratio)
    )

def point_in_rect(point: Tuple[int, int], rect: pygame.Rect) -> bool:
    """Check if a point is inside a rectangle"""
    return rect.collidepoint(point)

def create_rounded_rect_surface(size: Tuple[int, int], color: Tuple[int, int, int], 
                               border_radius: int = 10) -> pygame.Surface:
    """Create a surface with a rounded rectangle"""
    surface = pygame.Surface(size, pygame.SRCALPHA)
    rect = pygame.Rect(0, 0, *size)
    pygame.draw.rect(surface, color, rect, border_radius=border_radius)
    return surface