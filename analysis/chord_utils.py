"""
Utility functions for chord processing and analysis.
"""
import numpy as np

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
        # Try to detect chord type from the string
        chord_str = chord_str.strip()
        
        # Common chord type indicators
        if chord_str.endswith('m7'):
            root = chord_str[:-2]
            chord_type = 'min7'
        elif chord_str.endswith('7'):
            root = chord_str[:-1]
            chord_type = 'dom7'
        elif chord_str.endswith('maj7'):
            root = chord_str[:-4]
            chord_type = 'maj7'
        elif chord_str.endswith('dim7'):
            root = chord_str[:-4]
            chord_type = 'dim7'
        elif chord_str.endswith('half-dim7'):
            root = chord_str[:-9]
            chord_type = 'half-dim7'
        elif chord_str.endswith('m'):
            root = chord_str[:-1]
            chord_type = 'min'
        elif chord_str.endswith('dim'):
            root = chord_str[:-3]
            chord_type = 'dim'
        elif chord_str.endswith('aug'):
            root = chord_str[:-3]
            chord_type = 'aug'
        else:
            # Assume major if no type specified
            root = chord_str
            chord_type = 'maj'
    
    return root, chord_type

def get_chord_notes(root, chord_type, include_seventh=False):
    """Get the notes for a chord (triad or 7th chord)"""
    # Define note names and their semitone offsets
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
    # Find root note index
    root_idx = notes.index(root)
    
    # Define intervals for different chord types
    if chord_type == 'maj':
        intervals = [0, 4, 7]  # Root, major third, perfect fifth
        if include_seventh:
            intervals.append(11)  # Major seventh
    elif chord_type == 'min':
        intervals = [0, 3, 7]  # Root, minor third, perfect fifth
        if include_seventh:
            intervals.append(10)  # Minor seventh
    elif chord_type == 'dim':
        intervals = [0, 3, 6]  # Root, minor third, diminished fifth
        if include_seventh:
            intervals.append(9)  # Diminished seventh
    elif chord_type == 'aug':
        intervals = [0, 4, 8]  # Root, major third, augmented fifth
        if include_seventh:
            intervals.append(11)  # Major seventh
    elif chord_type == 'dom7' or chord_type == '7':
        intervals = [0, 4, 7, 10]  # Root, major third, perfect fifth, minor seventh
    elif chord_type == 'maj7':
        intervals = [0, 4, 7, 11]  # Root, major third, perfect fifth, major seventh
    elif chord_type == 'min7':
        intervals = [0, 3, 7, 10]  # Root, minor third, perfect fifth, minor seventh
    elif chord_type == 'dim7':
        intervals = [0, 3, 6, 9]  # Root, minor third, diminished fifth, diminished seventh
    elif chord_type == 'half_dim7':
        intervals = [0, 3, 6, 10]  # Root, minor third, diminished fifth, minor seventh
    elif chord_type == 'sus2':
        intervals = [0, 2, 7]  # Root, major second, perfect fifth
        if include_seventh:
            intervals.append(10)  # Minor seventh (common sus2+7)
    elif chord_type == 'sus4':
        intervals = [0, 5, 7]  # Root, perfect fourth, perfect fifth
        if include_seventh:
            intervals.append(10)  # Minor seventh (common sus4+7)
    elif chord_type == 'add9':
        intervals = [0, 4, 7, 14]  # Root, major third, perfect fifth, major ninth
    elif chord_type == 'madd9':
        intervals = [0, 3, 7, 14]  # Root, minor third, perfect fifth, major ninth
    else:
        # Default to major
        intervals = [0, 4, 7]
        if include_seventh:
            intervals.append(11)  # Major seventh
    
    # Calculate note indices
    chord_notes = []
    for interval in intervals:
        note_idx = (root_idx + interval) % 12
        chord_notes.append(notes[note_idx])
    
    return chord_notes

def should_use_seventh_chord(chord_type):
    """Determine if a chord type should automatically include 7ths"""
    # These chord types inherently include 7ths
    seventh_chord_types = ['dom7', '7', 'maj7', 'min7', 'dim7', 'half_dim7', 'half-dim7']
    return chord_type in seventh_chord_types

