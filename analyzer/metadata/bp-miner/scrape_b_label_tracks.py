"""
Scrape top 10 and latest 10 tracks from B-level labels for Afterlife Records.

For each B-label, extracts:
- Top 10 tracks (from "Top Ten Tracks" section on label page)
- Latest 10 tracks (from newest releases on /tracks page)

Writes all results to: afterlife_b_label_top_and_latest_tracks.csv
"""

import time
import random
import re
from typing import List, Dict, Optional
from pathlib import Path
import pandas as pd
from bs4 import BeautifulSoup
from scraper_utils import fetch_html


# B-level labels for Afterlife Records
B_LABELS = [
    {
        "label_b_name": "Rose Avenue",
        "label_a_similar_to": "Afterlife Records",
        "beatport_label_url": "https://www.beatport.com/label/rose-avenue/73321"
    },
    {
        "label_b_name": "Cercle Records",
        "label_a_similar_to": "Afterlife Records",
        "beatport_label_url": "https://www.beatport.com/label/cercle-records/XXXX"  # Need to find actual URL
    },
    {
        "label_b_name": "Odd One Out",
        "label_a_similar_to": "Afterlife Records",
        "beatport_label_url": "https://www.beatport.com/label/odd-one-out/XXXX"  # Need to find actual URL
    },
    {
        "label_b_name": "Future Classic",
        "label_a_similar_to": "Afterlife Records",
        "beatport_label_url": "https://www.beatport.com/label/future-classic/XXXX"  # Need to find actual URL
    },
    {
        "label_b_name": "Embassy One",
        "label_a_similar_to": "Afterlife Records",
        "beatport_label_url": "https://www.beatport.com/label/embassy-one/XXXX"  # Need to find actual URL
    }
]


def extract_top10_tracks(html: str, label_name: str) -> List[Dict]:
    """
    Extract top 10 tracks from label page HTML.
    
    Args:
        html: HTML content of label page
        label_name: Name of the B-label
    
    Returns:
        List of track dictionaries with: track_name, artist_name, genre, bpm, key
    """
    soup = BeautifulSoup(html, "html.parser")
    tracks = []
    
    # Find "Top Ten Tracks" section - look for heading first
    top10_section = None
    headings = soup.find_all(["h2", "h3"], string=re.compile(r"top\s*ten\s*tracks", re.I))
    
    if headings:
        # Find the parent container of the heading
        for heading in headings:
            parent = heading.find_parent(["div", "section"])
            if parent:
                top10_section = parent
                break
    
    if not top10_section:
        # Alternative: look for div with class containing "top" or "ten"
        top10_section = soup.find("div", class_=re.compile(r"top.*ten|top10|TopTracks", re.I))
    
    if not top10_section:
        print(f"Warning: Could not find Top Ten Tracks section for {label_name}")
        return tracks
    
    # Find track items by data-testid attribute (most reliable)
    track_items = top10_section.find_all("div", attrs={"data-testid": re.compile(r"tracks.*list.*item", re.I)})
    
    if not track_items:
        # Alternative: find by class
        track_items = top10_section.find_all("div", class_=re.compile(r"Lists.*Item|Item.*track", re.I))
    
    # Extract track data from items (limit to 10)
    for item in track_items[:10]:
        track_data = _parse_track_item(item, label_name)
        if track_data and track_data.get("track_name"):
            tracks.append(track_data)
    
    return tracks


def _parse_track_item(item, label_name: str) -> Optional[Dict]:
    """Parse a single track item element from Top 10 section."""
    try:
        # Extract track name - look for link with track URL
        track_name = ""
        track_link = item.find("a", href=re.compile(r"/track/"))
        if track_link:
            # Get text content, may include "Original Mix" suffix
            track_name = track_link.get_text(strip=True)
            # Remove "Original Mix" or similar suffixes if present
            track_name = re.sub(r"\s*Original Mix\s*$", "", track_name, flags=re.I).strip()
        
        if not track_name:
            # Try finding by class name (ItemName class)
            name_elem = item.find(["span", "div"], class_=re.compile(r"ItemName|title|name", re.I))
            if name_elem:
                track_name = name_elem.get_text(strip=True)
                # Clean up
                track_name = re.sub(r"\s*Original Mix\s*$", "", track_name, flags=re.I).strip()
        
        # Extract artists - look for ArtistNames class or artist links
        artist_name = ""
        artist_div = item.find("div", class_=re.compile(r"ArtistNames", re.I))
        if artist_div:
            artist_links = artist_div.find_all("a", href=re.compile(r"/artist/"))
            if artist_links:
                artists = [link.get_text(strip=True) for link in artist_links if link.get_text(strip=True)]
                artist_name = "; ".join(artists)
        
        if not artist_name:
            # Fallback: find all artist links in the item
            artist_links = item.find_all("a", href=re.compile(r"/artist/"))
            if artist_links:
                artists = []
                for link in artist_links:
                    artist_text = link.get_text(strip=True)
                    if artist_text:
                        artists.append(artist_text)
                artist_name = "; ".join(artists)
        
        # Top 10 section usually doesn't have BPM/key, so we'll leave them empty
        # They can be filled from track page if needed later
        genre = ""
        bpm = None
        key = None
        
        return {
            "track_name": track_name,
            "artist_name": artist_name,
            "genre": genre,
            "bpm": bpm,
            "key": key
        }
    except Exception as e:
        print(f"Error parsing track item: {e}")
        return None


