"""
Label similarity calculator using K-Nearest Neighbors approach.
Finds the most similar B-level labels to each A-level label.
"""
import pandas as pd
from typing import List, Dict
from collections import Counter
import math


def calculate_label_similarity(
    tracks_df: pd.DataFrame,
    a_level_labels: List[str],
    k: int = 5
) -> Dict[str, List[Dict]]:
    """
    Calculate similarity between A-level and B-level labels using KNN.
    
    Similarity is based on:
    - Shared artists
    - Genre overlap
    - BPM distribution similarity
    - Key distribution similarity
    
    Args:
        tracks_df: DataFrame with track data.
        a_level_labels: List of A-level label names.
        k: Number of similar B-level labels to return per A-level.
    
    Returns:
        Dictionary mapping A-level label name to list of similar B-level labels
        with similarity scores.
    """
    # Filter to only artist tracks (where we discovered B-level labels)
    artist_tracks = tracks_df[tracks_df["source_page_type"] == "artist_tracks"]
    
    if artist_tracks.empty:
        return {}
    
    # Get all B-level labels from tracks
    b_level_labels = tracks_df[
        (tracks_df["label_tier"] == "B") |
        (~tracks_df["label"].isin(a_level_labels))
    ]["label"].unique()
    
    # Remove A-level labels from B-level candidates
    b_level_labels = [label for label in b_level_labels if label not in a_level_labels]
    
    if not b_level_labels:
        return {}
    
    # Calculate similarity for each A-level label
    results = {}
    
    for a_label in a_level_labels:
        # Get tracks from this A-level label
        a_tracks = tracks_df[tracks_df["label"] == a_label]
        
        if a_tracks.empty:
            continue
        
        # Calculate features for A-level label
        a_features = _extract_label_features(a_tracks)
        
        # Calculate similarity to each B-level label
        similarities = []
        
        for b_label in b_level_labels:
            # Get tracks from this B-level label
            b_tracks = artist_tracks[artist_tracks["label"] == b_label]
            
            if b_tracks.empty:
                continue
            
            # Calculate features for B-level label
            b_features = _extract_label_features(b_tracks)
            
            # Calculate similarity score
            similarity = _calculate_feature_similarity(a_features, b_features)
            
            similarities.append({
                "label_name": b_label,
                "similarity_score": similarity,
                "shared_artists": len(a_features["artists"] & b_features["artists"]),
                "shared_genres": len(a_features["genres"] & b_features["genres"])
            })
        
        # Sort by similarity and take top K
        similarities.sort(key=lambda x: x["similarity_score"], reverse=True)
        results[a_label] = similarities[:k]
    
    return results


def _extract_label_features(tracks_df: pd.DataFrame) -> Dict:
    """Extract features from tracks for similarity calculation."""
    features = {
        "artists": set(),
        "genres": set(),
        "bpm_values": [],
        "keys": []
    }
    
    for _, track in tracks_df.iterrows():
        # Artists
        if pd.notna(track.get("artists")) and track.get("artists"):
            artists = [a.strip() for a in str(track["artists"]).split(",")]
            features["artists"].update(artists)
        
        # Genres
        if pd.notna(track.get("genre")) and track.get("genre"):
            features["genres"].add(str(track["genre"]).strip())
        
        # BPM
        if pd.notna(track.get("bpm")) and track.get("bpm"):
            try:
                features["bpm_values"].append(float(track["bpm"]))
            except:
                pass
        
        # Keys
        if pd.notna(track.get("key")) and track.get("key"):
            features["keys"].append(str(track["key"]).strip())
    
    # Calculate statistics
    features["avg_bpm"] = sum(features["bpm_values"]) / len(features["bpm_values"]) if features["bpm_values"] else None
    features["bpm_std"] = _calculate_std(features["bpm_values"]) if features["bpm_values"] else None
    features["key_distribution"] = Counter(features["keys"])
    
    return features


def _calculate_feature_similarity(features_a: Dict, features_b: Dict) -> float:
    """Calculate similarity score between two label feature sets."""
    score = 0.0
    weights = {
        "artists": 0.4,
        "genres": 0.3,
        "bpm": 0.2,
        "keys": 0.1
    }
    
    # Artist overlap (Jaccard similarity)
    if features_a["artists"] or features_b["artists"]:
        intersection = len(features_a["artists"] & features_b["artists"])
        union = len(features_a["artists"] | features_b["artists"])
        artist_sim = intersection / union if union > 0 else 0
        score += weights["artists"] * artist_sim
    
    # Genre overlap (Jaccard similarity)
    if features_a["genres"] or features_b["genres"]:
        intersection = len(features_a["genres"] & features_b["genres"])
        union = len(features_a["genres"] | features_b["genres"])
        genre_sim = intersection / union if union > 0 else 0
        score += weights["genres"] * genre_sim
    
    # BPM similarity (inverse distance)
    if features_a["avg_bpm"] and features_b["avg_bpm"]:
        bpm_diff = abs(features_a["avg_bpm"] - features_b["avg_bpm"])
        # Normalize: max difference ~40 BPM, so divide by 40
        bpm_sim = max(0, 1 - (bpm_diff / 40))
        score += weights["bpm"] * bpm_sim
    
    # Key distribution similarity (cosine similarity)
    if features_a["key_distribution"] and features_b["key_distribution"]:
        all_keys = set(features_a["key_distribution"].keys()) | set(features_b["key_distribution"].keys())
        if all_keys:
            vec_a = [features_a["key_distribution"].get(k, 0) for k in all_keys]
            vec_b = [features_b["key_distribution"].get(k, 0) for k in all_keys]
            key_sim = _cosine_similarity(vec_a, vec_b)
            score += weights["keys"] * key_sim
    
    return score


def _calculate_std(values: List[float]) -> float:
    """Calculate standard deviation."""
    if not values:
        return 0
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return math.sqrt(variance)


def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    magnitude_a = math.sqrt(sum(a * a for a in vec_a))
    magnitude_b = math.sqrt(sum(b * b for b in vec_b))
    
    if magnitude_a == 0 or magnitude_b == 0:
        return 0
    
    return dot_product / (magnitude_a * magnitude_b)

