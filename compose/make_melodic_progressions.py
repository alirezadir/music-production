#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import mido
from mido import MidiFile, MidiTrack, Message
import time
import os

# --- Camelot minor wheel (A = minor)
CAMELOT_MINOR = {
    "G#m":"1A",  "Abm":"1A",
    "D#m":"2A",  "Ebm":"2A",
    "A#m":"3A",  "Bbm":"3A",
    "Fm":"4A",
    "Cm":"5A",
    "Gm":"6A",
    "Dm":"7A",
    "Am":"8A",
    "Em":"9A",
    "Bm":"10A",
    "F#m":"11A", "Gbm":"11A",
    "C#m":"12A", "Dbm":"12A",
}

def key_to_camelot_minor(key_name: str) -> str:
    k = key_name.strip()
    if not k.endswith('m'): k += 'm'
    return CAMELOT_MINOR.get(k, "?")

# Prefer common display (flats for Abm/Dbm/Gbm names only when given as such)
def normalize_display_key_minor(key_name: str) -> str:
    k = key_name.strip()
    return k if k.endswith('m') else k+"m"

def build_outfile_basename(key_minor: str, mode: str, use_7ths: bool) -> str:
    disp = normalize_display_key_minor(key_minor)
    cam = key_to_camelot_minor(key_minor)
    q = "sevenths" if use_7ths else "triads"
    return f"{disp}_{cam}_minor_{mode}_{q}"

def ensure_outdir(path: str):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)

# Write a UTF-8 text log (mirrors dry-run lines)
def write_txt_log(path: str, header: str, lines: list[str]):
    ensure_outdir(path)
    with open(path, 'w', encoding='utf-8') as f:
        if header:
            f.write(header.strip()+"\n\n")
        for ln in lines:
            f.write(ln+"\n")

# json metadata is optional
try:
    from json_metadata import create_midi_metadata  # type: ignore
except Exception:
    def create_midi_metadata(**kwargs):
        return None

# -----------------------
# Progression set (minor key, Aeolian feel)
# -----------------------
PROGRESSIONS_AEOLIAN = [
    ["i","VI","VII","i"],
    ["i","VI","III","VII"],
    ["i","iv","VI","VII"],
    ["i","V","VI","VII"],           # borrowed V lift
    ["i","VI","iv","V"],            # borrowed V cadence
    ["i","VI","VII","III"],
    ["i","VII","i","VI"],
    ["i","III","VI","VII"],
    ["i","iv","V","i"],             # borrowed V resolve
    ["i","III","i","VI"],
    ["i","VI","iv","i"],
    ["i","iv","i","VII"],
    ["i","iv","VII","i"],
    ["i","VI","iv","VII"],
    ["i","iv","v","i"],
    ["i","III","VI","i"],
    ["i","VI","i","VI","VII","i"],
    ["i","iv","i","VI","VII","i"],
    ["i","iv","V","VI"],            # borrowed V lift chain
    ["i","VII","VI","VII"],
]

PROGRESSIONS_DORIAN = [
    ["i","IV","v","IV"],          # quintessential dorian roll (moody)
    ["i","VII","IV","i"],         # anthemic lift via VII
    ["i","IV","III","IV"],        # III color against IV
    ["i","III","IV","i"],         # classic melodic movement
    ["i","IV","i","VII"],         # back-half lift
    ["i","VII","i","IV"],         # call/response, keeps tension
    ["i","v","IV","i"],           # minor v, underground feel
    ["i","IV","VII","i"],         # cadence via VII
    ["i","III","VII","IV"],       # brighter pass then back to IV
    ["i","IV","III","i"],         # gentle resolve home
]

PROGRESSIONS_PHRYGIAN = [
    ["i","II","i","VII"],        # P01 signature phrygian loop (b2 showcased)
    ["i","II","iv","i"],         # P02 darker/haunting variant
    ["i","iv","VII","i"],        # P03 dark bridge then return
    ["i","VII","VI","V"],        # P04 edited: end on V (setup/loop)
    ["i","VI","II","i"],         # P05 edited: detour to b2 then resolve to i
    ["i","VII","i","II"],        # P07 call/response into b2
    ["i","VI","VII","i"],        # P08 rising VI→VII energy
    ["i","II","VI","i"],         # P09 edited: tension→VI resolve→i
    ["i","II","VII","i"],        # P10 edited: cadence variant resolving to i
    ["i","II","VI","VII"],       # (from original P10 set, distinct shape)
    # --- additional newer patterns (kept, non-duplicates) ---
    ["i","II","i"],                 # compact i–bII–i loop
    ["i","VII","VI","II","i"],  # long loop ending on b2→i
    ["II","i","VII","V"],        # b2→i then b7→V setup
    # ["i","v°","II","i"],         # diminished colour into b2→i
    ["iv","III","II","i"],       # Andalusian-style ostinato in phrygian
    ["i","II","VII","VI"],       # cadence variant (b2 active)
]

