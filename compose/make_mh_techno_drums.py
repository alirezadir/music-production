import argparse, random
import mido
from mido import MidiFile, MidiTrack, Message
from json_metadata import create_midi_metadata

# ---------------------------
# GM-ish Drum Map (works fine with most drum racks)
# ---------------------------
GM = dict(
    KICK=36,
    SNARE=38,
    CLAP=39,
    CH=42,      # Closed Hat
    PH=44,      # Pedal Hat
    OH=46,      # Open Hat
    LTOM=45,    # Low Tom
    MTOM=47,    # Mid Tom
    HTOM=50,    # High Tom
    RIDE=51,
    TAMBO=54,   # Tambourine
    CONGA_H=63, # High Conga
    CONGA_M=62,
    CONGA_L=64,
    SHAKER=82,  # Shaker
    COWBELL=56,
    CABASA=69
)

# ---------------------------
# Groove helpers
# ---------------------------
def bpm_to_tempo(bpm:int)->int:
    return int(60_000_000 / bpm)

def swing_offset(tpb:int, sixteenth_idx:int, swing=0.56)->int:
    # swing even sixteenths (2,4,6..)
    if swing <= 0: return 0
    return int((tpb / 4) * swing) if (sixteenth_idx % 2 == 1) else 0

def humanize_ticks(max_abs:int, rng)->int:
    return 0 if max_abs<=0 else rng.randint(-max_abs, max_abs)

def add_note(track, typ, note, vel, dt):
    if typ == "on":
        track.append(Message('note_on', note=note, velocity=max(1, min(127, vel)), time=max(0, dt)))
    else:
        track.append(Message('note_off', note=note, velocity=0, time=max(1, dt)))

# ---------------------------
# Pattern primitives (bars -> 16th grid)
# ---------------------------
def grid_events(pattern_16ths, note, tpb, velocity=100, swing=0.0, human=3, rng=None):
    """
    pattern_16ths: list of length (bars*16), elements are velocity multipliers or 0 (rest)
    Emits pairs of (on, off) with 16th note length by default (gate 90%).
    
    FIXED: Now properly calculates cumulative timing for each step position
    so kicks appear on beats 1,2,3,4 instead of every 16th note.
    """
    rng = rng or random.Random()
    events=[]
    gate = int((tpb/4) * 0.9)  # 90% of 16th
    
    for i, val in enumerate(pattern_16ths):
        if not val: continue
        
        # Calculate the actual time position of this step (16th note grid)
        step_position = int((tpb/4) * i)  # Each step is 1/16th of a bar
        
        # Add swing offset and humanization
        swing_delay = swing_offset(tpb, i, swing)
        human_delay = humanize_ticks(human, rng)
        
        # Total delay is the step position plus swing and humanization
        total_delay = step_position + swing_delay + human_delay
        
        # ON event
        events.append(("on", note, int(velocity*val), total_delay))
        # OFF event (note off happens after the gate duration)
        events.append(("off", note, 0, gate))
    
    return events

def expand_bars_16(pattern_1bar):
    return pattern_1bar[:]  # copy

def concat_bars(*bars):
    out=[]
    for b in bars:
        out+=b
    return out

def repeat_bar(bar, times):
    out=[]
    for _ in range(times): out += bar
    return out

# ---------------------------
# House/Techno pattern libraries (1 bar = 16 steps)
# Values are velocity multipliers: 0 (rest), 0.6 ghost, 1.0 accent
# ---------------------------
HOUSE_KICK = [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0]                   # four-on-the-floor
HOUSE_CLAP = [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0]                   # 2 & 4
HOUSE_CLAP_FLAM = [0,0,0,0, 0.35,0,0,0, 0,0,0,0, 0.35,0,0,0]        # pre-flams
HOUSE_CH_16 = [0.7]*16                                              # 16th hats
HOUSE_CH_ACC = [1 if i%4==0 else 0.7 for i in range(16)]            # accents each beat
HOUSE_OH_OFF = [0,0,0,0, 0,0,1,0, 0,0,0,0, 0,0,1,0]                  # open hat on offbeats (the & of 2,4)
HOUSE_RIDE_8 = [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0]                  # straight 8ths
HOUSE_SHAKER_16_SYNC = [0.8 if i%2==0 else 0.6 for i in range(16)]  # 8th + lighter off-16ths

