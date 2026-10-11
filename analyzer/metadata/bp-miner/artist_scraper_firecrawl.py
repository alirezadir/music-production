"""Artist page scraper using Firecrawl MCP for better parsing."""
import re
from typing import List, Optional
from bs4 import BeautifulSoup
from models import TrackMeta
from scraper_utils import fetch_html

# Note: This module uses Firecrawl MCP tools which should be called externally
# For now, we'll create a wrapper that can use Firecrawl when available


def search_artist_url_firecrawl(artist_name: str) -> str:
    """
    Search for Beatport artist URL using Firecrawl MCP.
    
    This function is designed to be called with Firecrawl MCP tools.
    The actual implementation would use mcp_firecrawl_search and mcp_firecrawl_scrape.
    
    Args:
        artist_name: Name of the artist to search for.
    
    Returns:
        Canonical Beatport artist URL, or empty string if not found.
    """
    # This is a placeholder - actual implementation would use MCP tools
    # The caller should use Firecrawl MCP tools directly
    pass


def search_artist_url(artist_name: str, use_firecrawl: bool = False) -> str:
    """
    Search for Beatport artist URL by name.
    
    Args:
        artist_name: Name of the artist to search for.
        use_firecrawl: If True, attempt to use Firecrawl (requires MCP setup).
    
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

