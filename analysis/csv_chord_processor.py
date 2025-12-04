"""
This script processes a CSV file containing chord progressions and creates a MIDI file with piano triads.
It also generates an analysis summary of the chord progressions.
"""
import pandas as pd
import numpy as np
from midiutil import MIDIFile
import re
import sys
import os
from chord_utils import (
    time_to_bars, bars_to_range, parse_chord, get_chord_notes, 
    should_use_seventh_chord, get_chord_complexity, get_smooth_voicing,
    detect_key_from_chords, normalize_key_input
)

def create_midi_with_chords(chords_data, output_midi_path, bpm=124, use_seventh_chords=False, base_octave=3):
    """Create a MIDI file with piano chords (triads or 7th chords) using smooth voicings"""
    # Create MIDI file
    midi = MIDIFile(1)  # 1 track
    track = 0
    time_pos = 0
    channel = 0
    volume = 100
    duration = 1  # 1 beat per chord
    
    # Set tempo
    midi.addTempo(track, time_pos, bpm)
    
    prev_notes = None  # Track previous chord for smooth transitions
    
    for _, row in chords_data.iterrows():
        chord = row['chord']
        start_bar = row['start_bar']
        end_bar = row['end_bar']
        
        # Parse chord
        root, chord_type = parse_chord(chord)
        
        # Auto-detect if this chord should include 7ths
        auto_seventh = should_use_seventh_chord(chord_type)
        # Use 7ths if explicitly requested OR if the chord type inherently includes 7ths
        final_use_seventh = use_seventh_chords or auto_seventh
        
        # Get smooth voicing considering previous chord
        chord_notes = get_smooth_voicing(root, chord_type, final_use_seventh, base_octave, prev_notes)
        
        # Calculate duration in beats
        duration_beats = (end_bar - start_bar) * 4  # 4 beats per bar
        
        # Add notes to MIDI
        for note_number in chord_notes:
            # Add note (track, channel, note, time, duration, volume)
            midi.addNote(track, channel, note_number, time_pos, duration_beats, volume)
        
        # Store current chord notes for next iteration
        prev_notes = chord_notes
        time_pos += duration_beats
    
    # Write MIDI file
    with open(output_midi_path, 'wb') as output_file:
        midi.writeFile(output_file)

def analyze_chord_types(chords_data):
    """Analyze the types of chords in the data"""
    chord_types = {}
    chord_roots = {}
    seventh_chords = 0
    triad_chords = 0
    
    for _, row in chords_data.iterrows():
        chord = row['chord']
        root, chord_type = parse_chord(chord)
        
        # Count chord types
        if chord_type not in chord_types:
            chord_types[chord_type] = 0
        chord_types[chord_type] += 1
        
        # Count chord roots
        if root not in chord_roots:
            chord_roots[root] = 0
        chord_roots[root] += 1
        
        # Count 7th vs triad chords
        if should_use_seventh_chord(chord_type):
            seventh_chords += 1
        else:
            triad_chords += 1
    
    return chord_types, chord_roots, seventh_chords, triad_chords