# Afro/Middle Eastern flavors (shaker/tambo/conga syncopes)
AFRO_TAMBO = [1,0,0.7,0, 0,0.7,0,0, 1,0,0.7,0, 0,0.7,0,0]
ME_TAMBO =  [1,0,0,0.7, 0,0.7,0,0, 1,0,0,0.7, 0,0.7,0,0]            # darbuka-ish offbeats
AFRO_CONGA_H = [0,0.7,0,0, 0,0,0,0.7, 0,0.7,0,0, 0,0,0,0.7]
AFRO_CONGA_M = [0,0,0.6,0, 0,0,0,0.6, 0,0,0.6,0, 0,0,0,0.6]

# Tom fills (end of 4 or 8 bars)
FILL_TOMS_1BAR = [0,0,0,0, 0,0.7,0.7,0, 0,0.7,0.7,0, 0.7,0.7,1,1]

# Snare build roll (crescendo 4, 2, 1 bars)
def snare_roll_bar(stride_16=2, base=0.6, grow=0.2):
    """
    stride_16: play every Nth 16th (2=8ths,1=16ths)
    """
    pat=[0]*16
    vel=base
    for i in range(0,16,stride_16):
        pat[i]=vel
        vel=min(1.0, vel+grow)
    return pat

# ---------------------------
# Generator
# ---------------------------
def generate_drum_tracks(bars_total:int, tpb:int, swing:float, human:int, rng, flavor:str):
    """
    Returns dict of instrument -> events list
    """
    events = {k:[] for k in ["KICK","CLAP","SNARE","CH","OH","RIDE","SHAKER","TAMBO","TOMS","CONGA_H","CONGA_M"]}
    
    # Process each bar separately to maintain proper timing
    for bar in range(bars_total):
        # Calculate bar offset: each bar is 4 beats = 4 * tpb ticks
        bar_offset = bar * 4 * tpb
        
        # KICK (accent small variations)
        kick_bar = HOUSE_KICK[:]
        # occasional extra off-beat ghost kick (bar 7 or random)
        if bar%8 in (6,) and rng.random()<0.6:
            kick_bar[10] = max(kick_bar[10], 0.35)
        
        # Generate events for this bar with proper timing
        kick_events = grid_events(kick_bar, GM["KICK"], tpb, velocity=100, swing=swing, human=human, rng=rng)
        # Add bar offset to all events in this bar
        for event in kick_events:
            events["KICK"].append((event[0], event[1], event[2], event[3] + bar_offset))

        # CLAP + flam
        clap_bar = [max(c, f) for c,f in zip(HOUSE_CLAP, HOUSE_CLAP_FLAM)]
        clap_events = grid_events(clap_bar, GM["CLAP"], tpb, velocity=100, swing=swing, human=human, rng=rng)
        for event in clap_events:
            events["CLAP"].append((event[0], event[1], event[2], event[3] + bar_offset))

        # SNARE: lightly layer with clap hits (ghosts before/after)
        sn = [0]*16
        for i in (4, 12):
            sn[i] = 0.65
            if rng.random()<0.5: sn[max(0,i-1)] = 0.3
            if rng.random()<0.5: sn[min(15,i+1)] = 0.3
        snare_events = grid_events(sn, GM["SNARE"], tpb, velocity=100, swing=swing, human=human, rng=rng)
        for event in snare_events:
            events["SNARE"].append((event[0], event[1], event[2], event[3] + bar_offset))

        # CH hats with accent
        ch = [max(a,b) for a,b in zip(HOUSE_CH_16, HOUSE_CH_ACC)]
        ch_events = grid_events(ch, GM["CH"], tpb, velocity=100, swing=swing, human=human, rng=rng)
        for event in ch_events:
            events["CH"].append((event[0], event[1], event[2], event[3] + bar_offset))

        # OH offbeats, occasional extra
        oh = HOUSE_OH_OFF[:]
        if rng.random()<0.35: oh[7] = max(oh[7], 0.7)  # add & of 2
        oh_events = grid_events(oh, GM["OH"], tpb, velocity=100, swing=swing, human=human, rng=rng)
        for event in oh_events:
            events["OH"].append((event[0], event[1], event[2], event[3] + bar_offset))

        # RIDE (use in drops every other bar)
        ride = [0]*16 if (bar%8<4) else HOUSE_RIDE_8[:]
        ride_events = grid_events(ride, GM["RIDE"], tpb, velocity=100, swing=swing, human=human, rng=rng)
        for event in ride_events:
            events["RIDE"].append((event[0], event[1], event[2], event[3] + bar_offset))

        # SHAKER base
        shaker_events = grid_events(HOUSE_SHAKER_16_SYNC, GM["SHAKER"], tpb, velocity=100, swing=swing, human=human, rng=rng)
        for event in shaker_events:
            events["SHAKER"].append((event[0], event[1], event[2], event[3] + bar_offset))

        # TAMBO + CONGAS (flavor)
        if flavor=="afro":
            tambo_events = grid_events(AFRO_TAMBO, GM["TAMBO"], tpb, velocity=100, swing=swing, human=human, rng=rng)
            conga_h_events = grid_events(AFRO_CONGA_H, GM["CONGA_H"], tpb, velocity=100, swing=swing, human=human, rng=rng)
            conga_m_events = grid_events(AFRO_CONGA_M, GM["CONGA_M"], tpb, velocity=100, swing=swing, human=human, rng=rng)
        elif flavor=="me":
            tambo_events = grid_events(ME_TAMBO, GM["TAMBO"], tpb, velocity=100, swing=swing, human=human, rng=rng)
            conga_h_events = grid_events([0]*16, GM["CONGA_H"], tpb, velocity=100, swing=swing, human=human, rng=rng)
            conga_m_events = grid_events([0]*16, GM["CONGA_M"], tpb, velocity=100, swing=swing, human=human, rng=rng)
        else:
            tambo_events = grid_events([0]*16, GM["TAMBO"], tpb, velocity=100, swing=swing, human=human, rng=rng)
            conga_h_events = grid_events([0]*16, GM["CONGA_H"], tpb, velocity=100, swing=swing, human=human, rng=rng)
            conga_m_events = grid_events([0]*16, GM["CONGA_M"], tpb, velocity=100, swing=swing, human=human, rng=rng)
        
        # Add events with bar offset
        for event in tambo_events:
            events["TAMBO"].append((event[0], event[1], event[2], event[3] + bar_offset))
        for event in conga_h_events:
            events["CONGA_H"].append((event[0], event[1], event[2], event[3] + bar_offset))
        for event in conga_m_events:
            events["CONGA_M"].append((event[0], event[1], event[2], event[3] + bar_offset))

        # TOM fills at the end of each 8 bars
        if (bar+1)%8==0:
            toms_events = grid_events(FILL_TOMS_1BAR, GM["LTOM"], tpb, velocity=100, swing=swing, human=human, rng=rng)
        else:
            toms_events = grid_events([0]*16, GM["LTOM"], tpb, velocity=100, swing=swing, human=human, rng=rng)
        
        for event in toms_events:
            events["TOMS"].append((event[0], event[1], event[2], event[3] + bar_offset))

    return events

