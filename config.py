"""
Central configuration file for music-production tools.
Uses environment variables with sensible defaults.
"""
import os
from pathlib import Path
from typing import Optional

# Base paths - can be overridden via environment variables
DEFAULT_BASE_PATH = os.getenv("MUSIC_PRODUCTION_BASE_PATH", str(Path.home() / "Music"))
DEFAULT_SAMPLES_PATH = os.getenv("MUSIC_PRODUCTION_SAMPLES_PATH", str(Path(DEFAULT_BASE_PATH) / "Samples"))
DEFAULT_PRESETS_PATH = os.getenv("MUSIC_PRODUCTION_PRESETS_PATH", str(Path(DEFAULT_BASE_PATH) / "Presets"))
DEFAULT_MIDI_PATH = os.getenv("MUSIC_PRODUCTION_MIDI_PATH", str(Path(DEFAULT_BASE_PATH) / "MIDI"))

# Output directories
OUTPUT_DIR = os.getenv("MUSIC_PRODUCTION_OUTPUT_DIR", str(Path(__file__).parent / "out"))
ANALYSIS_OUTPUT_DIR = os.getenv("MUSIC_PRODUCTION_ANALYSIS_OUTPUT", str(Path(OUTPUT_DIR) / "analysis"))
COMPOSE_OUTPUT_DIR = os.getenv("MUSIC_PRODUCTION_COMPOSE_OUTPUT", str(Path(OUTPUT_DIR) / "compose"))
TAG_SOUNDS_OUTPUT_DIR = os.getenv("MUSIC_PRODUCTION_TAG_SOUNDS_OUTPUT", str(Path(OUTPUT_DIR) / "tag-sounds"))

# Default audio processing settings
DEFAULT_SAMPLE_RATE = int(os.getenv("MUSIC_PRODUCTION_SAMPLE_RATE", "44100"))
DEFAULT_BPM = int(os.getenv("MUSIC_PRODUCTION_DEFAULT_BPM", "124"))

# API Keys (optional)
LALALAI_API_KEY = os.getenv("LALALAI_API_KEY", "")
FADR_API_KEY = os.getenv("FADR_API_KEY", "")

# Analysis settings
DEFAULT_CHORD_HOP = float(os.getenv("MUSIC_PRODUCTION_CHORD_HOP", "0.5"))
DEFAULT_CHORD_SMOOTH_WIN = int(os.getenv("MUSIC_PRODUCTION_CHORD_SMOOTH_WIN", "3"))

# MIDI settings
DEFAULT_MIDI_CHANNEL = int(os.getenv("MUSIC_PRODUCTION_MIDI_CHANNEL", "0"))
DEFAULT_MIDI_VELOCITY = int(os.getenv("MUSIC_PRODUCTION_MIDI_VELOCITY", "100"))

def get_base_path() -> Path:
    """Get the base path for music production files."""
    return Path(DEFAULT_BASE_PATH)

def get_samples_path() -> Path:
    """Get the path to samples directory."""
    return Path(DEFAULT_SAMPLES_PATH)

def get_presets_path() -> Path:
    """Get the path to presets directory."""
    return Path(DEFAULT_PRESETS_PATH)

def get_midi_path() -> Path:
    """Get the path to MIDI files directory."""
    return Path(DEFAULT_MIDI_PATH)

def get_output_dir() -> Path:
    """Get the output directory."""
    path = Path(OUTPUT_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_analysis_output_dir() -> Path:
    """Get the analysis output directory."""
    path = Path(ANALYSIS_OUTPUT_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_compose_output_dir() -> Path:
    """Get the compose output directory."""
    path = Path(COMPOSE_OUTPUT_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_tag_sounds_output_dir() -> Path:
    """Get the tag-sounds output directory."""
    path = Path(TAG_SOUNDS_OUTPUT_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path

