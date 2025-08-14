import pandas as pd
import numpy as np
from midiutil import MIDIFile
import re
import sys
import os

def time_to_bars(time_seconds, bpm=124):
    """Convert time in seconds to bar numbers"""
    # 4 beats per bar (4/4 time signature)
    beats_per_bar = 4
    seconds_per_beat = 60 / bpm
    beats = time_seconds / seconds_per_beat
    bars = beats / beats_per_bar
    return bars

def bars_to_range(start_bar, end_bar):
    """Convert start and end bars to a range string like '1-8'"""
    start_bar_rounded = int(np.floor(start_bar)) + 1
    end_bar_rounded = int(np.ceil(end_bar))
    return f"{start_bar_rounded}-{end_bar_rounded}"

def parse_chord(chord_str):
    """Parse chord string and return root note and chord type"""
    # Handle different chord formats
    if ':' in chord_str:
        root, chord_type = chord_str.split(':')
    else:
        # Assume major if no type specified
        root = chord_str
        chord_type = 'maj'
    
    return root, chord_type

def get_chord_notes(root, chord_type):
    """Get the three notes for a chord triad"""
    # Define note names and their semitone offsets
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
    # Find root note index
    root_idx = notes.index(root)
    
    # Define intervals for different chord types
    if chord_type == 'maj':
        intervals = [0, 4, 7]  # Root, major third, perfect fifth
    elif chord_type == 'min':
        intervals = [0, 3, 7]  # Root, minor third, perfect fifth
    elif chord_type == 'dim':
        intervals = [0, 3, 6]  # Root, minor third, diminished fifth
    elif chord_type == 'aug':
        intervals = [0, 4, 8]  # Root, major third, augmented fifth
    else:
        # Default to major
        intervals = [0, 4, 7]
    
    # Calculate note indices
    chord_notes = []
    for interval in intervals:
        note_idx = (root_idx + interval) % 12
        chord_notes.append(notes[note_idx])
    
    return chord_notes

def create_midi_with_chords(chords_data, output_midi_path, bpm=124):
    """Create a MIDI file with piano triads"""
    # Create MIDI file
    midi = MIDIFile(1)  # 1 track
    track = 0
    time_pos = 0
    channel = 0
    volume = 100
    duration = 1  # 1 beat per chord
    
    # Set tempo
    midi.addTempo(track, time_pos, bpm)
    
    for _, row in chords_data.iterrows():
        chord = row['chord']
        start_bar = row['start_bar']
        end_bar = row['end_bar']
        
        # Parse chord
        root, chord_type = parse_chord(chord)
        chord_notes = get_chord_notes(root, chord_type)
        
        # Calculate duration in beats
        duration_beats = (end_bar - start_bar) * 4  # 4 beats per bar
        
        # Add notes to MIDI
        for note_name in chord_notes:
            # Convert note name to MIDI note number
            # C4 = 60, C#4 = 61, etc.
            note_number = 60 + ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'].index(note_name)
            
            # Add note (track, channel, note, time, duration, volume)
            midi.addNote(track, channel, note_number, time_pos, duration_beats, volume)
        
        time_pos += duration_beats
    
    # Write MIDI file
    with open(output_midi_path, 'wb') as output_file:
        midi.writeFile(output_file)

def main():
    # Get input file from command line argument or use default
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        # Ensure input file is in data directory
        if not input_file.startswith('data/'):
            input_file = f"data/{input_file}"
    else:
        input_file = "data/All_you_need_is_love_chords.csv"
    
    # Generate output file names based on input file name
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_csv = f"data/out/{base_name}_with_bars.csv"
    output_midi = f"data/out/{base_name}_piano_triads.mid"
    bpm = 124
    
    # Read the CSV file
    df = pd.read_csv(input_file)
    
    # Convert time to bars
    df['start_bar'] = df['start'].apply(lambda x: time_to_bars(x, bpm))
    df['end_bar'] = df['end'].apply(lambda x: time_to_bars(x, bpm))
    
    # Create bar range column
    df['bar_range'] = df.apply(lambda row: bars_to_range(row['start_bar'], row['end_bar']), axis=1)
    
    # Create new CSV with bar information
    output_df = df[['chord', 'bar_range', 'start_bar', 'end_bar']].copy()
    output_df.to_csv(output_csv, index=False)
    
    # Create MIDI file
    create_midi_with_chords(df, output_midi, bpm)
    
    # Generate analysis summary
    try:
        from chord_analysis import ChordAnalyzer
        analyzer = ChordAnalyzer(key="Bb")
        summary_content = analyzer.generate_summary_markdown(df)
        summary_file = f"data/out/{base_name}_analysis_summary.md"
        with open(summary_file, 'w') as f:
            f.write(summary_content)
        print(f"Created {summary_file} with analysis summary")
    except ImportError:
        print("Note: Run 'python chord_analysis.py' to create analysis summary")
    
    print(f"Processed {len(df)} chords")
    print(f"Created {output_csv} with bar ranges")
    print(f"Created {output_midi} with piano triads")
    print(f"BPM: {bpm}")
    
    # Display first few rows
    print("\nFirst few chords with bar ranges:")
    print(output_df.head(10))

if __name__ == "__main__":
    main()