def generate_build_section(bars_build:int, tpb:int, swing:float, human:int, rng):
    """
    Snare roll crescendo + open hat ramps for build before drop.
    """
    out = {k:[] for k in ["SNARE","OH"]}
    if bars_build<=0: return out

    # progressively faster rolls: 8ths -> 16ths -> 16ths dense
    if bars_build == 1:
        patterns = [snare_roll_bar(stride_16=1, base=0.6, grow=0.03)]
    elif bars_build == 2:
        patterns = [snare_roll_bar(stride_16=2, base=0.6, grow=0.05),
                    snare_roll_bar(stride_16=1, base=0.75, grow=0.05)]
    else:
        patterns = [snare_roll_bar(stride_16=2, base=0.55, grow=0.06),
                    snare_roll_bar(stride_16=1, base=0.7,  grow=0.05),
                    snare_roll_bar(stride_16=1, base=0.85, grow=0.03)]

    # concatenate until reaching bars_build
    pats=[]
    for p in patterns:
        pats += p
    # trim/extend to exact bars
    target_len = bars_build*16
    if len(pats) > target_len: pats = pats[:target_len]
    if len(pats) < target_len: pats += [0]*(target_len-len(pats))

    # Generate events with proper timing
    snare_events = grid_events(pats, GM["SNARE"], tpb, velocity=112, swing=swing, human=human, rng=rng)
    
    # Add bar offsets to build section events
    for i, event in enumerate(snare_events):
        # Calculate which bar this event belongs to (16 steps per bar)
        bar_num = i // 32  # 32 events per bar (16 on + 16 off)
        bar_offset = bar_num * 4 * tpb
        out["SNARE"].append((event[0], event[1], event[2], event[3] + bar_offset))

    # OH rising (every bar last 2 sixteenths open)
    oh_pat=[]
    for b in range(bars_build):
        bar = [0]*16
        bar[14] = 0.8; bar[15] = 1.0
        oh_pat += bar
    oh_events = grid_events(oh_pat, GM["OH"], tpb, velocity=98, swing=swing, human=human, rng=rng)
    
    # Add bar offsets to OH events
    for i, event in enumerate(oh_events):
        bar_num = i // 32  # 32 events per bar (16 on + 16 off)
        bar_offset = bar_num * 4 * tpb
        out["OH"].append((event[0], event[1], event[2], event[3] + bar_offset))
    
    return out

