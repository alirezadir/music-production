"""Artist page scraper for Beatport."""
import re
from typing import List, Optional
from bs4 import BeautifulSoup
from models import TrackMeta
from scraper_utils import fetch_html

# Try to use Firecrawl if available
try:
    # This would be called via MCP, but for now we'll use direct HTML parsing
    USE_FIRECRAWL = False
except:
    USE_FIRECRAWL = False


def search_artist_url_firecrawl_markdown(markdown_content: str, artist_name: str) -> str:
    """
    Parse Firecrawl markdown output to extract artist URL.
    
    Args:
        markdown_content: Markdown content from Firecrawl scrape.
        artist_name: Name of the artist to search for.
    
    Returns:
        Canonical Beatport artist URL, or empty string if not found.
    """
    import re
    
    # Normalize artist name for matching
    artist_name_lower = artist_name.lower().strip()
    artist_name_clean = re.sub(r'\s*\([^)]+\)\s*', '', artist_name_lower)
    
    # Look for artist links in markdown format: [Artist Name](URL)
    # Pattern: [Artist Name](https://www.beatport.com/artist/...)
    pattern = r'\[([^\]]+)\]\(https://www\.beatport\.com/artist/([^/]+)/(\d+)\)'
    
    matches = re.findall(pattern, markdown_content)
    
    best_match = None
    best_score = 0
    
    for match_text, artist_slug, artist_id in matches:
        match_text_lower = match_text.lower().strip()
        match_text_clean = re.sub(r'\s*\([^)]+\)\s*', '', match_text_lower)
        
        score = 0
        
        # Exact match
        if artist_name_lower == match_text_lower:
            score = 100
        # Clean name match
        elif artist_name_clean and match_text_clean and artist_name_clean == match_text_clean:
            score = 90
        # Contains match
        elif artist_name_lower and match_text_lower:
            if artist_name_lower in match_text_lower or match_text_lower in artist_name_lower:
                score = 70
        
        if score > best_score:
            best_score = score
            best_match = f"https://www.beatport.com/artist/{artist_slug}/{artist_id}"
    
    if best_match and best_score >= 50:
        return best_match
    
    return ""


def search_artist_url(artist_name: str) -> str:
    """
    Search for Beatport artist URL by name.
    
    Args:
        artist_name: Name of the artist to search for.
    
    Returns:
        Canonical Beatport artist URL, or empty string if not found.
    """
    # Use Beatport search
    search_url = f"https://www.beatport.com/search?q={artist_name.replace(' ', '+')}"
    
    html = fetch_html(search_url)
    if not html:
        return ""
    
    soup = BeautifulSoup(html, "html.parser")
    
    # Normalize artist name for matching
    artist_name_lower = artist_name.lower().strip()
    # Remove common suffixes like "(ofc)", "(UK)", etc. for matching
    artist_name_clean = re.sub(r'\s*\([^)]+\)\s*', '', artist_name_lower)
    
    # Try multiple strategies to find artist links
    
    # Strategy 1: Look in the "Artists" section
    artists_section = soup.find("section", string=re.compile("Artists", re.I))
    if not artists_section:
        # Try finding by heading
        artists_heading = soup.find(["h2", "h3"], string=re.compile("Artists", re.I))
        if artists_heading:
            artists_section = artists_heading.find_parent()
    
    # Strategy 2: Find all artist links anywhere
    artist_links = soup.find_all("a", href=re.compile("/artist/"))
    
    # If we found an artists section, prioritize links within it
    if artists_section:
        section_links = artists_section.find_all("a", href=re.compile("/artist/"))
        if section_links:
            artist_links = section_links
    
    if not artist_links:
        return ""
    
    # Score and find best match
    best_match = None
    best_score = 0
    
    for link in artist_links:
        href = link.get("href", "")
        if not href:
            continue
            
        # Get link text - try multiple ways
        link_text = link.get_text(strip=True)
        if not link_text:
            # Try getting from title attribute
            link_text = link.get("title", "")
        if not link_text:
            # Try getting from alt text of image
            img = link.find("img")
            if img:
                link_text = img.get("alt", "")
        
        link_text_lower = link_text.lower().strip() if link_text else ""
        link_text_clean = re.sub(r'\s*\([^)]+\)\s*', '', link_text_lower)
        
        # Calculate match score
        score = 0
        
        # Exact match (highest priority)
        if artist_name_lower == link_text_lower:
            score = 100
        # Clean name match (without parentheses)
        elif artist_name_clean and link_text_clean and artist_name_clean == link_text_clean:
            score = 90
        # Contains match
        elif artist_name_lower and link_text_lower:
            if artist_name_lower in link_text_lower or link_text_lower in artist_name_lower:
                score = 70
        # Partial match on cleaned names
        elif artist_name_clean and link_text_clean:
            if artist_name_clean in link_text_clean or link_text_clean in artist_name_clean:
                score = 50
        
        # Prefer matches without extra text
        if score > 0 and link_text_lower and len(link_text_lower) <= len(artist_name_lower) + 10:
            score += 10
        
        if score > best_score:
            best_score = score
            best_match = href
    
    if best_match and best_score >= 50:
        if best_match.startswith("/"):
            return f"https://www.beatport.com{best_match}"
        elif best_match.startswith("http"):
            return best_match
        else:
            return f"https://www.beatport.com/{best_match}"
    
    return ""


