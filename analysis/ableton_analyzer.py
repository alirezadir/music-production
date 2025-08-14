import gzip
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any
import json
import os

class AbletonProjectReader:
    """Read and parse Ableton Live .als project files"""
    
    def __init__(self, als_path: str):
        self.als_path = Path(als_path)
        self.tree = None
        self.root = None
        
    def load(self):
        """Load and decompress the .als file"""
        with gzip.open(self.als_path, 'rb') as f:
            xml_content = f.read()
            
        # Parse XML
        self.root = ET.fromstring(xml_content)
        self.tree = ET.ElementTree(self.root)
        
    def get_project_info(self) -> Dict[str, Any]:
        """Get basic project information"""
        # Find the Ableton element
        ableton = self.root
        
        return {
            "creator": ableton.get("Creator", "Unknown"),
            "major_version": ableton.get("MajorVersion", "Unknown"),
            "minor_version": ableton.get("MinorVersion", "Unknown"),
            "revision": ableton.get("Revision", "Unknown"),
            "tempo": self._get_tempo(),
            "time_signature": self._get_time_signature()
        }
        
    def _get_tempo(self) -> float:
        """Extract project tempo"""
        tempo_elem = self.root.find(".//Tempo/Manual")
        if tempo_elem is not None:
            return float(tempo_elem.get("Value", 120))
        return 120.0
        
    def _get_time_signature(self) -> Dict[str, int]:
        """Extract time signature"""
        numerator = self.root.find(".//TimeSignature/Numerator")
        denominator = self.root.find(".//TimeSignature/Denominator")
        
        return {
            "numerator": int(numerator.get("Value", 4)) if numerator is not None else 4,
            "denominator": int(denominator.get("Value", 4)) if denominator is not None else 4
        }
        
    def get_tracks(self) -> List[Dict[str, Any]]:
        """Get all tracks in the project"""
        tracks = []
        
        # MIDI Tracks
        for track in self.root.findall(".//MidiTrack"):
            tracks.append(self._parse_track(track, "MIDI"))
            
        # Audio Tracks
        for track in self.root.findall(".//AudioTrack"):
            tracks.append(self._parse_track(track, "Audio"))
            
        # Return Tracks
        for track in self.root.findall(".//ReturnTrack"):
            tracks.append(self._parse_track(track, "Return"))
            
        # Master Track
        master = self.root.find(".//MasterTrack")
        if master is not None:
            tracks.append(self._parse_track(master, "Master"))
            
        return tracks
        
    def _parse_track(self, track_elem: ET.Element, track_type: str) -> Dict[str, Any]:
        """Parse individual track information"""
        track_info = {
            "id": track_elem.get("Id", "Unknown"),
            "type": track_type,
            "name": self._get_track_name(track_elem),
            "color": self._get_track_color(track_elem),
            "clips": self._get_track_clips(track_elem),
            "devices": self._get_track_devices(track_elem),
            "volume": self._get_track_volume(track_elem),
            "pan": self._get_track_pan(track_elem),
            "mute": self._is_track_muted(track_elem),
            "solo": self._is_track_soloed(track_elem)
        }
        
        return track_info
        
    def _get_track_name(self, track_elem: ET.Element) -> str:
        """Extract track name"""
        name_elem = track_elem.find(".//EffectiveName")
        if name_elem is not None:
            return name_elem.get("Value", "Untitled")
            
        name_elem = track_elem.find(".//UserName")
        if name_elem is not None:
            return name_elem.get("Value", "Untitled")
            
        return "Untitled"
        
    def _get_track_color(self, track_elem: ET.Element) -> int:
        """Extract track color"""
        color_elem = track_elem.find(".//Color")
        if color_elem is not None:
            return int(color_elem.get("Value", -1))
        return -1
        
    def _get_track_clips(self, track_elem: ET.Element) -> List[Dict[str, Any]]:
        """Extract all clips from a track"""
        clips = []
        
        # For MIDI tracks
        midi_clips = track_elem.findall(".//MidiClip")
        for clip in midi_clips:
            clips.append(self._parse_midi_clip(clip))
            
        # For Audio tracks
        audio_clips = track_elem.findall(".//AudioClip")
        for clip in audio_clips:
            clips.append(self._parse_audio_clip(clip))
            
        return clips
        
    def _parse_midi_clip(self, clip_elem: ET.Element) -> Dict[str, Any]:
        """Parse MIDI clip information"""
        return {
            "id": clip_elem.get("Id", "Unknown"),
            "type": "MIDI",
            "name": self._get_clip_name(clip_elem),
            "color": self._get_clip_color(clip_elem),
            "start": self._get_clip_start(clip_elem),
            "end": self._get_clip_end(clip_elem),
            "loop_start": self._get_loop_start(clip_elem),
            "loop_end": self._get_loop_end(clip_elem),
            "notes": self._get_midi_notes(clip_elem),
            "is_looped": self._is_clip_looped(clip_elem)
        }
        
    def _parse_audio_clip(self, clip_elem: ET.Element) -> Dict[str, Any]:
        """Parse audio clip information"""
        return {
            "id": clip_elem.get("Id", "Unknown"),
            "type": "Audio",
            "name": self._get_clip_name(clip_elem),
            "color": self._get_clip_color(clip_elem),
            "start": self._get_clip_start(clip_elem),
            "end": self._get_clip_end(clip_elem),
            "file_ref": self._get_audio_file_ref(clip_elem),
            "warp_markers": self._get_warp_markers(clip_elem),
            "is_warped": self._is_clip_warped(clip_elem)
        }
        
    def _get_midi_notes(self, clip_elem: ET.Element) -> List[Dict[str, Any]]:
        """Extract MIDI notes from a clip"""
        notes = []
        notes_elem = clip_elem.find(".//Notes")
        
        if notes_elem is not None:
            for key_track in notes_elem.findall(".//KeyTrack"):
                note_pitch = int(key_track.get("Id", 60))
                
                for note in key_track.findall(".//MidiNoteEvent"):
                    time = note.get("Time", 0)
                    duration = note.get("Duration", 0)
                    velocity = note.get("Velocity", 64)
                    
                    notes.append({
                        "pitch": note_pitch,
                        "time": float(time),
                        "duration": float(duration),
                        "velocity": int(velocity),
                        "muted": note.get("IsEnabled", "true") == "false"
                    })
                    
        return notes
        
    def _get_clip_name(self, clip_elem: ET.Element) -> str:
        """Extract clip name"""
        name_elem = clip_elem.find(".//Name")
        if name_elem is not None:
            return name_elem.get("Value", "Untitled")
        return "Untitled"
        
    def _get_clip_color(self, clip_elem: ET.Element) -> int:
        """Extract clip color"""
        color_elem = clip_elem.find(".//Color")
        if color_elem is not None:
            return int(color_elem.get("Value", -1))
        return -1
        
    def _get_clip_start(self, clip_elem: ET.Element) -> float:
        """Get clip start time"""
        current_start = clip_elem.find(".//CurrentStart")
        if current_start is not None:
            return float(current_start.get("Value", 0))
        return 0.0
        
    def _get_clip_end(self, clip_elem: ET.Element) -> float:
        """Get clip end time"""
        current_end = clip_elem.find(".//CurrentEnd")
        if current_end is not None:
            return float(current_end.get("Value", 0))
        return 0.0
        
    def _get_loop_start(self, clip_elem: ET.Element) -> float:
        """Get loop start time"""
        loop_start = clip_elem.find(".//Loop/LoopStart")
        if loop_start is not None:
            return float(loop_start.get("Value", 0))
        return 0.0
        
    def _get_loop_end(self, clip_elem: ET.Element) -> float:
        """Get loop end time"""
        loop_end = clip_elem.find(".//Loop/LoopEnd")
        if loop_end is not None:
            return float(loop_end.get("Value", 0))
        return 0.0
        
    def _is_clip_looped(self, clip_elem: ET.Element) -> bool:
        """Check if clip is looped"""
        loop_on = clip_elem.find(".//Loop/LoopOn")
        if loop_on is not None:
            return loop_on.get("Value", "false") == "true"
        return False
        
    def _get_audio_file_ref(self, clip_elem: ET.Element) -> str:
        """Get audio file reference"""
        file_ref = clip_elem.find(".//FileRef")
        if file_ref is not None:
            return file_ref.get("Value", "")
        return ""
        
    def _get_warp_markers(self, clip_elem: ET.Element) -> List[Dict[str, float]]:
        """Get warp markers"""
        markers = []
        warp_markers = clip_elem.findall(".//WarpMarker")
        for marker in warp_markers:
            markers.append({
                "time": float(marker.get("Time", 0)),
                "beat_time": float(marker.get("BeatTime", 0))
            })
        return markers
        
    def _is_clip_warped(self, clip_elem: ET.Element) -> bool:
        """Check if clip is warped"""
        is_warped = clip_elem.find(".//IsWarped")
        if is_warped is not None:
            return is_warped.get("Value", "false") == "true"
        return False
        
    def _get_track_devices(self, track_elem: ET.Element) -> List[Dict[str, str]]:
        """Extract devices/plugins from track"""
        devices = []
        
        # Check device chain
        device_chain = track_elem.find(".//DeviceChain/DeviceChain")
        if device_chain is not None:
            for device in device_chain.findall(".//Devices/*"):
                devices.append({
                    "type": device.tag,
                    "id": device.get("Id", "Unknown")
                })
                
        return devices
        
    def _get_track_volume(self, track_elem: ET.Element) -> float:
        """Get track volume"""
        volume_elem = track_elem.find(".//Mixer/Volume/Manual")
        if volume_elem is not None:
            return float(volume_elem.get("Value", 0))
        return 0.0
        
    def _get_track_pan(self, track_elem: ET.Element) -> float:
        """Get track pan"""
        pan_elem = track_elem.find(".//Mixer/Pan/Manual")
        if pan_elem is not None:
            return float(pan_elem.get("Value", 0))
        return 0.0
        
    def _is_track_muted(self, track_elem: ET.Element) -> bool:
        """Check if track is muted"""
        mute_elem = track_elem.find(".//DeviceChain/Mixer/Speaker/Manual")
        if mute_elem is not None:
            return mute_elem.get("Value", "true") == "false"
        return False
        
    def _is_track_soloed(self, track_elem: ET.Element) -> bool:
        """Check if track is soloed"""
        solo_elem = track_elem.find(".//DeviceChain/Mixer/SoloSink")
        if solo_elem is not None:
            return solo_elem.get("Value", "false") == "true"
        return False