PROGRESSIONS_PERSIAN = [
    ["i","VII","VI","V"],        # classic IR pop loop, clear cadence
    ["i","iv","V","i"],          # minor iv → V → i resolve
    ["i","V","i","VII"],         # tight cadence then lift
    ["i","VI","V","i"],          # (replaces old P04) softer VI then resolve
    ["i","VII","V","i"],         # b7 → V → i
    ["i","III","VII","i"],       # bright pass then home
    ["i","iv","VI","V"],         # build into V
    ["i","V","VI","V"],          # cadence pump (V featured)
    ["i","VI","III","V"],        # radio‑friendly lift into V
    ["i","V","i","V"],           # snappy turnaround loop
]

def pick_progressions(mode: str):
    if mode == "dorian":
        return PROGRESSIONS_DORIAN
    if mode == "phrygian":
        return PROGRESSIONS_PHRYGIAN
    if mode == "persian":
        return PROGRESSIONS_PERSIAN
    return PROGRESSIONS_AEOLIAN

NOTE_NAMES_SHARP = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
NAME_TO_PC = {n:i for i,n in enumerate(NOTE_NAMES_SHARP)}

# Diatonic semitone steps (degrees 1..7) per mode
SCALE_STEPS = {
    "aeolian":  [0,2,3,5,7,8,10],   # natural minor
    "dorian":   [0,2,3,5,7,9,10],   # raised 6
    "phrygian": [0,1,3,5,7,8,10],   # flat 2
    "persian":  [0,1,4,5,7,8,10],   # phrygian-dominant (1, b2, 3, 4, 5, b6, b7)
}

# Triad and 7th qualities per degree (1..7) by mode
TRIAD_QUALITIES = {
    "aeolian":  ["min","dim","maj","min","min","maj","maj"],
    "dorian":   ["min","min","maj","maj","min","dim","maj"],
    "phrygian": ["min","maj","maj","min","dim","maj","maj"],
    "persian":  ["min","dim","maj","min","min","maj","maj"],  # natural minor; use uppercase V for dominant
}
SEVENTH_QUALITIES = {
    "aeolian":  ["min7","half-dim7","maj7","min7","min7","maj7","dom7"],
    "dorian":   ["min7","min7","maj7","maj7","min7","half-dim7","dom7"],
    "phrygian": ["min7","maj7","maj7","min7","half-dim7","maj7","dom7"],
    "persian":  ["min7","half-dim7","maj7","min7","min7","maj7","dom7"],  # natural minor 7ths; V (uppercase) becomes dom7
}

# -----------------------
# ASCII-only meta text helper (Mido uses latin-1)
# -----------------------
def _safe_meta_text(s: str) -> str:
    if not isinstance(s, str):
        s = str(s)
    s = (s.replace("—","-")
           .replace("–","-")
           .replace("♭","b")
           .replace("♯","#"))
    try:
        return s.encode('latin-1', 'ignore').decode('latin-1')
    except Exception:
        return s.encode('ascii', 'ignore').decode('ascii')

# -----------------------
# Key / scale helpers
# -----------------------
def parse_key_minor(key_str: str) -> int:
    s = key_str.strip().lower().replace(" minor","" ).replace("minor","")
    s = s.replace("♯","#").replace("♭","b")
    if s.endswith("m"): s = s[:-1]
    flats = {"db":"C#","eb":"D#","gb":"F#","ab":"G#","bb":"A#","cb":"B","fb":"E"}
    s = flats.get(s, s).upper()
    if s not in NAME_TO_PC:
        raise ValueError(f"Unrecognized key '{key_str}'")
    return NAME_TO_PC[s]

def degree_to_pc(tonic_pc: int, degree: int, mode: str) -> int:
    return (tonic_pc + SCALE_STEPS[mode][degree-1]) % 12

def roman_to_degree(roman: str) -> int:
    base = roman.replace("°","" ).replace("b","" ).replace("#","" )
    mapping = {"i":1,"ii":2,"iii":3,"iv":4,"v":5,"vi":6,"vii":7,
               "I":1,"II":2,"III":3,"IV":4,"V":5,"VI":6,"VII":7}
    if base not in mapping:
        raise ValueError(f"Bad roman numeral: {roman}")
    return mapping[base]

# --- Modal helpers ---
def apply_accidental(pc: int, roman: str) -> int:
    if roman.startswith("b"): return (pc - 1) % 12
    if roman.startswith("#"): return (pc + 1) % 12
    return pc

def degree_quality(mode: str, degree: int, use_7ths: bool) -> str:
    return (SEVENTH_QUALITIES if use_7ths else TRIAD_QUALITIES)[mode][degree-1]

