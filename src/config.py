"""
Configuration file for Animal Maker application
"""

# Application settings
APP_TITLE = "Animal Maker"
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
FPS = 60

# Drawing settings
BRUSH_SIZE = 5
DRAWING_COLOR = (0, 0, 0)  # Black
CANVAS_BG_COLOR = (255, 255, 255)  # White

# Animation settings
DEFAULT_ANIMATION_DURATION = 3.0  # seconds
IDLE_DETECTION_TIME = 3000  # milliseconds

# OCR settings
TESSERACT_CONFIG = r'--oem 3 --psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
MIN_WORD_LENGTH = 3
MAX_EDIT_DISTANCE = 2

# Image settings
DEFAULT_IMAGE_SIZE = (400, 400)
CACHE_ENABLED = True

# Colors
UI_BG_COLOR = (240, 240, 245)
TEXT_COLOR = (50, 50, 50)
HINT_COLOR = (120, 120, 120)
ERROR_COLOR = (200, 50, 50)
SUCCESS_COLOR = (50, 150, 50)

# Paths
ASSETS_PATH = "assets"
ANIMALS_PATH = "assets/animals"
CACHE_PATH = "assets/animals/cache"

# API Configuration (optional)
UNSPLASH_API_KEY = "HSSjaMe-Vs4Q7DbCioROkXSOuJo2S_uR144dlvMueHU"  # Replace with your actual Unsplash API key
UNSPLASH_API_URL = "https://api.unsplash.com/search/photos"

# Particle system settings
PARTICLE_SAMPLING_STEP = 2  # Pixel sampling rate (higher = fewer particles)
MAX_PARTICLES = 1000
GRAVITY = 0.5
FRICTION = 0.95

# Common animal names for better recognition
COMMON_ANIMALS = [
    'cat', 'dog', 'elephant', 'lion', 'tiger', 'bear', 'wolf', 'fox',
    'rabbit', 'horse', 'cow', 'pig', 'sheep', 'goat', 'deer', 'zebra',
    'giraffe', 'hippo', 'rhino', 'monkey', 'bird', 'eagle', 'owl',
    'penguin', 'snake', 'turtle', 'fish', 'shark', 'whale', 'dolphin'
]
