#!/usr/bin/env python3
"""
Test script to verify config is working correctly
"""

import os
from config import BASE_PATH, OUTPUT_DIR, SAMPLES_PRESETS_PATH

def test_config():
    print("Testing Configuration...")
    print("=" * 50)
    
    print(f"BASE_PATH: {BASE_PATH}")
    print(f"OUTPUT_DIR: {OUTPUT_DIR}")
    print(f"SAMPLES_PRESETS_PATH: {SAMPLES_PRESETS_PATH}")
    
    print("\nChecking if directories exist:")
    print(f"  BASE_PATH exists: {os.path.exists(BASE_PATH)}")
    print(f"  OUTPUT_DIR exists: {os.path.exists(OUTPUT_DIR)}")
    print(f"  SAMPLES_PRESETS_PATH exists: {os.path.exists(SAMPLES_PRESETS_PATH)}")
    
    print("\nCreating output directory if it doesn't exist...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"  OUTPUT_DIR now exists: {os.path.exists(OUTPUT_DIR)}")
    
    print("\nConfiguration test completed successfully!")

if __name__ == "__main__":
    test_config() 