#!/usr/bin/env python3
import argparse, os, sys, json, subprocess, shutil, re
from pathlib import Path
import numpy as np
import pandas as pd
import soundfile as sf
import librosa, librosa.display
import matplotlib.pyplot as plt
from tqdm import tqdm

# ----------------------------
# Utility: key & Camelot maps
# ----------------------------
NOTE_NAMES = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
CAMELOT_MAJOR = ["8B","3B","10B","5B","12B","7B","2B","9B","4B","11B","6B","1B"]
CAMELOT_MINOR = ["5A","12A","7A","2A","9A","4A","11A","6A","1A","8A","3A","10A"]

def camelot_from_key(key_alpha:str):
    # key_alpha examples: "G#m", "Dm", "F#", "A"
    m = re.match(r'^([A-G]#?)(m)?$', key_alpha)
    if not m: return None
    root, is_minor = m.group(1), bool(m.group(2))
    idx = NOTE_NAMES.index(root)
    return (CAMELOT_MINOR[idx] if is_minor else CAMELOT_MAJOR[idx])

# -----------------------------------------
# Step 1: optional stemming via CLI alias
# -----------------------------------------
def ensure_stems_for(track_path: Path, force: bool, stem_cmd: str):
    """
    Uses your alias `stem` to create stems under ./stems/<track_stem>/...
    We assume stem <file> creates a folder 'stems' in the same directory.
    """
    track_dir = track_path.parent
    stems_dir = track_dir / "stems" / track_path.stem
    if stems_dir.exists() and not force:
        return stems_dir
    # Run user-provided CLI alias
    cmd = [stem_cmd, str(track_path)]
    try:
        subprocess.run(cmd, check=True)
    except Exception as e:
        print(f"[WARN] Stemming failed for {track_path.name}: {e}")
    return stems_dir if stems_dir.exists() else None

# ------------------------------------------------
# Step 2: audio loading helpers (stems or fullmix)
# ------------------------------------------------
def load_audio_best(track: Path, stems_dir: Path | None, sr=44100):
    """
    Prioritize harmonic/melodic stem for chords & key.
    Fallbacks: 'other', then full mix.
    Also try bass/kick stems for arrangement & layer presence.
    """
    def try_load(p):
        if p and p.exists():
            y, _ = librosa.load(str(p), sr=sr, mono=True)
            return y
        return None

    y_mix, _ = librosa.load(str(track), sr=sr, mono=True)

    if stems_dir and stems_dir.exists():
        # common LALAL.AI names may vary; search heuristically
        candidates_harm = ["other.wav","instrumental.wav","accompaniment.wav","harmonic.wav","piano.wav","synth.wav"]
        candidates_drums = ["drums.wav","drum.wav","kick.wav","percussion.wav"]
        candidates_bass = ["bass.wav"]
        Y = {"mix": y_mix}
        for name in candidates_harm:
            p = stems_dir / name
            if p.exists(): Y["harm"] = try_load(p); break
        for name in candidates_drums:
            p = stems_dir / name
            if p.exists(): Y["drums"] = try_load(p); break
        for name in candidates_bass:
            p = stems_dir / name
            if p.exists(): Y["bass"] = try_load(p); break
        if "harm" not in Y: Y["harm"] = y_mix
        if "drums" not in Y: Y["drums"] = None
        if "bass" not in Y: Y["bass"] = None
        return Y
    else:
        return {"mix": y_mix, "harm": y_mix, "drums": None, "bass": None}

# ---------------------------------------------------
# Step 3: tempo, key, chords, arrangement, features
# ---------------------------------------------------
def estimate_bpm(y, sr):
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    return float(tempo)

