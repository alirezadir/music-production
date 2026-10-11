#!/usr/bin/python3

# Copyright (c) 2025 LALAL.AI
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import sys
import time
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, SUPPRESS
from dataclasses import dataclass
from email.message import EmailMessage
from urllib.parse import quote, unquote

try:
    import requests
except ImportError:
    print("ERROR: requests library is required. Install it with: pip install requests")
    sys.exit(1)

from tqdm import tqdm

# Try to import dotenv, but don't fail if it's not installed
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("Warning: python-dotenv not installed. Install with: pip install python-dotenv")


URL_API = "https://www.lalal.ai/api/v1/"

# Stem definitions by endpoint
_voice_clean_stems = ("voice",)
_demuser_stems = ("music",)
_stem_separator_stems = (
    "vocals",
    "drum",
    "piano",
    "bass",
    "electric_guitar",
    "acoustic_guitar",
    "synthesizer",
    "strings",
    "wind",
)

# All stems available for --stem all (excludes 'voice' and 'music' which are special-purpose)
_all_stems = _stem_separator_stems


# ---------------------------------------------------------------------------
# Params dataclasses
# ---------------------------------------------------------------------------

@dataclass
class VoiceCleanParams:
    """Parameters for /split/voice_clean/ endpoint."""
    source_id: str
    noise_cancelling_level: int  # 0, 1, or 2
    dereverb_enabled: bool = False
    splitter: str = "auto"


@dataclass
class DemuserParams:
    """Parameters for /split/demuser/ endpoint."""
    source_id: str
    dereverb_enabled: bool = False


@dataclass
class StemSeparatorParams:
    """Parameters for /split/stem_separator/ endpoint."""
    source_id: str
    stem: str
    extraction_level: str  # deep_extraction or clear_cut
    dereverb_enabled: bool = False
    multivocal: str | None = None  # lead_back for vocals stem only
    splitter: str = "auto"


# ---------------------------------------------------------------------------
# License loading
# ---------------------------------------------------------------------------

