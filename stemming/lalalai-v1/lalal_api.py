"""Shared LALAL.AI API v1 operations for local command-line tools."""

from __future__ import annotations

import json
import mimetypes
from email.message import EmailMessage
from pathlib import Path
from urllib.parse import quote, unquote, urlparse

import requests


API_URL = "https://www.lalal.ai/api/v1/"
MODELS = ("auto", "andromeda", "perseus", "orion", "phoenix")
EXTRACTION_LEVELS = ("deep_extraction", "clear_cut")
SUPPORTED_AUDIO_EXTENSIONS = {
    ".aac",
    ".aif",
    ".aiff",
    ".flac",
    ".m4a",
    ".mp3",
    ".ogg",
    ".wav",
}

_STEM_LABELS = {
    "vocals": {"vocal", "vocals"},
    "drum": {"drum", "drums"},
    "bass": {"bass"},
    "piano": {"piano"},
    "guitar": {"guitar"},
    "electric_guitar": {"electric_guitar"},
    "acoustic_guitar": {"acoustic_guitar"},
    "synthesizer": {"synth", "synthesizer"},
    "strings": {"string", "strings"},
    "wind": {"wind", "winds"},
}


class LalalError(RuntimeError):
    """Actionable error raised by the local LALAL.AI clients."""


def normalize_label(value: object) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def api_request(method: str, path: str, key: str, timeout: int, **kwargs) -> dict:
    headers = dict(kwargs.pop("headers", {}))
    headers["X-License-Key"] = key
    try:
        response = requests.request(
            method, API_URL + path, headers=headers, timeout=timeout, **kwargs
        )
    except requests.RequestException as exc:
        raise LalalError(f"{path}: network request failed: {exc}") from exc
    if response.status_code != 200:
        detail = response.text.strip() or "empty response"
        raise LalalError(f"{path}: HTTP {response.status_code}: {detail}")
    try:
        payload = response.json()
    except ValueError as exc:
        raise LalalError(f"{path}: invalid JSON response") from exc
    if not isinstance(payload, dict):
        raise LalalError(f"{path}: expected a JSON object")
    return payload


def make_content_disposition(filename: str) -> str:
    if "\r" in filename or "\n" in filename:
        raise LalalError("input filename contains an invalid newline")
    try:
        filename.encode("ascii")
    except UnicodeEncodeError:
        return f"attachment; filename*=utf-8''{quote(filename)}"
    escaped = filename.replace('"', "_")
    return f'attachment; filename="{escaped}"'


def upload_file(path: Path, key: str, timeout: int) -> str:
    with path.open("rb") as source:
        payload = api_request(
            "POST",
            "upload/",
            key,
            timeout,
            headers={"Content-Disposition": make_content_disposition(path.name)},
            data=source,
        )
    source_id = payload.get("id")
    if not source_id:
        raise LalalError("upload: response did not include a source id")
    return str(source_id)


def start_stem_task(
    source_id: str,
    stem: str,
    key: str,
    splitter: str,
    extraction_level: str,
    dereverb: bool,
    timeout: int,
) -> str:
    presets: dict[str, object] = {
        "stem": stem,
        "extraction_level": extraction_level,
        "splitter": splitter,
    }
    if dereverb:
        presets["dereverb_enabled"] = True
    payload = api_request(
        "POST",
        "split/stem_separator/",
        key,
        timeout,
        json={"source_id": source_id, "presets": presets},
    )
    task_id = payload.get("task_id")
    if not task_id:
        raise LalalError(f"{stem}: response did not include a task id")
    return str(task_id)


def wait_for_tasks(
    tasks: dict[str, str],
    key: str,
    timeout: int,
    poll_interval: float,
    quiet: bool,
    sleep,
) -> dict[str, list[dict]]:
    """Poll several task IDs together and return tracks keyed by caller label."""
    pending = dict(tasks)
    completed: dict[str, list[dict]] = {}
    last_progress: dict[str, int] = {}
    while pending:
        payload = api_request(
            "POST",
            "check/",
            key,
            timeout,
            json={"task_ids": list(pending.values())},
        )
        states = payload.get("result")
        if not isinstance(states, dict):
            raise LalalError("check: response did not include task results")
        for label, task_id in list(pending.items()):
            state = states.get(task_id)
            if not isinstance(state, dict):
                raise LalalError(f"{label}: task missing from check response")
            status = state.get("status")
            if status == "success":
                tracks = state.get("result", {}).get("tracks")
                if not isinstance(tracks, list) or not tracks:
                    raise LalalError(f"{label}: successful task returned no tracks")
                completed[label] = tracks
                pending.pop(label)
                if not quiet:
                    print(f"      {label}: complete")
            elif status == "progress":
                progress = int(state.get("progress", 0))
                if not quiet and last_progress.get(label) != progress:
                    print(f"      {label}: {progress}%")
                last_progress[label] = progress
            elif status in {"cancelled", "error", "server_error"}:
                error = state.get("error", "unknown API error")
                raise LalalError(f"{label}: task {status}: {error}")
            else:
                raise LalalError(f"{label}: unknown task status: {status}")
        if pending:
            sleep(poll_interval)
    return completed


def select_track_pair(tracks: list[dict], stem: str) -> tuple[dict, dict]:
    aliases = _STEM_LABELS.get(stem)
    if not aliases:
        raise LalalError(f"unsupported stem for track mapping: {stem}")
    isolated = [track for track in tracks if normalize_label(track.get("label")) in aliases]
    if len(isolated) != 1:
        labels = [track.get("label") for track in tracks]
        raise LalalError(f"cannot identify {stem} from API labels: {labels}")
    complement = [track for track in tracks if track is not isolated[0]]
    if len(complement) != 1:
        labels = [track.get("label") for track in tracks]
        raise LalalError(f"expected one complementary track; API labels: {labels}")
    return isolated[0], complement[0]


