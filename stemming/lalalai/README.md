# Lalal.ai Stem Splitter

A Python script and bash tools for splitting audio files into individual stems using the Lalal.ai API.

## Features

- ✅ **All stems processing** - Extract all available stems in one run
- ✅ **Progress visualization** - Beautiful tqdm progress bars
- ✅ **File existence checking** - Skip already processed stems
- ✅ **Environment variable support** - Load license from .env file
- ✅ **Bash wrapper script** - Easy-to-use `stemmer` command
- ✅ **Cleanup script** - `clean_stems` for post-processing

## Installation

1. **Install Python dependencies:**
   ```bash
   pip install python-dotenv tqdm
   ```

2. **Set up your license:**
   Create a `.env` file in the same directory:
   ```
   LALALAI_LICENSE=your_actual_license_key_here
   ```
   
   Or set the environment variable:
   ```bash
   export LALALAI_LICENSE=your_actual_license_key_here
   ```

3. **Make scripts executable:**
   ```bash
   chmod +x stemmer clean_stems
   ```

## Usage

### Method 1: Direct Python Script

```bash
# Process all stems from a single file
python3 lalalai_splitter.py --input "song.mp3"

# Process specific stem
python3 lalalai_splitter.py --input "song.mp3" --stem vocals

# Process multiple stems (comma-separated)
python3 lalalai_splitter.py --input "song.mp3" --stem vocals,drum,bass

# Specify output directory
python3 lalalai_splitter.py --input "song.mp3" --output "/path/to/output"

# Process all files in a directory
python3 lalalai_splitter.py --input "/path/to/audio/files"
```

### Method 2: Bash Script (Recommended)

```bash
# Process all stems from a single file
./stemmer "song.mp3"

# Process specific stems (comma-separated)
./stemmer "song.mp3" -s vocals,drum,bass

# Process all files in a directory
./stemmer "/path/to/audio/files"

# Specify output directory
./stemmer "song.mp3" -o "/path/to/output"

# Process specific stems with custom output
./stemmer "song.mp3" -s vocals,piano -o "/path/to/output"

# Get help
./stemmer --help
```

### Method 3: Cleanup After Processing

```bash
# Clean up stems directory
./clean_stems "./stems"

# This will:
# 1. Rename "_no_vocals_" to "_Instrumental_"
# 2. Delete all files with "_no_" in the name
```

## Available Stems

The script can extract these stems:
- `vocals` - Vocal tracks
- `drum` - Drum tracks  
- `piano` - Piano tracks
- `bass` - Bass tracks
- `electric_guitar` - Electric guitar tracks
- `acoustic_guitar` - Acoustic guitar tracks
- `synthesizer` - Synthesizer tracks
- `strings` - String instrument tracks
- `wind` - Wind instrument tracks

## Output Files

For each stem, you'll get:
- `{filename}_{stem}_split_by_lalalai.mp3` - The isolated stem
- `{filename}_no_{stem}_split_by_lalalai.mp3` - Everything except that stem

## Progress Visualization

The script now includes:
- **tqdm progress bars** showing overall progress
- **Detailed logging** with clear section separators
- **File existence checking** to avoid re-processing

Example output:
```
==================================================
Splitting vocals:
==================================================
Uploading the file "song.mp3"...
Processing stems: 100%|██████████| 9/9 [00:45<00:00,  5.0s/stem]
```

## File Existence Checking

The script automatically checks if stem files already exist and skips them:
```
Stem vocals already exists for song.mp3, skipping...
```

## Error Handling

- **License validation** - Clear error if license is missing
- **File validation** - Checks if input files exist
- **API error handling** - Graceful handling of API failures
- **Progress tracking** - Real-time status updates

## Examples

### Complete Workflow

```bash
# 1. Process all stems from a song
./stemmer "my_song.mp3"

# 2. Clean up the output (optional)
./clean_stems "./stems"

# 3. Check results
ls -la stems/
```

### Batch Processing

```bash
# Process all MP3 files in a directory
./stemmer "/path/to/audio/collection"

# Process with custom output directory
./stemmer "/path/to/audio/collection" -o "/path/to/processed/stems"
```

## Troubleshooting

### Common Issues

1. **"No module named '_tkinter'"** - Install tkinter:
   ```bash
   brew install python-tk
   ```

2. **"LALALAI_LICENSE environment variable not found"** - Set your license:
   ```bash
   export LALALAI_LICENSE=your_key_here
   ```

3. **"tqdm package not found"** - Install tqdm:
   ```bash
   pip install tqdm
   ```

### License Setup

Create a `.env` file in the script directory:
```
LALALAI_LICENSE=your_actual_license_key_here
```

Or set environment variable:
```bash
export LALALAI_LICENSE=your_actual_license_key_here
```

## Scripts Overview

| Script | Purpose | Usage |
|--------|---------|-------|
| `lalalai_splitter.py` | Main Python script | Direct API calls |
| `stemmer` | Bash wrapper | Easy command-line interface |
| `clean_stems` | Post-processing cleanup | Rename and delete files |

## License

This project uses the Lalal.ai API. You need to purchase credits from [Lalal.ai](https://lalal.ai) to use this service.

## Requirements

- Python 3.12 or earlier (due to cgi module compatibility)
- `python-dotenv` package
- `tqdm` package
- Valid Lalal.ai API license 