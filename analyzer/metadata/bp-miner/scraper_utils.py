"""Utility functions for web scraping."""
import time
import random
import requests
from typing import Optional


def fetch_html(url: str, retries: int = 3, delay_range: tuple = (1, 3)) -> Optional[str]:
    """
    Fetch HTML content from URL with retries and delays.
    
    Args:
        url: URL to fetch.
        retries: Number of retry attempts.
        delay_range: Tuple of (min, max) seconds to wait between requests.
    
    Returns:
        HTML content as string, or None if all retries failed.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    for attempt in range(retries):
        try:
            # Random delay to be polite
            if attempt > 0:
                delay = random.uniform(*delay_range)
                time.sleep(delay)
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.text
        
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1}/{retries} failed for {url}: {e}")
            if attempt == retries - 1:
                return None
    
    return None

