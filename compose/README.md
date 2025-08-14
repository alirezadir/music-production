# Music Production Composition Scripts

A collection of Python scripts for generating MIDI patterns, arrangements, and musical ideas for Melodic House & Techno production.

## 📁 Scripts Overview

### 1. `make_mh_techno_drums.py` - Drum Pattern Generator
Generates complete MIDI drum patterns with separate tracks for each instrument.

**Features:**
- **GM Drum Mapping**: Uses standard MIDI drum notes compatible with most drum racks
- **Pattern Libraries**: Pre-built House/Techno patterns (four-on-the-floor kicks, 2&4 claps, 16th note hats)
- **Flavor Variations**: Afro and Middle-Eastern rhythmic patterns with tambourine, conga, and shaker syncopations
- **Build Sections**: Progressive snare rolls and open hat ramps for build-ups
- **Humanization**: Swing and timing jitter for natural feel
- **Flexible Parameters**: BPM, bars, build length, swing amount, humanization level

**Usage:**
```bash
python make_mh_techno_drums.py [options]

Options:
  --bpm BPM              Tempo (default: 124)
  --bars BARS            Main loop length in bars (default: 8)
  --build BUILD          Build-up section length in bars (default: 2)
  --swing SWING          Swing amount 0.0-0.6 (default: 0.56)
  --human HUMAN          Timing jitter in ticks 0-12 (default: 3)
  --seed SEED            Random seed for reproducible patterns (default: 17)
  --flavor {none,afro,me} Rhythm style (default: none)
  --outfile OUTFILE      Output filename (default: out/midi-pack/mh_techno_drums.mid)
```

**Examples:**
```bash
# Default techno pattern
python make_mh_techno_drums.py

# Afro-flavored pattern with custom parameters
python make_mh_techno_drums.py --bpm 128 --bars 16 --build 4 --flavor afro

# Middle-Eastern style with heavy swing
python make_mh_techno_drums.py --bpm 132 --swing 0.58 --flavor me

# Extended version for longer tracks
python make_mh_techno_drums.py --bars 32 --build 8 --bpm 120
```

### 2. `make_arrangement_skeletons_mh.py` - Arrangement Template Generator
Creates MIDI arrangement skeletons for structuring Melodic House tracks.

**Features:**
- **10 x 4-minute templates**: ~120 bars @ 120 BPM
- **10 x 6-minute templates**: ~180 bars @ 120 BPM
- **Section Markers**: Clear timing and section information
- **Visual Guides**: Different MIDI pitches for different sections
- **Production Hints**: Descriptive text for each section
- **Guide Click**: First 8 bars of metronome for reference

**Usage:**
```bash
python make_arrangement_skeletons_mh.py
```

**Output Structure:**
Each MIDI file contains:
- **Track 1**: Section markers and timing information
- **Track 2**: Visual section blocks (different pitches for different sections)
- **Track 3**: Guide click for the first 8 bars

**Section Types:**
- **Intro**: Kick, Closed Hat, FX bed
- **Uplift**: Add bass low-pass, ride noise
- **Break**: Pads, arp fragments, vox chop
- **Build**: Snare roll, risers, filter open
- **Drop A/B**: Full groove, main lead, variations
- **Bridge**: Chord swap, new motif
- **Outro**: DJ-friendly drums only

### 3. `make_melodic_progressions.py` - Melodic Progression Generator
Generates melodic chord progressions and musical ideas.

### 4. `make_melodic_ht_ideas.py` - Melodic House & Techno Ideas
Creates melodic hooks and musical phrases.

### 5. `make_melodic_progressions_modes.py` - Modal Progression Generator
Generates progressions based on different musical modes.

### 6. `make_mh_techno_drums_pro.py` - Professional Drum Generator
Advanced drum pattern generator with additional features.

## 🗂️ Output Structure

```
compose/
├── out/
│   ├── midi-pack/          # Drum patterns and loops
│   │   ├── mh_techno_drums.mid
│   │   ├── mh_techno_afro_128bpm.mid
│   │   ├── mh_techno_me_132bpm.mid
│   │   └── mh_techno_extended_120bpm.mid
│   └── arrangements/        # Arrangement skeletons
│       ├── arr01_skeleton_4min.mid
│       ├── arr01_skeleton_6min.mid
│       ├── arr02_skeleton_4min.mid
│       └── ... (20 total files)
```

## 🎵 MIDI Import Guide

### For Ableton Live:
1. Drag and drop MIDI files into Live
2. Drum patterns will create separate tracks for each instrument
3. Arrangement skeletons provide section markers and timing
4. Use the visual blocks to structure your track

### For Other DAWs:
- Most DAWs will import the MIDI files correctly
- Drum patterns maintain separate instrument tracks
- Arrangement markers provide clear section divisions
- Adjust tempo and key as needed for your project

## 🔧 Requirements

- Python 3.8+
- `mido` package for MIDI handling
- Virtual environment recommended (`menv312`)

**Installation:**
```bash
# Activate virtual environment
source menv312/bin/activate

# Install required packages
pip install mido
```

## 🎯 Workflow Integration

1. **Start with Arrangement**: Use arrangement skeletons to plan your track structure
2. **Generate Drums**: Create drum patterns that fit your arrangement
3. **Add Melodies**: Use melodic progression generators for hooks and leads
4. **Import to DAW**: Bring everything into your production environment
5. **Refine and Arrange**: Use the generated MIDI as a foundation for your track

## 🎨 Customization

All scripts are designed to be easily customizable:
- Modify pattern libraries in the script files
- Adjust timing and swing parameters
- Create new flavor variations
- Extend section types for different genres

## 📚 Additional Resources

- Check the `docs/` folder for detailed documentation
- Review the `analysis/` folder for music analysis tools
- Explore the `utils/` folder for helpful utilities

## 🤝 Contributing

Feel free to modify and extend these scripts for your own production needs. The modular design makes it easy to add new features and patterns.

---

**Happy Producing! 🎵**