def extract_latest_tracks(html: str, label_name: str, limit: int = 10) -> List[Dict]:
    """
    Extract latest tracks from label /tracks page HTML.
    Tracks are sorted newest first by default on Beatport.
    
    Args:
        html: HTML content of tracks page
        label_name: Name of the B-label
        limit: Maximum number of tracks to extract
    
    Returns:
        List of track dictionaries
    """
    soup = BeautifulSoup(html, "html.parser")
    tracks = []
    
    # Find track table rows - tracks page uses table structure
    rows = soup.find_all("tr")
    
    # Filter for track rows (those with track links)
    track_rows = []
    for row in rows:
        if row.find("a", href=re.compile(r"/track/")):
            track_rows.append(row)
    
    # Extract first 'limit' tracks (newest first)
    for row in track_rows[:limit]:
        track_data = _parse_track_row(row, label_name)
        if track_data and track_data.get("track_name"):
            tracks.append(track_data)
    
    return tracks


def _parse_track_row(row, label_name: str) -> Optional[Dict]:
    """Parse a table row containing track data from tracks page."""
    try:
        # Extract track name from track link
        track_name = ""
        track_link = row.find("a", href=re.compile(r"/track/"))
        if track_link:
            track_name = track_link.get_text(strip=True)
            # Remove "Original Mix" suffix if present
            track_name = re.sub(r"\s*Original Mix\s*$", "", track_name, flags=re.I).strip()
        
        # Extract artists - look for artist links (excluding label links)
        artist_name = ""
        all_links = row.find_all("a", href=re.compile(r"/artist/|/label/"))
        artists = []
        for link in all_links:
            href = link.get("href", "")
            # Skip label links
            if "/label/" in href:
                continue
            if "/artist/" in href:
                artist_text = link.get_text(strip=True)
                if artist_text:
                    artists.append(artist_text)
        
        if artists:
            artist_name = "; ".join(artists)
        
        # Extract genre, BPM, key from the row
        genre = ""
        bpm = None
        key = None
        
        # Look for genre link
        genre_link = row.find("a", href=re.compile(r"/genre/"))
        if genre_link:
            genre = genre_link.get_text(strip=True)
        
        # Look for BPM and Key - they're often together like "122 BPM - D Minor"
        # or in separate cells
        cells = row.find_all(["td", "div"])
        row_text = row.get_text(separator=" ", strip=True)
        
        # Check for BPM pattern (e.g., "122 BPM")
        bpm_match = re.search(r"(\d+)\s*BPM", row_text, re.I)
        if bpm_match:
            try:
                bpm = int(bpm_match.group(1))
            except Exception:
                pass
        
        # Check for key pattern (e.g., "D Minor", "A# Major")
        # Pattern: Letter, optional sharp/flat, space, Major/Minor
        key_match = re.search(r"([A-G][#b]?)\s*(Major|Minor)", row_text, re.I)
        if key_match:
            note = key_match.group(1).strip()
            scale = key_match.group(2).strip().capitalize()
            key = f"{note} {scale}"
        
        return {
            "track_name": track_name,
            "artist_name": artist_name,
            "genre": genre,
            "bpm": bpm,
            "key": key
        }
    except Exception as e:
        print(f"Error parsing track row: {e}")
        return None


