#!/usr/bin/env python3
"""
Unified sample analyzer - consolidates all analyze_samples variants.

This script provides a single interface for analyzing audio samples with
different modes: basic, fast, smart, and comprehensive.
"""
import os
import re
import argparse
from collections import defaultdict, Counter
from pathlib import Path
from typing import List, Dict, Optional
import json
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from config import get_samples_path, get_tag_sounds_output_dir
    SAMPLES_PATH = get_samples_path()
    OUTPUT_DIR = get_tag_sounds_output_dir()
except ImportError:
    from config import SAMPLES_PATH, OUTPUT_DIR
    SAMPLES_PATH = Path(SAMPLES_PATH)
    OUTPUT_DIR = Path(OUTPUT_DIR)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class UnifiedSampleAnalyzer:
    """Unified analyzer that supports multiple analysis modes."""
    
    def __init__(self, mode: str = "smart"):
        """
        Initialize analyzer.
        
        Args:
            mode: Analysis mode - 'basic', 'fast', 'smart', or 'comprehensive'
        """
        self.mode = mode
        self.base_path = SAMPLES_PATH
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
    
    def extract_tokens(self, filename: str) -> List[str]:
        """Extract meaningful tokens from filename."""
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
    
    def analyze_folder_patterns(self, folder_path: Path) -> None:
        """Analyze naming patterns in a specific folder."""
        folder_name = folder_path.name
        samples = []
        
        try:
            for file in folder_path.iterdir():
                if file.is_file() and file.suffix.lower() == '.wav':
                    samples.append(file.name)
                    self.total_wavs += 1
        except PermissionError:
            print(f"Warning: Permission denied for {folder_path}")
            return
        
        if samples:
            self.samples_by_folder[folder_name] = samples[:5]  # Store examples
            
            # Extract common patterns
            for sample in samples:
                tokens = self.extract_tokens(sample)
                self.all_tokens.update(tokens)
    
    def scan_all_files(self, fast: bool = False) -> None:
        """Scan all WAV files and extract tokens."""
        print("Phase 1: Scanning all folders and files...")
        
        if fast:
            # Fast mode: only scan top-level directories
            try:
                for folder in self.base_path.iterdir():
                    if folder.is_dir():
                        self.analyze_folder_patterns(folder)
            except (PermissionError, FileNotFoundError) as e:
                print(f"Error scanning {self.base_path}: {e}")
        else:
            # Full scan: recursive
            try:
                for root, dirs, files in os.walk(self.base_path):
                    folder_path = Path(root)
                    wav_files = [f for f in files if f.lower().endswith('.wav')]
                    if wav_files:
                        self.analyze_folder_patterns(folder_path)
                        
                        # Also analyze folder structure for context
                        folder_parts = str(folder_path.relative_to(self.base_path)).split(os.sep)
                        for part in folder_parts:
                            tokens = self.extract_tokens(part)
                            self.all_tokens.update(tokens)
            except (PermissionError, FileNotFoundError) as e:
                print(f"Error scanning {self.base_path}: {e}")
        
        print(f"Found {self.total_wavs} WAV files")
        print(f"Discovered {len(self.all_tokens)} unique tokens")
    
    def identify_categories(self) -> Dict[str, any]:
        """Use frequency analysis to identify likely categories."""
        print("\nPhase 2: Identifying categories from discovered tokens...")
        
        # Identify shot types
        for token, count in self.all_tokens.most_common():
            if token in self.known_shot_types:
                self.shot_categories[token] += count
        
        # Identify other categories (instruments, genres, etc.)
        # This is a simplified version - can be enhanced
        category_keywords = {
            'drum': 'drums',
            'kick': 'drums',
            'snare': 'drums',
            'hat': 'drums',
            'bass': 'bass',
            'lead': 'lead',
            'pad': 'pads',
            'pluck': 'plucks',
            'vocal': 'vocals',
            'fx': 'effects',
            'ambient': 'ambient',
            'techno': 'techno',
            'house': 'house',
        }
        
        for token, count in self.all_tokens.most_common():
            for keyword, category in category_keywords.items():
                if keyword in token:
                    self.sample_categories[category] += count
                    break
        
        return {
            'shot_categories': dict(self.shot_categories),
            'sample_categories': dict(self.sample_categories),
            'top_tokens': dict(self.all_tokens.most_common(50))
        }
    
    def analyze(self) -> Dict[str, any]:
        """Run the analysis based on mode."""
        fast_mode = self.mode == "fast"
        self.scan_all_files(fast=fast_mode)
        
        if self.mode in ["smart", "comprehensive"]:
            categories = self.identify_categories()
        else:
            categories = {}
        
        results = {
            'total_files': self.total_wavs,
            'unique_tokens': len(self.all_tokens),
            'top_tokens': dict(self.all_tokens.most_common(100)),
            'samples_by_folder': dict(self.samples_by_folder),
            **categories
        }
        
        return results
    
    def save_results(self, results: Dict[str, any], output_file: Optional[Path] = None) -> Path:
        """Save analysis results to JSON file."""
        if output_file is None:
            output_file = OUTPUT_DIR / f"sample_analysis_{self.mode}.json"
        
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nResults saved to: {output_file}")
        return output_file


def main():
    parser = argparse.ArgumentParser(
        description="Unified sample analyzer - analyzes audio sample files"
    )
    parser.add_argument(
        '--mode',
        choices=['basic', 'fast', 'smart', 'comprehensive'],
        default='smart',
        help='Analysis mode (default: smart)'
    )
    parser.add_argument(
        '--samples-path',
        type=Path,
        help='Path to samples directory (overrides config)'
    )
    parser.add_argument(
        '--output',
        type=Path,
        help='Output file path (default: auto-generated)'
    )
    
    args = parser.parse_args()
    
    # Override samples path if provided
    if args.samples_path:
        global SAMPLES_PATH
        SAMPLES_PATH = Path(args.samples_path)
    
    if not SAMPLES_PATH.exists():
        print(f"Error: Samples path does not exist: {SAMPLES_PATH}")
        print("Please set MUSIC_PRODUCTION_SAMPLES_PATH environment variable or use --samples-path")
        return 1
    
    print(f"Analyzing samples in: {SAMPLES_PATH}")
    print(f"Mode: {args.mode}")
    
    analyzer = UnifiedSampleAnalyzer(mode=args.mode)
    results = analyzer.analyze()
    
    output_file = analyzer.save_results(results, args.output)
    
    print(f"\nAnalysis complete!")
    print(f"  Total files: {results['total_files']}")
    print(f"  Unique tokens: {results['unique_tokens']}")
    if 'top_tokens' in results:
        print(f"  Top 5 tokens: {list(results['top_tokens'].keys())[:5]}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

