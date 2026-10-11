# Music-Production Track Analyzer (4 Pillars)

A Python toolkit for analyzing musical content with a consistent, expandable output schema. This repo currently includes chord/progression tools, Ableton `.als` parsing, an audio analysis pipeline (MHT), and sample-tag utilities.

## Overview

This package is evolving towards a **track analyzer** with four pillars:

- **Chord progressions**: key, roman numerals, cadence/progression summaries
- **Elements**: musical elements and instruments (e.g. synth types, bassline, drums), primarily from Ableton track/device metadata
- **Patterns (sounds)**: similarity-friendly descriptions of sounds/patterns (initially from filenames/tags; later from embeddings/features)
- **Arrangement analysis**: sections like intro/break/build/drop/outro from audio and/or Ableton arrangement

## Module Structure

```
analyzer/
├── progression/           # Chord/progression analysis (CSV → bars, roman numerals, summaries)
├── abelton/               # Ableton `.als` analysis + MHT audio pipeline (historical spelling)
├── arrangement/           # Placeholder package for arrangement analysis pillar
├── sound/                 # Sample tagging utilities (scripts)
├── metadata/              # Beatport mining (separate concern; used for dataset building)
├── data/                  # Sample inputs + outputs
├── track_schema.py        # Unified output schema (maps to your 4 pillars)
├── chord_analysis.py      # Compatibility wrapper → progression/
├── chord_utils.py         # Compatibility wrapper → progression/
├── csv_chord_processor.py # Compatibility wrapper → progression/
├── ableton_analyzer.py    # Compatibility wrapper → abelton/
└── analyze_mht_pipeline.py# Compatibility wrapper → abelton/
```

### Stable output schema (recommended)

All new work should target `TrackAnalysis` (`analyzer/track_schema.py`) so you can index/search consistently across pillars.

### Sound similarity (starter)

For a lightweight “good enough to start” similarity search over your sample names/tags (no extra deps), see `analyzer/sound/sample_similarity.py`.
It can build an index from the JSON created by `analyzer/sounds/tag-sounds/analyze_samples_unified.py` (script).

---

## 1. Chord Analysis

### Features

- **Roman Numeral Analysis**: Convert chords to scale degrees (I, ii, iii, IV, V, vi, vii°)
- **Progression Pattern Detection**: Identify common progressions (I-IV-V, vi-IV-V, etc.)
- **Cadence Detection**: Identify authentic, plagal, and half cadences
- **Harmonic Rhythm Analysis**: Analyze chord change frequency
- **Tension & Resolution**: Analyze harmonic tension and resolution patterns
- **Section Structure**: Identify song sections (verse, chorus, bridge)
- **MIDI Generation**: Create MIDI files with piano triads from chord progressions
- **Key Detection**: Automatically detect musical key from chord progressions

### Usage

#### Basic Chord Processing

```bash
# Process a CSV file with time-based chord data
python -m analyzer.progression.csv_chord_processor data/All_you_need_is_love_chords.csv --bpm=124 --key=Gm

# Outputs:
# - data/out/chords_with_bars.csv (bar-based notation)
# - data/out/chords_piano_triads.mid (MIDI file)
```

#### Comprehensive Analysis

```bash
# Run full chord analysis (requires chords_with_bars.csv)
python -m analyzer.progression.chord_analysis All_you_need_is_love_chords

# Outputs:
# - data/out/All_you_need_is_love_chords_analysis_summary.md
```

#### CSV Format

Input CSV should have columns:
- `chord`: Chord notation (e.g., "G:min", "D#:maj", "F:maj")
- `start_time` / `end_time` **or** `start` / `end`: Start/end time in seconds

Optional columns:
- `bar_start`: Bar number (if already calculated)
- `bar_end`: Bar number (if already calculated)

### Chord Analysis Classes

**`ChordAnalyzer`** (`chord_analysis.py`)
- Initialized with key and BPM
- Provides roman numeral conversion
- Analyzes progressions, cadences, harmonic rhythm
- Generates markdown analysis summaries