def get_chord_complexity(chord_type):
    """Get a human-readable description of chord complexity"""
    if chord_type in ['maj', 'min', 'dim', 'aug']:
        return "triad"
    elif chord_type in ['dom7', '7', 'maj7', 'min7', 'dim7', 'half_dim7', 'half-dim7']:
        return "7th chord"
    elif chord_type in ['sus2', 'sus4']:
        return "suspended chord"
    elif chord_type in ['add9', 'madd9']:
        return "extended chord"
    else:
        return "chord"

def build_inversion_notes(pcs, base_oct=3):
    """Build all possible inversions of a chord"""
    out = []
    ntones = len(pcs)
    for inv in range(ntones):
        order = pcs[inv:] + pcs[:inv]
        notes = []
        n = order[0] + 12 * base_oct
        while n % 12 != order[0]: 
            n += 1
        notes.append(n)
        last = n
        for pc in order[1:]:
            m = last
            while m % 12 != pc: 
                m += 1
            if m <= last: 
                m += 12
            notes.append(m)
            last = m
        out.append((inv, notes))
    return out

def choose_smooth_inversion(pcs, base_oct=3, prev_notes=None):
    """Choose the smoothest inversion based on previous chord"""
    candidates = build_inversion_notes(pcs, base_oct)
    if prev_notes is None:
        return candidates[0][1]  # Return root position if no previous chord
    
    # Find the inversion with the smallest total voice leading distance
    return min(candidates, key=lambda t: sum(abs(a-b) for a,b in zip(prev_notes, t[1])))[1]

def chord_notes_to_pitch_classes(chord_notes):
    """Convert note names to pitch class numbers (0-11)"""
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    pcs = []
    for note_name in chord_notes:
        pc = notes.index(note_name)
        pcs.append(pc)
    return pcs

def get_smooth_voicing(root, chord_type, include_seventh=False, base_oct=3, prev_notes=None):
    """Get a smooth voicing for a chord considering previous chord"""
    # Get the chord notes
    chord_notes = get_chord_notes(root, chord_type, include_seventh)
    
    # Convert to pitch classes
    pcs = chord_notes_to_pitch_classes(chord_notes)
    
    # Choose the smoothest inversion
    smooth_notes = choose_smooth_inversion(pcs, base_oct, prev_notes)
    
    return smooth_notes

def detect_key_from_chords(chord_roots, chord_types):
    """Detect the most likely key from the most common chord root and chord qualities"""
    if not chord_roots:
        return "C"  # Default fallback
    
    # Find the most common root
    most_common_root = max(chord_roots, key=chord_roots.get)
    
    # Analyze chord qualities to determine if we should assume major or minor
    # Count major vs minor chords for this root
    major_count = 0
    minor_count = 0
    
    # Look through all chords to see the quality of the most common root
    for chord_type in chord_types:
        if chord_type in ['maj', 'maj7', 'aug']:
            major_count += chord_types[chord_type]
        elif chord_type in ['min', 'min7', 'dim', 'dim7', 'half_dim7']:
            minor_count += chord_types[chord_type]
    
    # If we have more minor chords, assume minor key
    # If we have more major chords, assume major key
    # If equal or unclear, default to minor (more common in pop/rock)
    if minor_count > major_count:
        return most_common_root + "m"
    else:
        return most_common_root  # Major key (no suffix)

def normalize_key_input(key_input):
    """Normalize key input to standard format"""
    if not key_input:
        return None
    
    key_input = key_input.strip()
    
    # Handle common variations
    if key_input.lower().endswith('min'):
        # Convert "Gmin", "Gmin", "G minor" to "Gm"
        root = key_input[:-3] if key_input.lower().endswith('min') else key_input.split()[0]
        return root + "m"
    elif key_input.lower().endswith('minor'):
        # Convert "G minor" to "Gm"
        root = key_input.split()[0]
        return root + "m"
    elif key_input.lower().endswith('maj'):
        # Convert "Gmaj", "G major" to "G"
        root = key_input[:-3] if key_input.lower().endswith('maj') else key_input.split()[0]
        return root
    elif key_input.lower().endswith('major'):
        # Convert "G major" to "G"
        root = key_input.split()[0]
        return root
    elif key_input.endswith('m'):
        # Already in correct format
        return key_input
    else:
        # Assume major key if no suffix
        return key_input
