keys="G#m,F#m,Em,D#m,C#m,Bm,Am,Gm,Fm,Ebm,Dbm,Abm"
for m in aeolian dorian phrygian persian; do
  # Triads
  python3 compose/make_melodic_progressions.py --keys "$keys" --mode "$m" --split
  # 7ths
  python3 compose/make_melodic_progressions.py --keys "$keys" --mode "$m" --sevenths --split
done