def load_license():
    """Load license key from environment variable or .env file."""
    if DOTENV_AVAILABLE:
        load_dotenv()
    license_key = os.getenv('LALALAI_LICENSE')
    if license_key:
        return license_key
    raise FileNotFoundError(
        "LALALAI_LICENSE environment variable not found. "
        "Please set it in your .env file or environment variables."
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def check_file_exists(output_path, input_filename, stem):
    """Check if a stem file already exists in the output directory."""
    base_name = os.path.splitext(input_filename)[0]
    stem_file = os.path.join(output_path, f"{base_name}_{stem}_split_by_lalalai.mp3")
    return os.path.exists(stem_file)


def _update_percent(pct):
    pct = str(pct)
    sys.stdout.write("\b" * len(pct))
    sys.stdout.write(" " * len(pct))
    sys.stdout.write("\b" * len(pct))
    sys.stdout.write(pct)
    sys.stdout.flush()


def make_content_disposition(filename, disposition="attachment"):
    try:
        filename.encode("ascii")
        file_expr = f'filename="{filename}"'
    except UnicodeEncodeError:
        quoted = quote(filename)
        file_expr = f"filename*=utf-8''{quoted}"
    return f"{disposition}; {file_expr}"


def get_filename_from_content_disposition(header):
    """Parse Content-Disposition header to extract filename (RFC 5987 safe)."""
    msg = EmailMessage()
    msg["content-disposition"] = header
    filename = msg.get_filename()
    if filename:
        return filename
    # Fallback: manual parsing for RFC 5987 encoded filenames
    if "filename*=" in header:
        for raw_segment in header.split(";"):
            segment = raw_segment.strip()
            if segment.startswith("filename*="):
                encoded = segment.split("=", 1)[1]
                if "''" in encoded:
                    encoding, quoted = encoded.split("''", 1)
                    return unquote(quoted, encoding)
    raise ValueError("Invalid header Content-Disposition")


def _strtobool(val: str) -> bool:
    """Convert a string representation of truth to true or false."""
    val = val.lower()
    if val in ("y", "yes", "t", "true", "on", "1"):
        return True
    elif val in ("n", "no", "f", "false", "off", "0"):
        return False
    else:
        raise ValueError(f"invalid bool value {val!r}")


# ---------------------------------------------------------------------------
# API calls — v1
# ---------------------------------------------------------------------------

def upload_file(file_path, license):
    """Upload file to LALAL.AI v1 API, returns source_id."""
    url_for_upload = URL_API + "upload/"
    _, filename = os.path.split(file_path)
    headers = {
        "Content-Disposition": make_content_disposition(filename),
        "X-License-Key": license,
    }
    with open(file_path, "rb") as f:
        response = requests.post(url_for_upload, data=f, headers=headers, timeout=30)
    if response.status_code != 200:
        raise RuntimeError(f"Upload failed: {response.status_code} - {response.text}")
    upload_result = response.json()
    if upload_result.get("status") == "error":
        raise RuntimeError(upload_result.get("error", "Unknown upload error"))
    return upload_result["id"]


def _split_voice_clean(params: VoiceCleanParams, license: str) -> str:
    """Start voice cleaning task, returns task_id."""
    url = URL_API + "split/voice_clean/"
    headers = {"X-License-Key": license}
    presets = {
        "stem": "voice",
        "noise_cancelling_level": params.noise_cancelling_level,
        "splitter": params.splitter,
    }
    if params.dereverb_enabled:
        presets["dereverb_enabled"] = True
    body = {"source_id": params.source_id, "presets": presets}
    print("Split task request body:", body)
    response = requests.post(url, json=body, headers=headers, timeout=30)
    if response.status_code != 200:
        raise RuntimeError(f"Split failed: {response.status_code} - {response.text}")
    return response.json()["task_id"]


def _split_demuser(params: DemuserParams, license: str) -> str:
    """Start music removal (demuser) task, returns task_id."""
    url = URL_API + "split/demuser/"
    headers = {"X-License-Key": license}
    presets: dict = {"stem": "music"}
    if params.dereverb_enabled:
        presets["dereverb_enabled"] = True
    body = {"source_id": params.source_id, "presets": presets}
    print("Split task request body:", body)
    response = requests.post(url, json=body, headers=headers, timeout=30)
    if response.status_code != 200:
        raise RuntimeError(f"Split failed: {response.status_code} - {response.text}")
    return response.json()["task_id"]


def _split_stem_separator(params: StemSeparatorParams, license: str) -> str:
    """Start stem separation task, returns task_id."""
    url = URL_API + "split/stem_separator/"
    headers = {"X-License-Key": license}
    presets = {
        "stem": params.stem,
        "extraction_level": params.extraction_level,
        "splitter": params.splitter,
    }
    if params.dereverb_enabled:
        presets["dereverb_enabled"] = True
    if params.multivocal and params.stem == "vocals":
        presets["multivocal"] = params.multivocal
    body = {"source_id": params.source_id, "presets": presets}
    print("Split task request body:", body)
    response = requests.post(url, json=body, headers=headers, timeout=30)
    if response.status_code != 200:
        raise RuntimeError(f"Split failed: {response.status_code} - {response.text}")
    return response.json()["task_id"]


def build_split_params(
    source_id: str,
    stem: str,
    noise_cancelling: int,
    dereverb_enabled: bool,
    extraction_level: str,
    multivocal: str | None,
    splitter: str,
) -> VoiceCleanParams | DemuserParams | StemSeparatorParams:
    """Build appropriate params object based on stem type."""
    if stem == "voice":
        return VoiceCleanParams(
            source_id=source_id,
            noise_cancelling_level=noise_cancelling,
            dereverb_enabled=dereverb_enabled,
            splitter=splitter,
        )
    elif stem == "music":
        return DemuserParams(
            source_id=source_id,
            dereverb_enabled=dereverb_enabled,
        )
    else:
        return StemSeparatorParams(
            source_id=source_id,
            stem=stem,
            extraction_level=extraction_level,
            dereverb_enabled=dereverb_enabled,
            multivocal=multivocal,
            splitter=splitter,
        )


def split_file(params, license: str) -> str:
    """Dispatch to the correct split endpoint and return task_id."""
    if isinstance(params, VoiceCleanParams):
        return _split_voice_clean(params, license)
    elif isinstance(params, DemuserParams):
        return _split_demuser(params, license)
    elif isinstance(params, StemSeparatorParams):
        return _split_stem_separator(params, license)
    else:
        raise ValueError(f"Unsupported params type: {type(params)}")


def check_task(task_id: str, license: str) -> dict:
    """Poll /check/ until task completes, returns result dict with 'tracks' list."""
    url_for_check = URL_API + "check/"
    headers = {"X-License-Key": license}
    body = {"task_ids": [task_id]}
    is_queued = False

    while True:
        response = requests.post(url_for_check, json=body, headers=headers, timeout=30)
        if response.status_code != 200:
            raise RuntimeError(f"Check failed: {response.status_code} - {response.text}")

        check_result = response.json()
        if task_id not in check_result.get("result", {}):
            raise RuntimeError(f"Task {task_id} not found in response")

        task_status = check_result["result"][task_id]
        status = task_status.get("status")

        if status == "success":
            _update_percent("Progress: 100%\n")
            print("Using settings:", task_status.get("presets"))
            return task_status["result"]
        elif status == "cancelled":
            raise RuntimeError("Task was cancelled")
        elif status == "error":
            raise RuntimeError(task_status.get("error", "Unknown task error"))
        elif status == "progress":
            progress = int(task_status.get("progress", 0))
            if progress == 0 and not is_queued:
                print("Task queued, processing...")
                print("Using settings:", task_status.get("presets"))
                is_queued = True
            elif progress > 0:
                _update_percent(f"Progress: {progress}%")
        else:
            raise RuntimeError(f"Unknown task status: {status}")

        time.sleep(5)


def download_file(url_for_download: str, output_path: str) -> str:
    """Download a file from URL and save to output_path, return local file path."""
    response = requests.get(url_for_download, stream=True, timeout=60)
    if response.status_code != 200:
        raise RuntimeError(f"Download failed: {response.status_code}")
    content_disp = response.headers.get("Content-Disposition", "")
    filename = get_filename_from_content_disposition(content_disp)
    file_path = os.path.join(output_path, filename)
    with open(file_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    return file_path


def delete_tracks(source_id: str, license: str):
    """Delete source file and all resulting tracks from LALAL.AI storage."""
    url_for_delete = URL_API + "delete/"
    headers = {"X-License-Key": license}
    response = requests.post(
        url_for_delete, json={"source_id": source_id}, headers=headers, timeout=30
    )
    if response.status_code != 200:
        raise RuntimeError(f"Delete failed: {response.status_code} - {response.text}")


# ---------------------------------------------------------------------------
# Batch processing
# ---------------------------------------------------------------------------

def _process_single_stem(
    license, source_id, input_filename, output_path, stem,
    noise_cancelling, dereverb_enabled, extraction_level, multivocal,
    delete, splitter,
):
    """Upload already done — split, check, download for one stem."""
    if check_file_exists(output_path, input_filename, stem):
        print(f"Stem '{stem}' already exists for {input_filename}, skipping...")
        return

    params = build_split_params(
        source_id, stem, noise_cancelling, dereverb_enabled,
        extraction_level, multivocal, splitter,
    )
    task_id = split_file(params, license)
    print(f"Task started (task_id: {task_id})")
    split_result = check_task(task_id, license)

    for track in split_result["tracks"]:
        url = track["url"]
        label = track.get("label", stem)
        print(f'Downloading {label} track from "{url}"...')
        downloaded_file = download_file(url, output_path)
        print(f'Downloaded to "{downloaded_file}"')


def batch_process_for_file(
    license, input_path, output_path, stem,
    noise_cancelling, dereverb_enabled, extraction_level, multivocal,
    delete, splitter,
):
    """Process a single file: upload once, then split for requested stem(s)."""
    try:
        input_filename = os.path.basename(input_path)
        print(f'Uploading "{input_path}"...')
        source_id = upload_file(file_path=input_path, license=license)
        print(f'Uploaded successfully (source_id: {source_id})')

        if stem == "all":
            _batch_all_stems(
                license, source_id, input_filename, output_path,
                noise_cancelling, dereverb_enabled, extraction_level,
                multivocal, delete, splitter,
            )
        elif "," in stem:
            stems_list = [s.strip() for s in stem.split(",")]
            _batch_selected_stems(
                license, source_id, input_filename, output_path, stems_list,
                noise_cancelling, dereverb_enabled, extraction_level,
                multivocal, delete, splitter,
            )
        else:
            print(f'Processing stem "{stem}"...')
            _process_single_stem(
                license, source_id, input_filename, output_path, stem,
                noise_cancelling, dereverb_enabled, extraction_level,
                multivocal, delete, splitter,
            )
            print(f'Successfully split "{input_path}"')

        if delete:
            print(f"Deleting files from LALAL.AI storage (source_id: {source_id})...")
            delete_tracks(source_id, license)
            print("Deleted from storage.")

    except Exception as err:
        print(f'Cannot process "{input_path}": {err}')


def _batch_all_stems(
    license, source_id, input_filename, output_path,
    noise_cancelling, dereverb_enabled, extraction_level,
    multivocal, delete, splitter,
):
    """Process all instrument stems for an already-uploaded file."""
    with tqdm(total=len(_all_stems), desc="Processing stems", unit="stem") as pbar:
        for stem in _all_stems:
            print(f"\n{'='*50}\nSplitting '{stem}':\n{'='*50}")
            try:
                _process_single_stem(
                    license, source_id, input_filename, output_path, stem,
                    noise_cancelling, dereverb_enabled, extraction_level,
                    multivocal, delete, splitter,
                )
            except Exception as err:
                print(f"Error on stem '{stem}': {err}")
            pbar.update(1)
    print(f'\nAll stems for "{input_filename}" processed.')


def _batch_selected_stems(
    license, source_id, input_filename, output_path, stems_list,
    noise_cancelling, dereverb_enabled, extraction_level,
    multivocal, delete, splitter,
):
    """Process a specific list of stems for an already-uploaded file."""
    with tqdm(total=len(stems_list), desc="Processing stems", unit="stem") as pbar:
        for stem in stems_list:
            print(f"\n{'='*50}\nSplitting '{stem}':\n{'='*50}")
            try:
                _process_single_stem(
                    license, source_id, input_filename, output_path, stem,
                    noise_cancelling, dereverb_enabled, extraction_level,
                    multivocal, delete, splitter,
                )
            except Exception as err:
                print(f"Error on stem '{stem}': {err}")
            pbar.update(1)
    print(f'\nSelected stems for "{input_filename}" processed.')


def batch_process(
    license, input_path, output_path, stem,
    noise_cancelling, dereverb_enabled, extraction_level,
    multivocal, delete, splitter,
):
    """Process file(s) — single file or all files in a directory."""
    if os.path.isfile(input_path):
        batch_process_for_file(
            license, input_path, output_path, stem,
            noise_cancelling, dereverb_enabled, extraction_level,
            multivocal, delete, splitter,
        )
    else:
        for path in os.listdir(input_path):
            full_path = os.path.join(input_path, path)
            if os.path.isfile(full_path):
                batch_process_for_file(
                    license, full_path, output_path, stem,
                    noise_cancelling, dereverb_enabled, extraction_level,
                    multivocal, delete, splitter,
                )


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _validate_stem(stem):
    """Validate stem against all supported v1 API stems."""
    if stem == "all":
        return
    if "," in stem:
        for s in [x.strip() for x in stem.split(",")]:
            _validate_stem(s)
        return
    valid_stems = _voice_clean_stems + _demuser_stems + _stem_separator_stems
    if stem not in valid_stems:
        raise ValueError(f'Unsupported stem "{stem}". Must be one of {valid_stems}')


def _validate_multivocal(stem, multivocal):
    if multivocal and stem != "vocals":
        raise ValueError(
            f'--multivocal is only supported for "vocals" stem, not "{stem}"'
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

_splitter_help = (
    "Splitter model to use. 'auto' selects the latest available model for the stem. "
    "Choices: auto, orion, perseus, phoenix, andromeda, lynx, lyra."
)

_stem_choices = list(_voice_clean_stems + _demuser_stems + _stem_separator_stems)
_stem_help = (
    'Stem to extract (default: vocals). '
    'Use "voice" for voice cleaning, "music" to remove background music, '
    '"all" for all instrument stems, or a comma-separated list (e.g., vocals,drum,bass). '
    f'Single-stem choices: {_stem_choices}'
)


def main():
    parser = ArgumentParser(
        description="LALAL.AI splitter — v1 API",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--input", required=True, type=str, default=SUPPRESS,
                        help="Input directory or file")
    parser.add_argument("--output", type=str, default=None,
                        help="Output directory (default: <input_dir>/stems)")
    parser.add_argument("--stem", type=str, default="vocals", help=_stem_help)
    parser.add_argument("--noise-cancelling", type=int, default=1, choices=[0, 1, 2],
                        help='Noise cancelling for "voice" stem (0: mild, 1: normal, 2: aggressive)')
    parser.add_argument("--dereverb-enabled",
                        type=lambda x: bool(_strtobool(x)), default=False,
                        choices=[True, False], help="Remove reverb/echo")
    parser.add_argument("--extraction-level", type=str, default="deep_extraction",
                        choices=["deep_extraction", "clear_cut"],
                        help='"deep_extraction": more detail (may bleed); "clear_cut": cleaner, less detail')
    parser.add_argument("--multivocal", type=str, default=None, choices=["lead_back"],
                        help='For "vocals" stem: separate lead and backing vocals')
    parser.add_argument("--splitter", type=str, default="auto",
                        choices=["auto", "orion", "perseus", "phoenix", "andromeda", "lynx", "lyra"],
                        help=_splitter_help)
    parser.add_argument("--delete",
                        type=lambda x: bool(_strtobool(x)), default=False,
                        choices=[True, False],
                        help="Delete source and output files from LALAL.AI storage after download")

    args = parser.parse_args()

    # Load license from env / .env file
    try:
        license = load_license()
    except Exception as e:
        print(f"Error loading license: {e}")
        return

    # Default output dir
    if args.output is None:
        input_dir = os.path.dirname(args.input) if os.path.isfile(args.input) else args.input
        args.output = os.path.join(input_dir, "stems")

    _validate_stem(args.stem)
    _validate_multivocal(args.stem, args.multivocal)

    # noise_cancelling only relevant for 'voice' stem
    noise_cancelling = args.noise_cancelling if args.stem == "voice" else 1

    os.makedirs(args.output, exist_ok=True)
    batch_process(
        license, args.input, args.output, args.stem,
        noise_cancelling, args.dereverb_enabled, args.extraction_level,
        args.multivocal, args.delete, args.splitter,
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(err)
