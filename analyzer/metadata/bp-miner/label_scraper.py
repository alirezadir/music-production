"""Label page scraper for Beatport."""
import re
from typing import List, Set
from bs4 import BeautifulSoup
from models import TrackMeta
from scraper_utils import fetch_html


def parse_label_page_for_tracks(html: str, label_name: str) -> List[TrackMeta]:
    """
    Parse label page HTML to extract track metadata.
    
    Handles:
    - Top Ten Tracks block
    - Latest Releases / main track list
    
    Args:
        html: HTML content of label page.
        label_name: Name of the label.
    
    Returns:
        List of TrackMeta objects.
    """
    soup = BeautifulSoup(html, "html.parser")
    tracks = []
    
    # Try to find Top Ten Tracks section
    top10_section = soup.find("div", class_=re.compile("top.*ten|top10", re.I))
    if not top10_section:
        # Look for common patterns
        top10_section = soup.find("section", string=re.compile("top.*ten", re.I))
    
    if top10_section:
        top10_tracks = _parse_track_list(top10_section, label_name, "label_top10")
        tracks.extend(top10_tracks)
    
    # Parse main track list / latest releases
    # Beatport typically uses data-ec-name or similar attributes
    track_elements = soup.find_all(["div", "li"], class_=re.compile("track|release", re.I))
    
    if not track_elements:
        # Try alternative selectors
        track_elements = soup.select("[data-ec-name], .bucket-item, .track-item")
    
    for element in track_elements:
        track = _parse_track_element(element, label_name, "label_tracks")
        if track:
            tracks.append(track)
    
    return tracks


def _parse_track_element(element, label_name: str, source_type: str) -> TrackMeta:
    """Parse a single track element from HTML."""
    try:
        # Extract title
        title_elem = element.find(["a", "span"], class_=re.compile("title|name", re.I))
        if not title_elem:
            title_elem = element.find("a", href=re.compile("/track/"))
        title = title_elem.get_text(strip=True) if title_elem else ""
        
        # Extract artists
        artists_elem = element.find(["a", "span"], class_=re.compile("artist", re.I))
        if not artists_elem:
            # Try finding artist links
            artist_links = element.find_all("a", href=re.compile("/artist/"))
            artists = ", ".join([a.get_text(strip=True) for a in artist_links])
        else:
            artists = artists_elem.get_text(strip=True)
        
        # Extract label (should be known, but get from element if available)
        label = label_name
        
        # Extract genre
        genre_elem = element.find(["span", "a"], class_=re.compile("genre", re.I))
        genre = genre_elem.get_text(strip=True) if genre_elem else ""
        
        # Extract BPM
        bpm_elem = element.find(["span", "div"], class_=re.compile("bpm", re.I))
        bpm = None
        if bpm_elem:
            bpm_text = bpm_elem.get_text(strip=True)
            bpm_match = re.search(r"(\d+)", bpm_text)
            if bpm_match:
                bpm = float(bpm_match.group(1))
        
        # Extract key
        key_elem = element.find(["span", "div"], class_=re.compile("key", re.I))
        key = key_elem.get_text(strip=True) if key_elem else None
        
        # Extract release date
        date_elem = element.find(["span", "time"], class_=re.compile("date|release", re.I))
        released_date = date_elem.get_text(strip=True) if date_elem else None
        
        # Extract track URL
        track_link = element.find("a", href=re.compile("/track/"))
        track_url = ""
        if track_link:
            href = track_link.get("href", "")
            if href:
                if href.startswith("/"):
                    track_url = f"https://www.beatport.com{href}"
                else:
                    track_url = href
        
        if not title:
            return None
        
        return TrackMeta(
            title=title,
            artists=artists or "",
            label=label,
            genre=genre,
            bpm=bpm,
            key=key,
            released_date=released_date,
            track_url=track_url,
            source_page_type=source_type
        )
    
    except Exception as e:
        print(f"Error parsing track element: {e}")
        return None


def _parse_track_list(section, label_name: str, source_type: str) -> List[TrackMeta]:
    """Parse a list of tracks from a section."""
    tracks = []
    track_elements = section.find_all(["div", "li"], class_=re.compile("track|item", re.I))
    
    for element in track_elements:
        track = _parse_track_element(element, label_name, source_type)
        if track:
            tracks.append(track)
    
    return tracks


def extract_artists_from_tracks(tracks: List[TrackMeta]) -> Set[str]:
    """
    Extract unique artist names from tracks.
    
    Args:
        tracks: List of TrackMeta objects.
    
    Returns:
        Set of unique artist names (normalized).
    """
    artists = set()
    
    for track in tracks:
        if track.artists:
            # Split by comma and normalize
            artist_list = [a.strip() for a in track.artists.split(",")]
            for artist in artist_list:
                if artist:
                    # Normalize: trim whitespace, basic cleanup
                    normalized = artist.strip()
                    if normalized:
                        artists.add(normalized)
    
    return artists


