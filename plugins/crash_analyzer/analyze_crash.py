#!/usr/bin/env python3
"""
Ableton Live Crash Report Analyzer

Loads an Ableton crash report .zip, parses Preferences/Log.txt,
categorizes errors, detects crash patterns, and suggests fixes.
Writes a report file alongside the input and prints a short summary.

Usage:
    python analyze_crash.py <crash_report.zip>
    python analyze_crash.py <Log.txt>
    python analyze_crash.py --all              # process every zip in Live Reports/
    python analyze_crash.py                    # auto-selects latest zip
"""

import argparse
import json
import os
import re
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

REPORTS_DIR = Path(__file__).parent / "Live Reports"
OUT_DIR = Path(__file__).parent / "Live Reports"

LOG_LINE_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2}T[\d:.]+):\s+(info|warning|error):\s+(.*)$"
)


# ── File loading ────────────────────────────────────────────────────────────

def find_latest_zip(directory: Path) -> Path | None:
    zips = sorted(directory.glob("*.zip"), key=lambda p: p.stat().st_mtime)
    return zips[-1] if zips else None


def extract_log_from_zip(zip_path: Path) -> str:
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        log_candidates = [n for n in names if os.path.basename(n) == "Log.txt"]
        pref_log = [n for n in log_candidates if "Preferences" in n]
        target = pref_log[0] if pref_log else (log_candidates[0] if log_candidates else None)
        if not target:
            print(f"⚠  No Log.txt found inside {zip_path.name}")
            print(f"   Archive contents: {names[:20]}")
            sys.exit(1)
        return zf.read(target).decode("utf-8", errors="replace")


def read_log_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


# ── Parsing helpers ─────────────────────────────────────────────────────────

def extract_system_info(text: str) -> dict:
    info = {}
    patterns = {
        "live_version": r"Started:\s+(.+)",
        "os": r"Init: OS:\s+'(.+)'",
        "hardware": r"Init: Hardware Model:\s+'(.+)'",
        "cpu": r"Init: CPU Brand String:\s+'(.+)'",
        "cpu_count": r"Init: CPU Count:\s+(\d+)",
        "ram_bytes": r"Init: Physical RAM:\s+(\d+)",
        "variant": r"Licensing: \[Variant=(\w+)\]",
    }
    for key, pat in patterns.items():
        m = re.search(pat, text)
        if m:
            info[key] = m.group(1)
    if "ram_bytes" in info:
        gb = int(info["ram_bytes"]) / (1024 ** 3)
        info["ram"] = f"{gb:.1f} GB"
    return info


def categorize_errors(lines: list[str]) -> dict:
    categories = defaultdict(list)
    for line in lines:
        m = LOG_LINE_RE.match(line)
        if not m:
            continue
        ts, level, msg = m.groups()
        if level != "error":
            continue
        if "RemoteScriptError" in msg:
            categories["remote_script_errors"].append((ts, msg))
        elif "FatalError" in msg or "Fatal error" in msg:
            categories["fatal_errors"].append((ts, msg))
        elif any(msg.startswith(p) for p in ("VST3:", "VST2:", "Audio Unit")):
            categories["plugin_errors"].append((ts, msg))
        elif "AudioIO:" in msg or "CoreAudio" in msg:
            categories["audio_errors"].append((ts, msg))
        elif "History:" in msg:
            categories["history_errors"].append((ts, msg))
        elif "Service Discovery" in msg:
            categories["service_errors"].append((ts, msg))
        elif "Error removing" in msg:
            categories["file_errors"].append((ts, msg))
        else:
            categories["other_errors"].append((ts, msg))
    return dict(categories)