def estimate_key_alpha(y, sr):
    # Simple template key detection (Krumhansl major/minor profiles)
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, bins_per_octave=36, hop_length=4096)
    maj_template = np.array([6.35,2.23,3.48,2.33,4.38,4.09,2.52,5.19,2.39,3.66,2.29,2.88])
    min_template = np.array([6.33,2.68,3.52,5.38,2.60,3.53,2.54,4.75,3.98,2.69,3.34,3.17])
    scores = []
    for i in range(12):
        score_maj = np.dot(maj_template, np.roll(chroma.mean(axis=1), -i))
        score_min = np.dot(min_template, np.roll(chroma.mean(axis=1), -i))
        scores.append(("{}"  .format(NOTE_NAMES[i]), score_maj, False))
        scores.append(("{}m".format(NOTE_NAMES[i]), score_min, True))
    best = max(scores, key=lambda x: x[1])
    return best[0]  # e.g., "G#m" or "E"

# quick chord dictionary: triads (maj/min/dim) over 12 roots
TRIAD_SET = []
for r_name, r in zip(NOTE_NAMES, range(12)):
    TRIAD_SET.append((f"{r_name}",            [(r)%12,(r+4)%12,(r+7)%12], "maj"))
    TRIAD_SET.append((f"{r_name}m",           [(r)%12,(r+3)%12,(r+7)%12], "min"))
    TRIAD_SET.append((f"{r_name}dim",         [(r)%12,(r+3)%12,(r+6)%12], "dim"))

def best_chord_from_chroma(vec12):
    # cosine similarity with templates
    def cos(a,b):
        if np.linalg.norm(a)==0 or np.linalg.norm(b)==0: return 0.0
        return float(np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b)))
    best = ("N", 0.0, "na")
    for name, pcs, q in TRIAD_SET:
        tpl = np.zeros(12); tpl[pcs]=1.0
        s = cos(vec12, tpl)
        if s > best[1]: best = (name, s, q)
    return best  # (chord_name, score, quality)

def chord_timeline(y, sr, hop_s=0.5, smooth_win=3):
    hop = int(hop_s*sr)
    C = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop, bins_per_octave=36)
    chroma = librosa.util.normalize(C, axis=0)
    times = librosa.frames_to_time(np.arange(chroma.shape[1]), sr=sr, hop_length=hop)
    chords = []
    for i in range(chroma.shape[1]):
        vec = chroma[:,i]
        # fold to 12
        v12 = np.zeros(12)
        for k in range(12):
            v12[k] = vec[k::12].sum()
        name, score, qual = best_chord_from_chroma(v12)
        chords.append((times[i], name, float(score)))
    # smooth by majority over small window
    if smooth_win>1:
        sm=[]
        w=smooth_win
        for i in range(len(chords)):
            s=i; e=min(len(chords), i+w)
            cand=[c[1] for c in chords[s:e]]
            name = max(set(cand), key=cand.count)
            sm.append((chords[i][0], name, np.mean([chords[j][2] for j in range(s,e)])))
        chords=sm
    return chords  # list of (time_sec, chord_name, confidence)

def romanize_chord(chord_name, key_alpha):
    # Map chord root to roman numeral relative to key (major/minor)
    m = re.match(r'^([A-G]#?)(m|dim)?$', chord_name)
    if not m or key_alpha is None: return "N"
    root, q = m.group(1), (m.group(2) or "")
    is_minor_key = key_alpha.endswith("m")
    key_root = key_alpha[:-1] if is_minor_key else key_alpha
    try:
        key_idx = NOTE_NAMES.index(key_root)
        root_idx = NOTE_NAMES.index(root)
    except ValueError:
        return "N"
    deg = (root_idx - key_idx) % 12
    DEGREE_TO_ROMAN_MIN  = {0:"i", 2:"ii", 3:"III", 5:"iv", 7:"v", 8:"VI", 10:"VII"}
    DEGREE_TO_ROMAN_MAJ  = {0:"I", 2:"ii", 4:"iii", 5:"IV", 7:"V", 9:"vi", 11:"vii°"}
    if is_minor_key:
        rn = DEGREE_TO_ROMAN_MIN.get(deg, "?")
        if q=="dim": rn = "ii°" if deg==2 else rn
        if q=="m" and rn.isupper(): rn = rn.lower()
    else:
        rn = DEGREE_TO_ROMAN_MAJ.get(deg, "?")
        if q=="dim": rn = "vii°" if deg==11 else rn
        if q=="m" and rn.isupper(): rn = rn.lower()
    return rn if rn else "N"

