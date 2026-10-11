import argparse, random
import mido
from mido import MidiFile, MidiTrack, Message
from json_metadata import create_midi_metadata

# -----------------------
# Core “best-of” progressions (minor)
# -----------------------
PROGRESSIONS = [
    ["i","VI","VII","i"], ["i","VII","VI","VII"], ["i","VI","III","VII"], ["i","iv","VI","VII"],
    ["i","VI","iv","V"], ["i","v","VI","VII"], ["i","VI","v","VII"], ["i","VII","i","VI"],
    ["i","VI","VII","III"], ["i","iv","v","i"], ["i","bVII","bVI","i"], ["i","V","VI","VII"],
    ["i","VI","i","VII"], ["i","VI","iv","VI"], ["i","III","VI","VII"], ["i","v","i","VI"],
    ["i","VI","bVII","i"], ["i","VI","ii°","V"], ["i","VI","i","VI","VII","i"],
    ["i","iv","i","VI","VII","i"],
]

NOTE_NAMES_SHARP = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
NAME_TO_PC = {n:i for i,n in enumerate(NOTE_NAMES_SHARP)}
AEOLIAN_STEPS = [0,2,3,5,7,8,10]

# -----------------------
# Utility: keys, degrees, chord pcs
# -----------------------
def parse_key_minor(s: str) -> int:
    s = s.strip().lower().replace(" minor","").replace("minor","")
    s = s.replace("♯","#").replace("♭","b")
    if s.endswith("m"): s = s[:-1]
    flats = {"db":"C#","eb":"D#","gb":"F#","ab":"G#","bb":"A#","cb":"B","fb":"E"}
    s = flats.get(s, s).upper()
    if s not in NAME_TO_PC: raise ValueError(f"Bad key '{s}'")
    return NAME_TO_PC[s]

def degree_to_pc(tonic_pc:int, degree:int)->int:
    return (tonic_pc + AEOLIAN_STEPS[degree-1]) % 12

def roman_to_degree(roman:str)->int:
    base = roman.replace("°","").replace("b","").replace("#","")
    mp = {"i":1,"ii":2,"iii":3,"iv":4,"v":5,"vi":6,"vii":7,
          "I":1,"II":2,"III":3,"IV":4,"V":5,"VI":6,"VII":7}
    return mp[base]

def chord_quality(roman:str, use_7ths:bool)->str:
    if "ii°" in roman: return "dim7" if use_7ths else "dim"
    if roman=="V":     return "dom7" if use_7ths else "maj"
    if roman.startswith("b") and ("VI" in roman or "VII" in roman):
        return "maj7" if use_7ths else "maj"
    if roman in ("i","iv","v"):     return "min7" if use_7ths else "min"
    if roman in ("III","VI","VII"): return "maj7" if use_7ths else "maj"
    return "min7" if use_7ths else "min"

def _flat_pc(pc:int, semis:int=2)->int: return (pc - semis) % 12

def build_chord_pcs(tonic:int, roman:str, use_7ths:bool, add9:bool):
    if roman.startswith("b") and "VI" in roman:
        root = _flat_pc(degree_to_pc(tonic,6))
    elif roman.startswith("b") and "VII" in roman:
        root = _flat_pc(degree_to_pc(tonic,7))
    else:
        root = degree_to_pc(tonic, roman_to_degree(roman.replace("°","")))
    q = chord_quality(roman, use_7ths)

    def pcs_q(root_pc, q):
        if q in ("min","min7"):
            third=(root_pc+3)%12; fifth=(root_pc+7)%12; seventh=(root_pc+10)%12
            tri=[root_pc,third,fifth]; sev=[*tri,seventh]
        elif q in ("maj","maj7"):
            third=(root_pc+4)%12; fifth=(root_pc+7)%12; seventh=(root_pc+11)%12
            tri=[root_pc,third,fifth]; sev=[*tri,seventh]
        elif q=="dom7":
            third=(root_pc+4)%12; fifth=(root_pc+7)%12; seventh=(root_pc+10)%12
            tri=[root_pc,third,fifth]; sev=[*tri,seventh]
        elif q in ("dim","dim7"):
            third=(root_pc+3)%12; fifth=(root_pc+6)%12; seventh=(root_pc+9)%12
            tri=[root_pc,third,fifth]; sev=[*tri,seventh]
        else:
            tri=[root_pc,(root_pc+4)%12,(root_pc+7)%12]; sev=[*tri,(root_pc+11)%12]
        return sev if ("7" in q) else tri

    pcs = pcs_q(root, q)
    if add9:
        ninth=(root+14)%12
        if ninth not in pcs: pcs.append(ninth)
    return pcs

