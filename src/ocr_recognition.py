"""
OCR Recognition - Handles text recognition from drawn images
"""

import pygame
import cv2
import numpy as np
from PIL import Image
import pytesseract
import easyocr
import re
from typing import Optional, List

# Handle PIL version compatibility
try:
    from PIL.Image import Resampling
    LANCZOS = Resampling.LANCZOS
except ImportError:
    # Fallback for older PIL versions
    LANCZOS = Image.LANCZOS

class OCRRecognizer:
    """Handles OCR recognition of handwritten text"""
    
    def __init__(self):
        # Configure Tesseract path for Windows if needed
        self.setup_tesseract()
        
        # Initialize EasyOCR reader for better handwriting recognition
        # Fix PIL compatibility issue
        self.patch_pil_compatibility()
        
        try:
            self.easyocr_reader = easyocr.Reader(['en'], verbose=False)
            print("EasyOCR initialized successfully")
        except Exception as e:
            print(f"Warning: EasyOCR initialization failed: {e}")
            self.easyocr_reader = None
            
        # Common animal names for validation
        self.animal_names = {
            'cat', 'dog', 'elephant', 'lion', 'tiger', 'bear', 'wolf', 'fox',
            'rabbit', 'horse', 'cow', 'pig', 'sheep', 'goat', 'deer', 'zebra',
            'giraffe', 'hippo', 'rhino', 'monkey', 'ape', 'gorilla', 'chimpanzee',
            'bird', 'eagle', 'hawk', 'owl', 'penguin', 'flamingo', 'parrot',
            'snake', 'lizard', 'turtle', 'crocodile', 'alligator', 'frog',
            'fish', 'shark', 'whale', 'dolphin', 'octopus', 'crab', 'lobster',
            'butterfly', 'bee', 'spider', 'ant', 'ladybug', 'dragonfly',
            'kangaroo', 'koala', 'panda', 'sloth', 'bat', 'squirrel', 'mouse',
            'hamster', 'guinea pig', 'ferret', 'chinchilla', 'hedgehog'
        }
        
    def setup_tesseract(self):
        """Setup Tesseract path for different operating systems"""
        import os
        import platform
        
        # Common Tesseract installation paths
        if platform.system() == "Windows":
            possible_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                r"C:\Users\{}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe".format(os.getenv('USERNAME')),
            ]
            
            for path in possible_paths:
                try:
                    if os.path.exists(path):
                        pytesseract.pytesseract.tesseract_cmd = path
                        pytesseract.get_tesseract_version()
                        print(f"Tesseract found at: {path}")
                        return
                except Exception:
                    continue
            
            # If not found in standard locations, try PATH
            try:
                pytesseract.get_tesseract_version()
                print("Tesseract found in PATH")
                return
            except Exception:
                print("Warning: Tesseract not found in common locations. Please ensure it's installed and in PATH.")
        else:
            # For macOS and Linux, tesseract should be in PATH
            try:
                pytesseract.get_tesseract_version()
                print("Tesseract found in PATH")
            except Exception:
                print("Warning: Tesseract not found. Please install tesseract-ocr package.")
        
    def preprocess_image(self, surface: pygame.Surface) -> np.ndarray:
        """Preprocess the drawing surface for better OCR recognition"""
        # Convert pygame surface to numpy array
        image_array = pygame.surfarray.array3d(surface)
        
        # Convert from RGB to BGR for OpenCV
        image_array = np.transpose(image_array, (1, 0, 2))
        image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        
        # Invert colors (black text on white background)
        gray = cv2.bitwise_not(gray)
        
        # Apply Gaussian blur to smooth edges
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # Apply threshold to get binary image
        _, thresh = cv2.threshold(blurred, 127, 255, cv2.THRESH_BINARY)
        
        # Apply morphological operations to clean up the image
        kernel = np.ones((2, 2), np.uint8)
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        # Resize image for better OCR (OCR works better on larger images)
        height, width = cleaned.shape
        if width < 200:
            scale_factor = 200 / width
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            cleaned = cv2.resize(cleaned, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        return cleaned
        
    def recognize_text_tesseract(self, processed_image: np.ndarray) -> Optional[str]:
        """Use Tesseract OCR to recognize text with improved configuration"""
        try:
            # Convert numpy array to PIL Image
            pil_image = Image.fromarray(processed_image)
            
            # Try multiple PSM modes for better handwriting recognition
            psm_modes = [8, 7, 13, 6]  # Single word, single text line, raw line, single uniform block
            
            for psm in psm_modes:
                try:
                    # More permissive character whitelist and better config for handwriting
                    custom_config = f'--oem 3 --psm {psm} -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
                    text = pytesseract.image_to_string(pil_image, config=custom_config)
                    
                    # Clean up the recognized text
                    text = text.strip().lower()
                    text = re.sub(r'[^a-zA-Z\s]', '', text)
                    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space
                    
                    if text and len(text) >= 2:  # At least 2 characters
                        return text
                        
                except Exception as e:
                    continue
            
            return None
            
        except Exception as e:
            print(f"Tesseract OCR error: {e}")
            return None
            
    def recognize_text_easyocr(self, processed_image: np.ndarray) -> Optional[str]:
        """Use EasyOCR to recognize text"""
        if not self.easyocr_reader:
            return None
            
        try:
            # EasyOCR expects image in standard format
            results = self.easyocr_reader.readtext(processed_image, detail=0)
            
            if results:
                # Join all recognized text
                text = ' '.join(results).strip().lower()
                text = re.sub(r'[^a-zA-Z\s]', '', text)
                return text if text else None
                
        except Exception as e:
            print(f"EasyOCR error: {e}")
            
        return None
        
    def find_best_animal_match(self, recognized_text: str) -> Optional[str]:
        """Find the best matching animal name from recognized text"""
        if not recognized_text:
            return None
            
        words = recognized_text.split()
        
        # First, try exact matches
        for word in words:
            if word in self.animal_names:
                return word
                
        # Then try partial matches
        for word in words:
            for animal in self.animal_names:
                if len(word) >= 3 and (word in animal or animal in word):
                    return animal
                    
        # Finally, try fuzzy matching (simple edit distance)
        best_match = None
        min_distance = float('inf')
        
        for word in words:
            if len(word) >= 3:
                for animal in self.animal_names:
                    distance = self.simple_edit_distance(word, animal)
                    if distance < min_distance and distance <= 2:  # Allow max 2 character differences
                        min_distance = distance
                        best_match = animal
                        
                return best_match
                
    def patch_pil_compatibility(self):
        """Patch PIL compatibility issues for EasyOCR"""
        try:
            from PIL import Image
            # Add the missing ANTIALIAS attribute for older code compatibility
            if not hasattr(Image, 'ANTIALIAS'):
                Image.ANTIALIAS = Image.Resampling.LANCZOS
            print("PIL compatibility patch applied")
        except Exception as e:
            print(f"PIL patch error (non-critical): {e}")
            
    def simple_edit_distance(self, s1: str, s2: str) -> int:
        """Calculate simple edit distance between two strings"""
        if len(s1) < len(s2):
            return self.simple_edit_distance(s2, s1)
            
        if len(s2) == 0:
            return len(s1)
            
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
            
        return previous_row[-1]
        
    def recognize_animal_name(self, surface: pygame.Surface) -> Optional[str]:
        """Main method to recognize animal name from drawing surface"""
        if not surface:
            return None
            
        # Preprocess the image
        try:
            processed_image = self.preprocess_image(surface)
        except Exception as e:
            print(f"Error preprocessing image: {e}")
            return None
        
        # Try both OCR methods
        recognized_texts = []
        
        # Try EasyOCR first (better for handwriting)
        if self.easyocr_reader:
            easyocr_text = self.recognize_text_easyocr(processed_image)
            if easyocr_text:
                recognized_texts.append(easyocr_text)
        else:
            print("EasyOCR not available, skipping...")
            
        # Try Tesseract as backup
        tesseract_text = self.recognize_text_tesseract(processed_image)
        if tesseract_text:
            recognized_texts.append(tesseract_text)
            
        # Find best animal match from all recognized texts
        for text in recognized_texts:
            animal = self.find_best_animal_match(text)
            if animal:
                print(f"Recognized animal: {animal} from text: {text}")
                return animal
                
        # If no animal found, print what was recognized for debugging
        if recognized_texts:
            print(f"No animal found in recognized text: {recognized_texts}")
            # Try to suggest the closest animal for any recognized word
            for text in recognized_texts:
                words = text.split()
                if words:
                    closest = self.suggest_closest_animal(words[0])
                    if closest:
                        print(f"Did you mean '{closest}'? Trying that...")
                        return closest
        else:
            print("No text could be recognized")
            
        return None
        
    def suggest_closest_animal(self, word: str) -> Optional[str]:
        """Suggest the closest animal name for a given word"""
        if len(word) < 2:
            return None
            
        best_match = None
        min_distance = float('inf')
        
        for animal in self.animal_names:
            distance = self.simple_edit_distance(word.lower(), animal)
            if distance < min_distance and distance <= 3:  # Allow up to 3 character differences
                min_distance = distance
                best_match = animal
                
        return best_match