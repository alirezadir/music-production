"""Data cleaning and normalization utilities."""
import pandas as pd
import re
from typing import Dict


def normalize_label_name(name: str) -> str:
    """
    Normalize label name.
    
    Args:
        name: Raw label name.
    
    Returns:
        Normalized label name.
    """
    if pd.isna(name) or name == "":
        return ""
    
    # Trim whitespace
    normalized = str(name).strip()
    
    # Basic normalization: title case (but preserve special cases)
    # Don't change if it's all caps (likely intentional)
    if not normalized.isupper():
        normalized = normalized.title()
    
    return normalized


def normalize_artist_name(name: str) -> str:
    """
    Normalize artist name.
    
    Args:
        name: Raw artist name.
    
    Returns:
        Normalized artist name.
    """
    if pd.isna(name) or name == "":
        return ""
    
    # Trim whitespace
    normalized = str(name).strip()
    
    # Basic normalization: title case (but preserve special cases)
    if not normalized.isupper():
        normalized = normalized.title()
    
    return normalized


def normalize_track_row(row: Dict) -> Dict:
    """
    Normalize a track row dictionary.
    
    Args:
        row: Dictionary representing a track row.
    
    Returns:
        Normalized dictionary.
    """
    normalized = row.copy()
    
    # Normalize string fields
    if "title" in normalized:
        normalized["title"] = str(normalized.get("title", "")).strip()
    
    if "artists" in normalized:
        # Normalize each artist in comma-separated list
        artists = str(normalized.get("artists", "")).strip()
        if artists:
            artist_list = [normalize_artist_name(a) for a in artists.split(",")]
            normalized["artists"] = ", ".join([a for a in artist_list if a])
        else:
            normalized["artists"] = ""
    
    if "label" in normalized:
        normalized["label"] = normalize_label_name(normalized.get("label", ""))
    
    if "genre" in normalized:
        normalized["genre"] = str(normalized.get("genre", "")).strip()
    
    if "key" in normalized:
        key = str(normalized.get("key", "")).strip()
        normalized["key"] = key if key else ""
    
    # Normalize BPM
    if "bpm" in normalized:
        bpm = normalized.get("bpm")
        if pd.isna(bpm) or bpm == "":
            normalized["bpm"] = None
        else:
            try:
                normalized["bpm"] = float(bpm)
            except (ValueError, TypeError):
                normalized["bpm"] = None
    
    # Normalize release date
    if "released_date" in normalized:
        date = normalized.get("released_date")
        if pd.isna(date) or date == "":
            normalized["released_date"] = ""
        else:
            # Try to normalize date format (basic)
            date_str = str(date).strip()
            normalized["released_date"] = date_str
    
    # Normalize URLs
    if "track_url" in normalized:
        url = str(normalized.get("track_url", "")).strip()
        normalized["track_url"] = url
    
    if "source_label" in normalized:
        normalized["source_label"] = normalize_label_name(normalized.get("source_label", ""))
    
    if "source_artist" in normalized:
        normalized["source_artist"] = normalize_artist_name(normalized.get("source_artist", ""))
    
    return normalized


def deduplicate_tracks(df: pd.DataFrame) -> pd.DataFrame:
    """
    Deduplicate tracks DataFrame.
    
    Uses track_url if available, else (title, artists, label, released_date).
    
    Args:
        df: DataFrame with tracks.
    
    Returns:
        Deduplicated DataFrame.
    """
    if df.empty:
        return df
    
    # Create deduplication key
    def create_key(row):
        if pd.notna(row.get("track_url")) and row.get("track_url") != "":
            return f"url:{row['track_url']}"
        else:
            title = str(row.get("title", "")).strip()
            artists = str(row.get("artists", "")).strip()
            label = str(row.get("label", "")).strip()
            date = str(row.get("released_date", "")).strip()
            return f"meta:{title}|{artists}|{label}|{date}"
    
    df["_dedup_key"] = df.apply(create_key, axis=1)
    
    # Keep first occurrence of each key
    df_dedup = df.drop_duplicates(subset=["_dedup_key"], keep="first")
    
    # Drop temporary key column
    df_dedup = df_dedup.drop(columns=["_dedup_key"])
    
    return df_dedup.reset_index(drop=True)

