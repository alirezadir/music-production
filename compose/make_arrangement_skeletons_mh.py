import sys
import argparse
from typing import List, Dict, Tuple
import mido
from mido import MidiFile, MidiTrack, Message
from json_metadata import create_midi_metadata
import os
import json

# Map roman numeral to scale degree (1-based)
ROMAN_DEGREE_MAP = {
    "I": 1, "i": 1,
    "II": 2, "ii": 2,
    "III": 3, "iii": 3,
    "IV": 4, "iv": 4,
    "V": 5, "v": 5,
    "VI": 6, "vi": 6,
    "VII": 7, "vii": 7,
    "ii°": 2, "vii°": 7,
}

def degree_quality(mode: str, degree: int, use_7ths: bool) -> str:
    # Returns chord quality string based on mode and degree
    # Simplified for demo purposes
    if mode == "ionian":
        qualities = ["maj", "min", "min", "maj", "dom7" if use_7ths else "maj", "min", "dim"]
    elif mode == "aeolian":
        qualities = ["min", "dim", "maj", "min", "min", "maj", "maj"]
    elif mode == "dorian":
        qualities = ["min", "min", "maj", "maj", "maj", "min", "dim"]
    else:
        qualities = ["maj"] * 7
    idx = (degree - 1) % 7
    return qualities[idx]

def build_chord_pcs(tonic_pc: int, mode: str, roman: str, use_7ths: bool, add9: bool):
    # Determine scale degree
    deg = ROMAN_DEGREE_MAP.get(roman, 1)
    # Borrowed dominant: if user wrote uppercase V in modal contexts
    if roman == "V":
        qual = "dom7" if use_7ths else "maj"
    else:
        qual = degree_quality(mode, deg, use_7ths)
    # For simplicity, return dummy pitch classes list
    # Real implementation would build chord tones based on tonic_pc, mode, degree, and quality
    pcs = [tonic_pc, (tonic_pc + 4) % 12, (tonic_pc + 7) % 12]
    if use_7ths and qual == "dom7":
        pcs.append((tonic_pc + 10) % 12)
    if add9:
        pcs.append((tonic_pc + 14) % 12)
    return pcs

def substitute_if_weak(mode: str, roman: str) -> str:
    # Substitutions for weak chords in modes (e.g., ii° -> iv in Aeolian)
    if mode == "aeolian":
        if roman == "ii°":
            return "iv"
    return roman

# Ensure displayed Roman matches any internal substitution (e.g., ii° -> iv in Aeolian)
def normalize_roman_for_display(mode: str, rn: str) -> str:
    return substitute_if_weak(mode, rn)

def pcs_to_spelled_root_first(pcs: List[int]) -> str:
    # Dummy function: convert pcs to string with root note first
    return ",".join(str(pc) for pc in pcs)

def print_pack_for_key(key_name: str, mode: str, pack: List[Tuple[str, List[int]]]):
    for rn, pcs in pack:
        spelled = []
        for rn, pcs in pack:
            rn_disp = normalize_roman_for_display(mode, rn)
            spelled.append(f"{rn_disp}:{pcs_to_spelled_root_first(pcs)}")
        print(f"{key_name} {mode} - {', '.join(spelled)}")

PROGRESSIONS_DORIAN = [
    ["i","IV","v","IV"],            # classic dorian loop
    ["i","VII","IV","i"],           # lift via VII
    ["i","IV","III","IV"],          # III color
    ["i","v","IV","i"],             # modal v
    ["i","VII","i","IV"],           # anthemic
    ["i","IV","VII","i"],           # cadence via VII
    ["i","IV","i","VII"],           # back-half lift
    ["i","V","IV","i"],             # **borrowed dominant V** for lift
    ["i","III","V","IV"],           # III then **V**
    ["i","IV","i","V","IV","i"], # extended cadence with **V**
]