def arrangement_segments(y, sr, bpm_est=None):
    # Novelty function + peak picking for section boundaries (8–16 bar scale)
    hop = 1024
    S = np.abs(librosa.stft(y, n_fft=2048, hop_length=hop))**2
    odf = librosa.onset.onset_strength(S=librosa.power_to_db(S), sr=sr, hop_length=hop)
    novelty = librosa.feature.delta(odf, width=9)
    novelty = librosa.util.normalize(novelty)
    peaks = librosa.util.peak_pick(novelty, pre_max=32, post_max=32, pre_avg=64, post_avg=64, delta=0.1, wait=64)
    times = librosa.frames_to_time(peaks, sr=sr, hop_length=hop)
    # Heuristic label assignment based on energy & hat density
    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=hop).flatten()
    rms_t = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop)
    segs=[]
    prev=0.0
    for t in times:
        if t - prev > 6.0:  # ignore tiny changes
            segs.append((prev, t))
            prev=t
    segs.append((prev, float(len(y)/sr)))
    # Label first/last segments as Intro/Outro; middle sections split into Break/Build/Drop by energy
    labels=[]
    if segs:
        labels.append(("Intro", segs[0][0], segs[0][1]))
        for s,e in segs[1:-1]:
            mid = (s+e)/2
            # energy around mid decides label
            idx = np.argmin(np.abs(rms_t - mid))
            ene = rms[idx]
            label = "Break" if ene < np.percentile(rms,40) else ("Build" if ene < np.percentile(rms,65) else "Drop")
            labels.append((label, s, e))
        labels.append(("Outro", segs[-1][0], segs[-1][1]))
    return labels

def layer_presence(y_dict, sr):
    out={}
    for name, y in y_dict.items():
        if y is None: continue
        S = np.abs(librosa.stft(y, n_fft=2048, hop_length=1024))**2
        low = S[:40].mean()     # ~sub/low
        mid = S[40:200].mean()  # ~mid
        high= S[200:].mean()    # ~high
        out[name] = {"low":float(low), "mid":float(mid), "high":float(high)}
    return out