def main():
    # Show help if requested
    if '--help' in sys.argv or '-h' in sys.argv:
        print("CSV Chord Processor - Creates MIDI files from chord progressions")
        print("\nUsage:")
        print("  python csv_chord_processor.py [input.csv] [options]")
        print("\nOptions:")
        print("  --seventh, -7     Force all chords to include 7ths")
        print("  --octave=N        Set base octave for chord voicings (default: 3)")
        print("  --bpm=N           Set BPM for timing (default: 124)")
        print("  --key=KEY         Specify musical key (e.g., Gm, C, F#m, Gmin, Gmaj, G major)")
        print("  --help, -h        Show this help message")
        print("\nExamples:")
        print("  python csv_chord_processor.py input.csv")
        print("  python csv_chord_processor.py input.csv --seventh")
        print("  python csv_chord_processor.py input.csv --seventh --octave=4")
        print("  python csv_chord_processor.py input.csv -7 --octave=2")
        print("  python csv_chord_processor.py input.csv --bpm=128 --key=Am")
        print("  python csv_chord_processor.py input.csv --key=G --bpm=140")
        print("  python csv_chord_processor.py input.csv --key=Gmaj --bpm=120")
        print("  python csv_chord_processor.py input.csv --key='G minor' --bpm=130")
        print("\nKey Detection:")
        print("  - If no key is specified, automatically detects key from most common chord")
        print("  - Specify key manually with --key for more accurate analysis")
        print("  - Key formats supported: G, Gm, Gmin, Gmin, Gmaj, G major, G minor")
        print("\nFile paths:")
        print("  - Use relative paths from current directory")
        print("  - Script will search in data/ and analysis/data/ directories")
        print("  - Output files go to corresponding out/ subdirectory")
        return
    
    # Get input file from command line argument or use default
    if len(sys.argv) > 1 and not sys.argv[1].startswith('--'):
        input_file = sys.argv[1]
        # Handle different path scenarios
        if not os.path.exists(input_file):
            # Try relative to current working directory
            if not input_file.startswith('data/') and not input_file.startswith('analysis/data/'):
                # Try both possible data directory locations
                possible_paths = [
                    f"data/{input_file}",
                    f"analysis/data/{input_file}",
                    input_file
                ]
                for path in possible_paths:
                    if os.path.exists(path):
                        input_file = path
                        break
                else:
                    print(f"Error: Could not find file '{input_file}' in any of these locations:")
                    print(f"  - {input_file}")
                    print(f"  - data/{input_file}")
                    print(f"  - analysis/data/{input_file}")
                    print(f"Current working directory: {os.getcwd()}")
                    return
    else:
        # Try to find the default file in different locations
        default_paths = [
            "data/All_you_need_is_love_chords.csv",
            "analysis/data/All_you_need_is_love_chords.csv"
        ]
        for path in default_paths:
            if os.path.exists(path):
                input_file = path
                break
        else:
            print("Error: Could not find default file 'All_you_need_is_love_chords.csv'")
            print("Please specify a file path or ensure the default file exists in:")
            print("  - data/All_you_need_is_love_chords.csv")
            print("  - analysis/data/All_you_need_is_love_chords.csv")
            print(f"Current working directory: {os.getcwd()}")
            return
    
    # Check for 7th chord option
    use_seventh_chords = '--seventh' in sys.argv or '-7' in sys.argv
    
    # Check for base octave option
    base_octave = 3  # Default octave
    for i, arg in enumerate(sys.argv):
        if arg == '--octave' and i + 1 < len(sys.argv):
            try:
                base_octave = int(sys.argv[i + 1])
            except ValueError:
                print(f"Warning: Invalid octave value '{sys.argv[i + 1]}', using default {base_octave}")
        elif arg.startswith('--octave='):
            try:
                base_octave = int(arg.split('=')[1])
            except ValueError:
                print(f"Warning: Invalid octave value in '{arg}', using default {base_octave}")
    
    # Check for BPM option
    bpm = 124  # Default BPM
    for i, arg in enumerate(sys.argv):
        if arg == '--bpm' and i + 1 < len(sys.argv):
            try:
                bpm = int(sys.argv[i + 1])
            except ValueError:
                print(f"Warning: Invalid BPM value '{sys.argv[i + 1]}', using default {bpm}")
        elif arg.startswith('--bpm='):
            try:
                bpm = int(arg.split('=')[1])
            except ValueError:
                print(f"Warning: Invalid BPM value in '{arg}', using default {bpm}")
    
    # Check for key option
    specified_key = None
    for i, arg in enumerate(sys.argv):
        if arg == '--key' and i + 1 < len(sys.argv):
            specified_key = normalize_key_input(sys.argv[i + 1])
        elif arg.startswith('--key='):
            specified_key = normalize_key_input(arg.split('=')[1])
    
    # Generate output file names based on input file name
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    
    # Determine output directory based on input file location
    if input_file.startswith('analysis/data/'):
        output_dir = "analysis/data/out"
    else:
        output_dir = "data/out"
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    output_csv = f"{output_dir}/{base_name}_with_bars.csv"
    chord_type = "seventh_chords" if use_seventh_chords else "piano_triads"
    output_midi = f"{output_dir}/{base_name}_{chord_type}.mid"
    
    # Read the CSV file
    df = pd.read_csv(input_file)
    
    # Analyze chord types
    chord_types, chord_roots, seventh_chords, triad_chords = analyze_chord_types(df)
    
    # Detect or use specified key
    if specified_key:
        detected_key = specified_key
        print(f"Using specified key: {detected_key}")
    else:
        detected_key = detect_key_from_chords(chord_roots, chord_types)
        print(f"Auto-detected key: {detected_key}")
    
    # Convert time to bars
    df['start_bar'] = df['start'].apply(lambda x: time_to_bars(x, bpm))
    df['end_bar'] = df['end'].apply(lambda x: time_to_bars(x, bpm))
    
    # Create bar range column
    df['bar_range'] = df.apply(lambda row: bars_to_range(row['start_bar'], row['end_bar']), axis=1)
    
    # Create new CSV with bar information
    output_df = df[['chord', 'bar_range', 'start_bar', 'end_bar']].copy()
    output_df.to_csv(output_csv, index=False)
    
    # Create MIDI file
    create_midi_with_chords(df, output_midi, bpm, use_seventh_chords, base_octave)
    
    # Generate analysis summary
    try:
        from chord_analysis import ChordAnalyzer
        analyzer = ChordAnalyzer(key=detected_key, bpm=bpm)
        summary_content = analyzer.generate_summary_markdown(df)
        summary_file = f"{output_dir}/{base_name}_analysis_summary.md"
        with open(summary_file, 'w') as f:
            f.write(summary_content)
        print(f"Created {summary_file} with analysis summary")
    except ImportError:
        print("Note: Run 'python chord_analysis.py' to create analysis summary")
    
    print(f"Processed {len(df)} chords")
    print(f"Created {output_csv} with bar ranges")
    chord_description = "7th chords" if use_seventh_chords else "piano triads"
    print(f"Created {output_midi} with {chord_description}")
    print(f"BPM: {bpm}")
    print(f"Base octave: {base_octave}")
    print(f"Key: {detected_key}")
    
    # Display chord analysis
    print(f"\nChord Analysis:")
    print(f"  Total chords: {len(df)}")
    print(f"  Triad chords: {triad_chords}")
    print(f"  Seventh chords: {seventh_chords}")
    print(f"  Chord types found: {', '.join(sorted(chord_types.keys()))}")
    print(f"  Most common chord root: {max(chord_roots, key=chord_roots.get) if chord_roots else 'None'}")
    print(f"  Using smooth voicings for transitions")
    
    # Display first few rows
    print("\nFirst few chords with bar ranges:")
    print(output_df.head(10))

if __name__ == "__main__":
    main()