def chord_quality(roman: str, use_7ths: bool) -> str:
    # Deprecated: replaced by degree_quality for modal logic.
    if "ii°" in roman: return "dim7" if use_7ths else "dim"
    if roman == "V":   return "dom7" if use_7ths else "maj"  # borrowed V
    if "bVII" in roman or "bVI" in roman:
        return "maj7" if use_7ths else "maj"
    if roman in ("i","iv","v"):      return "min7" if use_7ths else "min"
    if roman in ("III","VI","VII"):  return "maj7" if use_7ths else "maj"
    return "min7" if use_7ths else "min"

# --- Weakened/dominant policy ---

def substitute_if_weak(mode: str, roman: str) -> str:
    # Avoid ii° in Aeolian groove -> use iv
    if mode == "aeolian" and roman in ("ii°","ii"):
        return "iv"
    return roman

# Ensure dry-run labels match any internal substitution (e.g., Aeolian ii° -> iv)
def normalize_roman_for_display(mode: str, rn: str) -> str:
    return substitute_if_weak(mode, rn)

def build_chord_pcs(tonic_pc: int, mode: str, roman: str, use_7ths: bool, add9: bool):
    roman = substitute_if_weak(mode, roman)
    base = roman.replace("°","").replace("b","").replace("#","")
    deg = roman_to_degree(base)
    root = degree_to_pc(tonic_pc, deg, mode)
    # apply accidental after mapping degree
    root = apply_accidental(root, roman)

    # Borrowed dominant: if user wrote uppercase V in minor contexts
    if roman == "V":
        qual = "dom7" if use_7ths else "maj"
    else:
        qual = degree_quality(mode, deg, use_7ths)

    def pcs_from_quality(root_pc, qual):
        if qual in ("min","min7"):
            third=(root_pc+3)%12; fifth=(root_pc+7)%12; seventh=(root_pc+10)%12
            pcs=[root_pc,third,fifth];  pcs7=[root_pc,third,fifth,seventh]
        elif qual in ("maj","maj7"):
            third=(root_pc+4)%12; fifth=(root_pc+7)%12; seventh=(root_pc+11)%12
            pcs=[root_pc,third,fifth];  pcs7=[root_pc,third,fifth,seventh]
        elif qual == "dom7":
            third=(root_pc+4)%12; fifth=(root_pc+7)%12; seventh=(root_pc+10)%12
            pcs=[root_pc,third,fifth];  pcs7=[root_pc,third,fifth,seventh]
        elif qual in ("dim","dim7","half-dim7"):
            third=(root_pc+3)%12; fifth=(root_pc+6)%12
            if qual == "dim":
                pcs = [root_pc,third,fifth]; pcs7 = [root_pc,third,fifth,(root_pc+9)%12]
            elif qual == "dim7":
                pcs = [root_pc,third,fifth]; pcs7 = [root_pc,third,fifth,(root_pc+9)%12]
            else:  # half-dim7
                pcs = [root_pc,third,fifth]; pcs7 = [root_pc,third,fifth,(root_pc+10)%12]
            return pcs7 if ("7" in qual) else pcs
        else:
            pcs=[root_pc,(root_pc+4)%12,(root_pc+7)%12]; pcs7=[*pcs,(root_pc+11)%12]
        return pcs7 if ("7" in qual) else pcs

    pcs = pcs_from_quality(root, qual)

    if add9:
        ninth = (root + 14) % 12
        if ninth not in pcs: pcs.append(ninth)
    return pcs

# -----------------------
# Voicing / inversions
# -----------------------
def build_inversion_notes(pcs, base_oct: int):
    out=[]
    ntones=len(pcs)
    for inv in range(ntones):
        order=pcs[inv:]+pcs[:inv]
        notes=[]
        n=order[0]+12*base_oct
        while n%12!=order[0]: n+=1
        notes.append(n)
        last=n
        for pc in order[1:]:
            m=last
            while m%12!=pc: m+=1
            if m<=last: m+=12
            notes.append(m); last=m
        out.append((inv,notes))
    return out

def choose_smooth_inversion(pcs, base_oct: int, prev_notes=None):
    candidates = build_inversion_notes(pcs, base_oct)
    if prev_notes is None:
        return candidates[0][1]
    return min(candidates, key=lambda t: sum(abs(a-b) for a,b in zip(prev_notes,t[1])))[1]

# -----------------------
# MIDI helpers
# -----------------------
def bpm_to_tempo(bpm:int)->int: return int(60_000_000/bpm)

def roman_list_to_slug(seq):  # ["i","VI","VII","i"] -> "i-VI-VII-i"
    return "-".join(seq)

def _write_chord_event(track: MidiTrack, notes, duration_ticks, velocity=90):
    for i, n in enumerate(notes):
        track.append(Message('note_on', note=n, velocity=velocity, time=0 if i else 0))
    first_off = True
    for n in notes:
        track.append(Message('note_off', note=n, velocity=0, time=duration_ticks if first_off else 0))
        first_off = False

