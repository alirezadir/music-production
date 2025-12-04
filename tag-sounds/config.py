#!/usr/bin/env python3
"""
Configuration file for tag-sounds project.
Now uses central config system with environment variable support.
"""
import sys
from pathlib import Path

# Add parent directory to path to import central config
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from config import (
        get_samples_path,
        get_presets_path,
        get_midi_path,
        get_tag_sounds_output_dir,
        DEFAULT_SAMPLES_PATH,
        DEFAULT_PRESETS_PATH,
        DEFAULT_MIDI_PATH,
        TAG_SOUNDS_OUTPUT_DIR
    )
    
    # Use central config with fallback to defaults
    SAMPLES_PRESETS_PATH = str(get_samples_path().parent) if get_samples_path().exists() else DEFAULT_SAMPLES_PATH
    SAMPLES_PATH = str(get_samples_path())
    PRESETS_PATH = str(get_presets_path())
    MIDI_PATH = str(get_midi_path())
    OUTPUT_DIR = str(get_tag_sounds_output_dir())
    
except ImportError:
    # Fallback if central config not available
    import os
    BASE_PATH = os.getenv("MUSIC_PRODUCTION_BASE_PATH", str(Path.home() / "Music"))
    
    SAMPLES_PRESETS_PATH = os.getenv("MUSIC_PRODUCTION_SAMPLES_PATH", f"{BASE_PATH}/Samples")
    SAMPLES_PATH = os.getenv("MUSIC_PRODUCTION_SAMPLES_PATH", f"{BASE_PATH}/Samples")
    PRESETS_PATH = os.getenv("MUSIC_PRODUCTION_PRESETS_PATH", f"{BASE_PATH}/Presets")
    MIDI_PATH = os.getenv("MUSIC_PRODUCTION_MIDI_PATH", f"{BASE_PATH}/MIDI")
    OUTPUT_DIR = os.getenv("MUSIC_PRODUCTION_TAG_SOUNDS_OUTPUT", str(Path(__file__).parent / "out")) 
