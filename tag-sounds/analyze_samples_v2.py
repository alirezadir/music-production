#!/usr/bin/env python3
import os
import re
import json
from collections import defaultdict, Counter
from config import SAMPLES_PRESETS_PATH, OUTPUT_DIR

# File paths for this script
INPUT_FILES = {
    'tags_categories': 'tags_categories_modified.json',
    'synonym_map': 'synonym_map.json'
}

OUTPUT_FILES = {
    'frequency_analysis': f"{OUTPUT_DIR}/frequency_analysis_results.txt",
    'detailed_results': f"{OUTPUT_DIR}/detailed_tagging_results.json"
}

def load_synonym_map():
    """Load synonym mapping from JSON file"""
    try:
        with open(INPUT_FILES['synonym_map'], 'r') as f:
            synonym_map = json.load(f)
        print(f"✅ Loaded {len(synonym_map)} synonym mappings from {INPUT_FILES['synonym_map']}")
        return synonym_map
    except FileNotFoundError:
        print(f"⚠️  Warning: {INPUT_FILES['synonym_map']} not found! Using empty synonym map.")
        return {}
    except json.JSONDecodeError:
        print(f"⚠️  Warning: Invalid JSON in {INPUT_FILES['synonym_map']}! Using empty synonym map.")
        return {}

def normalize_token(token: str, synonym_map: dict) -> str:
    """Normalize a single token using synonym mapping and plural stripping"""
    # 1. Normalize casing
    token = token.lower()
    
    # 2. Strip plurals (only for words > 3 letters to avoid "hh" → "h")
    if token.endswith("s") and len(token) > 3:
        token = token[:-1]
    
    # 3. Apply synonym map
    normalized_token = synonym_map.get(token, token)
    
    return normalized_token

def load_categories():
    """Load tag categories from JSON file"""
    try:
        with open(INPUT_FILES['tags_categories'], 'r') as f:
            categories = json.load(f)
        print(f"✅ Loaded {len(categories)} categories from {INPUT_FILES['tags_categories']}")
        return categories
    except FileNotFoundError:
        print(f"❌ Error: {INPUT_FILES['tags_categories']} not found!")
        return {}
    except json.JSONDecodeError:
        print(f"❌ Error: Invalid JSON in {INPUT_FILES['tags_categories']}")
        return {}

def extract_tokens_from_path(filepath, synonym_map):
    """Extract and normalize meaningful tokens from filepath"""
    # Get filename and directory path
    filename = os.path.basename(filepath).lower()
    dirname = os.path.dirname(filepath).lower()
    
    # Remove file extension
    filename = os.path.splitext(filename)[0]
    
    # Split by common delimiters
    raw_tokens = re.split(r'[-_\s\.\(\)\[\]]+', filename + ' ' + dirname)
    
    # Filter and normalize tokens
    meaningful_tokens = []
    stop_words = {'the', 'and', 'vol', 'version', 'remix', 'edit', 'wav', 'audio', 
                  'sound', 'sample', 'pack', 'stereo', 'mono', 'dry', 'wet', 'of', 'in', 'to'}
    
    for token in raw_tokens:
        if (len(token) > 2 and 
            not token.isdigit() and 
            token not in stop_words and
            not re.match(r'^\d+$', token) and
            not re.match(r'.*bpm.*', token) and
            not re.match(r'[a-g]#?(maj|min|m)$', token)):  # Skip musical keys
            
            # Normalize the token
            normalized_token = normalize_token(token, synonym_map)
            meaningful_tokens.append(normalized_token)
    
    # 5. Deduplicate final tag set
    return list(set(meaningful_tokens))

def extract_bpm_and_key(filepath):
    """Extract BPM and Key from filepath"""
    full_path_lower = filepath.lower()
    basename_lower = os.path.basename(filepath).lower()
    
    # Extract BPM
    bpm = None
    bpm_match = re.search(r'(\d{2,3})\s*bpm', full_path_lower)
    if bpm_match:
        bpm = int(bpm_match.group(1))
    
    # Extract key
    key = None
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
            break
    
    return bpm, key