def _derive_bass_root(pcs, chord_notes):
    root_pc = pcs[0]
    base_n = root_pc + 12*2  # around octave 2
    while base_n % 12 != root_pc: base_n += 1
    while chord_notes[0] - base_n < 12: base_n -= 12
    return base_n

# -----------------------
# Clip naming utilities
# -----------------------
def generate_clip_name(key_minor: str, mode: str, progression: list, chord_type: str = "triads", 
                      add9: bool = False, make_bass: bool = False, progression_index: int = None) -> str:
    """
    Generate a unique and descriptive clip name for Ableton Live.
    
    Args:
        key_minor: The key (e.g., "Am", "F#m")
        mode: The harmonic mode (e.g., "aeolian", "dorian", "phrygian")
        progression: List of roman numerals (e.g., ["i", "VI", "VII", "i"])
        chord_type: Type of chords ("triads" or "7ths")
        add9: Whether add9 is enabled
        make_bass: Whether bass track is included
        progression_index: Index number for the progression (optional)
    
    Returns:
        A descriptive clip name string
    """
    # Convert key to a clean format
    key_clean = key_minor.replace("#", "s").replace("♯", "s").replace("♭", "b")
    
    # Create progression slug
    progression_slug = roman_list_to_slug(progression)
    
    # Build the clip name components
    components = []
    
    # Add progression index if provided
    if progression_index is not None:
        components.append(f"P{progression_index:02d}")
    
    # Add key and mode
    components.append(f"{key_clean} {mode}")
    
    # Add progression
    components.append(progression_slug)
    
    # Add chord type
    components.append(chord_type)
    
    # Add add9 if enabled
    if add9:
        components.append("add9")
    
    # Add bass indicator if enabled
    if make_bass:
        components.append("bass")
    
    # Join all components with spaces
    clip_name = " ".join(components)
    
    return clip_name

def generate_filename_safe_clip_name(key_minor: str, mode: str, progression: list, 
                                   chord_type: str = "triads", add9: bool = False, 
                                   make_bass: bool = False, progression_index: int = None) -> str:
    """
    Generate a filename-safe version of the clip name (no spaces, safe characters only).
    
    Args:
        key_minor: The key (e.g., "Am", "F#m")
        mode: The harmonic mode (e.g., "aeolian", "dorian", "phrygian")
        progression: List of roman numerals (e.g., ["i", "VI", "VII", "i"])
        chord_type: Type of chords ("triads" or "7ths")
        add9: Whether add9 is enabled
        make_bass: Whether bass track is included
        progression_index: Index number for the progression (optional)
    
    Returns:
        A filename-safe string
    """
    clip_name = generate_clip_name(key_minor, mode, progression, chord_type, add9, make_bass, progression_index)
    
    # Replace spaces with underscores and remove any potentially problematic characters
    safe_name = (clip_name.replace(" ", "_")
                           .replace("/", "-")
                           .replace("\\", "-")
                           .replace(":", "-")
                           .replace("*", "")
                           .replace("?", "")
                           .replace('"', "")
                           .replace("'", "")
                           .replace("<", "")
                           .replace(">", "")
                           .replace("|", ""))
    
    return safe_name

