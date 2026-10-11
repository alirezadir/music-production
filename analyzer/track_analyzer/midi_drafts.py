from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

try:
    import mido  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    mido = None  # type: ignore


@dataclass(frozen=True)
class MidiDraftSpec:
    bpm: float
    time_signature: str = "4/4"
    key_center: str = "C minor"
    loop_bars: int = 16
    ticks_per_beat: int = 480


def _tempo_meta(bpm: float) -> mido.MetaMessage:
    return mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(bpm), time=0)


def _time_sig_meta(ts: str) -> mido.MetaMessage:
    num_s, den_s = ts.split("/")
    num = int(num_s)
    den = int(den_s)
    # MIDI stores denominator as power-of-two exponent: 2 -> 4, 3 -> 8, etc.
    den_pow = {1: 0, 2: 1, 4: 2, 8: 3, 16: 4}.get(den)
    if den_pow is None:
        den_pow = 2  # fallback to 4/4 style
    return mido.MetaMessage("time_signature", numerator=num, denominator=den_pow, clocks_per_click=24, notated_32nd_notes_per_beat=8, time=0)


def _bars_to_ticks(bars: int, ticks_per_beat: int, beats_per_bar: int = 4) -> int:
    return bars * beats_per_bar * ticks_per_beat


def _note_on(track: mido.MidiTrack, note: int, time: int, vel: int = 90, ch: int = 0) -> None:
    track.append(mido.Message("note_on", note=note, velocity=vel, time=time, channel=ch))


def _note_off(track: mido.MidiTrack, note: int, time: int, vel: int = 0, ch: int = 0) -> None:
    track.append(mido.Message("note_off", note=note, velocity=vel, time=time, channel=ch))


def _basic_minor_chord(root_midi: int) -> list[int]:
    # root, minor 3rd, perfect 5th
    return [root_midi, root_midi + 3, root_midi + 7]


def _key_to_root_midi(key_center: str) -> int:
    """Very small heuristic mapping. If unknown, default to C3 (48)."""
    # Normalize: "C minor", "F# minor", "Am", etc. We only use root pitch class.
    k = key_center.strip().lower().replace("major", "").replace("minor", "").replace("m", "").strip()
    # handle common spellings
    mapping = {
        "c": 48,
        "c#": 49, "db": 49,
        "d": 50,
        "d#": 51, "eb": 51,
        "e": 52,
        "f": 53,
        "f#": 54, "gb": 54,
        "g": 55,
        "g#": 56, "ab": 56,
        "a": 57,
        "a#": 58, "bb": 58,
        "b": 59,
    }
    return mapping.get(k, 48)


def write_midi_drafts(out_dir: Path, spec: MidiDraftSpec) -> dict[str, Path]:
    """Write simple placeholder MIDI clips: chords, arp, bass.

    These are intentionally basic: they give you an arrangement scaffold, not a finished composition.
    """
    if mido is None:
        raise ModuleNotFoundError(
            "mido is not installed. Install it to use --make-midi-drafts "
            "(see requirements.txt: mido>=1.3.0)."
        )
    out_dir.mkdir(parents=True, exist_ok=True)
    beats_per_bar = int(spec.time_signature.split("/")[0]) if "/" in spec.time_signature else 4

    root = _key_to_root_midi(spec.key_center)
    chord_notes = _basic_minor_chord(root)

    # Common duration helpers
    loop_ticks = _bars_to_ticks(spec.loop_bars, spec.ticks_per_beat, beats_per_bar=beats_per_bar)
    beat_ticks = spec.ticks_per_beat
    eighth_ticks = spec.ticks_per_beat // 2
    sixteenth_ticks = spec.ticks_per_beat // 4

    written: dict[str, Path] = {}

    # 1) Chords (block chords, one per bar)
    mf = mido.MidiFile(ticks_per_beat=spec.ticks_per_beat)
    tr = mido.MidiTrack()
    mf.tracks.append(tr)
    tr.append(_tempo_meta(spec.bpm))
    tr.append(_time_sig_meta(spec.time_signature))
    tr.append(mido.MetaMessage("track_name", name="Chords (draft)", time=0))

    # one chord per bar, sustained
    for bar in range(spec.loop_bars):
        # note_on with delta time since last event
        if bar == 0:
            dt = 0
        else:
            dt = 0
        # start at bar boundary: we need to advance time to boundary; easiest: use note_off time to carry
        # We'll encode sustained by: on at time=0 for first chord, then off after one bar (tick time).
        for i, n in enumerate(chord_notes):
            _note_on(tr, n, time=0 if (bar == 0 and i == 0) else 0)
        # turn them off after 1 bar
        _note_off(tr, chord_notes[0], time=beat_ticks * beats_per_bar)
        for n in chord_notes[1:]:
            _note_off(tr, n, time=0)
    tr.append(mido.MetaMessage("end_of_track", time=0))
    p_chords = out_dir / "chords_draft.mid"
    mf.save(p_chords)
    written["chords"] = p_chords

    # 2) Arp (8th notes cycling chord tones)
    mf = mido.MidiFile(ticks_per_beat=spec.ticks_per_beat)
    tr = mido.MidiTrack()
    mf.tracks.append(tr)
    tr.append(_tempo_meta(spec.bpm))
    tr.append(_time_sig_meta(spec.time_signature))
    tr.append(mido.MetaMessage("track_name", name="Arp (draft)", time=0))

    t = 0
    steps = spec.loop_bars * beats_per_bar * 2  # 8ths
    for i in range(steps):
        note = chord_notes[i % len(chord_notes)] + 12  # one octave up
        _note_on(tr, note, time=0 if i == 0 else 0)
        _note_off(tr, note, time=eighth_ticks)
        t += eighth_ticks
    tr.append(mido.MetaMessage("end_of_track", time=0))
    p_arp = out_dir / "arp_draft.mid"
    mf.save(p_arp)
    written["arp"] = p_arp

    # 3) Bass (simple rolling 16ths on root)
    mf = mido.MidiFile(ticks_per_beat=spec.ticks_per_beat)
    tr = mido.MidiTrack()
    mf.tracks.append(tr)
    tr.append(_tempo_meta(spec.bpm))
    tr.append(_time_sig_meta(spec.time_signature))
    tr.append(mido.MetaMessage("track_name", name="Bass (draft)", time=0))

    bass_note = root - 12  # one octave down
    steps = spec.loop_bars * beats_per_bar * 4  # 16ths
    for i in range(steps):
        _note_on(tr, bass_note, time=0 if i == 0 else 0, vel=85)
        _note_off(tr, bass_note, time=sixteenth_ticks)
    tr.append(mido.MetaMessage("end_of_track", time=0))
    p_bass = out_dir / "bass_draft.mid"
    mf.save(p_bass)
    written["bass"] = p_bass

    return written


