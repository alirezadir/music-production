import pandas as pd
import numpy as np
from collections import Counter, defaultdict
import os
import sys

class ChordAnalyzer:
    def __init__(self, key="Bb", bpm=124):
        self.key = key
        self.bpm = bpm
        self.key_mode = self.detect_key_mode()
        self.setup_key_analysis()
    
    def detect_key_mode(self):
        """Detect if the key is major or minor"""
        if self.key.endswith('m'):
            return 'minor'
        else:
            return 'major'
    
    def get_key_signature(self):
        """Get the key signature for the current key"""
        # Basic key signature mapping
        key_signatures = {
            'C': '0 sharps/flats',
            'G': '1 sharp (F#)',
            'D': '2 sharps (F#, C#)',
            'A': '3 sharps (F#, C#, G#)',
            'E': '4 sharps (F#, C#, G#, D#)',
            'B': '5 sharps (F#, C#, G#, D#, A#)',
            'F#': '6 sharps (F#, C#, G#, D#, A#, E#)',
            'F': '1 flat (Bb)',
            'Bb': '2 flats (Bb, Eb)',
            'Eb': '3 flats (Bb, Eb, Ab)',
            'Ab': '4 flats (Bb, Eb, Ab, Db)',
            'Db': '5 flats (Bb, Eb, Ab, Db, Gb)',
            'Gb': '6 flats (Bb, Eb, Ab, Db, Gb, Cb)',
            # Minor keys
            'Am': '0 sharps/flats',
            'Em': '1 sharp (F#)',
            'Bm': '2 sharps (F#, C#)',
            'F#m': '3 sharps (F#, C#, G#)',
            'C#m': '4 sharps (F#, C#, G#, D#)',
            'G#m': '5 sharps (F#, C#, G#, D#, A#)',
            'D#m': '6 sharps (F#, C#, G#, D#, A#, E#)',
            'Dm': '1 flat (Bb)',
            'Gm': '2 flats (Bb, Eb)',
            'Cm': '3 flats (Bb, Eb, Ab)',
            'Fm': '4 flats (Bb, Eb, Ab, Db)',
            'Bbm': '5 flats (Bb, Eb, Ab, Db, Gb)',
            'Ebm': '6 flats (Bb, Eb, Ab, Db, Gb, Cb)'
        }
        
        return key_signatures.get(self.key, 'Unknown key signature')
        
    def setup_key_analysis(self):
        """Setup key-specific analysis parameters"""
        if self.key == "Bb":
            # Bb major scale: Bb, C, D, Eb, F, G, A
            self.scale_degrees = {
                'Bb': 'I', 'C': 'ii', 'D': 'iii', 'Eb': 'IV', 
                'F': 'V', 'G': 'vi', 'A': 'vii°'
            }
            self.chord_functions = {
                'I': 'Tonic', 'IV': 'Subdominant', 'V': 'Dominant',
                'ii': 'Supertonic', 'iii': 'Mediant', 'vi': 'Submediant', 'vii°': 'Leading Tone'
            }
            self.common_progressions = {
                'I-IV-V': 'Basic progression',
                'I-vi-IV-V': 'Pop progression',
                'vi-IV-V': 'Minor pop progression',
                'I-V-vi-IV': 'Pop progression variant',
                'ii-V-I': 'Jazz progression'
            }
    
    def chord_to_degree(self, chord_str):
        """Convert chord to roman numeral degree"""
        if ':' in chord_str:
            root, chord_type = chord_str.split(':')
        else:
            root = chord_str
            chord_type = 'maj'
        
        # Handle enharmonic equivalents
        enharmonic_map = {'D#': 'Eb', 'A#': 'Bb'}
        if root in enharmonic_map:
            root = enharmonic_map[root]
        
        # For Bb major key
        if chord_type == 'maj':
            if root == 'Bb': return 'I'
            elif root == 'Eb': return 'IV'
            elif root == 'F': return 'V'
            elif root == 'C': return 'ii'
            elif root == 'D': return 'iii'
            elif root == 'G': return 'vi'
            elif root == 'A': return 'vii°'
        elif chord_type == 'min':
            if root == 'G': return 'vi'
            elif root == 'C': return 'ii'
            elif root == 'D': return 'iii'
            elif root == 'A': return 'vii°'
        
        return f"{root}:{chord_type}"
    
    def analyze_progressions(self, df):
        """Analyze chord progressions and find common patterns"""
        progressions = []
        for i in range(len(df) - 1):
            current_chord = df.iloc[i]['chord']
            next_chord = df.iloc[i+1]['chord']
            
            current_degree = self.chord_to_degree(current_chord)
            next_degree = self.chord_to_degree(next_chord)
            
            progression = f"{current_degree} → {next_degree}"
            progressions.append(progression)
        
        return progressions
    
    def find_progression_patterns(self, df):
        """Find repeating progression patterns"""
        progressions = []
        for i in range(len(df) - 2):  # Look for 3-chord patterns
            pattern = []
            for j in range(3):
                if i + j < len(df):
                    chord = df.iloc[i + j]['chord']
                    degree = self.chord_to_degree(chord)
                    pattern.append(degree)
            if len(pattern) == 3:
                progressions.append(' → '.join(pattern))
        
        return Counter(progressions)
    
    def analyze_cadences(self, df):
        """Identify cadences in the progression"""
        cadences = []
        for i in range(len(df) - 1):
            current_chord = df.iloc[i]['chord']
            next_chord = df.iloc[i+1]['chord']
            
            current_degree = self.chord_to_degree(current_chord)
            next_degree = self.chord_to_degree(next_chord)
            
            # Identify common cadences
            if current_degree == 'V' and next_degree == 'I':
                cadences.append(f"Perfect Cadence: {current_degree} → {next_degree}")
            elif current_degree == 'IV' and next_degree == 'I':
                cadences.append(f"Plagal Cadence: {current_degree} → {next_degree}")
            elif current_degree == 'V' and next_degree == 'vi':
                cadences.append(f"Deceptive Cadence: {current_degree} → {next_degree}")
            elif current_degree == 'I' and next_degree == 'V':
                cadences.append(f"Half Cadence: {current_degree} → {next_degree}")
        
        return cadences
    
    def analyze_harmonic_rhythm(self, df):
        """Analyze the harmonic rhythm (chord change frequency)"""
        chord_durations = df['end_bar'] - df['start_bar']
        
        rhythm_analysis = {
            'avg_duration': chord_durations.mean(),
            'min_duration': chord_durations.min(),
            'max_duration': chord_durations.max(),
            'fast_changes': len(chord_durations[chord_durations < 2]),
            'slow_changes': len(chord_durations[chord_durations > 4]),
            'medium_changes': len(chord_durations[(chord_durations >= 2) & (chord_durations <= 4)])
        }
        
        return rhythm_analysis
    
    def analyze_tension_and_resolution(self, df):
        """Analyze tension and resolution patterns"""
        tension_analysis = []
        
        for i in range(len(df) - 1):
            current_chord = df.iloc[i]['chord']
            next_chord = df.iloc[i+1]['chord']
            
            current_degree = self.chord_to_degree(current_chord)
            next_degree = self.chord_to_degree(next_chord)
            
            # Analyze tension
            if current_degree == 'V' and next_degree == 'I':
                tension_analysis.append("Strong resolution (V→I)")
            elif current_degree == 'V' and next_degree == 'vi':
                tension_analysis.append("Deceptive resolution (V→vi)")
            elif current_degree == 'IV' and next_degree == 'I':
                tension_analysis.append("Plagal resolution (IV→I)")
            elif current_degree == 'I' and next_degree == 'V':
                tension_analysis.append("Building tension (I→V)")
            elif current_degree == 'V' and next_degree == 'IV':
                tension_analysis.append("Retrograde motion (V→IV)")
            else:
                tension_analysis.append(f"Standard progression ({current_degree}→{next_degree})")
        
        return tension_analysis
    
    def analyze_chord_functions(self, df):
        """Analyze chord functions in the key"""
        chord_functions = defaultdict(list)
        
        for _, row in df.iterrows():
            chord = row['chord']
            degree = self.chord_to_degree(chord)
            
            # Categorize by function
            if degree in ['I', 'IV', 'V']:
                chord_functions['Primary Chords'].append(f"{chord} ({degree})")
            elif degree in ['ii', 'iii', 'vi']:
                chord_functions['Secondary Chords'].append(f"{chord} ({degree})")
            elif degree == 'vii°':
                chord_functions['Leading Tone'].append(f"{chord} ({degree})")
            else:
                chord_functions['Other'].append(f"{chord} ({degree})")
        
        return chord_functions
    
    def analyze_section_structure(self, df):
        """Analyze the song's section structure based on chord patterns"""
        sections = []
        current_section = []
        
        for i, row in df.iterrows():
            chord = row['chord']
            duration = row['end_bar'] - row['start_bar']
            degree = self.chord_to_degree(chord)
            
            # Identify section boundaries
            if duration > 6:  # Long chord might indicate section change
                if current_section:
                    sections.append(current_section)
                current_section = [{'chord': chord, 'degree': degree, 'bars': row['bar_range']}]
            else:
                current_section.append({'chord': chord, 'degree': degree, 'bars': row['bar_range']})
        
        if current_section:
            sections.append(current_section)
        
        return sections
    
    def generate_summary_markdown(self, df):
        """Generate comprehensive markdown summary"""
        
        # Basic statistics
        total_bars = df['end_bar'].max()
        total_chords = len(df)
        avg_duration = (df['end_bar'] - df['start_bar']).mean()
        
        # Chord frequency analysis
        chord_counts = Counter(df['chord'])
        chord_frequency = []
        for chord, count in chord_counts.most_common():
            degree = self.chord_to_degree(chord)
            percentage = (count / total_chords) * 100
            chord_frequency.append(f"{chord} ({degree}) - {count} times ({percentage:.1f}%)")
        
        # Progression analysis
        progressions = self.analyze_progressions(df)
        progression_counts = Counter(progressions)
        most_common_progressions = []
        for progression, count in progression_counts.most_common(5):
            most_common_progressions.append(f"{progression}: {count} times")
        
        # Cadence analysis
        cadences = self.analyze_cadences(df)
        
        # Harmonic rhythm analysis
        rhythm = self.analyze_harmonic_rhythm(df)
        
        # Long chords (section markers)
        long_chords = df[df['end_bar'] - df['start_bar'] > rhythm['avg_duration'] * 2]
        section_markers = []
        for _, row in long_chords.iterrows():
            duration = row['end_bar'] - row['start_bar']
            degree = self.chord_to_degree(row['chord'])
            section_markers.append(f"{row['chord']} ({degree}) at bars {row['bar_range']} (duration: {duration:.1f} bars)")
        
        # Generate markdown content
        markdown_content = f"""# Chord Progression Analysis Summary

## Song Information
- **Key**: {self.key} {self.key_mode.title()}
- **BPM**: {self.bpm}
- **Total Duration**: {total_bars:.1f} bars ({(total_bars * 4 / self.bpm * 60):.1f} seconds at {self.bpm} BPM)
- **Total Chords**: {total_chords} chords
- **Average Chord Duration**: {avg_duration:.1f} bars

## Chord Frequency Analysis

### Most Common Chords (in {self.key} Major)
"""
        
        for i, chord_info in enumerate(chord_frequency, 1):
            markdown_content += f"{i}. **{chord_info}**\n"
        
        markdown_content += f"""
### Chord Function Distribution (in {self.key} {self.key_mode.title()})
- **Primary Chords** (I, IV, V): {sum(1 for chord in df['chord'] if self.chord_to_degree(chord) in ['I', 'IV', 'V'])} chords
- **Secondary Chords** (ii, iii, vi): {sum(1 for chord in df['chord'] if self.chord_to_degree(chord) in ['ii', 'iii', 'vi'])} chords

## Progression Analysis

### Most Common 2-Chord Progressions
"""
        
        for i, progression in enumerate(most_common_progressions, 1):
            markdown_content += f"{i}. **{progression}**\n"
        
        markdown_content += f"""
## Harmonic Rhythm Analysis

### Chord Duration Distribution
- **Fast changes** (< 2 bars): {rhythm['fast_changes']} chords
- **Medium changes** (2-4 bars): {rhythm['medium_changes']} chords
- **Slow changes** (> 4 bars): {rhythm['slow_changes']} chords

### Long Chords (Section Markers)
"""
        
        for marker in section_markers:
            markdown_content += f"- **{marker}**\n"
        
        markdown_content += f"""
## Tension and Resolution Analysis

### Cadences Identified
"""
        
        if cadences:
            for cadence in cadences:
                markdown_content += f"- **{cadence}**\n"
        else:
            markdown_content += "- No traditional cadences identified\n"
        
        markdown_content += f"""
## Musical Characteristics

### Key Insights
1. **Most Common Chord**: {chord_counts.most_common(1)[0][0]} ({self.chord_to_degree(chord_counts.most_common(1)[0][0])}) - {chord_counts.most_common(1)[0][1]} times
2. **Most Common Progression**: {progression_counts.most_common(1)[0][0]} - {progression_counts.most_common(1)[0][1]} times
3. **Harmonic Rhythm**: {'Fast' if rhythm['avg_duration'] < 2 else 'Moderate' if rhythm['avg_duration'] < 4 else 'Slow'} ({rhythm['avg_duration']:.1f} bars average)
4. **Total Cadences**: {len(cadences)}

### Musical Style Indicators
- **Key**: {self.key} {self.key_mode.title()}
- **Character**: Modern pop/rock with emphasis on {'minor' if 'vi' in [self.chord_to_degree(chord) for chord in chord_counts.keys()] else 'major'} chords
- **Harmonic Rhythm**: {'Fast' if rhythm['avg_duration'] < 2 else 'Moderate' if rhythm['avg_duration'] < 4 else 'Slow'}
- **Sectional Structure**: {'Clear' if len(section_markers) > 0 else 'Unclear'} section markers

## Technical Notes
- **BPM**: {self.bpm}
- **Time Signature**: 4/4 (assumed)
- **Key**: {self.key} {self.key_mode.title()}
- **Key Signature**: {self.get_key_signature()}
- **Enharmonic Equivalents**: D# = E♭, A# = B♭

This analysis reveals a modern progression in {self.key} {self.key_mode.title()} with {'strong emphasis on minor chords' if 'vi' in [self.chord_to_degree(chord) for chord in chord_counts.keys()] else 'balanced chord usage'}, creating a {'melancholic' if 'vi' in [self.chord_to_degree(chord) for chord in chord_counts.keys()] else 'bright'} character typical of contemporary popular music.
"""
        
        return markdown_content