# -----------------------
# Writers (helpers)
# -----------------------
def _write_single_progression_midi(
    key_minor, mode, progression, outfile, tempo_bpm, bars_per_chord,
    base_octave, velocity, use_7ths, add9, make_bass
):
    tonic_pc = parse_key_minor(key_minor)
    mid = MidiFile(ticks_per_beat=480)
    file_stem = os.path.splitext(os.path.basename(outfile))[0]

    meta = MidiTrack(); mid.tracks.append(meta)
    meta.append(mido.MetaMessage('set_tempo', tempo=bpm_to_tempo(tempo_bpm), time=0))
    meta.append(mido.MetaMessage('track_name', name=_safe_meta_text(file_stem), time=0))

    chords = MidiTrack(); mid.tracks.append(chords)
    chords.append(mido.MetaMessage('track_name', name=_safe_meta_text(file_stem), time=0))
    
    # Add more descriptive clip information
    progression_slug = roman_list_to_slug(progression)
    chord_type = '7ths' if use_7ths else 'triads'
    add9_info = ' +9' if add9 else ''
    bass_info = ' +bass' if make_bass else ''
    
    # Create a unique and descriptive clip name
    clip_name = f"{key_minor} {mode} {progression_slug} {chord_type}{add9_info}{bass_info}"
    chords.append(mido.MetaMessage('text', text=_safe_meta_text(clip_name), time=0))
    
    # Add progression details as additional metadata
    chords.append(mido.MetaMessage('text', text=_safe_meta_text(f"Progression: {progression_slug}"), time=0))
    chords.append(mido.MetaMessage('text', text=_safe_meta_text(f"Key: {key_minor}, Mode: {mode}"), time=0))
    chords.append(mido.MetaMessage('text', text=_safe_meta_text(f"Tempo: {tempo_bpm} BPM, {bars_per_chord} bar(s) per chord"), time=0))

    bass = None
    if make_bass:
        bass = MidiTrack(); mid.tracks.append(bass)
        bass.append(mido.MetaMessage('track_name', name=_safe_meta_text(file_stem + " - Bass"), time=0))
        # Add bass track metadata
        bass.append(mido.MetaMessage('text', text=_safe_meta_text(f"Bass - {key_minor} {mode} {progression_slug}"), time=0))

    ticks_per_bar = mid.ticks_per_beat * 4
    dur = ticks_per_bar * bars_per_chord

    prev = None
    for rn in progression:
        pcs = build_chord_pcs(tonic_pc, mode, rn, use_7ths, add9)
        notes = choose_smooth_inversion(pcs, base_octave, prev_notes=prev)
        _write_chord_event(chords, notes, dur, velocity)
        if bass:
            b = _derive_bass_root(pcs, notes)
            bass.append(Message('note_on', note=b, velocity=96, time=0))
            bass.append(Message('note_off', note=b, velocity=0, time=dur))
        prev = notes

    mid.save(outfile)

    # JSON metadata (optional)
    params = {
        "key_minor": key_minor,
        "tempo_bpm": tempo_bpm,
        "bars_per_chord": bars_per_chord,
        "base_octave": base_octave,
        "velocity": velocity,
        "use_7ths": use_7ths,
        "add9": add9,
        "make_bass": make_bass
    }
    theory = {
        "key": key_minor,
        "mode": mode,
        "scale_degrees": SCALE_STEPS[mode],
        "progression": progression,
        "chord_qualities": ["triads" if not use_7ths else "7ths"]
    }
    voicing = {"add9": add9, "use_7ths": use_7ths, "bass_line": make_bass}
    timeline = {
        "ppq": 480,
        "tempo_bpm": tempo_bpm,
        "bars_per_chord": bars_per_chord,
        "total_bars": len(progression) * bars_per_chord
    }
    tags = ["melodic-house", "chord-progressions", f"{mode}-harmony", "midi-loops"]
    derived = {
        "total_duration_seconds": len(progression) * bars_per_chord * 4 * 60 / tempo_bpm,
        "complexity": "advanced" if use_7ths and add9 else ("intermediate" if use_7ths or add9 else "basic")
    }
    create_midi_metadata(
        script_name="make_melodic_progressions.py",
        midi_filepath=outfile,
        params=params,
        theory=theory,
        voicing=voicing,
        timeline=timeline,
        tags=tags,
        derived=derived
    )
    return outfile


