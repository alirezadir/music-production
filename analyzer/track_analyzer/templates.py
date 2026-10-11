from __future__ import annotations

from analyzer.track_analyzer.schemas import AnalyzerInitSpec


def summary_md(spec: AnalyzerInitSpec) -> str:
    return f"""# Track Analysis Summary — {spec.artist} - {spec.title}

## Reference + context
- **Artist**: {spec.artist}
- **Title**: {spec.title}
- **Label reference**: {spec.label_reference or "TBD"}
- **Audio path**: {spec.audio_path or "TBD"}

## Tempo & grid
- **BPM**: {spec.bpm if spec.bpm is not None else "TBD"}
- **Time signature**: {spec.time_signature}
- **Loop bars (progression)**: {spec.loop_bars if spec.loop_bars is not None else "TBD"}
- **Key center**: {spec.key_center or "TBD"}

## Notes (high-level)
- What label/style is this aiming at?
- What are the 1–2 signature elements?
- Where is the emotional identity (breakdown/chorus)?
- Are drops mostly instrumental (stabs + call/response + groove + bass movement)?
"""


def arrangement_template_md(spec: AnalyzerInitSpec) -> str:
    return f"""# Arrangement Template Plan — {spec.artist} - {spec.title}

> Use 8-bar blocks. Quantize all boundaries to bars. Keep notes evidence-based.

## Section map (fill in)

| Section | Start bar | End bar | Blocks (×8) | Energy (1–5) | Notes |
|---|---:|---:|---:|---:|---|
| Intro |  |  |  |  |  |
| Groove/Tease |  |  |  |  |  |
| Build 1 |  |  |  |  |  |
| Drop 1 (instrumental) |  |  |  |  |  |
| Breakdown/Chorus (vocal identity) |  |  |  |  |  |
| Verse (post-vocal) |  |  |  |  |  |
| Build 2 |  |  |  |  |  |
| Drop 2 (main peak) |  |  |  |  |  |
| Cooldown/Break |  |  |  |  |  |
| Outro |  |  |  |  |  |

## Transition checklist (fill in)
- Master/group filter sweeps (kick+bass filtered together?)
- Reverb throws / delays on vocals
- Risers / raises into drops
- Call/response alternation logic

## Vocal placement rules (style)
- Full vocals mainly in breakdown/chorus
- Drops: no full lines; allow short chops/fragments
"""


def skeleton_checklist_md(spec: AnalyzerInitSpec) -> str:
    return f"""# Ableton Skeleton Checklist — {spec.artist} - {spec.title}

## Tracks / groups (create)

### Drums
- Kick
- Clap/Snare
- Closed Hat
- Open Hat
- Perc/Fills
- FX (uplifters/impacts)

### Bass
- Sub bass (mono)
- Bass mid layer (optional)
- Reese (if used)

### Music (6 melodic instruments minimum)
- Arpeggio
- Atmosphere/Texture
- Pad
- Lead Call
- Lead Response
- Stabs

### Vocals
- Main vocal
- Vocal chops
- Choir/adlibs

## Clip plan
- Create empty MIDI clips per section (8/16/32 bars).
- Name clips by section + function (e.g. `DROP1 - Lead Call`).

## Notes
- Keep “call” and “response” as separate tracks.
- Use a clear naming convention: `Label – Artist – Track – Empty Template`.
"""


def layers_timeline_csv_header() -> str:
    return "layer,category,start_bar,end_bar,confidence,notes\n"