# ---------------------------------------------------
# Step 4: plotting & dumping
# ---------------------------------------------------
def plot_timeline(track_name, chords, segments, out_png):
    plt.figure(figsize=(12,3))
    # Chord labels
    t = [c[0] for c in chords]; labels=[c[1] for c in chords]
    plt.plot(t, [0]*len(t), alpha=0)  # dummy for x axis
    for ti, lab in zip(t[::max(1,len(t)//30+1)], labels[::max(1,len(t)//30+1)]):
        plt.text(ti, 0.5, lab, rotation=90, fontsize=8, va='center')
    # Segments
    for (name, s, e) in segments:
        plt.axvspan(s, e, alpha=0.08)
        plt.text((s+e)/2, 0.9, name, ha='center', va='center', fontsize=9)
    plt.title(f"{track_name} — chord/segment timeline")
    plt.yticks([])
    plt.xlabel("Time (s)")
    plt.tight_layout()
    plt.savefig(out_png, dpi=140)
    plt.close()

# ---------------------------------------------------
# Step 5: per-track analysis
# ---------------------------------------------------
def analyze_track(track_path: Path, args, agg_rows):
    stems_dir = None
    if args.use_stems:
        stems_dir = ensure_stems_for(track_path, force=args.force_stem, stem_cmd=args.stem_cmd)

    Y = load_audio_best(track_path, stems_dir, sr=args.sr)
    y_harm = Y["harm"]; y_mix = Y["mix"]

    # BPM (optional), Key
    bpm = estimate_bpm(y_mix, args.sr) if args.bpm else None
    key_alpha = estimate_key_alpha(y_harm, args.sr)
    camelot = camelot_from_key(key_alpha)
    is_minor = key_alpha.endswith("m")

    # Chords
    chords = chord_timeline(y_harm, args.sr, hop_s=args.chord_hop, smooth_win=3)
    chords_roman = [(t, romanize_chord(name, key_alpha), float(conf)) for (t,name,conf) in chords]

    # Arrangement
    segments = arrangement_segments(y_mix, args.sr, bpm_est=bpm)

    # Layers (energy by band) from stems/mix
    layers = layer_presence(Y, args.sr)

    # Save per-track outputs
    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)
    base = outdir / track_path.stem
    # CSV chords
    pd.DataFrame(chords, columns=["time_s","chord","conf"]).to_csv(f"{base}_chords.csv", index=False)
    pd.DataFrame(chords_roman, columns=["time_s","roman","conf"]).to_csv(f"{base}_roman.csv", index=False)
    # Segments
    pd.DataFrame(segments, columns=["section","start_s","end_s"]).to_csv(f"{base}_segments.csv", index=False)
    # Layers JSON
    with open(f"{base}_layers.json","w") as f: json.dump(layers, f, indent=2)
    # Quick plot
    plot_timeline(track_path.name, chords, segments, f"{base}_timeline.png")

    # Aggregate row (progression compression)
    # Reduce roman timeline to bar-sized tiles then to common progression string
    romans = [r for _,r,_ in chords_roman if r!="N"]
    # compress consecutive same
    comp=[]
    for r in romans:
        if not comp or comp[-1]!=r: comp.append(r)
    # take first 8–16 as summary
    short = comp[:16]
    agg_rows.append(dict(
        track=track_path.name, bpm=bpm, key_alpha=key_alpha, camelot=camelot, is_minor=is_minor,
        roman_summary="-".join(short) if short else ""
    ))

# ---------------------------------------------------
# Step 6: run over folder & aggregate
# ---------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Melodic H&T analysis pipeline (keys, chords, arrangement, layers)")
    ap.add_argument("--in", dest="indir", required=True, help="Folder with .wav/.aiff")
    ap.add_argument("--outdir", default="analysis_out")
    ap.add_argument("--sr", type=int, default=44100)
    ap.add_argument("--use-stems", action="store_true", help="Use stems via your 'stem' CLI alias")
    ap.add_argument("--stem-cmd", default="stem", help="Alias/command to run stemming for a file")
    ap.add_argument("--force-stem", action="store_true", help="Re-run stemming even if stems exist")
    ap.add_argument("--bpm", action="store_true", help="Estimate BPM")
    ap.add_argument("--chord-hop", type=float, default=0.5, help="Chord frame hop in seconds")
    args = ap.parse_args()

    indir = Path(args.indir)
    if not indir.exists(): sys.exit(f"Input folder not found: {indir}")

    tracks = sorted([p for p in indir.rglob("*") if p.suffix.lower() in (".wav",".aif",".aiff")])
    if not tracks: sys.exit("No audio files found.")

    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)

    agg=[]
    for p in tqdm(tracks, desc="Analyzing tracks"):
        try:
            analyze_track(p, args, agg)
        except Exception as e:
            print(f"[ERROR] {p.name}: {e}")

    # Aggregate CSV
    df = pd.DataFrame(agg)
    if not df.empty:
        # Simple frequency of roman sequences (first 8 tokens)
        df["roman_8"] = df["roman_summary"].apply(lambda s: "-".join(s.split("-")[:8]) if isinstance(s,str) else "")
        df.to_csv(outdir / "aggregate_tracks.csv", index=False)
        freq = df["roman_8"].value_counts().rename_axis("progression").reset_index(name="count")
        freq.to_csv(outdir / "top_progressions.csv", index=False)

        # Key distribution
        key_counts = df["key_alpha"].value_counts().rename_axis("key").reset_index(name="count")
        key_counts.to_csv(outdir / "key_distribution.csv", index=False)

        print(f"[DONE] Wrote aggregate CSVs in {outdir.resolve()}")
    else:
        print("[WARN] No aggregate rows created.")

if __name__ == "__main__":
    main()