def _write_all_progressions_midi(
    key_minor, mode, progs, outfile, tempo_bpm, bars_per_chord,
    base_octave, velocity, use_7ths, add9, make_bass
):
    tonic_pc = parse_key_minor(key_minor)
    mid = MidiFile(ticks_per_beat=480)
    file_stem = os.path.splitext(os.path.basename(outfile))[0]

    meta = MidiTrack(); mid.tracks.append(meta)
    meta.append(mido.MetaMessage('set_tempo', tempo=bpm_to_tempo(tempo_bpm), time=0))
    meta.append(mido.MetaMessage('track_name', name=_safe_meta_text(file_stem), time=0))

    chords = MidiTrack(); mid.tracks.append(chords)
    chords.append(mido.MetaMessage('track_name', name=_safe_meta_text(file_stem), time=0))
    
    # Add pack-level metadata
    chord_type = '7ths' if use_7ths else 'triads'
    add9_info = ' +9' if add9 else ''
    bass_info = ' +bass' if make_bass else ''
    
    pack_name = f"{key_minor} {mode} Progression Pack {chord_type}{add9_info}{bass_info}"
    chords.append(mido.MetaMessage('text', text=_safe_meta_text(pack_name), time=0))
    chords.append(mido.MetaMessage('text', text=_safe_meta_text(f"Key: {key_minor}, Mode: {mode}"), time=0))
    chords.append(mido.MetaMessage('text', text=_safe_meta_text(f"Tempo: {tempo_bpm} BPM, {bars_per_chord} bar(s) per chord"), time=0))

    bass = None
    if make_bass:
        bass = MidiTrack(); mid.tracks.append(bass)
        bass.append(mido.MetaMessage('track_name', name=_safe_meta_text(file_stem + " - Bass"), time=0))
        # Add bass track metadata
        bass.append(mido.MetaMessage('text', text=_safe_meta_text(f"Bass - {key_minor} {mode} Progression Pack"), time=0))

    ticks_per_bar = mid.ticks_per_beat * 4
    dur = ticks_per_bar * bars_per_chord
    gap = ticks_per_bar  # 1-bar gap between progressions
   
    for idx, prog in enumerate(progs, start=1):
        if idx > 1:
            chords.append(mido.MetaMessage('text', text=_safe_meta_text('-'), time=gap))
            if bass: bass.append(mido.MetaMessage('text', text=_safe_meta_text('-'), time=gap))
        
        roman_slug = roman_list_to_slug(prog)
        # Create more descriptive progression labels
        progression_label = f"P{idx:02d} {roman_slug} - {key_minor} {mode}"
        chords.append(mido.MetaMessage('text', text=_safe_meta_text(progression_label), time=0))

        prev = None
        for rn in prog:
            pcs = build_chord_pcs(tonic_pc, mode, rn, use_7ths, add9)
            notes = choose_smooth_inversion(pcs, base_octave, prev_notes=prev)
            _write_chord_event(chords, notes, dur, velocity)
            if bass:
                b = _derive_bass_root(pcs, notes)
                bass.append(Message('note_on', note=b, velocity=96, time=0))
                bass.append(Message('note_off', note=b, velocity=0, time=dur))
            prev = notes

    mid.save(outfile)

    # JSON metadata (optional)
    params = {
        "key_minor": key_minor,
        "tempo_bpm": tempo_bpm,
        "bars_per_chord": bars_per_chord,
        "base_octave": base_octave,
        "velocity": velocity,
        "use_7ths": use_7ths,
        "add9": add9,
        "make_bass": make_bass
    }
    theory = {
        "key": key_minor,
        "mode": mode,
        "scale_degrees": SCALE_STEPS[mode],
        "progression_count": len(progs),
        "chord_qualities": ["triads" if not use_7ths else "7ths"]
    }
    voicing = {"add9": add9, "use_7ths": use_7ths, "bass_line": make_bass}
    total_bars = sum(len(p) for p in progs) * bars_per_chord
    timeline = {"ppq": 480, "tempo_bpm": tempo_bpm, "bars_per_chord": bars_per_chord, "total_bars": total_bars}
    tags = ["melodic-house", "chord-progressions", f"{mode}-harmony", "midi-loops", "progression-pack"]
    derived = {"total_duration_seconds": total_bars * 4 * 60 / tempo_bpm,
               "complexity": "advanced" if use_7ths and add9 else ("intermediate" if use_7ths or add9 else "basic")}
    create_midi_metadata(
        script_name="make_melodic_progressions.py",
        midi_filepath=outfile,
        params=params,
        theory=theory,
        voicing=voicing,
        timeline=timeline,
        tags=tags,
        derived=derived
    )
    return outfile

# -----------------------
# Dry-run printing (root-first spellings)
# -----------------------
PITCH_NAMES = NOTE_NAMES_SHARP

def pcs_to_spelled_root_first(pcs):
    out=[]; seen=set()
    for p in pcs:
        pc = p % 12
        if pc in seen: continue
        seen.add(pc)
        out.append(PITCH_NAMES[pc])
    return "/".join(out)

def print_pack_for_key(key_minor: str, mode: str, base_octave=3, use_7ths=False, add9=False):
    tonic_pc = parse_key_minor(key_minor)
    print(f"Key={key_minor} Mode={mode}")
    for idx, prog in enumerate(pick_progressions(mode), start=1):
        spelled=[]
        prev=None
        for rn in prog:
            pcs = build_chord_pcs(tonic_pc, mode, rn, use_7ths, add9)
            # show chord tones as pitch classes (root-first order of pcs)
            rn_disp = normalize_roman_for_display(mode, rn)
            spelled.append(f"{rn_disp}:{pcs_to_spelled_root_first(pcs)}")
        print(f"P{idx:02d}: " + " | ".join(spelled))

# -----------------------
# Spell progression as lines for .txt logs (used by write_pack_for_key)
# -----------------------
def _spell_progression_lines(tonic_pc: int, mode: str, progression: list[str], use_7ths: bool, add9: bool) -> list[str]:
    spelled=[]
    for rn in progression:
        pcs = build_chord_pcs(tonic_pc, mode, rn, use_7ths, add9)
        rn_disp = normalize_roman_for_display(mode, rn)
        spelled.append(f"{rn_disp}:{pcs_to_spelled_root_first(pcs)}")
    return spelled

