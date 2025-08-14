# Chord Processing Script

This script processes chord progression data from a CSV file and converts it to both bar-based notation and MIDI format.

## File Structure

```
analysis/
├── data/
│   ├── All_you_need_is_love_best_v4_2025-08-06T17_59_06.mp3-chord_csv.csv  # Input CSV
│   └── out/
│       ├── chords_with_bars.csv      # Output CSV with bar ranges
│       ├── chords_piano_triads.mid   # Output MIDI file
│       └── chord_analysis_summary.md # Analysis summary
├── csv_chord_processor.py           # CSV processing script
├── chord_analysis.py                 # Comprehensive analysis script
├── requirements.txt                  # Dependencies
└── README.md                        # Documentation
```

## Files Generated

1. **`data/out/chords_with_bars.csv`** - Original chord data converted to bar ranges
2. **`data/out/chords_piano_triads.mid`** - MIDI file with piano triads for each chord
3. **`data/out/chord_analysis_summary.md`** - Comprehensive analysis summary

## Analysis Results

- **Total chords**: 49
- **Total bars**: 151.3
- **Duration**: 292.8 seconds (at 124 BPM)
- **Key**: G minor (most common chord: G:min - 17 times)

## Chord Frequency

- G:min: 17 times
- D#:maj: 15 times  
- F:maj: 13 times
- C:maj: 3 times
- A#:maj: 1 time

## Common Chord Patterns

The progression shows a repeating pattern:
- G:min → F:maj → D#:maj → G:min

## Usage

```bash
# Activate the virtual environment
source ../menv312/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the CSV chord processor (generates CSV, MIDI, and summary)
python csv_chord_processor.py [input_filename.csv]

# Or run comprehensive analysis
python chord_analysis.py [input_filename]

# Examples:
python csv_chord_processor.py All_you_need_is_love_chords.csv
python chord_analysis.py All_you_need_is_love_chords
```

## MIDI File Details

The generated MIDI file contains:
- Piano triads for each chord
- 124 BPM tempo
- 4/4 time signature
- Each chord played for its corresponding duration

## Dependencies

- pandas: Data manipulation
- numpy: Numerical operations  
- midiutil: MIDI file generation

## Features

- **Chord Processing**: Converts time-based chord data to bar-based notation
- **MIDI Generation**: Creates piano triad MIDI files
- **Comprehensive Analysis**: 
  - Chord frequency analysis
  - Progression pattern identification
  - Cadence detection
  - Harmonic rhythm analysis
  - Tension and resolution analysis
  - Section structure analysis
- **Summary Generation**: Creates detailed markdown analysis reports