def show_file_structure():
    """Display the current file structure and file information"""
    
    print("=== CURRENT FILE STRUCTURE ===")
    print()
    
    # Show main directory
    print("analysis/")
    
    # Show data directory
    print("├── data/")
    
    # List input files
    if os.path.exists("data"):
        input_files = [f for f in os.listdir("data") if f.endswith('.csv') and not f.startswith('.')]
        for file in input_files:
            print(f"│   ├── {file}")
    
    print("│   └── out/")
    
    # List output files
    if os.path.exists("data/out"):
        output_files = [f for f in os.listdir("data/out") if not f.startswith('.')]
        for file in output_files:
            print(f"│       ├── {file}")
    
    print()
    
    # Show script files
    print("├── csv_chord_processor.py")
    print("├── chord_analysis.py")
    print("├── requirements.txt")
    print("└── README.md")
    print()
    
    # Show file information
    print("=== FILE INFORMATION ===")
    
    # Check input files
    if os.path.exists("data"):
        input_files = [f for f in os.listdir("data") if f.endswith('.csv') and not f.startswith('.')]
        for input_file in input_files:
            file_path = f"data/{input_file}"
            if os.path.exists(file_path):
                df_input = pd.read_csv(file_path)
                print(f"Input CSV {input_file}: {len(df_input)} chords")
    
    # Check output files
    if os.path.exists("data/out"):
        output_files = [f for f in os.listdir("data/out") if not f.startswith('.')]
        for output_file in output_files:
            file_path = f"data/out/{output_file}"
            if os.path.exists(file_path):
                if output_file.endswith('.csv'):
                    df_output = pd.read_csv(file_path)
                    print(f"Output CSV {output_file}: {len(df_output)} chords")
                elif output_file.endswith('.mid'):
                    size = os.path.getsize(file_path)
                    print(f"Output MIDI {output_file}: {size} bytes")
                elif output_file.endswith('.md'):
                    size = os.path.getsize(file_path)
                    print(f"Output Summary {output_file}: {size} bytes")
    
    print()
    print("=== WORKFLOW ===")
    print("1. Input CSV → csv_chord_processor.py [filename] → Output CSV + MIDI + Summary")
    print("2. Output CSV → chord_analysis.py [filename] → Comprehensive analysis")
    print()
    print("=== USAGE EXAMPLES ===")