def detect_crash_events(text: str) -> list[dict]:
    events = []
    for m in re.finditer(
        r"(\d{4}-\d{2}-\d{2}T[\d:.]+).*Detected a prior crash", text
    ):
        events.append({"type": "prior_crash", "timestamp": m.group(1)})
    for m in re.finditer(
        r"(\d{4}-\d{2}-\d{2}T[\d:.]+).*FatalError:\s+(.+)", text
    ):
        events.append({"type": "fatal", "timestamp": m.group(1), "detail": m.group(2)})
    for m in re.finditer(
        r"(\d{4}-\d{2}-\d{2}T[\d:.]+).*Fatal error:\s+(.+)", text
    ):
        events.append({"type": "fatal", "timestamp": m.group(1), "detail": m.group(2)})
    for m in re.finditer(
        r"(\d{4}-\d{2}-\d{2}T[\d:.]+).*Aborting with error code:\s+(\d+)", text
    ):
        events.append({"type": "abort", "timestamp": m.group(1), "code": m.group(2)})
    return events


def extract_failed_plugins(lines: list[str]) -> Counter:
    counter = Counter()
    for line in lines:
        m = re.search(r"error: (?:VST[23]|Audio Unit v\d): Restore \d+ failed: (.+)", line)
        if m:
            counter[m.group(1)] += 1
        m2 = re.search(r"error: (?:VST[23]|Audio Unit v\d): (?:Going to open|Scan).+failed.*?:\s*(.+)", line)
        if m2:
            counter[m2.group(1)] += 1
    return counter


def extract_memory_trend(text: str) -> list[tuple[str, float]]:
    trend = []
    for m in re.finditer(
        r"(\d{4}-\d{2}-\d{2}T[\d:.]+).*MemoryUsage:.*R:\s+([\d.]+)\s+(MB|GB)", text
    ):
        val = float(m.group(2))
        if m.group(3) == "GB":
            val *= 1024
        trend.append((m.group(1), val))
    return trend


def extract_crash_file_info(zip_path: Path) -> list[dict]:
    """Parse .ips crash dump files inside the zip for rich metadata."""
    crash_files = []
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            for name in zf.namelist():
                if not name.endswith(".ips"):
                    continue
                raw = zf.read(name).decode("utf-8", errors="replace")
                info = {"name": os.path.basename(name)}

                parts = raw.split("\n", 1)
                header = {}
                body = {}
                try:
                    header = json.loads(parts[0])
                except Exception:
                    pass
                if len(parts) > 1:
                    try:
                        body = json.loads(parts[1])
                    except Exception:
                        pass

                info["app_version"] = header.get("app_version", "")
                info["timestamp"] = header.get("timestamp", "")
                info["os_version"] = header.get("os_version", "")

                exc = body.get("exception", {})
                info["exception_type"] = exc.get("type", "")
                info["exception_subtype"] = exc.get("subtype", "")
                info["signal"] = exc.get("signal", "")

                term = body.get("termination", {})
                info["termination"] = term.get("indicator", "")

                info["proc_role"] = body.get("procRole", "")
                info["capture_time"] = body.get("captureTime", "")
                info["proc_launch"] = body.get("procLaunch", "")

                if body.get("threads"):
                    crashed = [t for t in body["threads"] if t.get("triggered")]
                    if crashed:
                        frames = crashed[0].get("frames", [])[:8]
                        info["crashed_thread_frames"] = [
                            str(f.get("symbol", f.get("imageOffset", "?"))) for f in frames
                        ]

                crash_files.append(info)
    except Exception:
        pass
    return crash_files


def extract_remote_script_issues(lines: list[str]) -> list[str]:
    scripts = set()
    for line in lines:
        m = re.search(r"RemoteScriptError.*import\s+(\S+)", line)
        if m:
            scripts.add(m.group(1))
    return sorted(scripts)


def extract_cpu_load(zip_path: Path) -> dict | None:
    """Parse CpuLoadLog.txt from the zip if present."""
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            candidates = [n for n in zf.namelist() if "CpuLoadLog" in n]
            if not candidates:
                return None
            raw = zf.read(candidates[0]).decode("utf-8", errors="replace")
            values = [float(x) for x in re.findall(r"([\d.]+)%?", raw) if float(x) <= 100]
            if not values:
                return None
            return {
                "samples": len(values),
                "avg": sum(values) / len(values),
                "peak": max(values),
            }
    except Exception:
        return None


