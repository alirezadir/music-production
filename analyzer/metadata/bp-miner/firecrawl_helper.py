"""
Helper module for using Firecrawl MCP tools.
This module provides a wrapper for Firecrawl MCP functionality.
"""
import re
from typing import Optional


def parse_artist_url_from_firecrawl_markdown(markdown_content: str, artist_name: str) -> Optional[str]:
    """
    Parse Firecrawl markdown output to extract artist URL.
    
    Args:
        markdown_content: Markdown content from Firecrawl scrape.
        artist_name: Name of the artist to search for.
    
    Returns:
        Canonical Beatport artist URL, or None if not found.
    """
    # Normalize artist name for matching
    artist_name_lower = artist_name.lower().strip()
    artist_name_clean = re.sub(r'\s*\([^)]+\)\s*', '', artist_name_lower)
    
    # Look for artist links in markdown format: [Artist Name](URL "title")
    # Pattern: [Artist Name](https://www.beatport.com/artist/...)
    # Handle both with and without title attribute
    pattern = r'\[([^\]]+)\]\(https://www\.beatport\.com/artist/([^/\)\s"]+)/(\d+)(?:\s+"[^"]*")?\)'
    
    matches = re.findall(pattern, markdown_content)
    
    best_match = None
    best_score = 0
    
    for match_text, artist_slug, artist_id in matches:
        match_text_lower = match_text.lower().strip()
        match_text_clean = re.sub(r'\s*\([^)]+\)\s*', '', match_text_lower)
        
        score = 0
        
        # Exact match (highest priority)
        if artist_name_lower == match_text_lower:
            score = 100
        # Clean name match (without parentheses)
        elif artist_name_clean and match_text_clean and artist_name_clean == match_text_clean:
            score = 90
        # Contains match
        elif artist_name_lower and match_text_lower:
            if artist_name_lower in match_text_lower or match_text_lower in artist_name_lower:
                score = 70
        # Partial match on cleaned names
        elif artist_name_clean and match_text_clean:
            if artist_name_clean in match_text_clean or match_text_clean in artist_name_clean:
                score = 50
        
        # Prefer matches without extra text
        if score > 0 and match_text_lower and len(match_text_lower) <= len(artist_name_lower) + 10:
            score += 10
        
        if score > best_score:
            best_score = score
            best_match = f"https://www.beatport.com/artist/{artist_slug}/{artist_id}"
    
    if best_match and best_score >= 50:
        return best_match
    
    return None