class AbletonAnalyzer:
    """Analyze Ableton Live projects and extract musical information"""
    
    def __init__(self):
        self.reader = None
        
    def analyze_project(self, als_file_path: str) -> Dict[str, Any]:
        """Analyze an Ableton Live project file"""
        print(f"Analyzing Ableton project: {als_file_path}")
        
        # Load the project
        self.reader = AbletonProjectReader(als_file_path)
        self.reader.load()
        
        # Get project info
        project_info = self.reader.get_project_info()
        print(f"Project info: {project_info}")
        
        # Get all tracks
        tracks = self.reader.get_tracks()
        print(f"Found {len(tracks)} tracks")
        
        # Analyze each track
        track_analyses = []
        for track in tracks:
            if track['clips']:  # Only analyze tracks with clips
                analysis = self._analyze_track(track)
                track_analyses.append(analysis)
                print(self._generate_track_report(analysis))
        
        # Create summary
        summary = {
            "project_info": project_info,
            "total_tracks": len(tracks),
            "tracks_with_clips": len([t for t in tracks if t['clips']]),
            "track_analyses": track_analyses
        }
        
        return summary
    
    def _analyze_track(self, track: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single track"""
        analysis = {
            "track_id": track['id'],
            "track_name": track['name'],
            "track_type": track['type'],
            "total_clips": len(track['clips']),
            "total_notes": 0,
            "note_range": {"min": 127, "max": 0},
            "velocity_range": {"min": 127, "max": 0},
            "average_velocity": 0,
            "clips": []
        }
        
        all_notes = []
        
        for clip in track['clips']:
            clip_analysis = self._analyze_clip(clip)
            analysis['clips'].append(clip_analysis)
            analysis['total_notes'] += clip_analysis['total_notes']
            all_notes.extend(clip_analysis['notes'])
        
        # Calculate overall statistics
        if all_notes:
            pitches = [note['pitch'] for note in all_notes]
            velocities = [note['velocity'] for note in all_notes]
            
            analysis['note_range'] = {
                "min": min(pitches),
                "max": max(pitches)
            }
            analysis['velocity_range'] = {
                "min": min(velocities),
                "max": max(velocities)
            }
            analysis['average_velocity'] = sum(velocities) / len(velocities)
        
        return analysis
    
    def _analyze_clip(self, clip: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single clip"""
        analysis = {
            "clip_id": clip['id'],
            "clip_name": clip['name'],
            "clip_type": clip['type'],
            "total_notes": len(clip['notes']),
            "notes": clip['notes'],
            "start_time": clip['start'],
            "end_time": clip['end'],
            "duration": clip['end'] - clip['start'] if clip['end'] > clip['start'] else 0
        }
        
        return analysis
    
    def _generate_track_report(self, analysis: Dict[str, Any]) -> str:
        """Generate a text report for a track"""
        report = f"\n=== TRACK ANALYSIS: {analysis['track_name']} ===\n"
        report += f"Type: {analysis['track_type']}\n"
        report += f"Total Clips: {analysis['total_clips']}\n"
        report += f"Total Notes: {analysis['total_notes']}\n"
        
        if analysis['total_notes'] > 0:
            report += f"Note Range: {analysis['note_range']['min']} - {analysis['note_range']['max']}\n"
            report += f"Velocity: {analysis['velocity_range']['min']} - {analysis['velocity_range']['max']} (avg: {analysis['average_velocity']:.1f})\n"
        else:
            report += "Note Range: No notes\n"
            report += "Velocity: No notes\n"
        
        return report


def main():
    """Main function"""
    import sys
    
    # Default file path
    als_file = "data/Anyma-Higher Power.als"
    
    # Check if file path is provided as argument
    if len(sys.argv) > 1:
        als_file = sys.argv[1]
        if not als_file.startswith('data/'):
            als_file = f"data/{als_file}"
    
    # Check if file exists
    if not os.path.exists(als_file):
        print(f"Error: File {als_file} not found")
        return
    
    # Analyze the project
    analyzer = AbletonAnalyzer()
    analysis_result = analyzer.analyze_project(als_file)
    
    # Save detailed analysis to JSON
    base_name = os.path.splitext(os.path.basename(als_file))[0]
    output_file = f"data/out/{base_name}_analysis.json"
    
    with open(output_file, 'w') as f:
        json.dump(analysis_result, f, indent=2)
    
    print(f"\n=== SUMMARY ===")
    print(f"Analyzed {analysis_result['total_tracks']} tracks")
    print(f"Tracks with clips: {analysis_result['tracks_with_clips']}")
    print(f"Detailed analysis saved to: {output_file}")


if __name__ == "__main__":
    main()