def count_sessions(text: str) -> int:
    return len(re.findall(r"Started: Live \d+", text))


def extract_disk_space(text: str) -> list[dict]:
    """Return only the most recent disk space snapshot (last reporting block)."""
    all_entries = []
    for m in re.finditer(
        r'Volume "([^"]+)":\s+([\d.]+)\s+(GB|MB|KB)\s+of\s+([\d.]+)\s+(GB|MB|KB|TB)', text
    ):
        def to_gb(val, unit):
            val = float(val)
            return {"TB": val * 1024, "GB": val, "MB": val / 1024, "KB": val / (1024**2)}[unit]
        free = to_gb(m.group(2), m.group(3))
        total = to_gb(m.group(4), m.group(5))
        all_entries.append({"volume": m.group(1), "free_gb": free, "total_gb": total, "pos": m.start()})
    if not all_entries:
        return []
    last_pos = all_entries[-1]["pos"]
    last_block = []
    for e in reversed(all_entries):
        if last_pos - e["pos"] < 2000:
            last_block.append(e)
            last_pos = e["pos"]
        else:
            break
    last_block.reverse()
    return [{k: v for k, v in e.items() if k != "pos"} for e in last_block]


# ── Solution engine ─────────────────────────────────────────────────────────

def generate_solutions(
    errors: dict,
    crash_events: list,
    failed_plugins: Counter,
    memory_trend: list,
    remote_scripts: list,
    crash_files: list,
    sys_info: dict,
    disk_space: list,
) -> list[dict]:
    solutions = []

    ni_fatal = [e for e in crash_events if "boost::filesystem" in e.get("detail", "")]
    if ni_fatal:
        solutions.append({
            "severity": "CRITICAL",
            "issue": "Native Instruments filesystem crash (boost::filesystem::create_directories)",
            "fix": (
                "1. Run: sudo mkdir -p '/Users/Shared/Native Instruments/installed_products'\n"
                "2. Fix permissions: sudo chmod 755 '/Users/Shared/Native Instruments'\n"
                "3. Update Native Access and all NI products to the latest versions.\n"
                "4. If issue persists, reinstall NI products via Native Access."
            ),
        })

    for cf in crash_files:
        if cf.get("exception_type") in ("EXC_BAD_ACCESS", "EXC_BAD_INSTRUCTION"):
            solutions.append({
                "severity": "CRITICAL",
                "issue": (
                    f"Crash dump: {cf['exception_type']} ({cf.get('signal', '?')}) "
                    f"– {cf.get('exception_subtype', 'unknown')}"
                ),
                "fix": (
                    f"File: {cf['name']}\n"
                    f"Termination: {cf.get('termination', 'n/a')}\n"
                    "1. This is typically caused by a faulty plugin or memory corruption.\n"
                    "2. If the crash happens during project load, identify the last plugin\n"
                    "   being restored before the crash in the Log.txt.\n"
                    "3. Try launching with all third-party plugins disabled.\n"
                    "4. Update macOS and Ableton Live to the latest versions.\n"
                    "5. If 'pointer authentication failure' appears, a plugin may be\n"
                    "   incompatible with Apple Silicon – check for an ARM-native update."
                ),
            })

    audio_fatal = [e for e in crash_events if "audio engine" in e.get("detail", "").lower()]
    if audio_fatal:
        solutions.append({
            "severity": "CRITICAL",
            "issue": "Audio engine not responding",
            "fix": (
                "1. Increase audio buffer size: Preferences → Audio → Buffer Size (try 512 or 1024).\n"
                "2. Reduce CPU load: freeze/flatten tracks, or lower plugin count.\n"
                "3. Check for driver conflicts with external audio interfaces.\n"
                "4. Disable unused audio inputs/outputs in Preferences → Audio."
            ),
        })

    if failed_plugins:
        top = failed_plugins.most_common(5)
        names = ", ".join(f"{n} ({c}x)" for n, c in top)
        solutions.append({
            "severity": "HIGH",
            "issue": f"Plugins failing to restore: {names}",
            "fix": (
                "1. Update these plugins to their latest versions.\n"
                "2. If still failing, rescan plugins: Preferences → Plugins → Rescan.\n"
                "3. For persistent issues, delete the plugin cache at\n"
                "   ~/Library/Application Support/Ableton/Live Database/Live-plugins-1.db\n"
                "   and restart Live.\n"
                "4. Check plugin compatibility with your Live + macOS versions."
            ),
        })

    if remote_scripts:
        solutions.append({
            "severity": "MEDIUM",
            "issue": f"Remote script import errors: {', '.join(remote_scripts)}",
            "fix": (
                "1. Scripts with hyphens in names are invalid Python modules.\n"
                "   Rename folders: e.g., 'AbletonJS-New' → 'AbletonJS_New'.\n"
                "2. Remove unused remote scripts from:\n"
                "   ~/Library/Preferences/Ableton/Live <version>/User Remote Scripts/\n"
                "3. Or remove the script references from Options.txt."
            ),
        })

    if errors.get("audio_errors"):
        solutions.append({
            "severity": "MEDIUM",
            "issue": f"Audio I/O errors ({len(errors['audio_errors'])} occurrences)",
            "fix": (
                "1. Ensure your audio interface drivers are up-to-date.\n"
                "2. Try a different sample rate (44100 / 48000).\n"
                "3. Disconnect and reconnect the audio interface.\n"
                "4. Reset audio preferences by removing Preferences.cfg and restarting."
            ),
        })

    boot_disk = [d for d in disk_space if d["volume"] == "/"]
    if boot_disk and boot_disk[-1]["free_gb"] < 50:
        solutions.append({
            "severity": "HIGH",
            "issue": f"Low disk space on boot volume: {boot_disk[-1]['free_gb']:.1f} GB free of {boot_disk[-1]['total_gb']:.0f} GB",
            "fix": (
                "1. Free up disk space – Ableton needs room for undo history, cache, and temp files.\n"
                "2. Clear the Ableton cache: ~/Library/Caches/Ableton/\n"
                "3. Move sample libraries to an external drive.\n"
                "4. Aim for at least 50-100 GB free on the boot volume."
            ),
        })

    if errors.get("file_errors"):
        solutions.append({
            "severity": "LOW",
            "issue": f"File removal errors ({len(errors['file_errors'])} occurrences)",
            "fix": (
                "1. Clear the Ableton decoding cache:\n"
                "   rm -rf ~/Library/Caches/Ableton/Cache/Decoding/\n"
                "2. This is usually harmless and happens with moved/deleted audio files."
            ),
        })

    if memory_trend:
        peak_mb = max(v for _, v in memory_trend)
        if peak_mb > 4000:
            solutions.append({
                "severity": "HIGH",
                "issue": f"High memory usage detected (peak: {peak_mb:.0f} MB)",
                "fix": (
                    "1. Freeze memory-heavy instrument tracks (Kontakt, Omnisphere, etc.).\n"
                    "2. Close other applications while running Live.\n"
                    "3. Reduce the number of simultaneously loaded sample libraries.\n"
                    "4. Consider increasing virtual memory / swap."
                ),
            })

    crash_dates = set()
    for e in crash_events:
        if e["type"] == "prior_crash":
            crash_dates.add(e["timestamp"][:10])
    if len(crash_dates) >= 3:
        solutions.append({
            "severity": "HIGH",
            "issue": f"Recurring crashes detected on {len(crash_dates)} different days",
            "fix": (
                "1. Update Ableton Live to the latest version.\n"
                "2. Disable third-party plugins and re-enable one by one to isolate the culprit.\n"
                "3. Create a fresh user library: rename the preferences folder and restart.\n"
                "4. Report to Ableton Support with the crash report zip attached."
            ),
        })

    if not solutions:
        solutions.append({
            "severity": "INFO",
            "issue": "No critical issues detected",
            "fix": "The log looks healthy. Keep Live and plugins updated.",
        })

    return solutions


