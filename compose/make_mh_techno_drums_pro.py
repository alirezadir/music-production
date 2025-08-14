import argparse, random
import mido
from mido import MidiFile, MidiTrack, Message
import os

# ======================
# GM-ish Drum Map
# ======================
GM = dict(
    KICK=36, SNARE=38, CLAP=39,
    CH=42, PH=44, OH=46,
    LTOM=45, MTOM=47, HTOM=50,
    RIDE=51, TAMBO=54, COWBELL=56,
    CONGA_M=62, CONGA_H=63, CONGA_L=64,
    SHAKER=82, CABASA=69,
    SC=37   # Sidechain trigger (rimshot/ghost channel)
)

# ======================
# Timing helpers
# ======================
def bpm_to_tempo(bpm:int)->int: return int(60_000_000 / bpm)

def swing_offset(tpb:int, sixteenth_idx:int, swing=0.0)->int:
    if swing <= 0: return 0
    # Only apply swing to offbeat 16ths (steps 1,3,5,7,9,11,13,15)
    # This ensures beats 1,2,3,4 (steps 0,4,8,12) stay on the grid
    return int((tpb//4)*swing) if (sixteenth_idx % 2 == 1) else 0

def humanize_ticks(max_abs:int, rng)->int:
    return 0 if max_abs <= 0 else rng.randint(-max_abs, max_abs)

def add_note(track, typ, note, vel, dt):
    if typ == "on":
        track.append(Message('note_on', note=note, velocity=max(1,min(127,vel)), time=max(0,dt)))
    else:
        track.append(Message('note_off', note=note, velocity=0, time=max(1,dt)))

# ======================
# Base 1-bar patterns (16th grid values = velocity multipliers)
# ======================
P_HOUSE_KICK   = [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0]  # Four-on-the-floor
P_HOUSE_CLAP   = [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0]  # Beats 2 & 4
P_CLAP_FLAM    = [0,0,0,0.35, 0,0,0,0, 0,0,0,0.35, 0,0,0,0]  # Pre-flams one 16th before beats 2 & 4 (steps 3,11)
P_CH_16_ACC = [
    1.00,0.40,0.70,0.40,
    0.90,0.40,0.70,0.40,
    1.00,0.40,0.70,0.40,
    0.90,0.40,0.70,0.40
]  # 16ths: strong on beats, medium on even 16ths, light on offs

P_OH_OFF = [
    0,0,1,0,
    0,0,1,0,
    0,0,1,0,
    0,0,1,0
]  # Open-hat offbeat 8ths (steps 2,6,10,14)
P_RIDE_8       = [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0]  # Eighth notes (steps 0,2,4,6,8,10,12,14)
P_SHAKER_16    = [0.85 if i%2==0 else 0.6 for i in range(16)]  # Every other step (8ths + 16ths)
P_TAMBO_AFRO   = [1,0,0.7,0, 0,0.7,0,0, 1,0,0.7,0, 0,0.7,0,0]  # Afro syncopation
P_TAMBO_ME     = [1,0,0,0.7, 0,0.7,0,0, 1,0,0,0.7, 0,0.7,0,0]  # Middle-Eastern offbeats
P_CONGA_H_AFRO = [0,0.7,0,0, 0,0,0,0.7, 0,0.7,0,0, 0,0,0,0.7]  # Afro conga high
P_CONGA_M_AFRO = [0,0,0.6,0, 0,0,0,0.6, 0,0,0.6,0, 0,0,0,0.6]  # Afro conga mid
P_TOMS_FILL    = [0,0,0,0, 0,0.7,0.7,0, 0,0.7,0.7,0, 0.7,0.7,1,1]  # Tom fill at end

def snare_roll_bar(stride_16=2, base=0.6, grow=0.2):
    pat=[0]*16; vel=base
    for i in range(0,16,stride_16):
        pat[i]=vel; vel=min(1.0, vel+grow)
    return pat

# ======================
# Variant library (per-instrument base pattern & tweaks)
# ======================
VARIANTS = {
    "classic": {
        "KICK": P_HOUSE_KICK,
        "CLAP": [max(a,b) for a,b in zip(P_HOUSE_CLAP, P_CLAP_FLAM)],
        "SNARE": None,     # layered by prob engine near claps
        "CH":   P_CH_16_ACC,
        "OH":   P_OH_OFF,
        "RIDE": [0]*16,
        "SHAKER": P_SHAKER_16,
        "TAMBO": [0]*16,
        "CONGA_H": [0]*16,
        "CONGA_M": [0]*16
    },
    "berlin": {  # tighter hats, fewer OH, rides in drops
        "KICK": P_HOUSE_KICK,
        "CLAP": P_HOUSE_CLAP,
        "SNARE": None,
        "CH":   [0.9 if i%2==0 else 0.5 for i in range(16)],   # bright 8ths + light 16ths
        "OH":   [0,0,0,0, 0,0,0.85,0, 0,0,0,0, 0,0,0.85,0],
        "RIDE": [0]*16,
        "SHAKER": [0.75 if i%2==0 else 0.55 for i in range(16)],
        "TAMBO": [0]*16,
        "CONGA_H": [0]*16,
        "CONGA_M": [0]*16
    },
    "afterlife": {  # wide OH, airy shaker; rides post-break
        "KICK": P_HOUSE_KICK,
        "CLAP": [max(a,b) for a,b in zip(P_HOUSE_CLAP, P_CLAP_FLAM)],
        "SNARE": None,
        "CH":   [1 if i%4==0 else 0.66 for i in range(16)],
        "OH":   [0,0,0,0, 0,0,1,0, 0,0,0.85,0, 0,0,1,0],
        "RIDE": [0]*16,
        "SHAKER": [0.88 if i%2==0 else 0.64 for i in range(16)],
        "TAMBO": [0]*16,
        "CONGA_H": [0]*16,
        "CONGA_M": [0]*16
    },
    "progressive": {  # rides on drops, more constant energy
        "KICK": P_HOUSE_KICK,
        "CLAP": P_HOUSE_CLAP,
        "SNARE": None,
        "CH":   [0.85 if i%2==0 else 0.6 for i in range(16)],
        "OH":   [0,0,0,0, 0,0,0.9,0, 0,0,0,0, 0,0,0.9,0],
        "RIDE": P_RIDE_8,
        "SHAKER": P_SHAKER_16,
        "TAMBO": [0]*16,
        "CONGA_H": [0]*16,
        "CONGA_M": [0]*16
    },
    "afro": {  # adds tambourine + congas
        "KICK": P_HOUSE_KICK,
        "CLAP": P_HOUSE_CLAP,
        "SNARE": None,
        "CH":   P_CH_16_ACC,
        "OH":   P_OH_OFF,
        "RIDE": [0]*16,
        "SHAKER": P_SHAKER_16,
        "TAMBO": P_TAMBO_AFRO,
        "CONGA_H": P_CONGA_H_AFRO,
        "CONGA_M": P_CONGA_M_AFRO
    },
    "me": {  # Middle-Eastern tambo phrasing
        "KICK": P_HOUSE_KICK,
        "CLAP": P_HOUSE_CLAP,
        "SNARE": None,
        "CH":   P_CH_16_ACC,
        "OH":   P_OH_OFF,
        "RIDE": [0]*16,
        "SHAKER": P_SHAKER_16,
        "TAMBO": P_TAMBO_ME,
        "CONGA_H": [0]*16,
        "CONGA_M": [0]*16
    },
}

# ======================
# Probability profiles (per section)
# ======================
PROB_PROFILES = {
    # values: base_on_prob, ghost_prob, dropout_prob, vel_accent, vel_ghost
    "intro":     dict(on=0.6, ghost=0.2, drop=0.15, accent=100, ghostv=60),
    "build":     dict(on=0.8, ghost=0.25, drop=0.05, accent=104, ghostv=64),
    "drop":      dict(on=0.95, ghost=0.3, drop=0.0,  accent=110, ghostv=68),
    "breakdown": dict(on=0.5, ghost=0.3, drop=0.35, accent=96,  ghostv=58),
    "outro":     dict(on=0.65, ghost=0.2, drop=0.15, accent=98,  ghostv=60),
}

# Per-instrument multipliers (how active each instrument is, by section)
SECTION_ACTIVITY = {
    "intro":     {"KICK":1.0, "CLAP":0.0, "SNARE":0.2, "CH":0.7, "OH":0.2, "RIDE":0.0,
                  "SHAKER":0.6, "TAMBO":0.3, "CONGA_H":0.2, "CONGA_M":0.2, "TOMS":0.0},
    "build":     {"KICK":1.0, "CLAP":0.9, "SNARE":0.8, "CH":0.9, "OH":0.7, "RIDE":0.2,
                  "SHAKER":0.9, "TAMBO":0.4, "CONGA_H":0.4, "CONGA_M":0.4, "TOMS":0.2},
    "drop":      {"KICK":1.0, "CLAP":1.0, "SNARE":0.4, "CH":1.0, "OH":1.0, "RIDE":0.7,
                  "SHAKER":1.0, "TAMBO":0.3, "CONGA_H":0.3, "CONGA_M":0.3, "TOMS":0.4},
    "breakdown": {"KICK":0.5, "CLAP":0.2, "SNARE":0.6, "CH":0.5, "OH":0.1, "RIDE":0.0,
                  "SHAKER":0.7, "TAMBO":0.3, "CONGA_H":0.3, "CONGA_M":0.3, "TOMS":0.0},
    "outro":     {"KICK":0.9, "CLAP":0.5, "SNARE":0.3, "CH":0.7, "OH":0.2, "RIDE":0.0,
                  "SHAKER":0.7, "TAMBO":0.3, "CONGA_H":0.2, "CONGA_M":0.2, "TOMS":0.0},
}

# Section templates (bars each)
ARRANGEMENTS = {
    "standard": [("intro",8),("build",4),("drop",16),("breakdown",8),("drop",16),("outro",8)],
    "dj_friendly": [("intro",16),("build",8),("drop",16),("breakdown",8),("drop",16),("outro",16)],
    "compact": [("intro",4),("build",4),("drop",16),("outro",4)],
}

# ======================
# Pattern to events with probability engine
# ======================
def pattern_to_events(pattern_16ths, note, tpb, rng, section_name, swing=0.56, human=1, activity_mult=1.0, base_vel=100, bar_start_ticks=0):
    prof = PROB_PROFILES[section_name]
    events=[]
    sixteenth = tpb//4  # Each 16th note = tpb/4 ticks
    gate = int(sixteenth*0.9)

    for i, mul in enumerate(pattern_16ths):
        if mul <= 0: continue
        # dropout
        if rng.random() < prof["drop"]*(1.0-activity_mult):
            continue
        # decide on vs ghost
        is_on = rng.random() < (prof["on"]*activity_mult)
        if not is_on and rng.random() < prof["ghost"]*activity_mult:
            vel = int(prof["ghostv"] * mul)
        elif is_on:
            vel = int(prof["accent"] * mul)
        else:
            continue

        # Calculate position: each step i is at position i * (tpb//4) ticks from bar start
        # This ensures steps 0,4,8,12 (beats 1,2,3,4) are at 0, tpb, 2*tpb, 3*tpb
        base_pos = bar_start_ticks + sixteenth*i
        swing_adjust = swing_offset(tpb, i, swing)
        human_adjust = humanize_ticks(human, rng)
        abs_on = base_pos + swing_adjust + human_adjust
        abs_off = abs_on + gate

        events.append(("on", note, vel, abs_on))
        events.append(("off", note, 0,   abs_off))
    return events

def merge_one_bar(base_pat, extra_pat=None):
    if extra_pat is None: return base_pat[:]
    return [max(a,b) for a,b in zip(base_pat, extra_pat)]

# ======================
# Section/bar generation
# ======================
def generate_section_bars(variant:str, section_name:str, bars:int, tpb:int, rng, swing, human, section_start_ticks=0):
    base = VARIANTS[variant]
    act = SECTION_ACTIVITY[section_name]
    ev = {k:[] for k in ["KICK","CLAP","SNARE","CH","OH","RIDE","SHAKER","TAMBO","CONGA_H","CONGA_M","TOMS"]}

    for bar in range(bars):
        bar_start = section_start_ticks + bar * 4 * tpb
        # KICK (ghost at step 10 sometimes in build/drop)
        kick_bar = base["KICK"][:]
        if section_name in ("build","drop") and rng.random()<0.35:
            kick_bar[10] = max(kick_bar[10], 0.35)
        ev["KICK"].extend(pattern_to_events(kick_bar, GM["KICK"], tpb, rng, section_name, swing, human, act["KICK"], bar_start))

        # CLAP
        ev["CLAP"].extend(pattern_to_events(base["CLAP"], GM["CLAP"], tpb, rng, section_name, swing, human, act["CLAP"], bar_start))

        # SNARE (around 2/4)
        sn = [0]*16
        if act["SNARE"]>0:
            for i in (4,12):
                sn[i] = 0.6
                if rng.random()<0.5: sn[max(0,i-1)] = max(sn[max(0,i-1)], 0.3)
                if rng.random()<0.5: sn[min(15,i+1)] = max(sn[min(15,i+1)], 0.3)
        ev["SNARE"].extend(pattern_to_events(sn, GM["SNARE"], tpb, rng, section_name, swing, human, act["SNARE"], bar_start))

        # CH, OH, RIDE
        ev["CH"].extend(pattern_to_events(base["CH"], GM["CH"], tpb, rng, section_name, swing, human, act["CH"], bar_start))
        ev["OH"].extend(pattern_to_events(base["OH"], GM["OH"], tpb, rng, section_name, swing, human, act["OH"], bar_start))
        ev["RIDE"].extend(pattern_to_events(base["RIDE"], GM["RIDE"], tpb, rng, section_name, swing, human, act["RIDE"], bar_start))

        # SHAKER / TAMBO / CONGAS
        ev["SHAKER"].extend(pattern_to_events(base["SHAKER"], GM["SHAKER"], tpb, rng, section_name, swing, human, act["SHAKER"], bar_start))
        ev["TAMBO"].extend(pattern_to_events(base["TAMBO"], GM["TAMBO"], tpb, rng, section_name, swing, human, act["TAMBO"], bar_start))
        ev["CONGA_H"].extend(pattern_to_events(base["CONGA_H"], GM["CONGA_H"], tpb, rng, section_name, swing, human, act["CONGA_H"], bar_start))
        ev["CONGA_M"].extend(pattern_to_events(base["CONGA_M"], GM["CONGA_M"], tpb, rng, section_name, swing, human, act["CONGA_M"], bar_start))

        # TOMS fill
        if section_name in ("build","drop") and (bar+1)%8==0:
            ev["TOMS"].extend(pattern_to_events(P_TOMS_FILL, GM["MTOM"], tpb, rng, section_name, swing, human, 1.0*act["TOMS"], bar_start))
    return ev

def generate_snare_build(bars:int, tpb:int, rng, swing, human, section_start_ticks=0):
    out={"SNARE":[], "OH":[]}
    if bars<=0: return out
    # escalating density
    if bars==1:
        pats=[snare_roll_bar(1,0.7,0.03)]
    elif bars==2:
        pats=[snare_roll_bar(2,0.6,0.05), snare_roll_bar(1,0.75,0.04)]
    else:
        pats=[snare_roll_bar(2,0.6,0.06), snare_roll_bar(1,0.75,0.05), snare_roll_bar(1,0.85,0.03)]
    pat=[]
    for p in pats: pat+=p
    target=bars*16
    pat = pat[:target] if len(pat)>=target else pat + [0]*(target-len(pat))
    out["SNARE"] = pattern_to_events(pat, GM["SNARE"], tpb, rng, "build", swing, human, 1.0, section_start_ticks)

    # OH lifts on last 2 steps of each bar
    oh=[]
    for bar in range(bars):
        b=[0]*16; b[14]=0.8; b[15]=1.0; oh+=b
    out["OH"] = pattern_to_events(oh, GM["OH"], tpb, rng, "build", swing, human, 0.8, section_start_ticks)
    return out

# ======================
# Write MIDI with sections and optional SC trigger
# ======================
def write_drum_arrangement(outfile, bpm=124, arrangement="standard", variant="classic",
                           swing=0.56, human=1, seed=17, flavor=None, sc_trigger=False,
                           split_files=False, outdir=None):
    rng = random.Random(seed)
    # Prepare output directory and stem
    import os
    if outdir is None:
        outdir = os.path.dirname(outfile) or "."
    os.makedirs(outdir, exist_ok=True)
    file_stem = os.path.splitext(os.path.basename(outfile))[0]

    if not split_files:
        mid = MidiFile(ticks_per_beat=480)
        tempo = bpm_to_tempo(bpm)

        # tracks
        names = ["KICK","CLAP","SNARE","CH","OH","RIDE","SHAKER","TAMBO","CONGA_H","CONGA_M","TOMS"]
        if sc_trigger: names.append("SC")
        tracks={}
        for n in names:
            t=MidiTrack(); mid.tracks.append(t)
            t.append(mido.MetaMessage('set_tempo', tempo=tempo, time=0))
            t.append(mido.MetaMessage('track_name', name=n, time=0))
            tracks[n]=t

        # pick variant (allow afro/me override)
        if flavor in ("afro","me"): variant = flavor
        if variant not in VARIANTS: variant="classic"

        # assemble sections
        sections = ARRANGEMENTS[arrangement]
        tpb = mid.ticks_per_beat

        abs_evs_by = {k: [] for k in ["KICK","CLAP","SNARE","CH","OH","RIDE","SHAKER","TAMBO","CONGA_H","CONGA_M","TOMS"]}
        section_start = 0
        for sec_name, bars in sections:
            evs = generate_section_bars(variant, sec_name, bars, tpb, rng, swing, human, section_start)
            for name, lst in evs.items():
                abs_evs_by[name].extend(lst)
            # dedicated build inside build section
            if sec_name=="build":
                build_evs = generate_snare_build(min(4, bars), tpb, rng, swing, human, section_start)
                for name, lst in build_evs.items():
                    abs_evs_by[name].extend(lst)
            section_start += bars * 4 * tpb

        for name, lst in abs_evs_by.items():
            lst.sort(key=lambda e: e[3])  # Sort by absolute time
            last = 0
            for typ, note, vel, abs_t in lst:
                dt = max(0, abs_t - last)  # Convert to relative timing
                add_note(tracks[name], typ, note, vel, dt)
                last = abs_t

        # optional SC trigger: steady quarters across whole arrangement
        if sc_trigger:
            total_bars = sum(b for _,b in sections)
            steps = total_bars*4
            for i in range(steps):
                delay = 0
                add_note(tracks["SC"], "on", GM["SC"], 100, delay)
                add_note(tracks["SC"], "off", GM["SC"], 0, tpb)  # one beat

        mid.save(outfile)
        return outfile
    else:
        sections = ARRANGEMENTS[arrangement]
        tpb_preview = 480
        rng2 = random.Random(seed)
        abs_evs_by = {k: [] for k in ["KICK","CLAP","SNARE","CH","OH","RIDE","SHAKER","TAMBO","CONGA_H","CONGA_M","TOMS"]}
        section_start = 0
        for sec_name, bars in sections:
            evs = generate_section_bars(variant, sec_name, bars, tpb_preview, rng2, swing, human, section_start)
            for name, lst in evs.items():
                abs_evs_by[name].extend(lst)
            if sec_name == "build":
                be = generate_snare_build(min(4, bars), tpb_preview, rng2, swing, human, section_start)
                for name, lst in be.items():
                    abs_evs_by[name].extend(lst)
            section_start += bars * 4 * tpb_preview

        names = ["KICK","CLAP","SNARE","CH","OH","RIDE","SHAKER","TAMBO","CONGA_H","CONGA_M","TOMS"]
        if sc_trigger:
            names.append("SC")
        saved_paths = []
        for n in names:
            mid_i = MidiFile(ticks_per_beat=480)
            tempo = bpm_to_tempo(bpm)
            t = MidiTrack(); mid_i.tracks.append(t)
            t.append(mido.MetaMessage('set_tempo', tempo=tempo, time=0))
            t.append(mido.MetaMessage('track_name', name=n, time=0))
            if n == "SC":
                total_bars = sum(b for _, b in sections)
                for _ in range(total_bars*4):
                    add_note(t, "on", GM["SC"], 100, 0)
                    add_note(t, "off", GM["SC"], 0, mid_i.ticks_per_beat)
            else:
                lst = abs_evs_by[n][:]
                lst.sort(key=lambda e: e[3])
                last = 0
                for typ, note, vel, abs_t in lst:
                    dt = max(0, abs_t - last)
                    add_note(t, typ, note, vel, dt)
                    last = abs_t
            outpath = os.path.join(outdir, f"{file_stem}_{n}.mid")
            mid_i.save(outpath)
            saved_paths.append(outpath)
        return saved_paths[0] if saved_paths else outfile

# ======================
# CLI
# ======================
def main():
    ap = argparse.ArgumentParser(description="Melodic House & Techno Drums — Variants + Probability + Sections")
    ap.add_argument("--bpm", type=int, default=124)
    ap.add_argument("--arrangement", default="standard", choices=list(ARRANGEMENTS.keys()))
    ap.add_argument("--variant", default="afterlife", choices=list(VARIANTS.keys()))
    ap.add_argument("--flavor", default=None, choices=[None,"afro","me"])
    ap.add_argument("--swing", type=float, default=0.56)
    ap.add_argument("--human", type=int, default=3)
    ap.add_argument("--seed", type=int, default=17)
    ap.add_argument("--sc", action="store_true", help="Add sidechain trigger track (quarters)")
    ap.add_argument("--outfile", default="mh_techno_drums_pro.mid")
    ap.add_argument("--split-files", action="store_true", help="Write one MIDI per instrument instead of a single multi-track file")
    ap.add_argument("--outdir", default=None, help="Output directory for MIDI files (defaults to dirname of --outfile)")
    args = ap.parse_args()

    path = write_drum_arrangement(
        outfile=args.outfile, bpm=args.bpm, arrangement=args.arrangement, variant=args.variant,
        swing=args.swing, human=args.human, seed=args.seed, flavor=args.flavor, sc_trigger=args.sc,
        split_files=args.split_files, outdir=args.outdir
    )
    print("Saved to:", args.outdir or (os.path.dirname(args.outfile) or "."))

if __name__ == "__main__":
    main()