def tag_file(filepath, categories, synonym_map):
    """Tag a single file based on categories with normalized tokens"""
    tokens = extract_tokens_from_path(filepath, synonym_map)
    found_tags = defaultdict(list)
    
    # Check each category with normalized comparison
    for category_name, category_tags in categories.items():
        for tag in category_tags:
            # Normalize the category tag for comparison
            normalized_tag = normalize_token(tag, synonym_map)
            if normalized_tag in tokens:
                found_tags[category_name].append(tag)  # Keep original tag name
    
    # Ensure at least one CATEGORY_1 tag
    if not found_tags.get('CATEGORY_1'):
        # Try to find a CATEGORY_1 tag based on context
        for category_name, category_tags in categories.items():
            if category_name == 'CATEGORY_1':
                for tag in category_tags:
                    normalized_tag = normalize_token(tag, synonym_map)
                    if normalized_tag in tokens:
                        found_tags['CATEGORY_1'].append(tag)
                        break
                if found_tags['CATEGORY_1']:
                    break
        
        # If still no CATEGORY_1, use a default based on CATEGORY_2
        if not found_tags.get('CATEGORY_1') and found_tags.get('CATEGORY_2'):
            # Map CATEGORY_2 to CATEGORY_1
            cat2_to_cat1_mapping = {
                'kick': 'drums', 'snare': 'drums', 'clap': 'drums', 'hat': 'drums',
                'hihat': 'drums', 'ride': 'drums', 'crash': 'drums', 'tom': 'drums',
                'perc': 'drums', 'percussion': 'drums', 'shaker': 'drums',
                'bass': 'bass', 'sub': 'bass', 'subbass': 'bass', 'low': 'bass',
                'synth': 'synth', 'lead': 'synth', 'pad': 'synth', 'arp': 'synth',
                'vocal': 'vocal', 'vox': 'vocal', 'voice': 'vocal', 'female': 'vocal',
                'male': 'vocal', 'choir': 'vocal', 'chant': 'vocal',
                'fx': 'fx', 'sfx': 'fx', 'effect': 'fx', 'riser': 'fx', 'impact': 'fx',
                'melody': 'melody', 'melodic': 'melody', 'chord': 'melody',
                'piano': 'instrument', 'guitar': 'instrument', 'string': 'instrument',
                'sequence': 'sequence', 'songstarter': 'songstarter'
            }
            
            for cat2_tag in found_tags['CATEGORY_2']:
                if cat2_tag in cat2_to_cat1_mapping:
                    found_tags['CATEGORY_1'].append(cat2_to_cat1_mapping[cat2_tag])
                    break
            
            # If still no mapping, use the first CATEGORY_2 tag as CATEGORY_1
            if not found_tags.get('CATEGORY_1') and found_tags.get('CATEGORY_2'):
                found_tags['CATEGORY_1'].append(found_tags['CATEGORY_2'][0])
    
    # If no CATEGORY_2 but has CATEGORY_1, use CATEGORY_1 as CATEGORY_2
    if not found_tags.get('CATEGORY_2') and found_tags.get('CATEGORY_1'):
        found_tags['CATEGORY_2'].extend(found_tags['CATEGORY_1'])
    
    return found_tags

