#!/usr/bin/env python3
import os
import re
from collections import defaultdict
import json
from config import SAMPLES_PRESETS_PATH, OUTPUT_DIR

# File paths for this script
OUTPUT_FILES = {
    'sample_analysis': f"{OUTPUT_DIR}/sample_analysis_results.json"
}

# Comprehensive sample categories
sample_categories = [
    "kick", "snare", "clap", "hat", "hihat", "hh", "ride", "cymbal", "crash",
    "tom", "perc", "percussion", "shaker", "tambourine", "conga", "bongo",
    "rim", "click", "snap", "foley", "drum", "break", "fill", "groove",
    "bass", "sub", "low", "808", "reese", "pluck",
    "arp", "chord", "pad", "lead", "melody", "melodic", "synth", "keys",
    "piano", "organ", "string", "brass", "wind",
    "stab", "hit", "shot", "oneshot", "one-shot",
    "drone", "atmosphere", "atmo", "ambient", "texture", "soundscape",
    "vocal", "vox", "voice", "chant", "choir", "adlib", "topline", "hook",
    "fx", "sfx", "effect", "riser", "impact", "downlifter", "sweep", "whoosh",
    "transition", "build", "drop", "noise", "glitch", "reverse", "filter",
    "loop", "phrase", "pattern", "sequence",
    "tonal", "note", "pitch"
]

# Initialize counters
category_counts = defaultdict(int)
loop_vs_oneshot = defaultdict(int)
bpm_distribution = defaultdict(int)
key_distribution = defaultdict(int)
total_wavs = 0
samples_by_category = defaultdict(list)

# Find all wav files
print("Scanning for .wav files...")
wav_files = []
for root, dirs, files in os.walk(SAMPLES_PRESETS_PATH):
    for file in files:
        if file.lower().endswith(('.wav', '.wav', '.wav')):
            wav_files.append(os.path.join(root, file))

print(f"Found {len(wav_files)} wav files. Analyzing...")

# Analyze each file
for wav_file in wav_files:
    total_wavs += 1
    full_path_lower = wav_file.lower()
    basename = os.path.basename(wav_file)
    basename_lower = basename.lower()
    dirname_lower = os.path.dirname(wav_file).lower()
    
    # Extract BPM if present
    bpm_match = re.search(r'(\d{2,3})\s*bpm', full_path_lower)
    if bpm_match:
        bpm = int(bpm_match.group(1))
        bpm_distribution[f"{(bpm//10)*10}-{(bpm//10)*10+9}"] += 1
    
    # Extract key if present
    key_patterns = [
        r'([a-g]#?)(min|maj|m\b)', # matches C#min, Cmaj, Am
        r'([a-g]#?)\s*(minor|major)',
        r'_([a-g]#?)_', # matches _C_
        r'\b([a-g]#?)\b(?!bpm|db|wav|mp3)' # standalone notes
    ]
    for pattern in key_patterns:
        key_match = re.search(pattern, basename_lower)
        if key_match:
            key = key_match.group(1).upper()
            if len(key_match.groups()) > 1 and key_match.group(2):
                key += key_match.group(2)[:3]
            key_distribution[key] += 1
            break
    
    # Check categories
    found_categories = []
    for category in sample_categories:
        # Check in filename and parent directory names
        if category in basename_lower or category in dirname_lower:
            category_counts[category] += 1
            found_categories.append(category)
    
    # Store sample info
    if found_categories:
        samples_by_category[', '.join(found_categories[:3])].append(basename[:50])
    
    # Loop vs oneshot detection
    if any(term in full_path_lower for term in ['loop', 'loops', 'phrase']):
        loop_vs_oneshot['loops'] += 1
    elif any(term in full_path_lower for term in ['oneshot', 'one shot', 'one-shot', 'hit', 'stab']):
        loop_vs_oneshot['oneshots'] += 1
    elif 'drum' in dirname_lower and 'loop' not in dirname_lower:
        loop_vs_oneshot['drum_hits'] += 1
    else:
        loop_vs_oneshot['unclear'] += 1

# Generate report
print("\n" + "="*60)
print("SAMPLE ANALYSIS REPORT")
print("="*60)
print(f"\nTotal .wav files analyzed: {total_wavs:,}")

print("\n--- TOP 20 CATEGORIES BY COUNT ---")
sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:20]
for category, count in sorted_categories:
    percentage = (count / total_wavs) * 100
    print(f"{category:20} {count:6,} files ({percentage:5.1f}%)")

print("\n--- LOOP vs ONE-SHOT ANALYSIS ---")
for type_name, count in sorted(loop_vs_oneshot.items(), key=lambda x: x[1], reverse=True):
    percentage = (count / total_wavs) * 100
    print(f"{type_name:20} {count:6,} files ({percentage:5.1f}%)")

print("\n--- BPM DISTRIBUTION ---")
for bpm_range, count in sorted(bpm_distribution.items()):
    print(f"{bpm_range:10} BPM: {count:6,} files")

print("\n--- TOP 15 MUSICAL KEYS ---")
sorted_keys = sorted(key_distribution.items(), key=lambda x: x[1], reverse=True)[:15]
for key, count in sorted_keys:
    print(f"{key:10} {count:6,} files")

print("\n--- SAMPLE EXAMPLES BY CATEGORY ---")
for category, samples in list(samples_by_category.items())[:10]:
    print(f"\n{category}:")
    for sample in samples[:3]:
        print(f"  - {sample}")

# Save detailed results
results = {
    'total_files': total_wavs,
    'categories': dict(sorted_categories),
    'loop_types': dict(loop_vs_oneshot),
    'bpm_distribution': dict(bpm_distribution),
    'key_distribution': dict(sorted(key_distribution.items(), key=lambda x: x[1], reverse=True)),
    'sample_examples': {k: v[:5] for k, v in list(samples_by_category.items())[:20]}
}

with open(OUTPUT_FILES['sample_analysis'], 'w') as f:
    json.dump(results, f, indent=2)

print(f"\nDetailed results saved to {OUTPUT_FILES['sample_analysis']}")