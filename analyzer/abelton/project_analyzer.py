"""Project-level Ableton Live set analysis.

Ableton .als files are gzipped XML. This module reads the project structure and
extracts musical/production summaries without requiring Ableton to be installed.
"""

from __future__ import annotations

import argparse
import gzip
import json
import math
import os
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


NEGATIVE_INFINITY_DB = -70.0
SENTINEL_TIME = -63072000.0


def _value(elem: Optional[ET.Element], default: Any = None) -> Any:
    if elem is None:
        return default
    return elem.get("Value", default)


def _float_value(elem: Optional[ET.Element], default: float = 0.0) -> float:
    raw = _value(elem)
    if raw is None:
        return default
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default


def _bool_value(elem: Optional[ET.Element], default: bool = False) -> bool:
    raw = _value(elem)
    if raw is None:
        return default
    return str(raw).lower() == "true"


def _linear_to_db(value: float) -> float:
    if value <= 0:
        return NEGATIVE_INFINITY_DB
    return round(20.0 * math.log10(value), 2)


def _bar_label(beat: float, beats_per_bar: int = 4) -> str:
    bar = int(beat // beats_per_bar) + 1
    beat_in_bar = int(beat % beats_per_bar) + 1
    return f"{bar}.{beat_in_bar}"


def _safe_round(value: float, places: int = 3) -> float:
    return round(value, places)


def _clip_duration(clip: Dict[str, Any]) -> float:
    return max(0.0, float(clip["end"]) - float(clip["start"]))


def _overlaps(start_a: float, end_a: float, start_b: float, end_b: float) -> bool:
    return start_a < end_b and start_b < end_a


def _classify_layer(name: str, track_type: str, devices: Sequence[Dict[str, Any]]) -> str:
    text = name.lower()
    device_text = " ".join(d["type"].lower() + " " + d.get("name", "").lower() for d in devices)

    checks = [
        ("drums", ("kick", "snare", "clap", "hat", "hihat", "ride", "tom", "perc", "drum")),
        ("bass", ("bass", "sub", "low")),
        ("lead", ("lead", "pluck", "arp", "seq", "hook", "riff")),
        ("chords", ("chord", "stab", "keys", "piano", "organ")),
        ("pad", ("pad", "string", "choir", "atmo")),
        ("vocal", ("vox", "vocal", "voice", "chant")),
        ("fx", ("fx", "sweep", "riser", "impact", "noise", "reverse", "downlifter", "uplifter")),
    ]
    for label, keywords in checks:
        if any(keyword in text for keyword in keywords):
            return label

    if "drumrack" in device_text:
        return "drums"
    if "operator" in device_text or "wavetable" in device_text or "serum" in device_text:
        return "instrument"
    if track_type == "Audio":
        return "audio"
    if track_type == "MIDI":
        return "instrument"
    return "utility"


@dataclass
class ProjectPaths:
    source: Path
    output_json: Optional[Path] = None
    output_markdown: Optional[Path] = None


class AbletonProjectAnalyzer:
    """Analyze arrangement, layers, mixing, devices, samples, and automation."""

    def __init__(self, als_path: str | os.PathLike[str], include_notes: bool = False):
        self.path = Path(als_path)
        self.include_notes = include_notes
        self.root: Optional[ET.Element] = None
        self.parent_map: Dict[int, ET.Element] = {}
        self.target_labels: Dict[str, str] = {}

    def load(self) -> None:
        if not self.path.exists():
            raise FileNotFoundError(self.path)

        with self.path.open("rb") as fh:
            prefix = fh.read(2)

        if prefix == b"\x1f\x8b":
            with gzip.open(self.path, "rb") as fh:
                xml_bytes = fh.read()
        else:
            xml_bytes = self.path.read_bytes()

        self.root = ET.fromstring(xml_bytes)
        self.parent_map = {id(child): parent for parent in self.root.iter() for child in parent}
        self.target_labels = self._build_automation_target_labels()

    def analyze(self) -> Dict[str, Any]:
        if self.root is None:
            self.load()

        assert self.root is not None
        project = self._project_info()
        tracks = self._tracks()
        locators = self._locators()
        arrangement = self._arrangement_summary(project, tracks, locators)
        layers = self._layer_summary(tracks, project)
        mixing = self._mixing_summary(tracks)
        automation = self._automation_summary(tracks, project)

        return {
            "source_file": str(self.path),
            "project": project,
            "arrangement": arrangement,
            "layers": layers,
            "mixing": mixing,
            "automation": automation,
            "tracks": tracks,
        }

    def _project_info(self) -> Dict[str, Any]:
        assert self.root is not None
        numerator = int(_float_value(self.root.find(".//TimeSignature/Numerator"), 4))
        denominator = int(_float_value(self.root.find(".//TimeSignature/Denominator"), 4))
        tempo = _float_value(self.root.find(".//Tempo/Manual"), 120.0)
        return {
            "creator": self.root.get("Creator", "Unknown"),
            "major_version": self.root.get("MajorVersion", "Unknown"),
            "minor_version": self.root.get("MinorVersion", "Unknown"),
            "revision": self.root.get("Revision", "Unknown"),
            "tempo_bpm": tempo,
            "time_signature": {"numerator": numerator, "denominator": denominator},
            "beats_per_bar": numerator,
        }

    def _tracks_container(self) -> Optional[ET.Element]:
        assert self.root is not None
        container = self.root.find(".//LiveSet/Tracks")
        if container is None:
            container = self.root.find(".//Tracks")
        return container

    def _tracks(self) -> List[Dict[str, Any]]:
        container = self._tracks_container()
        if container is None:
            return []

        tracks: List[Dict[str, Any]] = []
        for order, track_elem in enumerate(list(container), start=1):
            if track_elem.tag not in {"MidiTrack", "AudioTrack", "GroupTrack", "ReturnTrack", "MasterTrack"}:
                continue
            tracks.append(self._track(track_elem, order))

        master = self.root.find(".//LiveSet/MasterTrack") if self.root is not None else None
        if master is not None:
            tracks.append(self._track(master, len(tracks) + 1, track_type="Master"))

        return tracks

    def _track(self, elem: ET.Element, order: int, track_type: Optional[str] = None) -> Dict[str, Any]:
        devices = self._devices(elem)
        clips = self._clips(elem)
        automation = self._track_automation(elem)
        name = self._track_name(elem)
        mixer = self._mixer(elem)
        inferred_type = track_type or elem.tag.replace("Track", "") or elem.tag
        layer = _classify_layer(name, inferred_type, devices)
        start = min((clip["start"] for clip in clips), default=None)
        end = max((clip["end"] for clip in clips), default=None)

        note_count = sum(int(clip.get("note_count", 0)) for clip in clips)
        sample_names = sorted({clip["sample_name"] for clip in clips if clip.get("sample_name")})

        return {
            "order": order,
            "id": elem.get("Id", "Unknown"),
            "name": name,
            "type": inferred_type,
            "layer": layer,
            "color_index": int(_float_value(elem.find("./ColorIndex"), -1)),
            "muted": not mixer["speaker_on"],
            "solo": mixer["solo"],
            "mixer": mixer,
            "devices": devices,
            "clips": clips,
            "clip_count": len(clips),
            "note_count": note_count,
            "sample_names": sample_names,
            "automation": automation,
            "span": {
                "start": _safe_round(start, 3) if start is not None else None,
                "end": _safe_round(end, 3) if end is not None else None,
                "duration": _safe_round(end - start, 3) if start is not None and end is not None else 0,
            },
        }

    def _track_name(self, elem: ET.Element) -> str:
        for path in ("./Name/UserName", "./Name/EffectiveName", ".//EffectiveName", ".//UserName"):
            name = _value(elem.find(path), "")
            if name:
                return str(name)
        return f"{elem.tag} {elem.get('Id', '')}".strip()

    def _mixer(self, elem: ET.Element) -> Dict[str, Any]:
        mixer = elem.find("./DeviceChain/Mixer")
        if mixer is None:
            mixer = elem.find(".//Mixer")
        volume = _float_value(mixer.find("./Volume/Manual") if mixer is not None else None, 1.0)
        pan = _float_value(mixer.find("./Pan/Manual") if mixer is not None else None, 0.0)
        speaker_on = _bool_value(mixer.find("./Speaker/Manual") if mixer is not None else None, True)
        on = _bool_value(mixer.find("./On/Manual") if mixer is not None else None, True)
        solo = _bool_value(mixer.find("./SoloSink") if mixer is not None else None, False)
        sends: List[Dict[str, Any]] = []
        if mixer is not None:
            for idx, send in enumerate(mixer.findall(".//Sends/*")):
                manual = send.find("./Manual")
                if manual is not None:
                    val = _float_value(manual, 0.0)
                    sends.append({"index": idx, "value": _safe_round(val), "db": _linear_to_db(val)})
        return {
            "on": on,
            "speaker_on": speaker_on,
            "solo": solo,
            "volume": _safe_round(volume),
            "volume_db": _linear_to_db(volume),
            "pan": _safe_round(pan),
            "send_count": len(sends),
            "active_sends": [send for send in sends if send["value"] > 0.0001],
        }

    def _clips(self, elem: ET.Element) -> List[Dict[str, Any]]:
        events = elem.find("./DeviceChain/MainSequencer/ClipTimeable/ArrangerAutomation/Events")
        if events is None:
            events = elem.find("./DeviceChain/MainSequencer/Sample/ArrangerAutomation/Events")
        if events is None:
            events = elem.find("./DeviceChain/ClipTimeable/ArrangerAutomation/Events")
        if events is None:
            events = elem.find(".//Sample/ArrangerAutomation/Events")
        if events is None:
            events = elem.find(".//ClipTimeable/ArrangerAutomation/Events")
        if events is None:
            return []

        clips: List[Dict[str, Any]] = []
        for clip in list(events):
            if clip.tag not in {"MidiClip", "AudioClip"}:
                continue
            start = _float_value(clip.find("./CurrentStart"), float(clip.get("Time", 0) or 0))
            end = _float_value(clip.find("./CurrentEnd"), start)
            loop_start = _float_value(clip.find("./Loop/LoopStart"), 0.0)
            loop_end = _float_value(clip.find("./Loop/LoopEnd"), 0.0)
            notes = self._midi_notes(clip) if clip.tag == "MidiClip" else []
            sample_name = self._sample_name(clip)
            note_summary = self._note_summary(notes)
            clip_data = {
                "id": clip.get("Id", "Unknown"),
                "type": "MIDI" if clip.tag == "MidiClip" else "Audio",
                "name": _value(clip.find("./Name"), "") or sample_name or "",
                "start": _safe_round(start),
                "end": _safe_round(end),
                "duration": _safe_round(max(0.0, end - start)),
                "loop": {
                    "enabled": _bool_value(clip.find("./Loop/LoopOn"), False),
                    "start": _safe_round(loop_start),
                    "end": _safe_round(loop_end),
                    "duration": _safe_round(max(0.0, loop_end - loop_start)),
                },
                "warped": _bool_value(clip.find("./IsWarped"), False),
                "sample_name": sample_name,
                "note_count": len(notes),
                "note_summary": note_summary,
                "automation_envelope_count": len(clip.findall(".//Envelopes/AutomationEnvelope")),
            }
            if self.include_notes:
                clip_data["notes"] = notes
            clips.append(clip_data)
        return sorted(clips, key=lambda item: (item["start"], item["end"], item["id"]))

    def _note_summary(self, notes: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
        if not notes:
            return {}
        pitches = [int(note["pitch"]) for note in notes]
        velocities = [int(note["velocity"]) for note in notes]
        durations = [float(note["duration"]) for note in notes]
        return {
            "pitch_min": min(pitches),
            "pitch_max": max(pitches),
            "unique_pitches": len(set(pitches)),
            "velocity_min": min(velocities),
            "velocity_max": max(velocities),
            "velocity_avg": _safe_round(sum(velocities) / len(velocities), 2),
            "duration_avg": _safe_round(sum(durations) / len(durations), 3),
        }

    def _midi_notes(self, clip: ET.Element) -> List[Dict[str, Any]]:
        notes: List[Dict[str, Any]] = []
        for key_track in clip.findall(".//KeyTrack"):
            pitch = int(_float_value(key_track.find("./MidiKey"), 60.0))
            for note in key_track.findall("./Notes/MidiNoteEvent"):
                notes.append(
                    {
                        "pitch": pitch,
                        "time": _safe_round(float(note.get("Time", 0) or 0)),
                        "duration": _safe_round(float(note.get("Duration", 0) or 0)),
                        "velocity": int(float(note.get("Velocity", 0) or 0)),
                        "enabled": str(note.get("IsEnabled", "true")).lower() == "true",
                    }
                )
        return notes

    def _sample_name(self, clip: ET.Element) -> str:
        ref = clip.find(".//SampleRef/FileRef/Name")
        if ref is not None:
            return str(_value(ref, ""))
        ref = clip.find(".//FileRef/Name")
        return str(_value(ref, "")) if ref is not None else ""

    def _devices(self, elem: ET.Element) -> List[Dict[str, Any]]:
        chain = elem.find("./DeviceChain/DeviceChain")
        if chain is None:
            return []

        devices: List[Dict[str, Any]] = []
        for device in chain.findall(".//Devices/*"):
            if device.tag in {"ModulationTarget", "AutomationTarget"}:
                continue
            user_name = _value(device.find("./UserName"), "") or _value(device.find(".//UserName"), "")
            preset_name = _value(device.find(".//FileRef/Name"), "")
            plugin_name = _value(device.find(".//PlugName"), "")
            file_name = _value(device.find(".//FileName"), "")
            on = _bool_value(device.find("./On/Manual"), True)
            devices.append(
                {
                    "type": device.tag,
                    "id": device.get("Id", "Unknown"),
                    "name": str(user_name or plugin_name or preset_name or file_name or device.tag),
                    "preset_or_file": str(preset_name or file_name or ""),
                    "enabled": on,
                }
            )
        return devices

    def _track_automation(self, elem: ET.Element) -> List[Dict[str, Any]]:
        envelopes: List[Dict[str, Any]] = []
        for envelope in elem.findall("./AutomationEnvelopes/Envelopes/AutomationEnvelope"):
            target_id = str(_value(envelope.find("./EnvelopeTarget/PointeeId"), ""))
            events = []
            for event in envelope.findall("./Automation/Events/*"):
                time = float(event.get("Time", 0) or 0)
                if time <= SENTINEL_TIME + 1:
                    continue
                value = event.get("Value")
                events.append(
                    {
                        "type": event.tag,
                        "time": _safe_round(time),
                        "value": _coerce_number(value),
                    }
                )
            if events:
                envelopes.append(
                    {
                        "id": envelope.get("Id", "Unknown"),
                        "target_id": target_id,
                        "target": self.target_labels.get(target_id, f"Automation target {target_id}"),
                        "event_count": len(events),
                        "start": events[0]["time"],
                        "end": events[-1]["time"],
                        "min_value": _min_value(events),
                        "max_value": _max_value(events),
                        "events": events,
                    }
                )
        return envelopes

    def _build_automation_target_labels(self) -> Dict[str, str]:
        assert self.root is not None
        labels: Dict[str, str] = {}
        for target in self.root.iter("AutomationTarget"):
            target_id = target.get("Id")
            if not target_id:
                continue
            labels[target_id] = self._node_path_label(target)
        return labels

    def _node_path_label(self, target: ET.Element) -> str:
        names: List[str] = []
        node = target
        while id(node) in self.parent_map:
            node = self.parent_map[id(node)]
            if node.tag in {
                "Mixer",
                "DeviceChain",
                "Devices",
                "ParameterA",
                "ParameterB",
                "AutomationEnvelopes",
                "EnvelopeTarget",
            }:
                continue
            label = node.tag
            user = _value(node.find("./UserName"), "")
            plugin = _value(node.find("./PlugName"), "")
            if user:
                label = f"{label}({user})"
            elif plugin:
                label = f"{label}({plugin})"
            names.append(label)
            if node.tag in {"MidiTrack", "AudioTrack", "GroupTrack", "ReturnTrack", "MasterTrack"}:
                break
        return " / ".join(reversed(names[-5:]))

    def _locators(self) -> List[Dict[str, Any]]:
        assert self.root is not None
        locators = []
        for locator in self.root.findall(".//Locators/Locators/Locator"):
            time = _float_value(locator.find("./Time"), 0.0)
            locators.append(
                {
                    "id": locator.get("Id", "Unknown"),
                    "name": str(_value(locator.find("./Name"), "")),
                    "time": _safe_round(time),
                    "bar": _bar_label(time, 4),
                }
            )
        return sorted(locators, key=lambda item: item["time"])

    def _arrangement_summary(
        self, project: Dict[str, Any], tracks: Sequence[Dict[str, Any]], locators: Sequence[Dict[str, Any]]
    ) -> Dict[str, Any]:
        beats_per_bar = project["beats_per_bar"]
        all_clips = [(track, clip) for track in tracks for clip in track["clips"]]
        end_beat = max((clip["end"] for _, clip in all_clips), default=0.0)
        start_beat = min((clip["start"] for _, clip in all_clips), default=0.0)
        duration_beats = max(0.0, end_beat - start_beat)
        duration_seconds = duration_beats * 60.0 / max(project["tempo_bpm"], 1)

        sections = self._sections_from_locators_or_grid(tracks, locators, end_beat, beats_per_bar)
        density = self._density_windows(tracks, end_beat, beats_per_bar)

        return {
            "start_beat": _safe_round(start_beat),
            "end_beat": _safe_round(end_beat),
            "duration_beats": _safe_round(duration_beats),
            "duration_bars": _safe_round(duration_beats / beats_per_bar, 2) if beats_per_bar else 0,
            "duration_seconds": _safe_round(duration_seconds, 2),
            "locators": list(locators),
            "sections": sections,
            "density_windows": density,
            "peak_density": max((window["active_tracks"] for window in density), default=0),
        }

    def _sections_from_locators_or_grid(
        self,
        tracks: Sequence[Dict[str, Any]],
        locators: Sequence[Dict[str, Any]],
        end_beat: float,
        beats_per_bar: int,
    ) -> List[Dict[str, Any]]:
        boundaries = [0.0]
        labels: Dict[float, str] = {0.0: "Start"}
        for locator in locators:
            boundaries.append(float(locator["time"]))
            labels[float(locator["time"])] = locator["name"] or f"Locator {locator['id']}"
        if end_beat not in boundaries:
            boundaries.append(end_beat)
        boundaries = sorted(set(boundaries))

        if len(boundaries) <= 2 and end_beat > 0:
            step = beats_per_bar * 16
            boundaries = [float(pos) for pos in range(0, int(math.ceil(end_beat)) + step, step)]
            boundaries = [pos for pos in boundaries if pos < end_beat] + [end_beat]
            labels = {boundary: f"{int(boundary // beats_per_bar) + 1}-bar section" for boundary in boundaries}
            labels[0.0] = "Intro"

        sections: List[Dict[str, Any]] = []
        for idx, start in enumerate(boundaries[:-1]):
            end = boundaries[idx + 1]
            active_tracks = []
            layer_counts: Counter[str] = Counter()
            clip_count = 0
            for track in tracks:
                clips = [clip for clip in track["clips"] if _overlaps(clip["start"], clip["end"], start, end)]
                if clips:
                    active_tracks.append(track["name"])
                    layer_counts[track["layer"]] += 1
                    clip_count += len(clips)
            sections.append(
                {
                    "name": labels.get(start, f"Section {idx + 1}"),
                    "start": _safe_round(start),
                    "end": _safe_round(end),
                    "bar_range": f"{_bar_label(start, beats_per_bar)}-{_bar_label(max(start, end - 0.001), beats_per_bar)}",
                    "duration_bars": _safe_round((end - start) / beats_per_bar, 2) if beats_per_bar else 0,
                    "active_track_count": len(active_tracks),
                    "clip_count": clip_count,
                    "layers": dict(sorted(layer_counts.items())),
                    "active_tracks": active_tracks[:20],
                }
            )
        return sections

    def _density_windows(
        self, tracks: Sequence[Dict[str, Any]], end_beat: float, beats_per_bar: int
    ) -> List[Dict[str, Any]]:
        if end_beat <= 0:
            return []
        window = beats_per_bar * 8
        windows: List[Dict[str, Any]] = []
        start = 0.0
        while start < end_beat:
            end = min(end_beat, start + window)
            active = [
                track
                for track in tracks
                if any(_overlaps(clip["start"], clip["end"], start, end) for clip in track["clips"])
            ]
            layer_counts = Counter(track["layer"] for track in active)
            windows.append(
                {
                    "start": _safe_round(start),
                    "end": _safe_round(end),
                    "bar_range": f"{_bar_label(start, beats_per_bar)}-{_bar_label(max(start, end - 0.001), beats_per_bar)}",
                    "active_tracks": len(active),
                    "layers": dict(sorted(layer_counts.items())),
                }
            )
            start += window
        return windows

    def _layer_summary(self, tracks: Sequence[Dict[str, Any]], project: Dict[str, Any]) -> Dict[str, Any]:
        beats_per_bar = project["beats_per_bar"]
        groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for track in tracks:
            groups[track["layer"]].append(track)

        by_layer = {}
        for layer, layer_tracks in sorted(groups.items()):
            clips = [clip for track in layer_tracks for clip in track["clips"]]
            devices = Counter(device["type"] for track in layer_tracks for device in track["devices"])
            by_layer[layer] = {
                "track_count": len(layer_tracks),
                "clip_count": len(clips),
                "total_clip_bars": _safe_round(sum(_clip_duration(clip) for clip in clips) / beats_per_bar, 2),
                "midi_note_count": sum(clip.get("note_count", 0) for clip in clips),
                "top_devices": devices.most_common(10),
                "tracks": [track["name"] for track in layer_tracks],
            }

        return {
            "track_count": len(tracks),
            "tracks_with_clips": sum(1 for track in tracks if track["clips"]),
            "by_layer": by_layer,
            "layer_balance": {layer: data["track_count"] for layer, data in by_layer.items()},
        }

    def _mixing_summary(self, tracks: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
        regular_tracks = [track for track in tracks if track["type"] != "Master"]
        quiet = [track for track in regular_tracks if track["mixer"]["volume_db"] <= -18]
        loud = [track for track in regular_tracks if track["mixer"]["volume_db"] >= -3]
        panned = [track for track in regular_tracks if abs(track["mixer"]["pan"]) >= 0.1]
        muted = [track for track in regular_tracks if track["muted"]]
        soloed = [track for track in regular_tracks if track["solo"]]
        device_counter = Counter(device["type"] for track in tracks for device in track["devices"])

        return {
            "track_count": len(regular_tracks),
            "muted_tracks": [track["name"] for track in muted],
            "soloed_tracks": [track["name"] for track in soloed],
            "quiet_tracks": [{"name": track["name"], "db": track["mixer"]["volume_db"]} for track in quiet],
            "near_unity_or_loud_tracks": [{"name": track["name"], "db": track["mixer"]["volume_db"]} for track in loud],
            "panned_tracks": [{"name": track["name"], "pan": track["mixer"]["pan"]} for track in panned],
            "device_counts": dict(device_counter.most_common()),
            "tracks_with_active_sends": [
                {"name": track["name"], "sends": track["mixer"]["active_sends"]}
                for track in regular_tracks
                if track["mixer"]["active_sends"]
            ],
            "master_chain": next((track["devices"] for track in tracks if track["type"] == "Master"), []),
        }

    def _automation_summary(self, tracks: Sequence[Dict[str, Any]], project: Dict[str, Any]) -> Dict[str, Any]:
        envelopes = [
            {**envelope, "track": track["name"], "track_layer": track["layer"]}
            for track in tracks
            for envelope in track["automation"]
        ]
        layer_counts = Counter(envelope["track_layer"] for envelope in envelopes)
        target_counts = Counter(envelope["target"] for envelope in envelopes)
        event_count = sum(envelope["event_count"] for envelope in envelopes)

        return {
            "envelope_count": len(envelopes),
            "event_count": event_count,
            "automated_track_count": len({envelope["track"] for envelope in envelopes}),
            "by_layer": dict(layer_counts.most_common()),
            "top_targets": target_counts.most_common(20),
            "notable_envelopes": sorted(
                [
                    {
                        "track": envelope["track"],
                        "target": envelope["target"],
                        "event_count": envelope["event_count"],
                        "start": envelope["start"],
                        "end": envelope["end"],
                        "bar_range": f"{_bar_label(envelope['start'], project['beats_per_bar'])}-{_bar_label(envelope['end'], project['beats_per_bar'])}",
                        "min_value": envelope["min_value"],
                        "max_value": envelope["max_value"],
                    }
                    for envelope in envelopes
                ],
                key=lambda item: item["event_count"],
                reverse=True,
            )[:25],
        }


def _coerce_number(value: Optional[str]) -> Any:
    if value is None:
        return None
    try:
        number = float(value)
    except ValueError:
        return value
    if number.is_integer():
        return int(number)
    return _safe_round(number)


def _numeric_values(events: Sequence[Dict[str, Any]]) -> List[float]:
    return [float(event["value"]) for event in events if isinstance(event.get("value"), (int, float))]


def _min_value(events: Sequence[Dict[str, Any]]) -> Any:
    values = _numeric_values(events)
    return _safe_round(min(values)) if values else None


def _max_value(events: Sequence[Dict[str, Any]]) -> Any:
    values = _numeric_values(events)
    return _safe_round(max(values)) if values else None


def render_markdown(analysis: Dict[str, Any]) -> str:
    project = analysis["project"]
    arrangement = analysis["arrangement"]
    layers = analysis["layers"]
    mixing = analysis["mixing"]
    automation = analysis["automation"]

    lines = [
        f"# Ableton Project Analysis: {Path(analysis['source_file']).name}",
        "",
        "## Project",
        f"- Tempo: {project['tempo_bpm']} BPM",
        f"- Time signature: {project['time_signature']['numerator']}/{project['time_signature']['denominator']}",
        f"- Length: {arrangement['duration_bars']} bars ({arrangement['duration_seconds']} seconds)",
        f"- Tracks: {layers['track_count']} total, {layers['tracks_with_clips']} with clips",
        "",
        "## Arrangement",
    ]

    if arrangement["locators"]:
        lines.append("- Locators: " + ", ".join(f"{loc['name']} at {loc['bar']}" for loc in arrangement["locators"]))
    else:
        lines.append("- Locators: none found; sections inferred from 16-bar grid")

    for section in arrangement["sections"]:
        layer_text = ", ".join(f"{name}:{count}" for name, count in section["layers"].items()) or "no active layers"
        lines.append(
            f"- {section['name']} ({section['bar_range']}, {section['duration_bars']} bars): "
            f"{section['active_track_count']} tracks, {section['clip_count']} clips, {layer_text}"
        )

    lines += ["", "## Layers"]
    for layer, data in layers["by_layer"].items():
        track_names = ", ".join(data["tracks"][:12])
        if len(data["tracks"]) > 12:
            track_names += f", +{len(data['tracks']) - 12} more"
        lines.append(
            f"- {layer}: {data['track_count']} tracks, {data['clip_count']} clips, "
            f"{data['midi_note_count']} MIDI notes. Tracks: {track_names}"
        )

    lines += ["", "## Mixing"]
    if mixing["near_unity_or_loud_tracks"]:
        loud = ", ".join(f"{item['name']} ({item['db']} dB)" for item in mixing["near_unity_or_loud_tracks"][:15])
        lines.append(f"- Near-unity/loud tracks: {loud}")
    if mixing["quiet_tracks"]:
        quiet = ", ".join(f"{item['name']} ({item['db']} dB)" for item in mixing["quiet_tracks"][:15])
        lines.append(f"- Quiet tracks: {quiet}")
    if mixing["panned_tracks"]:
        panned = ", ".join(f"{item['name']} ({item['pan']})" for item in mixing["panned_tracks"][:15])
        lines.append(f"- Panned tracks: {panned}")
    if mixing["muted_tracks"]:
        lines.append("- Muted tracks: " + ", ".join(mixing["muted_tracks"]))
    if mixing["master_chain"]:
        lines.append("- Master chain: " + " -> ".join(device["name"] for device in mixing["master_chain"]))
    top_devices = list(mixing["device_counts"].items())[:12]
    if top_devices:
        lines.append("- Top devices: " + ", ".join(f"{name} x{count}" for name, count in top_devices))

    lines += ["", "## Automation"]
    lines.append(
        f"- {automation['envelope_count']} envelopes, {automation['event_count']} events, "
        f"{automation['automated_track_count']} automated tracks"
    )
    if automation["top_targets"]:
        lines.append("- Top automated targets: " + ", ".join(f"{target} x{count}" for target, count in automation["top_targets"][:8]))
    for env in automation["notable_envelopes"][:12]:
        lines.append(
            f"- {env['track']}: {env['target']} ({env['bar_range']}, "
            f"{env['event_count']} events, {env['min_value']} to {env['max_value']})"
        )

    lines += ["", "## Track Detail"]
    for track in analysis["tracks"]:
        if track["type"] == "Master" or track["clip_count"] or track["devices"]:
            device_names = ", ".join(device["name"] for device in track["devices"][:6]) or "none"
            lines.append(
                f"- {track['order']:02d}. {track['name']} [{track['type']}/{track['layer']}]: "
                f"{track['clip_count']} clips, {track['note_count']} notes, "
                f"{track['mixer']['volume_db']} dB, pan {track['mixer']['pan']}, devices: {device_names}"
            )

    return "\n".join(lines) + "\n"


def analyze_file(paths: ProjectPaths, markdown: bool = True, include_notes: bool = False) -> Dict[str, Any]:
    analyzer = AbletonProjectAnalyzer(paths.source, include_notes=include_notes)
    analysis = analyzer.analyze()

    if paths.output_json:
        paths.output_json.parent.mkdir(parents=True, exist_ok=True)
        paths.output_json.write_text(json.dumps(analysis, indent=2), encoding="utf-8")

    if markdown and paths.output_markdown:
        paths.output_markdown.parent.mkdir(parents=True, exist_ok=True)
        paths.output_markdown.write_text(render_markdown(analysis), encoding="utf-8")

    return analysis


def _default_outputs(source: Path, output_dir: Optional[Path]) -> Tuple[Path, Path]:
    directory = output_dir or source.parent
    stem = source.name
    if stem.endswith(".als"):
        stem = stem[:-4]
    elif stem.endswith(".xml"):
        stem = stem[:-4]
    return directory / f"{stem}_ableton_analysis.json", directory / f"{stem}_ableton_analysis.md"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze Ableton Live .als projects.")
    parser.add_argument("project", help="Path to an Ableton .als file or uncompressed .xml file")
    parser.add_argument("--out-dir", type=Path, default=None, help="Directory for JSON/Markdown outputs")
    parser.add_argument("--json", type=Path, default=None, help="Explicit JSON output path")
    parser.add_argument("--md", type=Path, default=None, help="Explicit Markdown output path")
    parser.add_argument("--no-md", action="store_true", help="Skip Markdown report generation")
    parser.add_argument("--include-notes", action="store_true", help="Include every MIDI note event in JSON output")
    parser.add_argument("--print-summary", action="store_true", help="Print the Markdown report to stdout")
    args = parser.parse_args(argv)

    source = Path(args.project)
    default_json, default_md = _default_outputs(source, args.out_dir)
    paths = ProjectPaths(
        source=source,
        output_json=args.json or default_json,
        output_markdown=None if args.no_md else (args.md or default_md),
    )
    analysis = analyze_file(paths, markdown=not args.no_md, include_notes=args.include_notes)

    if args.print_summary:
        print(render_markdown(analysis))
    else:
        print(f"Analyzed {source}")
        print(f"JSON: {paths.output_json}")
        if paths.output_markdown:
            print(f"Markdown: {paths.output_markdown}")
        print(
            f"Tracks: {analysis['layers']['track_count']} | "
            f"Length: {analysis['arrangement']['duration_bars']} bars | "
            f"Automation: {analysis['automation']['envelope_count']} envelopes"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