# Enhanced section colors with more distinct pitches for better visual separation
SECTION_PITCH = {
    "Intro": 60,        # C4 - White
    "Uplift": 62,       # D4 - Light Blue
    "Pre-Break": 61,    # C#4 - Light Purple
    "Break": 57,        # A3 - Green
    "Vocal/Hook": 65,   # F4 - Yellow
    "Build": 67,        # G4 - Orange
    "Build Up": 67,     # G4 - Orange (alternative name)
    "Fake Drop": 58,    # A#3 - Dark Blue
    "Drop A": 72,       # C5 - Bright Red
    "Drop 1": 72,       # C5 - Bright Red (alternative name)
    "Drop B": 74,       # D5 - Pink
    "Drop 2": 74,       # D5 - Pink (alternative name)
    "Bridge": 64,       # E4 - Purple
    "Re-Intro": 55,     # G3 - Brown
    "Break 2": 56,      # G#3 - Dark Green
    "Build 2": 69,      # A4 - Light Orange
    "Drop 2 A": 76,     # E5 - Bright Pink
    "Drop 2 B": 77,     # F5 - Magenta
    "Mini Break": 59,   # B3 - Light Blue
    "Outro": 52,        # E3 - Dark Brown

}

# Enhanced section hints with more detailed production notes
SECTION_HINTS = {
    "Intro": "Kick, Closed Hat, FX bed, establish groove",
    "Uplift": "Add bass low-pass, ride noise, energy build",
    "Pre-Break": "Pull bass, tease lead, tension build",
    "Break": "Pads, arp fragments, vox chop, atmospheric",
    "Vocal/Hook": "Hook phrase, sparse drums, focus on melody",
    "Build": "Snare roll, risers, filter open, energy peak",
    "Build Up": "Snare roll, risers, filter open, energy peak",
    "Fake Drop": "Silence/impact -> boom, surprise element",
    "Drop A": "Full groove, main lead, maximum energy",
    "Drop 1": "Full groove, main lead, maximum energy",
    "Drop B": "Variation lead/counterline, keep energy",
    "Drop 2": "Variation lead/counterline, keep energy",
    "Bridge": "Chord swap, new motif, transition section",
    "Re-Intro": "Strip to drums/bass, reset energy",
    "Break 2": "Atmos + tension, second breakdown",
    "Build 2": "Heavier roll + uplifters, final push",
    "Drop 2 A": "Max energy, final drop variation",
    "Drop 2 B": "Final variation, climax section",
    "Mini Break": "Filtered percussion, background pads, light FX, tension build",
    "Outro": "DJ-friendly drums only, clean ending",

}

# ===== Enhanced arrangement templates inspired by the image =====
# More varied and realistic arrangements
ARR4 = [
  [("Intro",16),("Build Up",8),("Drop 1",24),("Break",16),("Mini Break",8),("Build",8),("Drop 2",24),("Outro",16)],
  [("Intro",16),("Uplift",8),("Break",16),("Build",8),("Drop A",32),("Bridge",8),("Drop B",16),("Outro",16)],
  [("Intro",8),("Build Up",8),("Drop 1",28),("Break",16),("Build",8),("Drop 2",20),("Outro",16)],
  [("Intro",16),("Uplift",8),("Break",12),("Build",12),("Drop A",32),("Break 2",8),("Build 2",8),("Drop B",16),("Outro",8)],
  [("Intro",8),("Pre-Break",8),("Break",16),("Build",8),("Drop A",24),("Bridge",8),("Drop B",24),("Outro",24)],
  [("Intro",16),("Uplift",8),("Vocal/Hook",8),("Break",16),("Build",8),("Drop A",32),("Drop B",16),("Outro",16)],
  [("Intro",12),("Build Up",4),("Drop 1",28),("Break",16),("Build",8),("Drop 2",20),("Outro",16)],
  [("Intro",16),("Break",12),("Build",12),("Drop A",32),("Bridge",8),("Drop B",20),("Outro",20)],
  [("Intro",8),("Uplift",8),("Break",20),("Build",12),("Drop A",32),("Drop B",16),("Outro",24)],
  [("Intro",16),("Uplift",8),("Break",16),("Build",8),("Drop A",28),("Bridge",8),("Drop B",20),("Outro",16)],
]