# -----------------------
# Voicing / inversions
# -----------------------
def build_inversion_notes(pcs, base_oct:int):
    out=[]; nt=len(pcs)
    for inv in range(nt):
        order=pcs[inv:]+pcs[:inv]
        notes=[]; n=order[0]+12*base_oct
        while n%12!=order[0]: n+=1
        notes.append(n); last=n
        for pc in order[1:]:
            m=last
            while m%12!=pc: m+=1
            if m<=last: m+=12
            notes.append(m); last=m
        out.append((inv,notes))
    return out

def choose_smooth_inversion(pcs, base_oct:int, prev=None):
    cand=build_inversion_notes(pcs, base_oct)
    if prev is None: return cand[0][1]
    return min(cand, key=lambda t: sum(abs(a-b) for a,b in zip(prev,t[1])))[1]

# -----------------------
# Groove / timing helpers
# -----------------------
def bpm_to_tempo(bpm:int)->int: return int(60_000_000/bpm)
def roman_slug(seq): return "-".join(seq)

def swing_offset(ticks_per_beat:int, sixteenth_idx:int, swing_pct:float)->int:
    """
    Swing even 16ths by delaying them a fraction of a 16th.
    swing_pct = 0.0..0.6  (0.56 ≈ classic)
    """
    # odd 16ths (2,4,6...) get delayed
    if sixteenth_idx % 2 == 1:
        return int((ticks_per_beat/4) * swing_pct)
    return 0

def humanize_ticks(max_abs:int, rng:random.Random)->int:
    if max_abs<=0: return 0
    return rng.randint(-max_abs, max_abs)

# -----------------------
# Pattern presets
# -----------------------
BASS_PATTERNS = {
    "pedal":        [1.0, 0.0, 0.0, 0.0],             # hold root per bar
    "roller":       [0.5,0.5,0.5,0.5],                # 8ths
    "chug_16":      [0.25]*8,                         # 16ths
    "syncopate":    [0.5,0.25,0.25,0.5,0.25,0.25],    # offbeats
}

ARP_STYLES = {
    "up":           lambda tones: tones,
    "down":         lambda tones: list(reversed(tones)),
    "updown":       lambda tones: tones + list(reversed(tones))[1:-1],
    "skip3":        lambda tones: tones[::2] + tones[1::2],
    "oct_bounce":   lambda tones: [*tones, *(n+12 for n in tones)],
}

MELODY_PATTERNS = {
    "call":         [0.5,0.5,1.0,0.5,0.5,1.0],
    "answer":       [0.5,0.5,0.5,0.5,1.0,1.0],
    "legato":       [1.0,1.0],
    "busy16":       [0.25]*8,
}

# -----------------------
# Layer generators
# -----------------------
def derive_scale_pcs(tonic:int, mode:str="aeolian"):
    if mode=="aeolian": steps=AEOLIAN_STEPS
    elif mode=="dorian": steps=[0,2,3,5,7,9,10]
    elif mode=="harm_minor": steps=[0,2,3,5,7,8,11]
    else: steps=AEOLIAN_STEPS
    return [(tonic + s) % 12 for s in steps]

def derive_notes_from_pcs(pcs, target_above:int):
    """Lift pcs to nearest pitches >= target_above, preserving order."""
    notes=[]; last=target_above-1
    for pc in pcs:
        n = last+1
        while n%12 != pc: n+=1
        notes.append(n); last=n
    return notes