def build_artist_tracks_url(artist_url: str, per_page: int = 50) -> str:
    """
    Build URL for artist tracks page.
    
    Args:
        artist_url: Base artist URL.
        per_page: Number of tracks per page.
    
    Returns:
        URL to artist tracks page.
    """
    # Remove trailing slash
    artist_url = artist_url.rstrip("/")
    
    # Check if already a tracks URL
    if "/tracks" in artist_url:
        return artist_url
    
    # Append /tracks with pagination
    return f"{artist_url}/tracks?page=1&per_page={per_page}"


def parse_artist_tracks_page(html: str, artist_name: str) -> List[TrackMeta]:
    """
    Parse artist tracks page HTML to extract track metadata.
    
    Args:
        html: HTML content of artist tracks page.
        artist_name: Name of the artist.
    
    Returns:
        List of TrackMeta objects.
    """
    soup = BeautifulSoup(html, "html.parser")
    tracks = []
    
    # Find track table rows
    rows = soup.find_all("tr", class_=re.compile("track|row", re.I))
    if not rows:
        # Try alternative selectors
        rows = soup.select("table tbody tr, .track-list tr, [data-ec-name]")
    
    # If still no rows, try finding track items
    if not rows:
        track_items = soup.find_all(["div", "li"], class_=re.compile("track|item", re.I))
        for item in track_items:
            track = _parse_track_item(item, artist_name)
            if track:
                tracks.append(track)
        return tracks
    
    # Parse table rows
    for row in rows:
        track = _parse_track_row(row, artist_name)
        if track:
            tracks.append(track)
    
    return tracks


def _parse_track_row(row, artist_name: str) -> TrackMeta:
    """Parse a table row containing track data."""
    try:
        cells = row.find_all(["td", "div"])
        
        title = ""
        artists = artist_name  # Default to the artist we're scraping
        label = ""
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
        
        # Find artist links (may include collaborators)
        artist_links = row.find_all("a", href=re.compile("/artist/"))
        if artist_links:
            artists = ", ".join([a.get_text(strip=True) for a in artist_links])
        
        # Find label link
        label_link = row.find("a", href=re.compile("/label/"))
        if label_link:
            label = label_link.get_text(strip=True)
        
        # Extract other fields from cells
        for cell in cells:
            text = cell.get_text(strip=True)
            cell_class = cell.get("class", [])
            class_str = " ".join(cell_class).lower()
            
            if "genre" in class_str:
                if not genre:
                    genre = text
            
            if "bpm" in class_str or (not bpm and re.match(r"^\d+$", text)):
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
            artists=artists or artist_name,
            label=label,
            genre=genre,
            bpm=bpm,
            key=key,
            released_date=released_date,
            track_url=track_url,
            source_page_type="artist_tracks"
        )
    
    except Exception as e:
        print(f"Error parsing track row: {e}")
        return None


def _parse_track_item(item, artist_name: str) -> TrackMeta:
    """Parse a track item element."""
    try:
        # Extract title
        title_elem = item.find(["a", "span"], class_=re.compile("title|name", re.I))
        if not title_elem:
            title_elem = item.find("a", href=re.compile("/track/"))
        title = title_elem.get_text(strip=True) if title_elem else ""
        
        # Extract artists
        artists_elem = item.find(["a", "span"], class_=re.compile("artist", re.I))
        if not artists_elem:
            artist_links = item.find_all("a", href=re.compile("/artist/"))
            artists = ", ".join([a.get_text(strip=True) for a in artist_links]) if artist_links else artist_name
        else:
            artists = artists_elem.get_text(strip=True)
        
        # Extract label
        label_elem = item.find("a", href=re.compile("/label/"))
        label = label_elem.get_text(strip=True) if label_elem else ""
        
        # Extract genre
        genre_elem = item.find(["span", "a"], class_=re.compile("genre", re.I))
        genre = genre_elem.get_text(strip=True) if genre_elem else ""
        
        # Extract BPM
        bpm_elem = item.find(["span", "div"], class_=re.compile("bpm", re.I))
        bpm = None
        if bpm_elem:
            bpm_text = bpm_elem.get_text(strip=True)
            bpm_match = re.search(r"(\d+)", bpm_text)
            if bpm_match:
                bpm = float(bpm_match.group(1))
        
        # Extract key
        key_elem = item.find(["span", "div"], class_=re.compile("key", re.I))
        key = key_elem.get_text(strip=True) if key_elem else None
        
        # Extract release date
        date_elem = item.find(["span", "time"], class_=re.compile("date|release", re.I))
        released_date = date_elem.get_text(strip=True) if date_elem else None
        
        # Extract track URL
        track_link = item.find("a", href=re.compile("/track/"))
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
            artists=artists or artist_name,
            label=label,
            genre=genre,
            bpm=bpm,
            key=key,
            released_date=released_date,
            track_url=track_url,
            source_page_type="artist_tracks"
        )
    
    except Exception as e:
        print(f"Error parsing track item: {e}")
        return None