def parse_label_top10(html: str, label_name: str) -> List[TrackMeta]:
    """
    Parse Top Ten Tracks section from label page.
    
    Args:
        html: HTML content.
        label_name: Name of the label.
    
    Returns:
        List of TrackMeta objects.
    """
    soup = BeautifulSoup(html, "html.parser")
    tracks = []
    
    # Try to find Top Ten Tracks section specifically
    top10_section = soup.find("div", class_=re.compile("top.*ten|top10", re.I))
    if not top10_section:
        top10_section = soup.find("section", string=re.compile("top.*ten", re.I))
    
    if top10_section:
        top10_tracks = _parse_track_list(top10_section, label_name, "label_top10")
        tracks.extend(top10_tracks)
    
    return tracks


def parse_label_tracks_page(html: str, label_name: str) -> List[TrackMeta]:
    """
    Parse tracks table from label /tracks page.
    
    Args:
        html: HTML content.
        label_name: Name of the label.
    
    Returns:
        List of TrackMeta objects.
    """
    soup = BeautifulSoup(html, "html.parser")
    tracks = []
    
    # Find track table rows
    rows = soup.find_all("tr", class_=re.compile("track|row", re.I))
    if not rows:
        # Try alternative selectors
        rows = soup.select("table tbody tr, .track-list tr")
    
    for row in rows:
        track = _parse_track_row(row, label_name)
        if track:
            tracks.append(track)
    
    return tracks


def _parse_track_row(row, label_name: str) -> TrackMeta:
    """Parse a table row containing track data."""
    try:
        cells = row.find_all(["td", "div"])
        
        # Beatport track table typically has: Title, Artists, Label, Genre, BPM, Key, Release Date
        title = ""
        artists = ""
        genre = ""
        bpm = None
        key = None
        released_date = None
        track_url = ""
        
        # Try to find title link
        title_link = row.find("a", href=re.compile("/track/"))
        if title_link:
            title = title_link.get_text(strip=True)
            href = title_link.get("href", "")
            if href:
                if href.startswith("/"):
                    track_url = f"https://www.beatport.com{href}"
                else:
                    track_url = href
        
        # Find artist links
        artist_links = row.find_all("a", href=re.compile("/artist/"))
        if artist_links:
            artists = ", ".join([a.get_text(strip=True) for a in artist_links])
        
        # Extract other fields from cells
        for i, cell in enumerate(cells):
            text = cell.get_text(strip=True)
            cell_class = cell.get("class", [])
            class_str = " ".join(cell_class).lower()
            
            if "genre" in class_str or (not genre and text and len(text) > 2):
                if not genre:
                    genre = text
            
            if "bpm" in class_str or re.match(r"^\d+$", text):
                try:
                    bpm = float(text)
                except:
                    pass
            
            if "key" in class_str or re.match(r"^[A-G][#b]?m?$", text, re.I):
                if not key:
                    key = text
        
        # Try to find date
        date_elem = row.find("time") or row.find("span", class_=re.compile("date"))
        if date_elem:
            released_date = date_elem.get_text(strip=True)
        
        if not title:
            return None
        
        return TrackMeta(
            title=title,
            artists=artists or "",
            label=label_name,
            genre=genre,
            bpm=bpm,
            key=key,
            released_date=released_date,
            track_url=track_url,
            source_page_type="label_tracks"
        )
    
    except Exception as e:
        print(f"Error parsing track row: {e}")
        return None


def search_label_url(label_name: str) -> str:
    """
    Search for Beatport label URL by name.
    
    Args:
        label_name: Name of the label to search for.
    
    Returns:
        Canonical Beatport label URL, or empty string if not found.
    """
    # Use Beatport search
    search_url = f"https://www.beatport.com/search?q={label_name.replace(' ', '+')}"
    
    html = fetch_html(search_url)
    if not html:
        return ""
    
    soup = BeautifulSoup(html, "html.parser")
    
    # Look for label link in search results
    label_link = soup.find("a", href=re.compile(f"/label/.*{re.escape(label_name.lower().replace(' ', '-'))}", re.I))
    
    if not label_link:
        # Try alternative: look for any label link
        label_links = soup.find_all("a", href=re.compile("/label/"))
        if label_links:
            # Check if any match the label name
            for link in label_links:
                link_text = link.get_text(strip=True)
                if label_name.lower() in link_text.lower() or link_text.lower() in label_name.lower():
                    href = link.get("href", "")
                    if href.startswith("/"):
                        return f"https://www.beatport.com{href}"
                    return href
    
    if label_link:
        href = label_link.get("href", "")
        if href.startswith("/"):
            return f"https://www.beatport.com{href}"
        return href
    
    return ""


def build_label_tracks_url(label_url: str, per_page: int = 50) -> str:
    """
    Build URL for label tracks page.
    
    Args:
        label_url: Base label URL.
        per_page: Number of tracks per page.
    
    Returns:
        URL to label tracks page.
    """
    # Remove trailing slash
    label_url = label_url.rstrip("/")
    
    # Check if already a tracks URL
    if "/tracks" in label_url:
        return label_url
    
    # Append /tracks with pagination
    return f"{label_url}/tracks?page=1&per_page={per_page}"