# ---------------------------
# Write MIDI
# ---------------------------
def write_drums_midi(outfile, bpm=124, bars=8, build_bars=2, swing=0.56, human=3, seed=17, flavor="none"):
    rng = random.Random(seed)
    mid = MidiFile(ticks_per_beat=480)
    tempo = bpm_to_tempo(bpm)

    # tracks per piece
    tracks = {}
    for name in ["KICK","CLAP","SNARE","CH","OH","RIDE","SHAKER","TAMBO","TOMS","CONGA_H","CONGA_M"]:
        t = MidiTrack(); mid.tracks.append(t)
        t.append(mido.MetaMessage('set_tempo', tempo=tempo, time=0))
        t.append(mido.MetaMessage('track_name', name=name, time=0))
        tracks[name]=t

    # main loop patterns
    timed = generate_drum_tracks(bars, mid.ticks_per_beat, swing, human, rng, flavor)

    # write main
    for name, evs in timed.items():
        for typ, note, vel, dt in evs:
            add_note(tracks[name], typ, note, vel, dt)

    # build section
    if build_bars>0:
        build = generate_build_section(build_bars, mid.ticks_per_beat, swing, human, rng)
        # 1 bar gap before build for DJ cue (optional)
        gap_ticks = mid.ticks_per_beat*4
        for t in tracks.values():
            t.append(Message('note_off', note=0, velocity=0, time=gap_ticks))
        
        # Add build section events with proper timing offset
        # The build section starts after the main loop + gap
        build_start_offset = (bars * 4 * mid.ticks_per_beat) + gap_ticks
        
        for name, evs in build.items():
            for typ, note, vel, dt in evs:
                # Add the build start offset to all build events
                adjusted_dt = dt + build_start_offset
                add_note(tracks[name], typ, note, vel, adjusted_dt)

    mid.save(outfile)
    
    # Generate JSON metadata
    params = {
        "bpm": bpm,
        "bars": bars,
        "build_bars": build_bars,
        "swing": swing,
        "human": human,
        "seed": seed,
        "flavor": flavor,
        "ticks_per_beat": mid.ticks_per_beat
    }
    
    theory = {
        "style": "melodic-house-techno",
        "rhythm_type": "four-on-the-floor",
        "flavor": flavor,
        "groove_style": "house" if flavor == "none" else flavor
    }
    
    timeline = {
        "ppq": mid.ticks_per_beat,
        "tempo_bpm": bpm,
        "total_bars": bars + build_bars,
        "main_loop_bars": bars,
        "build_section_bars": build_bars
    }
    
    tags = ["melodic-house", "techno", "drum-patterns", "midi-loops"]
    if flavor != "none":
        tags.append(f"flavor-{flavor}")
    
    derived = {
        "total_duration_seconds": (bars + build_bars) * 4 * 60 / bpm,
        "pattern_complexity": "medium" if human > 2 else "simple",
        "swing_intensity": "heavy" if swing > 0.5 else "light" if swing < 0.3 else "medium"
    }
    
    create_midi_metadata(
        script_name="make_mh_techno_drums.py",
        midi_filepath=outfile,
        params=params,
        theory=theory,
        timeline=timeline,
        tags=tags,
        derived=derived
    )
    
    return outfile

# ---------------------------
# CLI
# ---------------------------
def main():
    ap = argparse.ArgumentParser(description="Melodic House & Techno Drum Generator")
    ap.add_argument("--bpm", type=int, default=124)
    ap.add_argument("--bars", type=int, default=8, help="Loop length (bars) before build")
    ap.add_argument("--build", type=int, default=2, help="Build-up bars appended after loop")
    ap.add_argument("--swing", type=float, default=0.56, help="0..0.6 swing amount")
    ap.add_argument("--human", type=int, default=3, help="+/- ticks jitter (0..12)")
    ap.add_argument("--seed", type=int, default=17)
    ap.add_argument("--flavor", default="none", choices=["none","afro","me"], help="Afro or Middle-Eastern spice")
    ap.add_argument("--outfile", default="out/midi-pack/mh_techno_drums.mid")
    args = ap.parse_args()

    path = write_drums_midi(
        outfile=args.outfile, bpm=args.bpm, bars=args.bars, build_bars=args.build,
        swing=args.swing, human=args.human, seed=args.seed, flavor=args.flavor
    )
    print("Saved:", path)

if __name__ == "__main__":
    main()