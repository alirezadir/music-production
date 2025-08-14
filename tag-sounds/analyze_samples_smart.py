#!/usr/bin/env python3
import os
import re
from collections import defaultdict, Counter
import json
from pathlib import Path
from config import SAMPLES_PRESETS_PATH, OUTPUT_DIR

# File paths for this script
OUTPUT_FILES = {
    'smart_sample_analysis': f"{OUTPUT_DIR}/smart_sample_analysis.json",
    'discovered_tags': f"{OUTPUT_DIR}/discovered_tags.txt"
}

class SmartSampleAnalyzer:
    def __init__(self):
        self.base_path = SAMPLES_PRESETS_PATH
        self.all_tokens = Counter()
        self.sample_categories = defaultdict(int)
        self.shot_categories = defaultdict(int)
        self.discovered_tags = Counter()
        self.samples_by_folder = defaultdict(list)
        self.total_wavs = 0
        
        # Known shot categories
        self.known_shot_types = {
            'loop', 'loops', 'phrase', 'pattern', 'groove', 'sequence',
            'oneshot', 'one-shot', 'shot', 'hit', 'stab', 'single'
        }
        
        # Common non-tag words to filter out
        self.stop_words = {
            'the', 'and', 'or', 'is', 'at', 'by', 'for', 'with', 'from',
            'wav', 'audio', 'sound', 'sample', 'pack', 'vol', 'version',
            'remix', 'edit', 'stereo', 'mono', 'dry', 'wet', 'processed',
            'original', 'master', 'final', 'bounce', 'render', 'export',
            'project', 'session', 'track', 'channel', 'bus', 'send',
            'bpm', 'key', 'scale', 'mode', 'major', 'minor', 'sharp', 'flat'
        }
        
    def extract_tokens(self, filename):
        """Extract meaningful tokens from filename"""
        # Remove file extension
        name = os.path.splitext(filename)[0]
        
        # Split by common delimiters
        tokens = re.split(r'[-_\s\.\(\)\[\]]+', name.lower())
        
        # Filter out numbers, single chars, and stop words
        meaningful_tokens = []
        for token in tokens:
            # Skip if empty, single char, pure number, or stop word
            if (len(token) > 1 and 
                not token.isdigit() and 
                token not in self.stop_words and
                not re.match(r'^\d+$', token)):
                meaningful_tokens.append(token)
        
        return meaningful_tokens
    
    def analyze_folder_patterns(self, folder_path):
        """Analyze naming patterns in a specific folder"""
        folder_name = os.path.basename(folder_path)
        samples = []
        
        for file in os.listdir(folder_path):
            if file.lower().endswith('.wav'):
                samples.append(file)
                self.total_wavs += 1
        
        if samples:
            self.samples_by_folder[folder_name] = samples[:5]  # Store examples
            
            # Extract common patterns
            for sample in samples:
                tokens = self.extract_tokens(sample)
                self.all_tokens.update(tokens)
    
    def scan_all_files(self):
        """Scan all WAV files and extract tokens"""
        print("Phase 1: Scanning all folders and files...")
        
        for root, dirs, files in os.walk(self.base_path):
            wav_files = [f for f in files if f.lower().endswith('.wav')]
            if wav_files:
                self.analyze_folder_patterns(root)
                
                # Also analyze folder structure for context
                folder_parts = root.replace(self.base_path, '').split(os.sep)
                for part in folder_parts:
                    tokens = self.extract_tokens(part)
                    self.all_tokens.update(tokens)
        
        print(f"Found {self.total_wavs} WAV files")
        print(f"Discovered {len(self.all_tokens)} unique tokens")
    
    def identify_categories(self):
        """Use frequency analysis to identify likely categories"""
        print("\nPhase 2: Identifying categories from discovered tokens...")
        
        # Filter tokens by frequency - likely categories appear multiple times
        min_frequency = 10  # Adjust threshold as needed
        potential_categories = {
            token: count for token, count in self.all_tokens.items() 
            if count >= min_frequency and len(token) >= 3
        }
        
        # Sort by frequency
        sorted_categories = sorted(potential_categories.items(), 
                                 key=lambda x: x[1], reverse=True)
        
        print(f"\nTop 50 discovered potential tags/categories:")
        for tag, count in sorted_categories[:50]:
            print(f"  {tag:20} appears {count:6} times")
        
        return sorted_categories
    
    def categorize_samples(self):
        """Re-scan files and categorize based on discovered tags"""
        print("\nPhase 3: Categorizing samples with discovered tags...")
        
        # Get top categories as our tag list
        discovered_categories = self.identify_categories()
        category_set = {cat[0] for cat in discovered_categories[:100]}  # Top 100 tags
        
        # Initialize detailed results
        categorized_samples = defaultdict(list)
        shot_type_distribution = defaultdict(int)
        
        # Re-scan with categories
        for root, dirs, files in os.walk(self.base_path):
            for file in files:
                if file.lower().endswith('.wav'):
                    filepath = os.path.join(root, file)
                    file_lower = file.lower()
                    path_lower = filepath.lower()
                    
                    # Extract sample categories
                    found_categories = []
                    tokens = self.extract_tokens(file) + self.extract_tokens(root)
                    
                    for token in tokens:
                        if token in category_set:
                            found_categories.append(token)
                            self.sample_categories[token] += 1
                    
                    # Determine shot type
                    shot_type = 'undefined'
                    for shot in self.known_shot_types:
                        if shot in path_lower:
                            if shot in ['loop', 'loops', 'phrase', 'pattern', 'groove']:
                                shot_type = 'loop'
                            elif shot in ['oneshot', 'one-shot', 'shot', 'hit', 'stab']:
                                shot_type = 'one-shot'
                            break
                    
                    shot_type_distribution[shot_type] += 1
                    
                    # Store categorized sample
                    if found_categories:
                        key = f"{','.join(found_categories[:2])}_{shot_type}"
                        categorized_samples[key].append(file[:60])
        
        return categorized_samples, shot_type_distribution, category_set
    
    def generate_report(self):
        """Generate comprehensive analysis report"""
        self.scan_all_files()
        categorized_samples, shot_distribution, discovered_tags = self.categorize_samples()
        
        # Prepare results
        results = {
            'total_files': self.total_wavs,
            'discovered_tags': list(discovered_tags)[:50],
            'sample_categories': dict(sorted(self.sample_categories.items(), 
                                           key=lambda x: x[1], reverse=True)[:30]),
            'shot_categories': dict(shot_distribution),
            'tag_frequency': dict(self.all_tokens.most_common(100)),
            'folder_examples': dict(list(self.samples_by_folder.items())[:20]),
            'categorized_examples': dict(list(categorized_samples.items())[:20])
        }
        
        # Save results
        with open(OUTPUT_FILES['smart_sample_analysis'], 'w') as f:
            json.dump(results, f, indent=2)
        
        # Print summary
        print("\n" + "="*60)
        print("SMART SAMPLE ANALYSIS REPORT")
        print("="*60)
        print(f"\nTotal WAV files: {self.total_wavs:,}")
        
        print("\n--- TOP 30 SAMPLE CATEGORIES ---")
        for cat, count in sorted(self.sample_categories.items(), 
                               key=lambda x: x[1], reverse=True)[:30]:
            print(f"{cat:20} {count:6,} files")
        
        print("\n--- SHOT TYPE DISTRIBUTION ---")
        for shot_type, count in shot_distribution.items():
            percentage = (count / self.total_wavs) * 100
            print(f"{shot_type:15} {count:6,} files ({percentage:5.1f}%)")
        
        print("\n--- SAMPLE FOLDER PATTERNS ---")
        for folder, samples in list(self.samples_by_folder.items())[:10]:
            print(f"\n{folder}:")
            for sample in samples[:3]:
                print(f"  - {sample}")
        
        print(f"\nDetailed results saved to {OUTPUT_FILES['smart_sample_analysis']}")
        print(f"\nDiscovered {len(discovered_tags)} unique category tags!")
        
        # Save discovered tags to separate file for easy access
        with open(OUTPUT_FILES['discovered_tags'], 'w') as f:
            f.write("DISCOVERED SAMPLE TAGS/CATEGORIES\n")
            f.write("="*50 + "\n\n")
            for tag in sorted(discovered_tags):
                f.write(f"{tag}\n")

# Run the analysis
if __name__ == "__main__":
    analyzer = SmartSampleAnalyzer()
    analyzer.generate_report()