print("python csv_chord_processor.py All_you_need_is_love_chords.csv")
print("python chord_analysis.py All_you_need_is_love_chords")

def main():
    """Main analysis function"""
    # Get input file from command line argument or use default
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        # If it's a CSV file, assume it's the processed file
        if input_file.endswith('.csv'):
            if not input_file.startswith('data/out/'):
                input_file = f"data/out/{input_file}"
        else:
            # If it's not a CSV, assume it's the base name and look for processed file
            base_name = input_file
            input_file = f"data/out/{base_name}_with_bars.csv"
    else:
        input_file = "data/out/All_you_need_is_love_chords_with_bars.csv"
    
    # Load the chord data
    df = pd.read_csv(input_file)
    
    # Initialize analyzer
    analyzer = ChordAnalyzer(key="Bb")
    
    print("=== COMPREHENSIVE CHORD ANALYSIS ===")
    print(f"Key: {analyzer.key} major")
    print()
    
    # Basic statistics
    total_bars = df['end_bar'].max()
    total_chords = len(df)
    print(f"Total chords: {total_chords}")
    print(f"Total bars: {total_bars:.1f}")
    print(f"Duration: {total_bars * 4 / 124 * 60:.1f} seconds")
    print()
    
    # Analyze chord frequencies
    chord_counts = Counter(df['chord'])
    print("=== CHORD FREQUENCY ===")
    for chord, count in chord_counts.most_common():
        degree = analyzer.chord_to_degree(chord)
        print(f"  {chord} ({degree}): {count} times")
    print()
    
    # Analyze progressions
    progressions = analyzer.analyze_progressions(df)
    progression_counts = Counter(progressions)
    
    print("=== MOST COMMON PROGRESSIONS ===")
    for progression, count in progression_counts.most_common(10):
        print(f"  {progression}: {count} times")
    print()
    
    # Analyze cadences
    cadences = analyzer.analyze_cadences(df)
    if cadences:
        print("=== CADENCES IDENTIFIED ===")
        for cadence in cadences:
            print(f"  {cadence}")
        print()
    
    # Analyze harmonic rhythm
    rhythm = analyzer.analyze_harmonic_rhythm(df)
    print("=== HARMONIC RHYTHM ===")
    print(f"  Average chord duration: {rhythm['avg_duration']:.2f} bars")
    print(f"  Fast changes (< 2 bars): {rhythm['fast_changes']}")
    print(f"  Medium changes (2-4 bars): {rhythm['medium_changes']}")
    print(f"  Slow changes (> 4 bars): {rhythm['slow_changes']}")
    print()
    
    # Analyze tension and resolution
    tension = analyzer.analyze_tension_and_resolution(df)
    tension_counts = Counter(tension)
    print("=== TENSION AND RESOLUTION ===")
    for tension_type, count in tension_counts.most_common():
        print(f"  {tension_type}: {count} times")
    print()
    
    # Generate summary
    summary_content = analyzer.generate_summary_markdown(df)
    # Extract base name from input file
    base_name = os.path.splitext(os.path.basename(input_file))[0].replace('_with_bars', '')
    summary_file = f"data/out/{base_name}_analysis_summary.md"
    with open(summary_file, 'w') as f:
        f.write(summary_content)
    
    print(f"Generated comprehensive analysis summary: {summary_file}")
    
    # Show structure
    show_file_structure()

if __name__ == "__main__":
    main()
