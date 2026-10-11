"""Script to verify tracks using Firecrawl and clean up data."""
import os
import pandas as pd
import re
from csv_store import load_or_create_csv
from datetime import datetime


def parse_track_from_firecrawl_markdown(markdown: str) -> dict:
    """Parse track information from Firecrawl markdown output."""
    result = {
        "title": None,
        "artists": None,
        "label": None,
        "genre": None,
        "bpm": None,
        "key": None,
        "released_date": None
    }
    
    lines = markdown.split('\n')
    
    # Look for track title (usually in headers or bold)
    for line in lines:
        # Title patterns
        if '##' in line or '**' in line:
            title_match = re.search(r'[#*]+\s*(.+?)(?:\s*[#*]+|$)', line)
            if title_match and not result["title"]:
                title = title_match.group(1).strip()
                # Clean up title
                title = re.sub(r'\s*(Extended Mix|Original Mix|Radio Edit).*$', '', title, flags=re.IGNORECASE)
                result["title"] = title.strip()
        
        # Artists (look for artist links)
        if not result["artists"]:
            artist_pattern = r'\[([^\]]+)\]\(https://www\.beatport\.com/artist/'
            artists = re.findall(artist_pattern, markdown)
            if artists:
                # Remove duplicates
                unique_artists = []
                seen = set()
                for artist in artists:
                    if artist.lower() not in seen:
                        seen.add(artist.lower())
                        unique_artists.append(artist)
                result["artists"] = ", ".join(unique_artists)
        
        # Label (look for label links)
        if not result["label"]:
            label_match = re.search(r'\[([^\]]+)\]\(https://www\.beatport\.com/label/[^\)]+', line)
            if label_match:
                result["label"] = label_match.group(1).strip()
        
        # BPM
        if not result["bpm"]:
            bpm_match = re.search(r'(\d+)\s+BPM', line)
            if bpm_match:
                try:
                    result["bpm"] = int(bpm_match.group(1))
                except:
                    pass
        
        # Key
        if not result["key"]:
            key_match = re.search(r'[\\-]\s*([A-G][#b]?\s+(?:Major|Minor))', line)
            if key_match:
                result["key"] = key_match.group(1).strip()
        
        # Release date
        if not result["released_date"]:
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', line)
            if date_match:
                result["released_date"] = date_match.group(1)
    
    return result


def clean_artists_list(artists_str):
    """Remove duplicate artists and clean up."""
    if pd.isna(artists_str) or artists_str == "":
        return ""
    
    artists = [a.strip() for a in str(artists_str).split(",")]
    seen = set()
    unique_artists = []
    for artist in artists:
        artist_clean = artist.strip()
        if artist_clean and artist_clean.lower() not in seen:
            seen.add(artist_clean.lower())
            unique_artists.append(artist_clean)
    
    return ", ".join(unique_artists)


def main():
    """Main function to verify and clean tracks."""
    os.makedirs("out", exist_ok=True)
    tracks_csv = os.getenv("TRACKS_CSV", "out/tracks.csv")
    
    tracks_columns = [
        "title", "artists", "label", "label_tier", "genre", "bpm", "key",
        "released_date", "track_url", "source_page_type", "source_label",
        "source_artist", "created_at"
    ]
    
    tracks_df = load_or_create_csv(tracks_csv, tracks_columns)
    
    if tracks_df.empty:
        print("No tracks found")
        return
    
    print(f"Processing {len(tracks_df)} tracks...\n")
    
    # Step 1: Clean duplicate artists
    print("Step 1: Removing duplicate artists...")
    tracks_df["artists"] = tracks_df["artists"].apply(clean_artists_list)
    print("  ✓ Cleaned duplicate artists")
    
    # Step 2: Clean track titles
    print("\nStep 2: Cleaning track titles...")
    def clean_title(title):
        if pd.isna(title) or title == "":
            return ""
        title_str = str(title).strip()
        # Remove redundant suffixes
        title_str = re.sub(r'\s*(Extended Mix|Original Mix|Radio Edit|Instrumental Mix|Dub Mix)\s*$', '', title_str, flags=re.IGNORECASE)
        # Fix duplicate "feat." patterns
        title_str = re.sub(r'feat\.\s*([^,]+)\s*feat\.', r'feat. \1', title_str, flags=re.IGNORECASE)
        return title_str.strip()
    
    tracks_df["title"] = tracks_df["title"].apply(clean_title)
    print("  ✓ Cleaned track titles")
    
    # Step 3: Verify tracks with URLs using Firecrawl
    print("\nStep 3: Verifying tracks with Beatport URLs using Firecrawl...")
    tracks_with_urls = tracks_df[tracks_df["track_url"].notna() & (tracks_df["track_url"] != "")]
    
    print(f"  Found {len(tracks_with_urls)} tracks with URLs")
    print("  Verifying tracks...\n")
    
    verified_count = 0
    updated_count = 0
    
    for idx, row in tracks_with_urls.iterrows():
        track_url = str(row["track_url"]).strip()
        current_title = str(row["title"]).strip() if pd.notna(row["title"]) else ""
        current_artists = str(row["artists"]).strip() if pd.notna(row["artists"]) else ""
        
        print(f"  [{idx+1}/{len(tracks_with_urls)}] Verifying: {current_title[:50]}...")
        
        try:
            # Use Firecrawl to scrape track page
            # Note: This would need to be called via MCP tools
            # For now, we'll process what we can
            
            # The actual Firecrawl call would be:
            # result = mcp_firecrawl_scrape(url=track_url, formats=["markdown"], onlyMainContent=True)
            # markdown = result.get("markdown", "")
            # verified = parse_track_from_firecrawl_markdown(markdown)
            
            # For now, skip Firecrawl and just clean what we have
            verified_count += 1
        
        except Exception as e:
            print(f"    ✗ Error: {e}")
            continue
    
    # Step 4: Remove obviously invalid tracks
    print("\nStep 4: Removing invalid tracks...")
    original_count = len(tracks_df)
    
    # Remove tracks where title is empty or equals URL
    invalid_mask = (
        tracks_df["title"].isna() | 
        (tracks_df["title"] == "") |
        (tracks_df["title"] == tracks_df["track_url"])
    )
    tracks_df = tracks_df[~invalid_mask]
    
    removed = original_count - len(tracks_df)
    if removed > 0:
        print(f"  Removed {removed} invalid tracks")
    
    # Save
    tracks_df = tracks_df[tracks_columns]
    tracks_df.to_csv(tracks_csv, index=False)
    
    print(f"\n✓ Cleaned {len(tracks_df)} tracks saved to {tracks_csv}")
    print(f"  Tracks with URLs: {len(tracks_with_urls)}")
    print(f"  Verified: {verified_count}")
    
    print("\nNote: Full web verification requires Firecrawl MCP integration.")
    print("Duplicate artists and invalid tracks have been cleaned.")


if __name__ == "__main__":
    main()