def analyze_samples():
    """Main analysis function"""
    print("🎵 Sample Analysis v2 - Category-Based Tagging with Normalization")
    print("=" * 70)
    
    # Load synonym map
    synonym_map = load_synonym_map()
    
    # Load categories
    categories = load_categories()
    if not categories:
        return
    
    # Initialize counters
    total_files = 0
    tagged_files = 0
    category_frequencies = defaultdict(Counter)
    category_combinations = Counter()  # For {CATEGORY_1: CATEGORY_2} format
    file_tagging_results = []
    bpm_distribution = Counter()
    key_distribution = Counter()
    normalization_stats = Counter()  # Track normalization usage
    
    # Find all wav files
    print(f"\n🔍 Scanning directory: {SAMPLES_PRESETS_PATH}")
    wav_files = []
    for root, dirs, files in os.walk(SAMPLES_PRESETS_PATH):
        for file in files:
            if file.lower().endswith('.wav'):
                wav_files.append(os.path.join(root, file))
    
    print(f"📁 Found {len(wav_files):,} WAV files")
    
    # Process each file
    print("\n🏷️  Tagging files with normalization...")
    for i, wav_file in enumerate(wav_files):
        total_files += 1
        
        # Extract BPM and Key
        bpm, key = extract_bpm_and_key(wav_file)
        if bpm:
            bpm_range = f"{(bpm//10)*10}-{(bpm//10)*10+9}"
            bpm_distribution[bpm_range] += 1
        if key:
            key_distribution[key] += 1
        
        # Tag the file
        file_tags = tag_file(wav_file, categories, synonym_map)
        
        if file_tags:
            tagged_files += 1
            
            # Store results
            file_result = {
                'file': os.path.basename(wav_file),
                'path': wav_file,
                'tags': dict(file_tags),
                'bpm': bpm,
                'key': key
            }
            file_tagging_results.append(file_result)
            
            # Update frequency counters
            for category, tags in file_tags.items():
                for tag in tags:
                    category_frequencies[category][tag] += 1
            
            # Create category combination for {CATEGORY_1: CATEGORY_2} format
            if file_tags.get('CATEGORY_1') and file_tags.get('CATEGORY_2'):
                for cat1_tag in file_tags['CATEGORY_1']:
                    for cat2_tag in file_tags['CATEGORY_2']:
                        combination = f"{{{cat1_tag}: {cat2_tag}}}"
                        category_combinations[combination] += 1
        
        # Progress indicator
        if (i + 1) % 1000 == 0:
            print(f"   Processed {i + 1:,} files...")
    
    print(f"\n✅ Analysis complete!")
    print(f"   Total files: {total_files:,}")
    print(f"   Tagged files: {tagged_files:,}")
    print(f"   Tagging rate: {(tagged_files/total_files)*100:.1f}%")
    print(f"   Synonym mappings used: {len(synonym_map)}")
    
    return (category_frequencies, category_combinations, file_tagging_results, 
            total_files, tagged_files, bpm_distribution, key_distribution)