# ── Executive summary ──────────────────────────────────────────────────────

SEVERITY_ICON = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🔵", "INFO": "🟢"}
SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}


def build_executive_summary(
    sys_info: dict,
    crash_events: list,
    crash_files: list,
    failed_plugins: Counter,
    remote_scripts: list,
    memory_trend: list,
    errors: dict,
    solutions: list,
) -> str:
    """One-paragraph TL;DR of what went wrong and what to do."""
    bullets = []

    ni_fatal = [e for e in crash_events if "boost::filesystem" in e.get("detail", "")]
    if ni_fatal:
        bullets.append(
            "NI Kontakt/Reaktor triggers a fatal boost::filesystem crash "
            "— fixable with: sudo mkdir -p '/Users/Shared/Native Instruments/installed_products'"
        )

    for cf in crash_files:
        exc = cf.get("exception_type", "")
        sig = cf.get("signal", "")
        sub = cf.get("exception_subtype", "")
        if exc:
            tag = f"{exc} ({sig})" if sig else exc
            extra = ""
            if "pointer authentication" in sub.lower():
                extra = " — likely a plugin incompatibility on Apple Silicon"
            elif "KERN_INVALID_ADDRESS" in sub:
                extra = " — null-pointer dereference, likely a faulty plugin"
            bullets.append(f".ips crash dump shows {tag}{extra}")

    audio_fatal = [e for e in crash_events if "audio engine" in e.get("detail", "").lower()]
    if audio_fatal:
        bullets.append(
            "Audio engine stopped responding — increase buffer size or reduce plugin count"
        )

    if failed_plugins:
        top3 = [n for n, _ in failed_plugins.most_common(3)]
        bullets.append(f"{', '.join(top3)} are the most frequently failing plugins")

    if remote_scripts:
        bullets.append(
            f"Remote scripts {', '.join(remote_scripts)} fail because hyphens are invalid in Python module names"
        )

    if memory_trend:
        peak_mb = max(v for _, v in memory_trend)
        if peak_mb > 4000:
            bullets.append(f"Peak memory hit {peak_mb:.0f} MB — consider freezing heavy instruments")

    crash_dates = {e["timestamp"][:10] for e in crash_events if e["type"] == "prior_crash"}
    if len(crash_dates) >= 3:
        bullets.append(f"Crashes detected on {len(crash_dates)} different days — recurring instability")

    if not bullets:
        bullets.append("No critical issues found — log looks healthy")

    return "\n".join(f"  • {b}" for b in bullets)