def gen_bass(prog_romans, tonic, tpb, bars_per_chord, base_oct=2,
             pattern="roller", swing=0.0, hum_ticks=3, rng=None, velocity=96):
    rng = rng or random.Random()
    dur_map = {0.25:int(tpb), 0.5:int(tpb*2), 1.0:int(tpb*4)}
    seq=[]
    for rn in prog_romans:
        root_pc = build_chord_pcs(tonic, rn, use_7ths=False, add9=False)[0]
        root_note = root_pc + 12*base_oct
        while root_note%12!=root_pc: root_note+=1
        # expand pattern to fill one bar
        times = BASS_PATTERNS[pattern]
        total = sum(times)
        reps = int(bars_per_chord / (total/4)) if total!=0 else 1
        for _ in range(max(1,reps)):
            sixteenth_idx=0
            for dur_beats in times:
                if dur_beats==0: continue
                ticks = int(tpb*4*dur_beats/1.0)
                delay = swing_offset(tpb, sixteenth_idx, swing)
                jitter = humanize_ticks(hum_ticks, rng)
                seq.append(("on", root_note, velocity, delay + max(0,jitter)))
                seq.append(("off", root_note, 0, ticks))
                sixteenth_idx += int(dur_beats*4)
    return seq

def gen_arp(prog_notes, style="updown", step_16ths=2, gate=0.9,
            swing=0.0, hum_ticks=3, rng=None, velocity=88):
    """
    prog_notes: list of voiced chord note lists per chord event (from inversions)
    step_16ths: 1=16ths, 2=8ths, 4=quarters
    """
    rng = rng or random.Random()
    seq=[]; tpb=480  # will be replaced by caller’s mid.ticks_per_beat if needed
    for chord in prog_notes:
        tones = sorted(set([n%12 for n in chord]))  # chord pcs
        # build register around upper-mid
        ladder = []
        for o in range(2):  # 2 octaves
            ladder += [pc + 12*(4+o) for pc in tones]
        # style mapping
        order = ARP_STYLES.get(style, ARP_STYLES["updown"])(ladder)
        # emit 1 bar of arps per chord input
        ticks_per_step = int((tpb*4)/ (16/step_16ths))
        note_len = int(ticks_per_step*gate)
        steps = max(1, int((tpb*4)/ticks_per_step))
        sixteenth_idx=0
        idx=0
        for _ in range(steps):
            p = order[idx % len(order)]
            delay = swing_offset(tpb, sixteenth_idx, swing) + humanize_ticks(hum_ticks, rng)
            seq.append(("on", p, velocity, delay))
            seq.append(("off", p, 0, note_len))
            sixteenth_idx += step_16ths
            idx += 1
    return seq

def gen_melody(prog_notes, scale_pcs, density="medium",
               swing=0.0, hum_ticks=4, rng=None, velocity=(82,110)):
    """
    Melodic strategy: chord tones on strong beats, scale passing tones on weak beats.
    """
    rng = rng or random.Random()
    tpb=480
    # density -> step size and phrase
    if density=="sparse": pat=[1.0,1.0]     # quarters
    elif density=="busy": pat=[0.5]*8       # 8ths across bar
    else: pat=[0.5,0.5,1.0,1.0]             # MH&T friendly

    seq=[]; sixteenth_idx=0
    for chord in prog_notes:
        chord_pcs = sorted(set([n%12 for n in chord]))
        upper = max(chord) + 2
        # build a register for melody (above chords)
        pool_chord = derive_notes_from_pcs(chord_pcs, upper)
        pool_scale = derive_notes_from_pcs(scale_pcs, upper-5)

        for dur in pat:
            ticks = int(tpb*4*dur)
            # pick source: 70% chord tone on strong beats, else scale passing
            use_chord = (dur>=1.0) or (rng.random()<0.7)
            pool = pool_chord if use_chord else pool_scale
            n = rng.choice(pool)
            delay = swing_offset(tpb, sixteenth_idx, swing) + humanize_ticks(hum_ticks, rng)
            vel = rng.randint(velocity[0], velocity[1])
            seq.append(("on", n, vel, delay))
            seq.append(("off", n, 0, ticks))
            sixteenth_idx += int(dur*4)
    return seq

# -----------------------
# MIDI writing
# -----------------------
def apply_events(track:MidiTrack, events, tpb):
    """
    events: list of tuples ("on"/"off", note, velocity, time_delta_ticks)
    Assumes each pair on/off follows with 'time' for note_off as duration.
    """
    for typ, note, vel, dt in events:
        if typ=="on":
            track.append(Message('note_on', note=note, velocity=vel, time=max(0, dt)))
        else:
            track.append(Message('note_off', note=note, velocity=0, time=max(1, dt)))

