"""Main orchestrator script to run the full pipeline."""
import sys
import argparse
from seed_artists_from_labels import main as seed_artists
from scrape_artist_tracks import main as scrape_artists
from classify_b_labels import main as classify_labels
from scrape_b_labels import main as scrape_b_labels
from clean_all import main as clean_all
from sync_all_to_sheets import main as sync_sheets


def main():
    """Run the full pipeline or selected phases."""
    parser = argparse.ArgumentParser(description="Run Beatport label mining pipeline")
    parser.add_argument(
        "--phases",
        type=str,
        default="1,2,3,4,5,6",
        help="Comma-separated list of phases to run (1-6). Default: 1,2,3,4,5,6"
    )
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Force refresh of artist URLs and tracks"
    )
    
    args = parser.parse_args()
    
    # Parse phases
    phases = [int(p.strip()) for p in args.phases.split(",")]
    
    print("=" * 60)
    print("Beatport Label Miner - Full Pipeline")
    print("=" * 60)
    
    # Phase 1: Seed artists from A-level labels
    if 1 in phases:
        print("\n[Phase 1] Seeding artists from A-level labels...")
        print("-" * 60)
        try:
            seed_artists()
        except Exception as e:
            print(f"Error in Phase 1: {e}")
            if not args.force_refresh:
                sys.exit(1)
    
    # Phase 2: Scrape artist tracks
    if 2 in phases:
        print("\n[Phase 2] Scraping artist tracks...")
        print("-" * 60)
        try:
            scrape_artists(force_refresh=args.force_refresh)
        except Exception as e:
            print(f"Error in Phase 2: {e}")
            if not args.force_refresh:
                sys.exit(1)
    
    # Phase 3: Classify B-level labels
    if 3 in phases:
        print("\n[Phase 3] Classifying B-level labels...")
        print("-" * 60)
        try:
            classify_labels()
        except Exception as e:
            print(f"Error in Phase 3: {e}")
            if not args.force_refresh:
                sys.exit(1)
    
    # Phase 4: Scrape B-level label tracks
    if 4 in phases:
        print("\n[Phase 4] Scraping B-level label tracks...")
        print("-" * 60)
        try:
            scrape_b_labels()
        except Exception as e:
            print(f"Error in Phase 4: {e}")
            if not args.force_refresh:
                sys.exit(1)
    
    # Phase 5: Clean and deduplicate
    if 5 in phases:
        print("\n[Phase 5] Cleaning and deduplicating data...")
        print("-" * 60)
        try:
            clean_all()
        except Exception as e:
            print(f"Error in Phase 5: {e}")
            if not args.force_refresh:
                sys.exit(1)
    
    # Phase 6: Sync to Google Sheets
    if 6 in phases:
        print("\n[Phase 6] Syncing to Google Sheets...")
        print("-" * 60)
        try:
            sync_sheets()
        except Exception as e:
            print(f"Error in Phase 6: {e}")
            print("Note: Google Sheets sync requires credentials.")
    
    print("\n" + "=" * 60)
    print("Pipeline completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()