# ── Report formatter ────────────────────────────────────────────────────────

def format_report(
    source: str,
    sys_info: dict,
    errors: dict,
    crash_events: list,
    failed_plugins: Counter,
    memory_trend: list,
    remote_scripts: list,
    crash_files: list,
    solutions: list,
    disk_space: list,
    cpu_load: dict | None,
    num_sessions: int,
) -> str:
    out = []
    w = out.append

    w("=" * 72)
    w("  ABLETON LIVE CRASH REPORT ANALYSIS")
    w("=" * 72)
    w(f"\nSource: {source}\n")

    summary = build_executive_summary(
        sys_info, crash_events, crash_files, failed_plugins,
        remote_scripts, memory_trend, errors, solutions,
    )
    w("── TL;DR ───────────────────────────────────────────────────")
    w(summary)

    w("\n── System Info ──────────────────────────────────────────────")
    for k in ("live_version", "os", "hardware", "cpu", "cpu_count", "ram", "variant"):
        if k in sys_info:
            label = k.replace("_", " ").title()
            w(f"  {label:20s}: {sys_info[k]}")
    w(f"  {'Sessions In Log':20s}: {num_sessions}")

    if disk_space:
        w("\n── Disk Space (at report time) ─────────────────────────────")
        for d in disk_space:
            pct = (d["free_gb"] / d["total_gb"] * 100) if d["total_gb"] else 0
            bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
            w(f"  {d['volume']:45s} {d['free_gb']:>7.1f} / {d['total_gb']:>7.0f} GB  [{bar}] {pct:.0f}% free")

    if cpu_load:
        w("\n── CPU Load ────────────────────────────────────────────────")
        w(f"  Samples: {cpu_load['samples']},  Avg: {cpu_load['avg']:.1f}%,  Peak: {cpu_load['peak']:.1f}%")

    w("\n── Crash Events ────────────────────────────────────────────")
    if crash_events:
        seen = set()
        for e in crash_events:
            key = (e["type"], e["timestamp"][:19])
            if key in seen:
                continue
            seen.add(key)
            detail = e.get("detail", e.get("code", ""))
            detail_short = (detail[:80] + "…") if len(detail) > 80 else detail
            w(f"  [{e['timestamp'][:19]}] {e['type'].upper():12s} {detail_short}")
    else:
        w("  None detected in Log.txt.")

    if crash_files:
        w("\n── Crash Dump Files (.ips) ─────────────────────────────────")
        for cf in crash_files:
            w(f"  📄 {cf['name']}")
            if cf.get("timestamp"):
                w(f"     Time:        {cf['timestamp']}")
            if cf.get("exception_type"):
                w(f"     Exception:   {cf['exception_type']} / {cf.get('signal', '?')}")
            if cf.get("exception_subtype"):
                w(f"     Subtype:     {cf['exception_subtype'][:100]}")
            if cf.get("termination"):
                w(f"     Termination: {cf['termination']}")
            if cf.get("proc_role"):
                w(f"     Proc Role:   {cf['proc_role']}")
            if cf.get("proc_launch"):
                w(f"     Launched:    {cf['proc_launch']}")
            if cf.get("crashed_thread_frames"):
                w(f"     Top frames:  {' → '.join(cf['crashed_thread_frames'][:5])}")

    w("\n── Error Summary ───────────────────────────────────────────")
    total = sum(len(v) for v in errors.values())
    w(f"  Total errors: {total}")
    for cat, items in sorted(errors.items(), key=lambda x: -len(x[1])):
        label = cat.replace("_", " ").title()
        w(f"    {label:30s}: {len(items):>5}")

    if failed_plugins:
        w("\n── Failed Plugins ──────────────────────────────────────────")
        for name, count in failed_plugins.most_common(15):
            w(f"    {name:45s}  ({count}x)")

    if remote_scripts:
        w("\n── Remote Script Issues ────────────────────────────────────")
        for s in remote_scripts:
            w(f"    • {s}")

    if memory_trend:
        peak = max(memory_trend, key=lambda x: x[1])
        low = min(memory_trend, key=lambda x: x[1])
        w("\n── Memory Usage (Resident) ─────────────────────────────────")
        w(f"  Samples: {len(memory_trend)}")
        w(f"  Low:  {low[1]:>8.1f} MB  at {low[0][:19]}")
        w(f"  Peak: {peak[1]:>8.1f} MB  at {peak[0][:19]}")

    w("\n" + "=" * 72)
    w("  SUGGESTED SOLUTIONS  (sorted by severity)")
    w("=" * 72)
    for i, sol in enumerate(sorted(solutions, key=lambda s: SEVERITY_ORDER.get(s["severity"], 5)), 1):
        icon = SEVERITY_ICON.get(sol["severity"], "⚪")
        w(f"\n{icon} [{sol['severity']}] Issue #{i}: {sol['issue']}")
        w("-" * 60)
        for fix_line in sol["fix"].split("\n"):
            w(f"  {fix_line}")

    w("\n" + "=" * 72)
    return "\n".join(out)