# Enhanced 6-minute templates with more complex structures
ARR6 = [
  [("Intro",32),("Build Up",8),("Drop 1",48),("Break",24),("Build",16),("Drop 2",32),("Outro",16)],
  [("Intro",24),("Break",24),("Build",16),("Drop A",48),("Vocal/Hook",8),("Drop B",24),("Outro",36)],
  [("Intro",32),("Uplift",8),("Break",24),("Build",16),("Fake Drop",4),("Drop A",44),("Bridge",16),("Drop B",20),("Outro",16)],
  [("Intro",28),("Uplift",4),("Break",24),("Build",16),("Drop A",48),("Break 2",16),("Build 2",16),("Drop B",24),("Outro",16)],
  [("Intro",24),("Pre-Break",8),("Break",24),("Build",16),("Drop A",40),("Bridge",16),("Drop B",24),("Outro",28)],
  [("Intro",32),("Uplift",8),("Vocal/Hook",16),("Break",24),("Build",16),("Drop A",48),("Drop B",24),("Outro",12)],
  [("Intro",24),("Build Up",8),("Drop 1",44),("Break",24),("Build",16),("Drop 2",24),("Outro",24)],
  [("Intro",32),("Break",20),("Build",16),("Drop A",48),("Bridge",16),("Drop B",28),("Outro",20)],
  [("Intro",24),("Uplift",8),("Break",28),("Build",16),("Drop A",48),("Drop B",24),("Outro",32)],
  [("Intro",28),("Uplift",4),("Break",24),("Build",16),("Drop A",44),("Bridge",16),("Drop B",28),("Outro",20)],
]



def write_skeleton(filename:str, arrangement, bpm=120, tpb=480):
    mid = MidiFile(ticks_per_beat=tpb)
    tempo = bpm_to_tempo(bpm)

    # Track 0: global tempo + markers
    t0 = MidiTrack(); mid.tracks.append(t0)
    t0.append(mido.MetaMessage('set_tempo', tempo=tempo, time=0))
    add_track_name(t0, "Sections & Markers")

    # Track 1: section blocks (visual guide) - enhanced for better DAW visualization
    t1 = MidiTrack(); mid.tracks.append(t1)
    add_track_name(t1, "Section Blocks (visual guide)")

    # Track 2: guide click (first 8 bars)
    t2 = MidiTrack(); mid.tracks.append(t2)
    add_track_name(t2, "Guide Click (first 8 bars)")
    for _ in range(8*4):  # 8 bars of quarters
        t2.append(Message('note_on', note=37, velocity=40, time=0))
        t2.append(Message('note_off', note=37, velocity=0, time=tpb))

    # Build the arrangement with enhanced visual blocks
    current_ticks = 0
    for (name, bars) in arrangement:
        # marker + hint - positioned at correct time
        add_marker(t0, f"{name}", current_ticks)
        add_text(t0, f"{name}: {SECTION_HINTS.get(name, '—')}", current_ticks)

        # Enhanced section block with better visual separation
        note = SECTION_PITCH.get(name, 60)
        dur = bars_to_ticks(bars, tpb)
        
        # Create a more prominent visual block
        add_block_note(t1, note, vel=100, dur_ticks=dur)  # Higher velocity for better visibility
        
        # advance time for next section
        current_ticks += dur

    mid.save(filename)
    
    # Calculate actual BPM from tempo
    actual_bpm = int(60_000_000 / tempo)
    
    # Generate enhanced JSON metadata
    params = {
        "bpm": actual_bpm,
        "ticks_per_beat": tpb,
        "total_bars": sum(bars for _, bars in arrangement),
        "sections_count": len(arrangement)
    }
    
    theory = {
        "style": "melodic-house",
        "arrangement_type": "skeleton-template",
        "track_structure": "3-track-midi",
        "visual_enhancement": "enhanced-section-blocks"
    }
    
    timeline = {
        "ppq": tpb,
        "tempo_bpm": actual_bpm,
        "sections": [
            {"name": name, "start_bar": sum(bars for _, bars in arrangement[:i]), "bars": bars, "pitch": SECTION_PITCH.get(name, 60)}
            for i, (name, bars) in enumerate(arrangement)
        ]
    }
    
    tags = ["melodic-house", "arrangement-skeletons", "midi-templates", "track-structure", "enhanced-visual"]
    
    # Determine template type based on total bars
    total_bars = sum(bars for _, bars in arrangement)
    if total_bars <= 120:
        template_type = "4min"
    elif total_bars <= 180:
        template_type = "6min"
    else:
        template_type = "8min"
    
    derived = {
        "total_duration_seconds": total_bars * 4 * 60 / actual_bpm,
        "template_type": template_type,
        "visual_complexity": "enhanced"
    }
    
    create_midi_metadata(
        script_name="make_arrangement_skeletons_mh.py",
        midi_filepath=filename,
        params=params,
        theory=theory,
        timeline=timeline,
        tags=tags,
        derived=derived
    )
    
    return filename

