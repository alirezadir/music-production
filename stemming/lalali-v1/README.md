# LALAL.AI v1 stemming tools

Production-oriented wrappers around the current LALAL.AI API v1 Python workflow.

The main command, `remake-stems`, implements the stem pipeline used for track reconstruction/remakes.

## Pipeline

```text
input
  |
  +-- [1] vocals split
  |      +-- vocals
  |      +-- instrumental
  |             |
  |             +-- [2] drum split
  |             |      +-- drums
  |             |      +-- instrumental_no_drums
  |             |
  |             +-- [3] bass split
  |                    +-- bass
  |                    +-- instrumental_no_bass
  |
  +-- instrumental_no_drums
         |
         +-- [4] bass split
                +-- secondary bass (discarded by default)
                +-- instrumental_melodics
                    (instrumental with drums and bass removed)
```

For `San-Francisco-HQ.wav`:

```text
San-Francisco-HQ/
├── San-Francisco-HQ_vocals_lalalai.wav
├── San-Francisco-HQ_instrumental_lalalai.wav
├── San-Francisco-HQ_drums_lalalai.wav
├── San-Francisco-HQ_instrumental_no_drums_lalalai.wav
├── San-Francisco-HQ_bass_lalalai.wav
├── San-Francisco-HQ_instrumental_no_bass_lalalai.wav
└── San-Francisco-HQ_instrumental_melodics_lalalai.wav
```

The step-4 bass is temporary by default because the preferred bass is the direct extraction from the full instrumental in step 3. Pass `--keep-secondary-bass` to retain it.

## API v1 implementation

The wrapper follows the current official v1 Python example:

1. `POST /api/v1/upload/`
2. `POST /api/v1/split/stem_separator/`
3. Poll `POST /api/v1/check/`
4. Download URLs from `result.tracks`
5. Optionally `POST /api/v1/delete/`

It identifies isolated vs complementary output using each returned track's API `label`. It intentionally does not depend on LALAL-generated filenames.

Current official stem-separator stems are:

`vocals`, `drum`, `piano`, `bass`, `guitar`, `electric_guitar`,
`acoustic_guitar`, `synthesizer`, `strings`, `wind`.

This pipeline uses only `vocals`, `drum`, and `bass`.

### Splitter models

The current v1 Python example exposes:

- `auto` - select the latest compatible model
- `andromeda` - current generation for vocals, drum, piano, bass, guitar
- `perseus`
- `orion`
- `phoenix`

The upstream generic script also lists `lynx` for voice cleaning and `lyra` for demuser/music removal. Those endpoints are not used by `remake-stems`.

## Setup

Requires Python 3.10+ and `requests`.

```bash
cd stemming/lalali-v1
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set the license key:

```bash
export LALAL_LICENSE="YOUR_LICENSE_KEY"
```

Do not commit the license key.

## Usage

Directly:

```bash
python3 remake_stems.py "San-Francisco-HQ.wav"
```

Or install the shell command:

```bash
chmod +x remake_stems.py
ln -sf "$(pwd)/remake_stems.py" /usr/local/bin/remake-stems
```

Then:

```bash
remake-stems "San-Francisco-HQ.wav"
```

Custom output:

```bash
remake-stems song.wav -o ./stems
```

Choose splitter:

```bash
remake-stems song.wav --splitter andromeda
```

Cleaner/lower-bleed extraction:

```bash
remake-stems song.wav --extraction-level clear_cut
```

Resume after an interrupted run:

```bash
remake-stems song.wav --resume
```

Replace existing files:

```bash
remake-stems song.wav --overwrite
```

Delete uploaded/processed files from LALAL.AI storage after each stage:

```bash
remake-stems song.wav --delete-remote
```

Keep the secondary bass produced during the melodics stage:

```bash
remake-stems song.wav --keep-secondary-bass
```

Full help:

```bash
remake-stems --help
```

## Arguments

| Argument | Meaning |
|---|---|
| `input` | Input audio file |
| `-o, --output` | Output folder; default is a folder named after the source track |
| `--license` | License key override; prefer `LALAL_LICENSE` |
| `--splitter` | `auto`, `andromeda`, `perseus`, `orion`, or `phoenix` |
| `--extraction-level` | `deep_extraction` or `clear_cut` |
| `--dereverb` | Apply dereverb to each separation |
| `--delete-remote` | Clean remote LALAL files after each stage |
| `--overwrite` | Replace existing local outputs |
| `--resume` | Reuse already completed local stages |
| `--keep-secondary-bass` | Retain step-4 bass |
| `--poll-interval` | Seconds between task status polls, default 5 |
| `--timeout` | HTTP timeout in seconds, default 60 |
| `-q, --quiet` | Reduce console output |

## Upstream reference

Official repository: https://github.com/OmniSaleGmbH/lalalai

The relevant current examples live in `api-v1/python/`. A snapshot of those official Python examples is kept under `lalalai/api-v1/python/` here for convenient reference. For the newest upstream changes, compare against or re-clone the official repository.

To replace the snapshot with a literal fresh clone locally:

```bash
cd stemming/lalali-v1
rm -rf lalalai
git clone https://github.com/OmniSaleGmbH/lalalai.git
```