def delete_remote(source_id: str, key: str, timeout: int) -> None:
    api_request("POST", "delete/", key, timeout, json={"source_id": source_id})


def _content_disposition_filename(header: str) -> str | None:
    if not header:
        return None
    message = EmailMessage()
    message["content-disposition"] = header
    filename = message.get_filename()
    if filename:
        return filename
    for segment in header.split(";"):
        segment = segment.strip()
        if not segment.lower().startswith("filename*="):
            continue
        value = segment.split("=", 1)[1].strip().strip('"')
        if "''" in value:
            encoding, quoted = value.split("''", 1)
            return unquote(quoted, encoding or "utf-8")
    return None


def _declared_extension(response: requests.Response, url: str) -> str | None:
    filename = _content_disposition_filename(
        response.headers.get("Content-Disposition", "")
    )
    candidates = []
    if filename:
        candidates.append(Path(filename).suffix.lower())
    content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip()
    if content_type:
        candidates.append((mimetypes.guess_extension(content_type) or "").lower())
    candidates.append(Path(urlparse(url).path).suffix.lower())
    for extension in candidates:
        if extension == ".mpga":
            extension = ".mp3"
        if extension in SUPPORTED_AUDIO_EXTENSIONS:
            return extension
    return None


def detect_audio_extension(path: Path) -> str:
    """Detect the downloaded audio container from its bytes, not the input suffix."""
    with path.open("rb") as source:
        header = source.read(64)
    if len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WAVE":
        return ".wav"
    if header.startswith(b"fLaC"):
        return ".flac"
    if header.startswith(b"OggS"):
        return ".ogg"
    if header.startswith(b"ADIF"):
        return ".aac"
    if len(header) >= 2 and header[0] == 0xFF and header[1] & 0xF6 == 0xF0:
        return ".aac"
    if header.startswith(b"ID3") or (
        len(header) >= 2
        and header[0] == 0xFF
        and header[1] & 0xE0 == 0xE0
        and header[1] & 0x06 != 0
    ):
        return ".mp3"
    if len(header) >= 12 and header[4:8] == b"ftyp":
        return ".m4a"
    if len(header) >= 12 and header[:4] == b"FORM" and header[8:12] in {b"AIFF", b"AIFC"}:
        return ".aiff"
    raise LalalError("downloaded track is empty or not a supported audio format")


def artifact_stem(source_name: str, output_label: str) -> str:
    return f"{source_name}_{output_label}_lalalai"


def find_artifacts(output_dir: Path, source_name: str, output_label: str) -> list[Path]:
    prefix = artifact_stem(source_name, output_label)
    return sorted(
        path
        for path in output_dir.glob(f"{prefix}.*")
        if path.is_file()
        and path.suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS
        and not path.name.endswith(".part")
    )


def validate_existing_artifact(path: Path) -> None:
    detected = detect_audio_extension(path)
    suffix = path.suffix.lower()
    equivalent = {detected, suffix} <= {".aif", ".aiff"}
    if detected != suffix and not equivalent:
        raise LalalError(
            f"existing output has mismatched format ({suffix} name, {detected} data): {path}"
        )


def resolve_outputs(
    output_dir: Path,
    source_name: str,
    output_labels: list[str],
    resume: bool,
    overwrite: bool,
) -> dict[str, Path | None]:
    """Resolve reusable outputs before any paid API request is started."""
    resolved: dict[str, Path | None] = {}
    for label in output_labels:
        matches = find_artifacts(output_dir, source_name, label)
        if overwrite:
            resolved[label] = None
            continue
        if len(matches) > 1:
            raise LalalError(
                f"multiple outputs found for {label}: {[path.name for path in matches]}"
            )
        if matches:
            if not resume:
                raise LalalError(
                    f"output exists: {matches[0]} (use --resume or --overwrite)"
                )
            validate_existing_artifact(matches[0])
            resolved[label] = matches[0]
        else:
            resolved[label] = None
    return resolved


def download_track(
    track: dict,
    output_dir: Path,
    source_name: str,
    output_label: str,
    timeout: int,
    overwrite: bool,
) -> Path:
    url = track.get("url")
    if not isinstance(url, str) or not url:
        raise LalalError(f"{output_label}: API track did not include a download URL")
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = artifact_stem(source_name, output_label)
    partial = output_dir / f".{prefix}.download.part"
    partial.unlink(missing_ok=True)
    try:
        try:
            response = requests.get(url, stream=True, timeout=timeout)
        except requests.RequestException as exc:
            raise LalalError(f"{output_label}: download request failed: {exc}") from exc
        with response:
            if response.status_code != 200:
                raise LalalError(
                    f"{output_label}: download HTTP {response.status_code}"
                )
            declared = _declared_extension(response, url)
            with partial.open("wb") as target:
                for chunk in response.iter_content(1024 * 1024):
                    if chunk:
                        target.write(chunk)
        detected = detect_audio_extension(partial)
        if declared and declared != detected and not {declared, detected} <= {".aif", ".aiff"}:
            raise LalalError(
                f"{output_label}: response declared {declared} but contained {detected} audio"
            )
        destination = output_dir / f"{prefix}{detected}"
        existing = find_artifacts(output_dir, source_name, output_label)
        if existing and not overwrite:
            raise LalalError(
                f"output exists: {existing[0]} (use --resume or --overwrite)"
            )
        if overwrite:
            for old_path in existing:
                if old_path != destination:
                    old_path.unlink()
        partial.replace(destination)
        return destination
    finally:
        partial.unlink(missing_ok=True)