def bpm_to_tempo(bpm:int) -> int:
    return int(60_000_000 / bpm)

def beats(bars:int, beats_per_bar:int=4) -> int:
    return bars * beats_per_bar

def add_marker(track: MidiTrack, text: str, t: int):
    track.append(mido.MetaMessage('marker', text=text, time=t))

def add_text(track: MidiTrack, text: str, t: int):
    track.append(mido.MetaMessage('text', text=text, time=t))

def add_track_name(track: MidiTrack, name: str):
    track.append(mido.MetaMessage('track_name', name=name, time=0))

def add_block_note(track: MidiTrack, note: int, vel: int, dur_ticks: int):
    # on then off after duration
    track.append(Message('note_on', note=note, velocity=vel, time=0))
    track.append(Message('note_off', note=note, velocity=0, time=dur_ticks))

def bars_to_ticks(bars:int, tpb:int, beats_per_bar:int=4) -> int:
    return bars * beats_per_bar * tpb

def print_arrangement_stats(arrangement, bpm=120):
    """Print detailed statistics about an arrangement"""
    total_bars = sum(bars for _, bars in arrangement)
    total_seconds = total_bars * 4 * 60 / bpm
    total_minutes = total_seconds / 60
    
    print(f"📊 Arrangement Statistics:")
    print(f"   Total bars: {total_bars}")
    print(f"   Duration: {total_minutes:.1f} minutes ({total_seconds:.0f}s)")
    print(f"   Sections: {len(arrangement)}")
    print(f"   Average section length: {total_bars/len(arrangement):.1f} bars")
    print(f"   Sections breakdown:")
    
    for i, (name, bars) in enumerate(arrangement):
        section_seconds = bars * 4 * 60 / bpm
        print(f"     {i+1:2d}. {name:12s}: {bars:2d} bars ({section_seconds:4.1f}s)")

def write_json_file(base_filename, arrangement, bpm=120):
    """Generate a JSON file for the arrangement with structured data"""
    # Remove .mid extension for base filename
    base_name = base_filename.replace('.mid', '')
    
    # Generate .json file
    json_filename = f"{base_name}.json"
    
    # Calculate timing information
    total_bars = sum(bars for _, bars in arrangement)
    total_seconds = total_bars * 4 * 60 / bpm
    
    # Build the JSON structure
    arrangement_data = {
        "metadata": {
            "filename": os.path.basename(base_name),
            "tempo_bpm": bpm,
            "total_bars": total_bars,
            "total_seconds": round(total_seconds, 1),
            "total_minutes": round(total_seconds / 60, 2),
            "sections_count": len(arrangement),
            "style": "melodic-house",
            "structure_type": "electronic-dance-music",
            "purpose": "arrangement-skeleton-for-production"
        },
        "sections": []
    }
    
    # Add each section with detailed information
    current_bar = 0
    for i, (name, bars) in enumerate(arrangement, start=1):
        section_seconds = bars * 4 * 60 / bpm
        section_data = {
            "order": i,
            "name": name,
            "bars": bars,
            "start_bar": current_bar,
            "end_bar": current_bar + bars - 1,
            "duration_seconds": round(section_seconds, 1),
            "production_notes": SECTION_HINTS.get(name, "—"),
            "visual_pitch": SECTION_PITCH.get(name, 60),
            "time_position": {
                "start_time_seconds": round(current_bar * 4 * 60 / bpm, 1),
                "end_time_seconds": round((current_bar + bars) * 4 * 60 / bpm, 1)
            }
        }
        arrangement_data["sections"].append(section_data)
        current_bar += bars
    
    # Add arrangement analysis
    arrangement_data["analysis"] = {
        "average_section_length": round(total_bars / len(arrangement), 1),
        "longest_section": max(arrangement, key=lambda x: x[1]),
        "shortest_section": min(arrangement, key=lambda x: x[1]),
        "energy_flow": "low-high-low-high-low" if len(arrangement) >= 4 else "standard",
        "breakdown_sections": [name for name, _ in arrangement if "break" in name.lower()],
        "drop_sections": [name for name, _ in arrangement if "drop" in name.lower()],
        "build_sections": [name for name, _ in arrangement if "build" in name.lower()]
    }
    
    # Write JSON file with pretty formatting
    with open(json_filename, 'w') as f:
        json.dump(arrangement_data, f, indent=2, ensure_ascii=False)
    
    return json_filename