def scrape_label_tracks(label_config: Dict) -> List[Dict]:
    """
    Scrape top 10 and latest 10 tracks for a B-label.
    
    Args:
        label_config: Dictionary with label_b_name, label_a_similar_to, beatport_label_url
    
    Returns:
        List of track dictionaries with category field
    """
    label_name = label_config["label_b_name"]
    label_url = label_config["beatport_label_url"]
    a_label = label_config["label_a_similar_to"]
    
    # Check if URL has placeholder
    if "XXXX" in label_url:
        print(f"Skipping {label_name}: URL not configured (contains XXXX)")
        return []
    
    print(f"Scraping {label_name}...")
    all_tracks = []
    
    # 1. Scrape Top 10 tracks from main label page
    print(f"  Fetching main page: {label_url}")
    html = fetch_html(label_url, retries=3, delay_range=(1, 3))
    if not html:
        print(f"  Error: Could not fetch main page for {label_name}")
    else:
        top10_tracks = extract_top10_tracks(html, label_name)
        print(f"  Found {len(top10_tracks)} top 10 tracks")
        
        for track in top10_tracks:
            track["label_b_name"] = label_name
            track["label_a_similar_to"] = a_label
            track["category"] = "most_pop_10"
            all_tracks.append(track)
    
    # Small delay between requests
    time.sleep(random.uniform(1, 3))
    
    # 2. Scrape Latest 10 tracks from /tracks page
    tracks_url = label_url.rstrip("/") + "/tracks"
    print(f"  Fetching tracks page: {tracks_url}")
    html = fetch_html(tracks_url, retries=3, delay_range=(1, 3))
    if not html:
        print(f"  Error: Could not fetch tracks page for {label_name}")
    else:
        latest_tracks = extract_latest_tracks(html, label_name, limit=10)
        print(f"  Found {len(latest_tracks)} latest tracks")
        
        for track in latest_tracks:
            track["label_b_name"] = label_name
            track["label_a_similar_to"] = a_label
            track["category"] = "latest_10"
            all_tracks.append(track)
    
    return all_tracks


def find_label_url(label_name: str) -> Optional[str]:
    """
    Search for Beatport label URL by name.
    Uses the search_label_url function from label_scraper if available.
    """
    try:
        from label_scraper import search_label_url
        return search_label_url(label_name)
    except Exception:
        # Fallback: construct URL from label name
        slug = label_name.lower().replace(" ", "-").replace("&", "").replace(".", "")
        return f"https://www.beatport.com/label/{slug}/XXXX"


def main():
    """Main function to scrape all B-labels and write to CSV."""
    output_file = Path(__file__).parent / "out" / "afterlife_b_label_top_and_latest_tracks.csv"
    output_file.parent.mkdir(exist_ok=True)
    
    all_results = []
    
    for label_config in B_LABELS:
        # Find URL if it has placeholder
        if "XXXX" in label_config["beatport_label_url"]:
            print(f"Searching for URL for {label_config['label_b_name']}...")
            found_url = find_label_url(label_config["label_b_name"])
            if found_url and "XXXX" not in found_url:
                label_config["beatport_label_url"] = found_url
                print(f"  Found: {found_url}")
            else:
                print(f"  Could not find URL, skipping...")
                continue
        
        tracks = scrape_label_tracks(label_config)
        all_results.extend(tracks)
        
        # Delay between labels
        if label_config != B_LABELS[-1]:  # Don't delay after last label
            delay = random.uniform(2, 4)
            print(f"Waiting {delay:.1f}s before next label...")
            time.sleep(delay)
    
    # Create DataFrame
    if not all_results:
        print("No tracks found!")
        return
    
    # Ensure all tracks have required fields
    for track in all_results:
        track.setdefault("track_name", "")
        track.setdefault("artist_name", "")
        track.setdefault("genre", "")
        track.setdefault("bpm", None)
        track.setdefault("key", None)
        track.setdefault("label_b_name", "")
        track.setdefault("label_a_similar_to", "")
        track.setdefault("category", "")
    
    df = pd.DataFrame(all_results)
    
    # Reorder columns to match required schema
    columns = ["label_b_name", "label_a_similar_to", "track_name", "category", 
               "artist_name", "genre", "bpm", "key"]
    df = df[columns]
    
    # Write to CSV
    df.to_csv(output_file, index=False)
    print(f"\n✅ Wrote {len(df)} tracks to {output_file}")
    print(f"\nSummary:")
    print(f"  Total tracks: {len(df)}")
    print(f"  Most popular (top 10): {len(df[df['category'] == 'most_pop_10'])}")
    print(f"  Latest (latest 10): {len(df[df['category'] == 'latest_10'])}")


if __name__ == "__main__":
    main()
