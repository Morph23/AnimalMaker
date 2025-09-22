#!/usr/bin/env python3
"""
AnimalMaker - Transform handwritten animal names into animated animal pictures
Main entry point for the application
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from animal_maker import AnimalMaker

def main():
    """Main entry point"""
    try:
        app = AnimalMaker()
        app.run()
    except KeyboardInterrupt:
        print("\nApplication terminated by user")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()