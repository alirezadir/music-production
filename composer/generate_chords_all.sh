#!/usr/bin/env bash
# Run from anywhere; output lands in out/midi-pack relative to the current dir.
script_dir="$(cd "$(dirname "$0")" && pwd)"
keys="G#m,F#m,Em,D#m,C#m,Bm,Am,Gm,Fm,Ebm,Dbm,Abm"
for m in aeolian dorian phrygian persian; do
  # Triads
  python3 "$script_dir/make_melodic_progressions.py" --keys "$keys" --mode "$m" --split
  # 7ths
  python3 "$script_dir/make_melodic_progressions.py" --keys "$keys" --mode "$m" --sevenths --split
done