def write_full_clip_for_progression(
    key_minor, progression, outfile, tempo_bpm, bars_per_chord,
    base_oct_chords, use_7ths, add9, swing, human_ticks, seed,
    bass_style, arp_style, arp_rate16, arp_gate, melody_density,
    add_bass, add_arp, add_melody
):
    rng = random.Random(seed)
    tonic = parse_key_minor(key_minor)
    mid = MidiFile(ticks_per_beat=480)

    # tempo
    tempo = bpm_to_tempo(tempo_bpm)

    # chords track: voiced with inversions
    tr_ch = MidiTrack(); mid.tracks.append(tr_ch)
    tr_ch.append(mido.MetaMessage('set_tempo', tempo=tempo, time=0))
    tr_ch.append(mido.MetaMessage('track_name', name=f"Chords - {key_minor} ({roman_slug(progression)})", time=0))

    # prepare voiced chords one bar each
    tpb = mid.ticks_per_beat
    dur = tpb*4*bars_per_chord
    voiced=[]; prev=None
    for rn in progression:
        pcs = build_chord_pcs(tonic, rn, use_7ths, add9)
        notes = choose_smooth_inversion(pcs, base_oct_chords, prev)
        # write chord block (no swing on sustained pads)
        for i,n in enumerate(notes):
            tr_ch.append(Message('note_on', note=n, velocity=88, time=0 if i else 0))
        first_off=True
        for n in notes:
            tr_ch.append(Message('note_off', note=n, velocity=0, time=dur if first_off else 0))
            first_off=False
        voiced.append(notes)
        prev = notes

    # optional layers
    if add_bass:
        tr_b = MidiTrack(); mid.tracks.append(tr_b)
        tr_b.append(mido.MetaMessage('set_tempo', tempo=tempo, time=0))
        tr_b.append(mido.MetaMessage('track_name', name="Bass", time=0))
        events = gen_bass(progression, tonic, tpb, bars_per_chord,
                          base_oct=2, pattern=bass_style, swing=swing,
                          hum_ticks=human_ticks, rng=rng, velocity=96)
        apply_events(tr_b, events, tpb)

    if add_arp:
        tr_a = MidiTrack(); mid.tracks.append(tr_a)
        tr_a.append(mido.MetaMessage('set_tempo', tempo=tempo, time=0))
        tr_a.append(mido.MetaMessage('track_name', name=f"Arp ({arp_style})", time=0))
        events = gen_arp(voiced, style=arp_style, step_16ths=arp_rate16,
                         gate=arp_gate, swing=swing, hum_ticks=human_ticks,
                         rng=rng, velocity=88)
        apply_events(tr_a, events, tpb)

    if add_melody:
        tr_m = MidiTrack(); mid.tracks.append(tr_m)
        tr_m.append(mido.MetaMessage('set_tempo', tempo=tempo, time=0))
        tr_m.append(mido.MetaMessage('track_name', name=f"Melody ({melody_density})", time=0))
        scale_pcs = derive_scale_pcs(tonic, mode="aeolian")
        events = gen_melody(voiced, scale_pcs, density=melody_density,
                            swing=swing, hum_ticks=human_ticks, rng=rng,
                            velocity=(82,110))
        apply_events(tr_m, events, tpb)

    mid.save(outfile)
    
    # Generate JSON metadata
    params = {
        "key_minor": key_minor,
        "tempo_bpm": tempo_bpm,
        "bars_per_chord": bars_per_chord,
        "base_oct_chords": base_oct_chords,
        "use_7ths": use_7ths,
        "add9": add9,
        "swing": swing,
        "human_ticks": human_ticks,
        "seed": seed,
        "bass_style": bass_style,
        "arp_style": arp_style,
        "arp_rate16": arp_rate16,
        "arp_gate": arp_gate,
        "melody_density": melody_density,
        "add_bass": add_bass,
        "add_arp": add_arp,
        "add_melody": add_melody
    }
    
    theory = {
        "key": key_minor,
        "mode": "aeolian",
        "scale_degrees": [0,2,3,5,7,8,10],
        "progression": progression,
        "chord_qualities": ["triads" if not use_7ths else "7ths"]
    }
    
    voicing = {
        "add9": add9,
        "use_7ths": use_7ths,
        "base_octave": base_oct_chords
    }
    
    timeline = {
        "ppq": tpb,
        "tempo_bpm": tempo_bpm,
        "bars_per_chord": bars_per_chord,
        "total_bars": len(progression) * bars_per_chord
    }
    
    tags = ["melodic-house", "techno", "chord-progressions", "midi-loops", "multi-track"]
    if add_bass:
        tags.append("bass")
    if add_arp:
        tags.append("arp")
    if add_melody:
        tags.append("melody")
    
    derived = {
        "total_duration_seconds": len(progression) * bars_per_chord * 4 * 60 / tempo_bpm,
        "complexity": "advanced" if use_7ths and add9 else "intermediate" if use_7ths or add9 else "basic",
        "track_count": 1 + (1 if add_bass else 0) + (1 if add_arp else 0) + (1 if add_melody else 0)
    }
    
    create_midi_metadata(
        script_name="make_melodic_ht_ideas.py",
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
# CLI
# -----------------------
def main():
    ap = argparse.ArgumentParser(description="Melodic House & Techno idea generator (chords+bass+arp+melody)")
    ap.add_argument("--keys", default="G#m,F#m,Em,D#m,C#m,Am,Gm,Fm",
                    help="Comma-separated keys (minor). e.g., 'G#m,C#m'")
    ap.add_argument("--bpm", type=int, default=122)
    ap.add_argument("--bars", type=int, default=1, help="Bars per chord")
    ap.add_argument("--oct", type=int, default=3, help="Chord base octave")
    ap.add_argument("--sevenths", action="store_true")
    ap.add_argument("--add9", action="store_true")
    ap.add_argument("--swing", type=float, default=0.0, help="0..0.6 (swing on even 16ths)")
    ap.add_argument("--human", type=int, default=3, help="+/- ticks jitter (0-12)")
    ap.add_argument("--seed", type=int, default=17, help="Random seed for reproducibility")

    ap.add_argument("--bass", action="store_true", help="Add bass track")
    ap.add_argument("--bass_style", default="roller", choices=list(BASS_PATTERNS.keys()))
    ap.add_argument("--arp", action="store_true", help="Add arp track")
    ap.add_argument("--arp_style", default="updown", choices=list(ARP_STYLES.keys()))
    ap.add_argument("--arp_rate16", type=int, default=2, choices=[1,2,4], help="1=16ths,2=8ths,4=quarters")
    ap.add_argument("--arp_gate", type=float, default=0.9)
    ap.add_argument("--melody", action="store_true", help="Add melody track")
    ap.add_argument("--melody_density", default="medium", choices=["sparse","medium","busy"])

    ap.add_argument("--progressions", default="1-5",
                    help="Which progressions to render (e.g., '1-5,8,12'). 1-indexed.")
    ap.add_argument("--prefix", default="mh_ideas", help="Output prefix")
    ap.add_argument("--split", action="store_true", help="One MIDI per progression per key")
    args = ap.parse_args()

    # choose progressions
    chosen=[]
    parts = [p.strip() for p in args.progressions.split(",")]
    for part in parts:
        if "-" in part:
            a,b = part.split("-")
            for i in range(int(a), int(b)+1): chosen.append(i)
        elif part.isdigit():
            chosen.append(int(part))
    chosen = sorted(set([i for i in chosen if 1 <= i <= len(PROGRESSIONS)]))

    keys = [k.strip() for k in args.keys.split(",") if k.strip()]
    for key in keys:
        for idx in chosen:
            prog = PROGRESSIONS[idx-1]
            name = f"{args.prefix}_{key.replace('#','s')}_p{idx:02d}_{roman_slug(prog)}.mid"
            write_full_clip_for_progression(
                key_minor=key, progression=prog, outfile=name, tempo_bpm=args.bpm,
                bars_per_chord=args.bars, base_oct_chords=args.oct,
                use_7ths=args.sevenths, add9=args.add9, swing=args.swing,
                human_ticks=args.human, seed=args.seed,
                bass_style=args.bass_style, arp_style=args.arp_style,
                arp_rate16=args.arp_rate16, arp_gate=args.arp_gate,
                melody_density=args.melody_density,
                add_bass=args.bass, add_arp=args.arp, add_melody=args.melody
            )
            if not args.split:
                # if not split, you can later concatenate; for simplicity we just output separate files
                pass

if __name__ == "__main__":
    main()