def write_text_files(base_filename, arrangement, bpm=120):
    """Generate text and markdown files for the arrangement"""
    # Remove .mid extension for base filename
    base_name = base_filename.replace('.mid', '')
    
    # Generate .txt file
    txt_filename = f"{base_name}.txt"
    with open(txt_filename, 'w') as f:
        f.write(f"Arrangement Skeleton - {os.path.basename(base_name)}\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Tempo: {bpm} BPM\n")
        f.write(f"Total bars: {sum(bars for _, bars in arrangement)}\n")
        f.write(f"Total time: {sum(bars for _, bars in arrangement) * 4 * 60 / bpm:.1f} seconds\n\n")
        
        f.write("Sections:\n")
        f.write("-" * 20 + "\n")
        for i, (name, bars) in enumerate(arrangement, start=1):
            section_seconds = bars * 4 * 60 / bpm
            f.write(f"{i:2d}. {name:12s}: {bars:2d} bars ({section_seconds:4.1f}s)\n")
            if name in SECTION_HINTS:
                f.write(f"    Production: {SECTION_HINTS[name]}\n")
            f.write("\n")
    
    # Generate .md file
    md_filename = f"{base_name}.md"
    with open(md_filename, 'w') as f:
        f.write(f"# Arrangement Skeleton - {os.path.basename(base_name)}\n\n")
        f.write(f"**Tempo**: {bpm} BPM  \n")
        f.write(f"**Total bars**: {sum(bars for _, bars in arrangement)}  \n")
        f.write(f"**Total time**: {sum(bars for _, bars in arrangement) * 4 * 60 / bpm:.1f} seconds\n\n")
        
        f.write("## Sections\n\n")
        for i, (name, bars) in enumerate(arrangement, start=1):
            section_seconds = bars * 4 * 60 / bpm
            f.write(f"### {i}. {name}\n")
            f.write(f"- **Bars**: {bars}\n")
            f.write(f"- **Duration**: {section_seconds:.1f} seconds\n")
            if name in SECTION_HINTS:
                f.write(f"- **Production Notes**: {SECTION_HINTS[name]}\n")
            f.write("\n")
        
        f.write("## Musical Characteristics\n\n")
        f.write("- **Style**: Melodic House\n")
        f.write("- **Structure**: Electronic Dance Music (EDM)\n")
        f.write("- **Purpose**: Arrangement skeleton for production\n\n")
        
        f.write("## Usage\n\n")
        f.write("This file provides a visual and textual reference for the arrangement structure.\n")
        f.write("Use it alongside the MIDI file for production planning and reference.\n")
    
    return txt_filename, md_filename

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Generate melodic house arrangement skeleton MIDIs")
    parser.add_argument("--bpm", type=int, default=122, help="Tempo in BPM (default: 122)")
    parser.add_argument("--tpb", type=int, default=480, help="Ticks per beat (default: 480)")
    parser.add_argument("--output", type=str, default="out/arrangements", help="Output directory (default: out/arrangements)")
    parser.add_argument("--types", nargs="+", choices=["4min", "6min"], default=["4min", "6min"], 
                       help="Arrangement types to generate (default: all)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be created without generating files")
    parser.add_argument("--stats", action="store_true", help="Show detailed statistics for each arrangement")
    parser.add_argument("--list", action="store_true", help="List all available arrangements without generating files")
    
    args = parser.parse_args()
    
    # Handle list option
    if args.list:
        print("📋 Available Arrangement Templates:")
        print("=" * 50)
        
        print(f"\n🔴 4-Minute Templates ({len(ARR4)}):")
        for i, arr in enumerate(ARR4, start=1):
            total_bars = sum(bars for _, bars in arr)
            print(f"   {i:2d}. {total_bars:3d} bars - {' → '.join(name for name, _ in arr)}")
        
        print(f"\n🟡 6-Minute Templates ({len(ARR6)}):")
        for i, arr in enumerate(ARR6, start=1):
            total_bars = sum(bars for _, bars in arr)
            print(f"   {i:2d}. {total_bars:3d} bars - {' → '.join(name for name, _ in arr)}")
        

        
        print("=" * 50)
        print("Use --types to select specific template types")
        print("Use --stats to see detailed breakdowns")
        return
    
    # Create output directory if it doesn't exist
    if not args.dry_run:
        os.makedirs(args.output, exist_ok=True)
    
    print("Creating enhanced arrangement skeletons...")
    print("=" * 50)
    print(f"🎵 Tempo: {args.bpm} BPM")
    print(f"🎵 Resolution: {args.tpb} ticks/beat")
    print(f"📁 Output: {args.output}")
    print("=" * 50)
    
    total_created = 0
    
    # Generate 4-minute skeletons
    if "4min" in args.types:
        print(f"\n🔴 Generating {len(ARR4)} four-minute skeletons...")
        for i, arr in enumerate(ARR4, start=1):
            filename = f"{args.output}/arr{i:02d}_skeleton_4min.mid"
            if args.stats:
                print(f"\n📊 Arrangement {i:02d}:")
                print_arrangement_stats(arr, args.bpm)
            if not args.dry_run:
                write_skeleton(filename, arr, bpm=args.bpm, tpb=args.tpb)
                txt_file, md_file = write_text_files(filename, arr, bpm=args.bpm)
                json_file = write_json_file(filename, arr, bpm=args.bpm)
                print(f"✅ Created: {filename}")
                print(f"✅ Created: {txt_file}")
                print(f"✅ Created: {md_file}")
                print(f"✅ Created: {json_file}")
            else:
                print(f"📝 Would create: {filename}")
                print(f"📝 Would create: {filename.replace('.mid', '.txt')}")
                print(f"📝 Would create: {filename.replace('.mid', '.md')}")
                print(f"📝 Would create: {filename.replace('.mid', '.json')}")
            total_created += 1
    
    # Generate 6-minute skeletons
    if "6min" in args.types:
        print(f"\n🟡 Generating {len(ARR6)} six-minute skeletons...")
        for i, arr in enumerate(ARR6, start=1):
            filename = f"{args.output}/arr{i:02d}_skeleton_6min.mid"
            if args.stats:
                print(f"\n📊 Arrangement {i:02d}:")
                print_arrangement_stats(arr, args.bpm)
            if not args.dry_run:
                write_skeleton(filename, arr, bpm=args.bpm, tpb=args.tpb)
                txt_file, md_file = write_text_files(filename, arr, bpm=args.bpm)
                json_file = write_json_file(filename, arr, bpm=args.bpm)
                print(f"✅ Created: {filename}")
                print(f"✅ Created: {txt_file}")
                print(f"✅ Created: {md_file}")
                print(f"✅ Created: {json_file}")
            else:
                print(f"📝 Would create: {filename}")
                print(f"📝 Would create: {filename.replace('.mid', '.txt')}")
                print(f"📝 Would create: {filename.replace('.mid', '.md')}")
                print(f"📝 Would create: {filename.replace('.mid', '.json')}")
            total_created += 1
    

        
    print("=" * 50)
    if args.dry_run:
        print(f"📋 Dry run: Would create {total_created} arrangement skeleton MIDIs")
        print(f"📋 Plus {total_created * 3} text files (.txt, .md, and .json)")
    else:
        print(f"🎵 Total: Created {total_created} enhanced arrangement skeleton MIDIs")
        print(f"📝 Plus {total_created * 3} text files (.txt, .md, and .json)")
    print("📁 Files saved in:", args.output)
    print("🎯 Each MIDI file has enhanced visual section blocks for better DAW integration")
    print("📝 Text files provide human-readable arrangement documentation")
    print("📊 JSON files provide structured data for programmatic use")
    print("🎵 Use --help for command line options")

if __name__ == "__main__":
    main()