def generate_frequency_report(category_frequencies, category_combinations, 
                            total_files, tagged_files, bpm_distribution, key_distribution):
    """Generate frequency analysis report"""
    report_lines = []
    
    report_lines.append("🎵 SAMPLE LIBRARY FREQUENCY ANALYSIS REPORT")
    report_lines.append("=" * 60)
    report_lines.append(f"Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    
    report_lines.append("📊 SUMMARY")
    report_lines.append("-" * 30)
    report_lines.append(f"Total files analyzed: {total_files:,}")
    report_lines.append(f"Files with tags: {tagged_files:,}")
    report_lines.append(f"Tagging success rate: {(tagged_files/total_files)*100:.1f}%")
    report_lines.append("")
    
    # Process each category
    for category_name, tag_frequencies in category_frequencies.items():
        if not tag_frequencies:
            continue
            
        report_lines.append(f"🏷️  {category_name.replace('_', ' ').title()}")
        report_lines.append("-" * 40)
        
        # Sort by frequency
        sorted_tags = tag_frequencies.most_common()
        
        # Show top tags
        for tag, count in sorted_tags[:20]:  # Top 20 tags per category
            percentage = (count / tagged_files) * 100
            report_lines.append(f"  {tag:20} {count:6,} occurrences ({percentage:5.1f}%)")
        
        # Category summary
        total_category_tags = sum(tag_frequencies.values())
        report_lines.append(f"  Total tags in category: {total_category_tags:,}")
        report_lines.append("")
    
    # Category combinations {CATEGORY_1: CATEGORY_2}
    report_lines.append("🔗 TOP CATEGORY COMBINATIONS {CATEGORY_1: CATEGORY_2}")
    report_lines.append("-" * 50)
    
    for combination, count in category_combinations.most_common(30):
        percentage = (count / tagged_files) * 100
        report_lines.append(f"  {combination:30} {count:6,} occurrences ({percentage:5.1f}%)")
    
    report_lines.append("")
    
    # BPM Distribution
    if bpm_distribution:
        report_lines.append("🎵 BPM DISTRIBUTION")
        report_lines.append("-" * 30)
        for bpm_range, count in sorted(bpm_distribution.items()):
            percentage = (count / total_files) * 100
            report_lines.append(f"  {bpm_range:10} BPM: {count:6,} files ({percentage:5.1f}%)")
        report_lines.append("")
    
    # Key Distribution
    if key_distribution:
        report_lines.append("🎼 MUSICAL KEY DISTRIBUTION")
        report_lines.append("-" * 35)
        for key, count in key_distribution.most_common(20):
            percentage = (count / total_files) * 100
            report_lines.append(f"  {key:10} {count:6,} files ({percentage:5.1f}%)")
        report_lines.append("")
    
    # Overall top tags across all categories
    report_lines.append("🔥 TOP TAGS ACROSS ALL CATEGORIES")
    report_lines.append("-" * 40)
    
    all_tags = Counter()
    for tag_frequencies in category_frequencies.values():
        all_tags.update(tag_frequencies)
    
    for tag, count in all_tags.most_common(30):
        percentage = (count / tagged_files) * 100
        report_lines.append(f"  {tag:20} {count:6,} occurrences ({percentage:5.1f}%)")
    
    return "\n".join(report_lines)

def save_results(category_frequencies, category_combinations, file_tagging_results, 
                total_files, tagged_files, bpm_distribution, key_distribution):
    """Save results to files"""
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Generate and save frequency report
    frequency_report = generate_frequency_report(category_frequencies, category_combinations,
                                               total_files, tagged_files, bpm_distribution, key_distribution)
    
    with open(OUTPUT_FILES['frequency_analysis'], 'w', encoding='utf-8') as f:
        f.write(frequency_report)
    
    print(f"📄 Frequency analysis saved to: {OUTPUT_FILES['frequency_analysis']}")
    
    # Save detailed results
    detailed_results = {
        'summary': {
            'total_files': total_files,
            'tagged_files': tagged_files,
            'tagging_rate': (tagged_files/total_files)*100,
            'categories_analyzed': len(category_frequencies)
        },
        'category_frequencies': {k: dict(v) for k, v in category_frequencies.items()},
        'category_combinations': dict(category_combinations.most_common(50)),
        'bpm_distribution': dict(bpm_distribution),
        'key_distribution': dict(key_distribution),
        'sample_files': file_tagging_results[:100]  # First 100 files as examples
    }
    
    with open(OUTPUT_FILES['detailed_results'], 'w') as f:
        json.dump(detailed_results, f, indent=2)
    
    print(f"📄 Detailed results saved to: {OUTPUT_FILES['detailed_results']}")

def main():
    """Main function"""
    print("🚀 Starting Sample Analysis v2 with Token Normalization...")
    
    # Run analysis
    results = analyze_samples()
    if not results:
        print("❌ Analysis failed!")
        return
    
    (category_frequencies, category_combinations, file_tagging_results, 
     total_files, tagged_files, bpm_distribution, key_distribution) = results
    
    # Save results
    save_results(category_frequencies, category_combinations, file_tagging_results,
                total_files, tagged_files, bpm_distribution, key_distribution)
    
    print("\n🎉 Analysis completed successfully!")
    print(f"📊 Check the output files in: {OUTPUT_DIR}")

if __name__ == "__main__":
    main() 