def export_clip_names_for_ableton(key_minor: str, mode: str, use_7ths=False, add9=False, 
                                 make_bass=False, output_file=None) -> str:
    """
    Export clip names in a format suitable for Ableton Live session view organization.
    
    Args:
        key_minor: The key (e.g., "Am", "F#m")
        mode: The harmonic mode (e.g., "aeolian", "dorian", "phrygian")
        use_7ths: Whether to use 7th chords
        add9: Whether add9 is enabled
        make_bass: Whether bass track is included
        output_file: Optional output file path for the clip names
    
    Returns:
        A formatted string with all clip names
    """
    progs = pick_progressions(mode)
    chord_type = '7ths' if use_7ths else 'triads'
    
    # Generate clip names for all progressions
    clip_names = []
    for idx, prog in enumerate(progs, start=1):
        clip_name = generate_clip_name(key_minor, mode, prog, chord_type, add9, make_bass, idx)
        clip_names.append(f"P{idx:02d}: {clip_name}")
    
    # Create the output content
    output_content = f"""# Clip Names for {key_minor} {mode} Progression Pack
# Generated by make_melodic_progressions.py
# Chord Type: {chord_type}
# Add9: {add9}
# Bass: {make_bass}

"""
    
    # Add clip names
    for clip_name in clip_names:
        output_content += f"{clip_name}\n"
    
    # Add summary
    output_content += f"""
# Summary
# Total Progressions: {len(progs)}
# Key: {key_minor}
# Mode: {mode}
# Chord Type: {chord_type}
# Add9: {add9}
# Bass: {make_bass}
"""
    
    # Write to file if specified
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output_content)
        print(f"Clip names exported to: {output_file}")
    
    return output_content

def generate_progression_summary(mode: str, use_7ths=False, add9=False, make_bass=False) -> str:
    """
    Generate a comprehensive summary of all available progressions for a given mode.
    
    Args:
        mode: The harmonic mode (e.g., "aeolian", "dorian", "phrygian")
        use_7ths: Whether to use 7th chords
        add9: Whether add9 is enabled
        make_bass: Whether bass track is included
    
    Returns:
        A formatted string with progression summary
    """
    progs = pick_progressions(mode)
    chord_type = '7ths' if use_7ths else 'triads'
    
    # Create the summary content
    summary = f"""# Progression Summary for {mode.title()} Mode
# Generated by make_melodic_progressions.py
# Chord Type: {chord_type}
# Add9: {add9}
# Bass: {make_bass}
# Total Progressions: {len(progs)}

"""
    
    # Add each progression with its details
    for idx, prog in enumerate(progs, start=1):
        progression_slug = roman_list_to_slug(prog)
        summary += f"## P{idx:02d}: {progression_slug}\n"
        summary += f"- **Progression**: {progression_slug}\n"
        summary += f"- **Length**: {len(prog)} chords\n"
        summary += f"- **Clip Name**: {generate_clip_name('Key', mode, prog, chord_type, add9, make_bass, idx)}\n"
        summary += f"- **Roman Numerals**: {', '.join(prog)}\n\n"
    
    # Add mode-specific information
    summary += f"## Mode Information\n"
    summary += f"- **Mode**: {mode.title()}\n"
    summary += f"- **Scale Steps**: {SCALE_STEPS[mode]}\n"
    summary += f"- **Triad Qualities**: {TRIAD_QUALITIES[mode]}\n"
    if use_7ths:
        summary += f"- **7th Qualities**: {SEVENTH_QUALITIES[mode]}\n"
    
    return summary

def export_progression_summary(mode: str, use_7ths=False, add9=False, make_bass=False, 
                              output_file=None) -> str:
    """
    Export a progression summary to a file.
    
    Args:
        mode: The harmonic mode (e.g., "aeolian", "dorian", "phrygian")
        use_7ths: Whether to use 7th chords
        add9: Whether add9 is enabled
        make_bass: Whether bass track is included
        output_file: Optional output file path
    
    Returns:
        The summary content as a string
    """
    summary = generate_progression_summary(mode, use_7ths, add9, make_bass)
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        print(f"Progression summary exported to: {output_file}")
    
    return summary

# -----------------------
# Public API
# -----------------------
def write_pack_for_key(
    key_minor: str, mode: str, outfile_prefix: str, tempo_bpm=122, bars_per_chord=1,
    base_octave=3, velocity=90, use_7ths=False, add9=False, make_bass=False,
    split=False
):
    progs = pick_progressions(mode)
    base = build_outfile_basename(key_minor, mode, use_7ths)
    out_dir = "out/midi-pack"
    # Generate a unique timestamp for this session to avoid filename conflicts
    timestamp = int(time.time())

    if split:
        for idx, prog in enumerate(progs, start=1):
            # Numbered prefix + Camelot basename
            numbered = f"{idx:02d}_{base}"
            outfile = os.path.join(out_dir, f"{numbered}.mid")
            ensure_outdir(outfile)

            # Build a per-progression dry-run mirror and write .txt
            tonic_pc = parse_key_minor(key_minor)
            log_lines = _spell_progression_lines(tonic_pc, mode, prog, use_7ths, add9)
            logfile = os.path.join(out_dir, f"{numbered}.txt")
            write_txt_log(logfile, header=f"Key={key_minor} Mode={mode}", lines=[" | ".join(log_lines)])

            _write_single_progression_midi(
                key_minor, mode, prog, outfile, tempo_bpm, bars_per_chord,
                base_octave, velocity, use_7ths, add9, make_bass
            )
    else:
        base = build_outfile_basename(key_minor, mode, use_7ths)
        outfile = os.path.join(out_dir, f"{base}.mid")
        ensure_outdir(outfile)

        # Also mirror a combined dry-run into a .txt next to the .mid
        tonic_pc = parse_key_minor(key_minor)
        combined_lines = []
        for idx, prog in enumerate(progs, start=1):
            spelled = _spell_progression_lines(tonic_pc, mode, prog, use_7ths, add9)
            combined_lines.append(f"P{idx:02d}: " + " | ".join(spelled))
        logfile = os.path.join(out_dir, f"{base}.txt")
        write_txt_log(logfile, header=f"Key={key_minor} Mode={mode}", lines=combined_lines)

        _write_all_progressions_midi(
            key_minor, mode, progs, outfile, tempo_bpm, bars_per_chord,
            base_octave, velocity, use_7ths, add9, make_bass
        )

