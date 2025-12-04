# Music Production Tools

A comprehensive collection of Python tools for music production, analysis, composition, and sample management.

## Overview

This repository contains tools for:
- **Analysis**: Chord progressions, Ableton Live projects, audio track analysis
- **Composition**: MIDI pattern generation (drums, arrangements, melodic progressions)
- **Sample Management**: Audio sample analysis, tagging, and organization
- **Stem Separation**: Integration with LALAL.AI and FADR for audio stem separation
- **Project Management**: File organization and deduplication utilities
- **Plugin Management**: VST plugin and Ableton instrument management scripts

## Quick Start

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd music-production
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment (optional):
```bash
cp .env.example .env
# Edit .env with your paths and settings
```

### Configuration

The project uses environment variables for configuration. Create a `.env` file based on `.env.example`:

```bash
# Base paths
MUSIC_PRODUCTION_BASE_PATH=/path/to/your/music
MUSIC_PRODUCTION_SAMPLES_PATH=/path/to/your/samples
MUSIC_PRODUCTION_PRESETS_PATH=/path/to/your/presets

# Output directories
MUSIC_PRODUCTION_OUTPUT_DIR=./out
```

Or set environment variables directly:
```bash
export MUSIC_PRODUCTION_SAMPLES_PATH="/path/to/samples"
```

## Module Documentation

### Analysis Module

Tools for analyzing musical content:

- **Chord Analysis**: Analyze chord progressions with roman numeral analysis
- **Ableton Analyzer**: Parse and analyze Ableton Live `.als` project files
- **MHT Pipeline**: Melodic House & Techno analysis pipeline

**Example**:
```bash
cd analysis
python csv_chord_processor.py data/chords.csv --bpm=128 --key=Am
python chord_analysis.py data/chords_with_bars.csv
python ableton_analyzer.py data/project.als
```

### Compose Module

Generate MIDI patterns and arrangements:

- **Drum Patterns**: Generate House/Techno drum patterns with swing and humanization
- **Arrangement Skeletons**: Create arrangement templates for tracks
- **Melodic Progressions**: Generate melodic chord progressions

**Example**:
```bash
cd compose
python make_mh_techno_drums.py --bpm=128 --bars=16 --flavor=afro
python make_arrangement_skeletons_mh.py
```

### Tag-Sounds Module

Analyze and tag audio samples:

- **Unified Analyzer**: Single interface for all analysis modes
- **Smart Tagging**: Automatic tag extraction from filenames
- **Category Identification**: Identify sample categories and types

**Example**:
```bash
cd tag-sounds
python analyze_samples_unified.py --mode=smart --samples-path=/path/to/samples
```

### Project Management

Organize and manage music files:

- **File Organization**: Organize files by date with deduplication
- **Missing File Finder**: Find missing files in projects
- **ASD Cleanup**: Remove Ableton .asd cache files

**Example**:
```bash
cd project-mngmnt
python organize_music.py --source=/path/to/source --dest=/path/to/dest
```

## Project Structure

```
music-production/
├── analysis/          # Music analysis tools
├── compose/           # MIDI generation
├── tag-sounds/        # Sample analysis and tagging
├── stemming/          # Audio stem separation
├── plugins/           # Plugin management
├── project-mngmnt/    # File organization
├── utils/             # Shared utilities
├── docs/              # Documentation
├── config.py          # Central configuration
├── requirements.txt   # Python dependencies
└── .env.example       # Environment variable template
```

## Dependencies

Core dependencies:
- `pandas` - Data manipulation
- `numpy` - Numerical operations
- `mido` / `midiutil` - MIDI processing
- `librosa` - Audio analysis
- `soundfile` - Audio I/O
- `matplotlib` - Visualization

See `requirements.txt` for complete list.

## Development

### Code Structure

The project follows a modular structure:
- Each module has an `__init__.py` for package imports
- Shared utilities are in `utils/`
- Configuration is centralized in `config.py`

### Adding New Features

1. Add your module to the appropriate directory
2. Update `__init__.py` to export public APIs
3. Use `config.py` for configuration (no hardcoded paths)
4. Add tests if possible
5. Update this README

## Recent Refactoring

This codebase has been refactored to:
- ✅ Remove hardcoded paths (now uses environment variables)
- ✅ Add proper package structure with `__init__.py` files
- ✅ Consolidate duplicate code (unified sample analyzer)
- ✅ Create central configuration system
- ✅ Add unified requirements.txt

See `CODEBASE_ANALYSIS.md` and `REFACTORING_PLAN.md` for details.

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
