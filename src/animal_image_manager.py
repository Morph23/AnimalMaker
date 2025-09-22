import pygame
import requests
import os
import json
from PIL import Image
from io import BytesIO
from typing import Optional, Dict, Any
import hashlib
import config

class AnimalImageManager:
    """Manages animal images from local assets and external APIs"""
    
    def __init__(self, assets_path: str = "assets/animals"):
        self.assets_path = assets_path
        self.cache_path = os.path.join(assets_path, "cache")
        self.cache_info_file = os.path.join(self.cache_path, "cache_info.json")
        
        # Ensure directories exist
        os.makedirs(self.cache_path, exist_ok=True)
        
        # Load cache info
        self.cache_info = self.load_cache_info()
        
        # Unsplash API configuration (free tier)
        self.unsplash_api_url = config.UNSPLASH_API_URL
        self.unsplash_access_key = config.UNSPLASH_API_KEY if config.UNSPLASH_API_KEY != "YOUR_API_KEY_HERE" else None
        
        # Debug API key detection
        print(f"Config API key value: '{config.UNSPLASH_API_KEY}'")
        print(f"API key comparison: {config.UNSPLASH_API_KEY != 'YOUR_API_KEY_HERE'}")
        
        if self.unsplash_access_key:
            print(f"Unsplash API key loaded: {self.unsplash_access_key[:10]}...")
        else:
            print("No Unsplash API key found - will use placeholders only")
        
        # Fallback to local placeholder generation
        self.default_size = (400, 400)
        
    def load_cache_info(self) -> Dict[str, Any]:
        """Load cache information from disk"""
        try:
            if os.path.exists(self.cache_info_file):
                with open(self.cache_info_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading cache info: {e}")
        return {}
        
    def save_cache_info(self) -> None:
        """Save cache information to disk"""
        try:
            with open(self.cache_info_file, 'w') as f:
                json.dump(self.cache_info, f, indent=2)
        except Exception as e:
            print(f"Error saving cache info: {e}")
            
    def get_cache_key(self, animal_name: str) -> str:
        """Generate cache key for animal name"""
        return hashlib.md5(animal_name.lower().encode()).hexdigest()
        
    def get_cached_image_path(self, animal_name: str) -> Optional[str]:
        """Get path to cached image if it exists"""
        cache_key = self.get_cache_key(animal_name)
        if cache_key in self.cache_info:
            image_path = os.path.join(self.cache_path, f"{cache_key}.png")
            if os.path.exists(image_path):
                return image_path
        return None
        
    def fetch_from_unsplash(self, animal_name: str) -> Optional[pygame.Surface]:
        """Fetch animal image from Unsplash API"""
        if not self.unsplash_access_key:
            print(f"No Unsplash API key - using placeholder for {animal_name}")
            return None
            
        try:
            import random
            # Add randomization to get different images each time
            random_page = random.randint(1, 10)  # Get from different pages
            random_per_page = random.randint(3, 20)  # Variable results per page
            random_pick = random.randint(0, min(random_per_page - 1, 9))  # Pick random result
            
            params = {
                'query': f'{animal_name} animal wildlife',
                'per_page': random_per_page,
                'page': random_page,
                'orientation': 'landscape',  # Changed from squarish for better variety
                'client_id': self.unsplash_access_key
            }
            
            response = requests.get(self.unsplash_api_url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            if data['results'] and len(data['results']) > random_pick:
                image_url = data['results'][random_pick]['urls']['regular']
                return self.download_image(image_url, animal_name)
                
        except Exception as e:
            print(f"Error fetching from Unsplash: {e}")
            
        return None
        
    def download_image(self, image_url: str, animal_name: str) -> Optional[pygame.Surface]:
        """Download image from URL and cache it"""
        try:
            response = requests.get(image_url, timeout=15)
            response.raise_for_status()
            
            # Open image with PIL
            pil_image = Image.open(BytesIO(response.content))
            
            # Resize to standard size
            try:
                
                pil_image = pil_image.resize(self.default_size, Image.Resampling.LANCZOS)
            except AttributeError:
                # Fallback to old syntax for older PIL versions
                pil_image = pil_image.resize(self.default_size, Image.LANCZOS)
            
            # Convert to RGBA if needed
            if pil_image.mode != 'RGBA':
                pil_image = pil_image.convert('RGBA')
            
            # Save to cache
            cache_key = self.get_cache_key(animal_name)
            cache_path = os.path.join(self.cache_path, f"{cache_key}.png")
            pil_image.save(cache_path)
            
            # Update cache info
            self.cache_info[cache_key] = {
                'animal_name': animal_name,
                'source': 'unsplash',
                'url': image_url
            }
            self.save_cache_info()
            
            # Convert to pygame surface
            mode = pil_image.mode
            size = pil_image.size
            data = pil_image.tobytes()
            
            pygame_image = pygame.image.fromstring(data, size, mode)
            return pygame_image
            
        except Exception as e:
            print(f"Error downloading image: {e}")
            return None
            
    def create_placeholder_image(self, animal_name: str) -> pygame.Surface:
        """Create a placeholder image for the animal"""
        surface = pygame.Surface(self.default_size, pygame.SRCALPHA)
        
        # Create simple black and white background
        width, height = self.default_size
        surface.fill((255, 255, 255))  # White background
        
        # Add black border
        pygame.draw.rect(surface, (0, 0, 0), (0, 0, width, height), 3)
        
        # Add animal name text
        font_size = min(48, width // max(len(animal_name), 1))
        try:
            font = pygame.font.Font(None, font_size)
        except:
            font = pygame.font.SysFont('Arial', font_size)
            
        text_color = (0, 0, 0)  # Black text
        text_surface = font.render(animal_name.title(), True, text_color)
        text_rect = text_surface.get_rect(center=(width // 2, height // 2))
        
        # Add simple shape based on animal type
        self.add_animal_shape(surface, animal_name)
        
        # Cache the placeholder
        cache_key = self.get_cache_key(animal_name)
        cache_path = os.path.join(self.cache_path, f"{cache_key}.png")
        pygame.image.save(surface, cache_path)
        
        # Update cache info
        self.cache_info[cache_key] = {
            'animal_name': animal_name,
            'source': 'placeholder'
        }
        self.save_cache_info()
        
        return surface
        
    def add_animal_shape(self, surface: pygame.Surface, animal_name: str) -> None:
        """Add simple shape representation of animal"""
        width, height = surface.get_size()
        center_x, center_y = width // 2, height // 2
        
        # Define colors (black and white only)
        shape_color = (0, 0, 0)  # Black shapes
        
        # Simple shapes based on animal type
        if animal_name in ['cat', 'dog', 'wolf', 'fox']:
            # Draw simple quadruped silhouette
            pygame.draw.ellipse(surface, shape_color, (center_x - 80, center_y + 20, 160, 60), 2)
            pygame.draw.circle(surface, shape_color, (center_x - 60, center_y + 10), 25, 2)
            
        elif animal_name in ['bird', 'eagle', 'owl', 'penguin']:
            # Draw bird shape
            pygame.draw.ellipse(surface, shape_color, (center_x - 30, center_y + 10, 60, 100), 2)
            pygame.draw.circle(surface, shape_color, (center_x, center_y - 20), 20, 2)
            
        elif animal_name in ['fish', 'shark']:
            # Draw fish shape
            pygame.draw.ellipse(surface, shape_color, (center_x - 60, center_y + 30, 120, 40), 2)
            # Triangle tail
            points = [(center_x + 60, center_y + 50), (center_x + 100, center_y + 30), (center_x + 100, center_y + 70)]
            pygame.draw.polygon(surface, shape_color, points, 2)
            
        else:
            # Default circle for other animals
            pygame.draw.circle(surface, shape_color, (center_x, center_y + 30), 50, 2)
            
    def get_animal_image(self, animal_name: str) -> pygame.Surface:
        """Get animal image - always fetch fresh random image, no caching"""
        print(f"Getting fresh image for: {animal_name}")
        
        # Always try to fetch a fresh random image from Unsplash
        if self.unsplash_access_key:
            print("Trying to fetch from Unsplash...")
            api_image = self.fetch_from_unsplash(animal_name)
            if api_image:
                print("Successfully fetched from Unsplash")
                return api_image
        else:
            print("No Unsplash API key - skipping API fetch")
                
        # Create placeholder as fallback
        print(f"Creating placeholder for {animal_name}")
        return self.create_placeholder_image(animal_name)
        
    def set_unsplash_api_key(self, api_key: str) -> None:
        """Set Unsplash API key for fetching real images"""
        self.unsplash_access_key = api_key
        
    def preload_common_animals(self, animal_list: list) -> None:
        """Preload images for common animals"""
        for animal in animal_list:
            if not self.get_cached_image_path(animal):
                print(f"Preloading {animal}...")
                self.get_animal_image(animal)