# ── Output file naming ─────────────────────────────────────────────────────

def make_report_filename(source_path: Path) -> str:
    """Derive 'Ableton_crash_analysis_report_2026-03-19_140424.txt' from source."""
    stem = source_path.stem
    m = re.search(r"(\d{4}-\d{2}-\d{2})\s+(\d{6})", stem)
    if m:
        date_part = m.group(1)
        time_part = m.group(2)
        return f"Ableton_crash_analysis_report_{date_part}_{time_part}.txt"
    clean = re.sub(r"[^\w\-.]", "_", stem)
    return f"Ableton_crash_analysis_report_{clean}.txt"


# ── Main ────────────────────────────────────────────────────────────────────

def analyze(source_path: Path) -> tuple[str, str]:
    """Returns (full_report, executive_summary)."""
    is_zip = source_path.suffix.lower() == ".zip"

    if is_zip:
        text = extract_log_from_zip(source_path)
        crash_files = extract_crash_file_info(source_path)
        cpu_load = extract_cpu_load(source_path)
    else:
        text = read_log_file(source_path)
        crash_files = []
        cpu_load = None

    lines = text.splitlines()

    sys_info = extract_system_info(text)
    errors = categorize_errors(lines)
    crash_events = detect_crash_events(text)
    failed_plugins = extract_failed_plugins(lines)
    memory_trend = extract_memory_trend(text)
    remote_scripts = extract_remote_script_issues(lines)
    disk_space = extract_disk_space(text)
    num_sessions = count_sessions(text)

    solutions = generate_solutions(
        errors, crash_events, failed_plugins, memory_trend,
        remote_scripts, crash_files, sys_info, disk_space,
    )

    summary = build_executive_summary(
        sys_info, crash_events, crash_files, failed_plugins,
        remote_scripts, memory_trend, errors, solutions,
    )

    report = format_report(
        source=str(source_path),
        sys_info=sys_info,
        errors=errors,
        crash_events=crash_events,
        failed_plugins=failed_plugins,
        memory_trend=memory_trend,
        remote_scripts=remote_scripts,
        crash_files=crash_files,
        solutions=solutions,
        disk_space=disk_space,
        cpu_load=cpu_load,
        num_sessions=num_sessions,
    )

    return report, summary