**Key Methods:**
- `chord_to_degree(chord_str)` - Convert chord to roman numeral
- `analyze_progressions(df)` - Find common progression patterns
- `detect_cadences(df)` - Identify cadence types
- `analyze_harmonic_rhythm(df)` - Analyze chord change frequency
- `analyze_tension_and_resolution(df)` - Tension/resolution analysis
- `generate_summary_markdown(df)` - Create detailed analysis report

**Utility Functions** (`chord_utils.py`)
- `time_to_bars(time_seconds, bpm)` - Convert seconds to bar numbers
- `bars_to_range(start_bar, end_bar)` - Create bar range string
- `parse_chord(chord_str)` - Parse chord notation
- `get_chord_notes(root, chord_type)` - Get MIDI notes for chord
- `get_smooth_voicing(root, chord_type, base_octave, prev_notes)` - Generate smooth voice leading
- `detect_key_from_chords(chords)` - Detect key from chord progression

---

## 2. Ableton Live Project Analysis

### Features

- Parse compressed `.als` project files (gzipped XML)
- Extract project metadata (tempo, time signature, version info)
- Analyze tracks (MIDI, Audio, Return, Master)
- Extract clip data, devices, automation
- Analyze arrangement structure
- Generate project-level JSON and Markdown reports covering arrangement sections, layer balance, mixer state, device chains, samples, and automation

### Usage

#### Project report CLI

```bash
python -m analyzer.ableton_project_analyzer "docs/Anyma-Higher Power.als" --out-dir analyzer/summaries
```

Outputs:

- `*_ableton_analysis.json`: structured analysis for indexing or further processing
- `*_ableton_analysis.md`: readable report for arrangement, layers, mixing, and automation

Useful options:

```bash
# Print the Markdown report to stdout
python -m analyzer.ableton_project_analyzer "path/to/project.als" --print-summary

# Include every MIDI note event in the JSON output; default keeps compact note summaries
python -m analyzer.ableton_project_analyzer "path/to/project.als" --include-notes

# Analyze an already decompressed Ableton XML file
python -m analyzer.ableton_project_analyzer "path/to/project.als.xml"
```

Run the self-contained analyzer smoke test:

```bash
PYTHONPYCACHEPREFIX=/private/tmp/pycache python3 -m unittest analyzer.abelton.test_project_analyzer
```

The report includes:

- **Arrangement**: project length, locators, inferred sections, active tracks/layers per section, density windows
- **Layers**: track classification such as drums, bass, chords, pad, lead, vocal, FX, audio, and utility
- **Mixing**: volume in dB, pan, mute/solo state, active sends, quiet/loud tracks, master chain, device counts
- **Automation**: envelope/event counts, automated tracks/layers, top targets, notable automation ranges

#### Legacy reader API

```python
from analyzer.ableton_analyzer import AbletonProjectReader

reader = AbletonProjectReader("path/to/project.als")
reader.load()

# Get project info
info = reader.get_project_info()
print(f"Tempo: {info['tempo']} BPM")
print(f"Time Signature: {info['time_signature']}")

# Get all tracks
tracks = reader.get_tracks()
for track in tracks:
    print(f"{track['name']} ({track['type']})")
    print(f"  Clips: {len(track['clips'])}")
    print(f"  Devices: {len(track['devices'])}")
```

### Output Format

Analysis results are saved as JSON:
```json
{
  "project_info": {
    "tempo": 124.0,
    "time_signature": {"numerator": 4, "denominator": 4}
  },
  "tracks": [
    {
      "name": "Lead Synth",
      "type": "MIDI",
      "clips": [...],
      "devices": [...]
    }
  ]
}
```

---

## 3. MHT (Melodic House & Techno) Audio Analysis Pipeline

### Features

- **BPM Detection**: Automatic tempo estimation using librosa
- **Key Detection**: Musical key detection using chroma analysis
- **Chord Extraction**: Extract chord progressions from audio
- **Stem Support**: Analyze harmonic/melodic stems separately (LALAL.AI, FADR)
- **Camelot Wheel Mapping**: Convert keys to Camelot wheel notation
- **Timeline Analysis**: Generate chord progression timelines

### Usage

```bash
# Analyze a track (with optional stemming)
python -m analyzer.abelton.analyze_mht_pipeline --in path/to/folder/with/audio --stem-cmd="your_stem_command"

# Outputs chord progression timeline and analysis
```

