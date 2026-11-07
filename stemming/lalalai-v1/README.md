# Local LALAL.AI v1 stem tools

Two manually invoked command-line tools use the LALAL.AI API v1:

- `lalal-stems` — request any supported musical stem, several stems, or all stems.
- `remake-stems` — run the established four-stage reconstruction workflow.

These are local CLI tools, not services or background processes. Audio is uploaded
to LALAL.AI when a non-dry-run command is executed.

## Setup

Requires Python 3.10+ and `requests`.

```bash
cd stemming/lalalai-v1
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export LALAL_LICENSE="YOUR_LICENSE_KEY"
```

Do not commit the license key. To make the generic command available from any
directory, link the executable while the repository remains at a stable path:

```bash
chmod +x lalal-stems remake-stems
ln -sf "$(pwd)/lalal-stems" ~/.local/bin/lalal-stems
ln -sf "$(pwd)/remake-stems" ~/.local/bin/remake-stems
```

## Generic `lalal-stems` CLI

### Examples

```bash
# Individual split: downloads the isolated and complementary tracks
lalal-stems song.wav vocals
lalal-stems song.wav drums
lalal-stems song.wav bass
lalal-stems song.wav piano
lalal-stems song.wav guitar
lalal-stems song.wav synth
lalal-stems song.wav strings
lalal-stems song.wav wind

# Guitar aliases
lalal-stems song.wav eguitar
lalal-stems song.wav aguitar

# Vocals + instrumental shortcut
lalal-stems song.wav vi

# Multiple splits reuse one source upload
lalal-stems song.wav vocals drums bass

# Every supported musical split
lalal-stems song.wav all

# Inspect the plan without uploading or consuming API minutes
lalal-stems song.wav all --dry-run
```

Accepted canonical stems are `vocals`, `drum`, `bass`, `piano`, `guitar`,
`electric_guitar`, `acoustic_guitar`, `synthesizer`, `strings`, and `wind`.
Aliases are `vi`, `drums`, `synth`, `eguitar`, and `aguitar`.

`vi` is a single `vocals` split; its two outputs are named `vocals` and
`instrumental`. `all` currently starts ten billable splits. Multiple requested
stems share one upload, but LALAL.AI charges processing time for every split.
Always check a costly plan with `--dry-run` first.

### Generic CLI options

| Option | Meaning |
|---|---|
| `input` | Local audio file |
| `stems` | One or more canonical names, aliases, or `all` |
| `-o, --output` | Output directory; default is `<input parent>/<input stem>` |
| `--splitter` | `auto`, `andromeda`, `perseus`, `orion`, or `phoenix` |
| `--extraction-level` | `deep_extraction` or `clear_cut` |
| `--dereverb` | Enable dereverb for each requested split |
| `--resume` | Reuse validated outputs and fetch only missing tracks |
| `--overwrite` | Replace existing outputs after a valid new download completes |
| `--delete-remote` | Delete the uploaded source and results after the run |
| `--dry-run` | Print upload count, split count, and expected outputs without API use |
| `--poll-interval` | Seconds between task checks; default 5 |
| `--timeout` | Per-request HTTP timeout in seconds; default 60 |
| `-q, --quiet` | Reduce progress output |

Named models are validated before upload. `auto` is recommended because it picks
the newest model compatible with each stem. A named model fails early when one
of the requested stems is unsupported.

## Reconstruction `remake-stems` CLI

The reconstruction command preserves the established workflow:

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
                +-- secondary bass (optional)
                +-- instrumental_melodics
```

```bash
remake-stems "San-Francisco-HQ.wav"
remake-stems song.wav -o ./stems
remake-stems song.wav --splitter andromeda
remake-stems song.wav --extraction-level clear_cut
remake-stems song.wav --resume
remake-stems song.wav --overwrite
remake-stems song.wav --delete-remote
remake-stems song.wav --keep-secondary-bass
remake-stems song.wav --dry-run
```

The secondary bass from stage 4 is not downloaded unless
`--keep-secondary-bass` is supplied. The preferred bass remains the direct
stage-3 extraction from the complete instrumental.

## Output naming, format, and recovery

Both commands preserve this convention:

```text
<source>_<stem>_lalalai.<actual-format>
```

The extension is detected from the downloaded audio bytes and checked against
the response headers. The input suffix is never assumed to be the returned
format. Downloads go to a temporary `.part` file and become visible under the
final name only after successful format validation.

Normal mode refuses existing outputs. `--resume` validates existing audio,
reuses complete tracks, and reruns only a split with missing output. For a
partially completed pair, the valid existing track is preserved and only its
missing counterpart is downloaded. `--overwrite` keeps old outputs until a new
download has completed and validated, then replaces them.

## API v1 behavior

The shared implementation follows the official workflow:

1. `POST /api/v1/upload/`
2. `POST /api/v1/split/stem_separator/`
3. Poll `POST /api/v1/check/`
4. Identify isolated and complementary tracks from response `label` values
5. Download and validate returned audio
6. Optionally `POST /api/v1/delete/`

The generic command uploads once and starts one task per requested split. It
polls all outstanding task IDs together. The reconstruction command keeps its
stage dependencies and uploads the correct intermediate file at each stage.

## Validation

```bash
python -m py_compile lalal_api.py lalal_stems.py remake_stems.py lalal-stems remake-stems
python -m unittest discover -s tests -v
./lalal-stems --help
python remake_stems.py --help
```

Authenticated integration tests consume API minutes and upload audio. Run them
only after explicit approval.

## Upstream reference

Official repository: https://github.com/OmniSaleGmbH/lalalai

The vendored official Python v1 examples remain under `lalalai/api-v1/python/`
for reference. The local CLIs use the shared `lalal_api.py` module instead of
modifying those examples.
