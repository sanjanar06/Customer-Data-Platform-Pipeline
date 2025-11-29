#!/usr/bin/env python3
"""Run the batch job scheduler."""
import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.python.batch.scheduler import main

if __name__ == "__main__":
    main()