### Stem Separation

The pipeline supports audio stem separation:
- Prioritizes harmonic/melodic stems for better chord detection
- Falls back to full mix if stems unavailable
- Supports LALAL.AI and FADR output formats

### Features Extracted

- **Tempo**: BPM estimation
- **Key**: Musical key (with Camelot wheel mapping)
- **Chords**: Detected chord progressions
- **Arrangement**: Section structure analysis
- **Energy**: Track energy levels over time

---

## 4. Beatport Data Miner (bp-miner)

A comprehensive system for scraping and analyzing Beatport data to discover labels, artists, and tracks.

### Pipeline Overview

**Phase 1**: Seed artists from A-level labels  
**Phase 2**: Scrape artist tracks  
**Phase 3**: Classify B-level labels using KNN similarity  
**Phase 4**: Scrape tracks from B-level labels  
**Phase 5**: Clean and deduplicate data  
**Phase 6**: Sync to Google Sheets (optional)

### Quick Start

```bash
cd bp-miner

# Install dependencies
pip install -r requirements.txt

# Run full pipeline
python run_full_pipeline.py

# Or run specific phases
python run_full_pipeline.py --phases 1,2,3
```

### Configuration

Edit `config.json`:
```json
{
  "a_level_labels": [
    "Afterlife Records",
    "Anjunadeep",
    "Toolroom",
    "Keinemusik",
    "Stil Vor Talent"
  ],
  "a_level_label_urls": {
    "Afterlife Records": "https://www.beatport.com/label/afterlife-records/56958",
    ...
  },
  "tracks_per_page": 50,
  "b_labels_per_a_label": 5
}
```

### Key Scripts

**Label & Artist Discovery:**
- `seed_artists_from_labels.py` - Extract artists from A-level label pages
- `scrape_artist_tracks.py` - Scrape tracks from artist pages
- `classify_b_labels.py` - Use KNN to find similar B-level labels
- `scrape_b_labels.py` - Scrape tracks from B-level labels
- `scrape_b_label_tracks.py` - Scrape Top 10 + Latest 10 from B-labels (NEW)

**Data Management:**
- `clean_all.py` - Clean and deduplicate all data
- `sync_all_to_sheets.py` - Sync data to Google Sheets
- `csv_store.py` - CSV storage utilities
- `models.py` - Data models (TrackMeta, etc.)

**Scraping Utilities:**
- `scraper_utils.py` - HTTP fetching with retries
- `label_scraper.py` - Label page parsing
- `artist_scraper.py` - Artist page parsing
- `firecrawl_helper.py` - Firecrawl MCP integration (alternative scraping)

### Data Schemas

**artists.csv:**
- `artist_name`, `beatport_url`, `source_label`, `created_at`

**labels.csv:**
- `label_name`, `beatport_url`, `tier` (A/B/unknown), `created_at`

**tracks.csv:**
- `title`, `artists`, `label`, `label_tier`, `genre`, `bpm`, `key`, `released_date`, `track_url`, `source_page_type`, `source_label`, `source_artist`, `created_at`

**afterlife_b_label_top_and_latest_tracks.csv:**
- `label_b_name`, `label_a_similar_to`, `track_name`, `category` (most_pop_10/latest_10), `artist_name`, `genre`, `bpm`, `key`

### KNN Label Classification

The system uses K-nearest neighbors (KNN) to find similar B-level labels:
- **Shared Artists** (40% weight): Artists appearing on both labels
- **Shared Genres** (30% weight): Genre overlap
- **BPM Distribution** (20% weight): Similar BPM ranges
- **Key Distribution** (10% weight): Similar key preferences

Top 5 most similar B-level labels are selected per A-level label.

---

## Dependencies

### Core Analysis
```txt
pandas>=1.5.0
numpy>=1.21.0
midiutil>=1.2.1
```

### Audio Analysis (MHT Pipeline)
```txt
librosa>=0.9.0
soundfile>=0.10.0
matplotlib>=3.5.0
```

### Beatport Scraping
```txt
beautifulsoup4>=4.12.0
requests>=2.31.0
gspread>=5.12.0
google-auth>=2.23.0
lxml>=4.9.0
```