def process_one(source: Path) -> None:
    """Analyze one file, write report, print summary."""
    report, summary = analyze(source)

    report_name = make_report_filename(source)
    report_path = OUT_DIR / report_name
    report_path.write_text(report, encoding="utf-8")

    print(f"{'─' * 72}")
    print(f"  📋 {source.name}")
    print(f"{'─' * 72}")
    print(summary)
    print(f"\n  → Report saved: {report_path}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze Ableton Live crash reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python analyze_crash.py 'Live Reports/crash.zip'   # single file\n"
            "  python analyze_crash.py --all                       # all zips in Live Reports/\n"
            "  python analyze_crash.py                             # latest zip\n"
            "  python analyze_crash.py --all --verbose             # all zips, full report to stdout"
        ),
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="Path to a crash report .zip or Log.txt. "
             "If omitted, uses the latest .zip in Live Reports/.",
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Process every .zip in Live Reports/.",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Also print the full report to stdout (not just the summary).",
    )
    args = parser.parse_args()

    sources: list[Path] = []

    if args.all:
        sources = sorted(REPORTS_DIR.glob("*.zip"), key=lambda p: p.stat().st_mtime)
        if not sources:
            print(f"No .zip files found in {REPORTS_DIR}")
            sys.exit(1)
    elif args.input:
        sources = [Path(args.input)]
    else:
        latest = find_latest_zip(REPORTS_DIR)
        if not latest:
            print(f"No .zip files found in {REPORTS_DIR}")
            sys.exit(1)
        sources = [latest]

    for source in sources:
        if not source.exists():
            print(f"⚠  File not found: {source}")
            continue

        if args.verbose:
            report, summary = analyze(source)
            report_name = make_report_filename(source)
            report_path = OUT_DIR / report_name
            report_path.write_text(report, encoding="utf-8")
            print(report)
            print(f"  → Report saved: {report_path}\n")
        else:
            process_one(source)


if __name__ == "__main__":
    main()
