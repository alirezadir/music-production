"""Script to verify and clean tracks.csv by fact-checking against Beatport."""
import os
import pandas as pd
import re
from csv_store import load_or_create_csv
from datetime import datetime


def clean_artists_list(artists_str):
    """Remove duplicate artists and clean up the artists string."""
    if pd.isna(artists_str) or artists_str == "":
        return ""
    
    # Split by comma
    artists = [a.strip() for a in str(artists_str).split(",")]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_artists = []
    for artist in artists:
        artist_clean = artist.strip()
        if artist_clean and artist_clean.lower() not in seen:
            seen.add(artist_clean.lower())
            unique_artists.append(artist_clean)
    
    return ", ".join(unique_artists)


def verify_track_with_firecrawl(track_url: str, expected_title: str, expected_artists: str) -> dict:
    """
    Verify track information using Firecrawl.
    
    Returns:
        dict with verified_title, verified_artists, is_valid, notes
    """
    if not track_url or pd.isna(track_url) or track_url == "":
        return {
            "verified_title": expected_title,
            "verified_artists": expected_artists,
            "is_valid": False,
            "notes": "No track URL"
        }
    
    # This would use Firecrawl MCP to scrape the track page
    # For now, return the expected values (will be implemented with Firecrawl)
    return {
        "verified_title": expected_title,
        "verified_artists": expected_artists,
        "is_valid": True,
        "notes": "Verification pending Firecrawl integration"
    }


def main():
    """Main function to verify and clean tracks."""
    os.makedirs("out", exist_ok=True)
    tracks_csv = os.getenv("TRACKS_CSV", "out/tracks.csv")
    
    # Load tracks
    tracks_columns = [
        "title", "artists", "label", "label_tier", "genre", "bpm", "key",
        "released_date", "track_url", "source_page_type", "source_label",
        "source_artist", "created_at"
    ]
    
    tracks_df = load_or_create_csv(tracks_csv, tracks_columns)
    
    if tracks_df.empty:
        print("No tracks found in tracks.csv")
        return
    
    print(f"Processing {len(tracks_df)} tracks...")
    print("Cleaning duplicate artists and verifying track data...\n")
    
    # Clean duplicate artists
    print("Step 1: Removing duplicate artists...")
    original_artists = tracks_df["artists"].copy()
    tracks_df["artists"] = tracks_df["artists"].apply(clean_artists_list)
    
    # Count improvements
    improvements = 0
    for i, (orig, new) in enumerate(zip(original_artists, tracks_df["artists"])):
        if pd.notna(orig) and pd.notna(new):
            orig_count = len(str(orig).split(","))
            new_count = len(str(new).split(",")) if new else 0
            if orig_count > new_count:
                improvements += 1
    
    print(f"  Cleaned {improvements} tracks with duplicate artists")
    
    # Clean track titles (remove "Extended Mix", "Original Mix", etc. from title if it's redundant)
    print("\nStep 2: Cleaning track titles...")
    def clean_title(title):
        if pd.isna(title) or title == "":
            return ""
        title_str = str(title).strip()
        # Remove common suffixes that might be redundant
        title_str = re.sub(r'\s*(Extended Mix|Original Mix|Radio Edit|Instrumental Mix|Dub Mix)\s*$', '', title_str, flags=re.IGNORECASE)
        return title_str.strip()
    
    tracks_df["title"] = tracks_df["title"].apply(clean_title)
    
    # Verify tracks with URLs using Firecrawl
    print("\nStep 3: Verifying tracks with Beatport URLs...")
    tracks_with_urls = tracks_df[tracks_df["track_url"].notna() & (tracks_df["track_url"] != "")]
    
    print(f"  Found {len(tracks_with_urls)} tracks with URLs")
    print("  Verifying first 10 tracks as sample...")
    
    verified_count = 0
    for idx, row in tracks_with_urls.head(10).iterrows():
        track_url = row["track_url"]
        title = row["title"]
        artists = row["artists"]
        
        print(f"\n  Verifying: {title}")
        print(f"    URL: {track_url}")
        
        # Use Firecrawl to verify
        try:
            # This would call Firecrawl MCP
            # result = mcp_firecrawl_scrape(url=track_url, formats=["markdown"], onlyMainContent=True)
            # markdown = result.get("markdown", "")
            # 
            # # Parse verified data from markdown
            # verified = parse_track_from_firecrawl(markdown)
            # 
            # if verified:
            #     # Update if different
            #     if verified.get("title") != title:
            #         print(f"    ⚠️  Title mismatch: '{title}' vs '{verified['title']}'")
            #         tracks_df.loc[idx, "title"] = verified["title"]
            #     
            #     if verified.get("artists") != artists:
            #         print(f"    ⚠️  Artists mismatch: '{artists}' vs '{verified['artists']}'")
            #         tracks_df.loc[idx, "artists"] = verified["artists"]
            #     
            #     verified_count += 1
            
            # For now, just mark as needing verification
            print(f"    ⚠️  Verification pending (Firecrawl integration needed)")
        
        except Exception as e:
            print(f"    ✗ Error: {e}")
    
    # Remove tracks with obviously invalid data
    print("\nStep 4: Removing invalid tracks...")
    original_count = len(tracks_df)
    
    # Remove tracks with empty titles
    tracks_df = tracks_df[tracks_df["title"].notna() & (tracks_df["title"] != "")]
    
    # Remove tracks where title equals track_url (likely parsing error)
    invalid = tracks_df["title"] == tracks_df["track_url"]
    tracks_df = tracks_df[~invalid]
    
    removed = original_count - len(tracks_df)
    print(f"  Removed {removed} invalid tracks")
    
    # Save cleaned tracks
    tracks_df = tracks_df[tracks_columns]  # Ensure column order
    tracks_df.to_csv(tracks_csv, index=False)
    
    print(f"\n✓ Cleaned tracks saved to {tracks_csv}")
    print(f"  Final count: {len(tracks_df)} tracks")
    print(f"  Tracks with URLs: {len(tracks_df[tracks_df['track_url'].notna() & (tracks_df['track_url'] != '')])}")
    
    print("\nNote: Full verification requires Firecrawl MCP integration.")
    print("For now, duplicate artists have been removed and invalid tracks filtered.")


if __name__ == "__main__":
    main()