# -----------------------
# CLI
# -----------------------
def main():
    ap = argparse.ArgumentParser(description="Melodic House & Techno progression pack generator (Aeolian/Dorian/Phrygian/Persian)")
    ap.add_argument("--keys", default="G#m,F#m,Em,D#m,C#m,Am,Gm,Fm,D,C#,E,G",
                    help="Comma-separated list of keys (e.g., 'G#m,Am,F#m')")
    ap.add_argument("--mode", default="aeolian", choices=["aeolian","dorian","phrygian","persian"], help="Harmonic mode")
    ap.add_argument("--bpm", type=int, default=122)
    ap.add_argument("--bars", type=int, default=1, help="Bars per chord")
    ap.add_argument("--oct", type=int, default=3, help="Base octave for chord stack")
    ap.add_argument("--vel", type=int, default=90, help="Chord velocity")
    ap.add_argument("--sevenths", action="store_true", help="Use 7th chords")
    ap.add_argument("--add9", action="store_true", help="Add add9 color tones")
    ap.add_argument("--bass", action="store_true", help="Add root-note bass track")
    ap.add_argument("--split", action="store_true", help="Export one MIDI per progression")
    ap.add_argument("--dry-run", action="store_true", help="Print chords only; do not write MIDI/JSON")
    ap.add_argument("--export-clip-names", action="store_true", help="Export clip names for Ableton Live organization")
    ap.add_argument("--clip-names-file", help="Output file for clip names (default: auto-generated)")
    ap.add_argument("--export-summary", action="store_true", help="Export progression summary for session planning")
    ap.add_argument("--summary-file", help="Output file for progression summary (default: auto-generated)")
    ap.add_argument("--prefix", default="melodic_pack", help="Output filename prefix")
    args = ap.parse_args()

    # Handle summary export first (mode-specific, not key-specific)
    if args.export_summary:
        if args.summary_file:
            summary_file = args.summary_file
        else:
            # Auto-generate filename
            chord_type = '7ths' if args.sevenths else 'triads'
            add9_suffix = '_add9' if args.add9 else ''
            bass_suffix = '_bass' if args.bass else ''
            summary_file = f"progression_summary_{args.mode}_{chord_type}{add9_suffix}{bass_suffix}.md"
        
        summary_content = export_progression_summary(
            args.mode, args.sevenths, args.add9, args.bass, summary_file
        )
        print(f"Progression summary exported for {args.mode} mode")
        return

    keys = [k.strip() for k in args.keys.split(",") if k.strip()]
    for k in keys:
        if args.dry_run:
            print_pack_for_key(k, args.mode, base_octave=args.oct, use_7ths=args.sevenths, add9=args.add9)
            continue
        
        # Export clip names if requested
        if args.export_clip_names:
            if args.clip_names_file:
                clip_names_file = args.clip_names_file
            else:
                # Auto-generate filename
                key_clean = k.replace('#', 's').replace('♯', 's').replace('♭', 'b')
                chord_type = '7ths' if args.sevenths else 'triads'
                add9_suffix = '_add9' if args.add9 else ''
                bass_suffix = '_bass' if args.bass else ''
                clip_names_file = f"clip_names_{key_clean}_{args.mode}_{chord_type}{add9_suffix}{bass_suffix}.txt"
            
            clip_names_content = export_clip_names_for_ableton(
                k, args.mode, args.sevenths, args.add9, args.bass, clip_names_file
            )
            print(f"Clip names exported for {k} {args.mode}")
            continue
        
        out_prefix = f"{args.prefix}_{k.replace('#','s')}"
        write_pack_for_key(
            key_minor=k,
            mode=args.mode,
            outfile_prefix=out_prefix,
            tempo_bpm=args.bpm,
            bars_per_chord=args.bars,
            base_octave=args.oct,
            velocity=args.vel,
            use_7ths=args.sevenths,
            add9=args.add9,
            make_bass=args.bass,
            split=args.split
        )
        print("Wrote:", out_prefix)

if __name__ == "__main__":
    main()