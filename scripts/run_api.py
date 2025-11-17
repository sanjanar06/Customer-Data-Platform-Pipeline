#!/usr/bin/env python3
"""
Wrapper script to run the refactored Personalization API.
Provides backward compatibility with the original personalization_api.py interface.
"""
import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.python.api.main import main

if __name__ == "__main__":
    sys.exit(main())
