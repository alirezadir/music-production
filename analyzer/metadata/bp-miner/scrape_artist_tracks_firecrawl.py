"""Script to scrape artist tracks using Firecrawl MCP."""
import os
import sys
import pandas as pd
from config_loader import load_config
from csv_store import load_or_create_csv, append_and_save
from models import TrackMeta
from datetime import datetime
import re


def parse_tracks_from_firecrawl_markdown(markdown: str, artist_name: str) -> list:
    """Parse tracks from Firecrawl markdown output."""
    tracks = []
    
    # Look for track patterns in markdown
    # Beatport track URLs: /track/track-name/track-id
    track_url_pattern = r'https?://www\.beatport\.com/track/[^/\s]+/\d+'
    track_urls = re.findall(track_url_pattern, markdown)
    
    # Also look for track titles and metadata
    # This is a simplified parser - may need refinement
    lines = markdown.split('\n')
    current_track = None
    
    for line in lines:
        # Look for track titles (often in headers or bold)
        if '##' in line or '**' in line:
            title_match = re.search(r'[#*]+\s*(.+?)(?:\s*[#*]+|$)', line)
            if title_match:
                title = title_match.group(1).strip()
                if title and len(title) > 3:  # Basic validation
                    current_track = {
                        'title': title,
                        'artists': artist_name,
                        'label': '',
                        'track_url': ''
                    }
        
        # Look for label mentions
        if current_track and ('label' in line.lower() or 'Label:' in line):
            label_match = re.search(r'Label[:\s]+([^\n,]+)', line, re.IGNORECASE)
            if label_match:
                current_track['label'] = label_match.group(1).strip()
        
        # Look for track URLs
        if current_track and not current_track['track_url']:
            url_match = re.search(track_url_pattern, line)
            if url_match:
                current_track['track_url'] = url_match.group(0)
                tracks.append(TrackMeta(**current_track))
                current_track = None
    
    # Also extract from URLs directly
    for url in set(track_urls):
        # Extract track name from URL
        track_name_match = re.search(r'/track/([^/]+)/', url)
        if track_name_match:
            track_name = track_name_match.group(1).replace('-', ' ').title()
            tracks.append(TrackMeta(
                title=track_name,
                artists=artist_name,
                label='',
                track_url=url
            ))
    
    return tracks


def scrape_artist_tracks_firecrawl(artist_name: str, artist_url: str, max_tracks: int = 50) -> list:
    """Scrape artist tracks using Firecrawl MCP."""
    try:
        # Use Firecrawl to scrape artist tracks page
        tracks_url = f"{artist_url}/tracks?page=1&per_page={max_tracks}"
        
        # Try to use Firecrawl MCP if available
        # Note: This would need to be called via MCP tools
        # For now, we'll return empty and let the caller handle Firecrawl
        
        return []
    except Exception as e:
        print(f"  Error scraping {artist_name}: {e}")
        return []


def main():
    """Main function to scrape artist tracks using Firecrawl."""
    # Load config
    config = load_config()
    tracks_per_page = config.get("tracks_per_page", 50)
    
    # Define CSV paths
    os.makedirs("out", exist_ok=True)
    artists_csv = os.getenv("ARTISTS_CSV", "out/artists.csv")
    tracks_csv = os.getenv("TRACKS_CSV", "out/tracks.csv")
    
    # Define schemas
    artists_columns = ["artist_name", "beatport_url", "source_label", "created_at"]
    tracks_columns = [
        "title", "artists", "label", "label_tier", "genre", "bpm", "key",
        "released_date", "track_url", "source_page_type", "source_label",
        "source_artist", "created_at"
    ]
    
    # Load CSVs
    artists_df = load_or_create_csv(artists_csv, artists_columns)
    tracks_df = load_or_create_csv(tracks_csv, tracks_columns)
    
    # Filter artists with URLs
    artists_with_urls = artists_df[
        artists_df["beatport_url"].notna() &
        (artists_df["beatport_url"].astype(str).str.strip() != "") &
        (artists_df["beatport_url"].astype(str).str.strip() != "nan")
    ]
    
    print(f"Found {len(artists_with_urls)} artists with URLs")
    print(f"Processing first 50 artists to discover B-level labels...")
    
    # Process first 50 artists (to get enough data for B-level discovery)
    artists_to_process = artists_with_urls.head(50)
    
    for idx, artist_row in artists_to_process.iterrows():
        artist_name = artist_row["artist_name"]
        artist_url = str(artist_row["beatport_url"]).strip()
        source_label = artist_row.get("source_label", "")
        
        print(f"\nProcessing artist: {artist_name}")
        print(f"  URL: {artist_url}")
        
        # Use Firecrawl to scrape tracks
        tracks_url = f"{artist_url}/tracks?page=1&per_page={tracks_per_page}"
        print(f"  Scraping: {tracks_url}")
        
        # This would need to call Firecrawl MCP tool
        # For now, we'll create a placeholder that the user can enhance
        print(f"  Note: Firecrawl MCP integration needed for full scraping")
        
        # TODO: Call Firecrawl MCP tool here
        # markdown = firecrawl_scrape(url=tracks_url, formats=["markdown"])
        # tracks = parse_tracks_from_firecrawl_markdown(markdown, artist_name)
    
    print("\nDone! (Note: Full implementation requires Firecrawl MCP integration)")


if __name__ == "__main__":
    main()
