#!/usr/bin/env python3
"""
Compare recommended plugins (from mentor) against installed VST3/AU plugins on macOS.
Reports which recommended plugins are found and which are missing.
"""

import os
import re
import sys
from pathlib import Path

VST3_DIRS = [
    Path("/Library/Audio/Plug-Ins/VST3"),
    Path.home() / "Library/Audio/Plug-Ins/VST3",
]

AU_DIRS = [
    Path("/Library/Audio/Plug-Ins/Components"),
    Path.home() / "Library/Audio/Plug-Ins/Components",
]

WAVES_DIRS = [
    Path("/Applications/Waves/Plug-Ins V16"),
    Path("/Applications/Waves/Plug-Ins V14"),
]

RECOMMENDED_PLUGINS = {
    "FUSER": {
        "search": ["fuser"],
        "vendor": "Native Instruments",
    },
    "bx_digital V3": {
        "search": ["bx_digital"],
        "vendor": "Brainworx / Plugin Alliance",
    },
    "bx_limiter": {
        "search": ["bx_limiter"],
        "vendor": "Brainworx / Plugin Alliance",
    },
    "Elevate Mastering Bundle": {
        "search": ["elevate"],
        "vendor": "Newfangled Audio / Eventide",
    },
    "NLS Buss": {
        "search": ["nls"],
        "vendor": "Waves",
    },
    "S1 Stereo Imager": {
        "search": ["s1 stereo", "s1stereo"],
        "vendor": "Waves",
    },
    "Shadow Hills Mastering Compressor": {
        "search": ["shadow hills"],
        "vendor": "Plugin Alliance / Brainworx",
    },
    "ShaperBox 3 Bundle": {
        "search": ["shaperbox"],
        "vendor": "Cableguys",
    },
    "LoAir": {
        "search": ["loair"],
        "vendor": "Waves",
    },
    "Black Box Analog Design HG-2": {
        "search": ["hg-2", "hg2", "black box"],
        "vendor": "Plugin Alliance / Brainworx",
    },
    "VocAlign 6 Pro": {
        "search": ["vocalign"],
        "vendor": "Synchro Arts",
    },
    "FabFilter Pro-Q 4": {
        "search": ["fabfilter", "pro-q", "pro q"],
        "vendor": "FabFilter",
    },
    "Soundtoys Bundle": {
        "search": ["soundtoys", "decapitator", "echoboy", "little alterboy", "radiator"],
        "vendor": "Soundtoys",
    },
    "Valhalla VintageVerb": {
        "search": ["valhallavintageverb", "valhalla vintage verb"],
        "vendor": "Valhalla DSP",
    },
    "Valhalla Room": {
        "search": ["valhallaroom"],
        "vendor": "Valhalla DSP",
    },
    "Valhalla Shimmer": {
        "search": ["valhallashimmer"],
        "vendor": "Valhalla DSP",
    },
    "Soothe 2": {
        "search": ["soothe"],
        "vendor": "oeksound",
    },
    "Trackspacer": {
        "search": ["trackspacer"],
        "vendor": "Wavesfactory",
    },
    "Kickstart 2": {
        "search": ["kickstart"],
        "vendor": "Nicky Romero / Cableguys",
    },
    "Metric AB (ADPTR)": {
        "search": ["metricab", "metric ab", "adptr"],
        "vendor": "ADPTR Audio / Plugin Alliance",
    },
    "SplitEQ": {
        "search": ["spliteq"],
        "vendor": "Eventide",
    },
    "Neutron Transient Shaper": {
        "search": ["neutron"],
        "vendor": "iZotope",
    },
    "Seventh Heaven Reverb": {
        "search": ["seventh heaven", "7th heaven"],
        "vendor": "LiquidSonics",
    },
    "Raum": {
        "search": ["raum"],
        "vendor": "Native Instruments",
    },
    "Maag EQ6": {
        "search": ["maag"],
        "vendor": "Plugin Alliance",
    },
    "Sugar": {
        "search": ["sugar"],
        "vendor": "Plugin Alliance",
    },
    "Limitless": {
        "search": ["limitless"],
        "vendor": "DMG Audio",
    },
    "Ozone": {
        "search": ["ozone"],
        "vendor": "iZotope",
    },
    "Invisible Limiter": {
        "search": ["invisible limiter"],
        "vendor": "AOM",
    },
    "Antares Auto-Tune": {
        "search": ["autotune", "auto-tune", "auto tune", "antares"],
        "vendor": "Antares",
    },
    "Melodyne": {
        "search": ["melodyne"],
        "vendor": "Celemony",
    },
    "Waves C4": {
        "search": ["waves c4", "c4.bundle"],
        "vendor": "Waves",
    },
    "Waves Rvox": {
        "search": ["rvox"],
        "vendor": "Waves",
    },
    "Waves CLA Vocals": {
        "search": ["cla vocals", "cla-vocals"],
        "vendor": "Waves",
    },
}


def scan_plugins() -> list[str]:
    """Scan all plugin directories and return normalized plugin names."""
    installed = []

    for dirs, ext in [(VST3_DIRS, ".vst3"), (AU_DIRS, ".component")]:
        for d in dirs:
            if not d.is_dir():
                continue
            for entry in d.iterdir():
                name = entry.name
                if name.endswith(ext):
                    name = name[: -len(ext)]
                installed.append(name)

    for d in WAVES_DIRS:
        if not d.is_dir():
            continue
        for entry in d.iterdir():
            if entry.suffix == ".bundle":
                installed.append(entry.stem)

    return sorted(set(installed))


def check_plugin(search_terms: list[str], installed: list[str]) -> str | None:
    """Return the installed plugin name if any search term matches, else None."""
    installed_lower = {p.lower().replace(" ", ""): p for p in installed}
    for term in search_terms:
        term_normalized = term.lower().replace(" ", "")
        for inst_key, inst_name in installed_lower.items():
            if term_normalized in inst_key or inst_key in term_normalized:
                return inst_name
    return None


def main():
    installed = scan_plugins()

    found = []
    missing = []

    for plugin_name, info in RECOMMENDED_PLUGINS.items():
        match = check_plugin(info["search"], installed)
        if match:
            found.append((plugin_name, match))
        else:
            missing.append((plugin_name, info["vendor"]))

    print("=" * 65)
    print("  RECOMMENDED PLUGINS — INSTALLATION CHECK")
    print("=" * 65)
    print(f"\n  Scanned {len(installed)} unique plugins across VST3, AU, and Waves\n")

    print("-" * 65)
    print(f"  INSTALLED ({len(found)}/{len(RECOMMENDED_PLUGINS)})")
    print("-" * 65)
    for plugin_name, matched_as in found:
        print(f"  [OK]  {plugin_name:<40} -> {matched_as}")

    print()
    print("-" * 65)
    print(f"  MISSING ({len(missing)}/{len(RECOMMENDED_PLUGINS)})")
    print("-" * 65)
    for plugin_name, vendor in missing:
        print(f"  [ ]   {plugin_name:<40}   ({vendor})")

    print()
    print("=" * 65)
    print(f"  Summary: {len(found)} installed, {len(missing)} missing")
    print("=" * 65)

    if missing:
        print("\n  Shopping list:")
        vendors: dict[str, list[str]] = {}
        for plugin_name, vendor in missing:
            vendors.setdefault(vendor, []).append(plugin_name)
        for vendor, plugins in sorted(vendors.items()):
            print(f"\n    {vendor}:")
            for p in plugins:
                print(f"      - {p}")
        print()

    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