### Full Installation

```bash
# Core analysis dependencies
pip install pandas numpy midiutil

# Audio analysis dependencies
pip install librosa soundfile matplotlib

# Beatport scraping dependencies
pip install beautifulsoup4 requests gspread google-auth lxml
```

---

## Examples

### Example 1: Chord Analysis

```python
from chord_analysis import ChordAnalyzer
import pandas as pd

# Load chord data
df = pd.read_csv("data/chords_with_bars.csv")

# Create analyzer for G minor key
analyzer = ChordAnalyzer(key="Gm", bpm=124)

# Analyze progressions
progressions = analyzer.analyze_progressions(df)
print(progressions)

# Detect cadences
cadences = analyzer.detect_cadences(df)
print(cadences)
```

### Example 2: Generate MIDI from Chords

```python
from csv_chord_processor import create_midi_with_chords
import pandas as pd

# Load chord data
df = pd.read_csv("data/chords_with_bars.csv")

# Create MIDI file
create_midi_with_chords(
    chords_data=df,
    output_midi_path="output/chords.mid",
    bpm=124,
    use_seventh_chords=False,
    base_octave=3
)
```

### Example 3: Analyze Ableton Project

```python
from ableton_analyzer import AbletonProjectReader

reader = AbletonProjectReader("project.als")
reader.load()

project_info = reader.get_project_info()
tracks = reader.get_tracks()

print(f"Tempo: {project_info['tempo']} BPM")
print(f"Tracks: {len(tracks)}")
```

### Example 4: Run Beatport Pipeline

```python
# Run full pipeline
from run_full_pipeline import main
main()

# Or run specific phases
# Phase 1: Seed artists
from seed_artists_from_labels import main as seed_artists
seed_artists()

# Phase 3: Classify B-level labels
from classify_b_labels import main as classify_labels
classify_labels()
```

---

## Output Files

### Chord Analysis Outputs
- `data/out/chords_with_bars.csv` - Bar-based chord notation
- `data/out/chords_piano_triads.mid` - MIDI file with piano chords
- `data/out/chord_analysis_summary.md` - Comprehensive analysis report

### Ableton Analysis Outputs
- `data/out/{project_name}_analysis.json` - Project structure and metadata

### MHT Pipeline Outputs
- Chord progression timeline (CSV)
- Audio analysis summary

### Beatport Miner Outputs
- `bp-miner/out/artists.csv` - Discovered artists
- `bp-miner/out/labels.csv` - Discovered labels (A & B level)
- `bp-miner/out/tracks.csv` - Discovered tracks
- `bp-miner/out/afterlife_b_label_top_and_latest_tracks.csv` - B-label Top 10 + Latest 10

---

## Notes & Best Practices

### Chord Analysis
- Default BPM is 124 (common for electronic music) - specify `--bpm` for other tempos
- Key detection is automatic but can be overridden with `--key` parameter
- MIDI files use piano triads by default; enable 7th chords with `--seventh` flag

### Audio Analysis
- Stem separation significantly improves chord detection accuracy
- BPM detection works best on tracks with clear rhythmic elements
- Key detection uses chroma analysis and works well on harmonic content

### Beatport Scraping
- Includes delays between requests to be respectful to Beatport
- All data is deduplicated before saving
- Google Sheets sync requires service account credentials
- Firecrawl MCP integration available for JS-rendered pages

---

## Troubleshooting

### Common Issues

**Import Errors:**
```bash
# Make sure dependencies are installed
pip install -r requirements.txt
```

**MIDI Generation Errors:**
- Check that chord notation is valid (e.g., "G:min", "D#:maj")
- Verify BPM is set correctly for time calculations

**Beatport Scraping Errors:**
- Check internet connection
- Verify Beatport URLs are still valid
- Check rate limiting (add longer delays if needed)

**Ableton File Errors:**
- Ensure `.als` file is not corrupted
- Check that file is a valid Ableton Live project

---

## Contributing

When adding new features:
- Follow existing code patterns
- Add docstrings to functions and classes
- Update this README with new features
- Test with sample data before committing

---

## License

[Your License Here]
