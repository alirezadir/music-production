# Beatport Label Miner

Automated system for scraping Beatport to discover A-level and B-level labels, artists, and tracks.

## Overview

This system scrapes Beatport for:
- **A-level labels** (top-tier labels like Afterlife Records, Anjunadeep)
- **Artists** associated with those labels
- **B-level labels** that those artists release on
- **Tracks** from those B-level labels

All data is stored in CSV files and can be synced to Google Sheets.

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure the system:
   - Edit `config.json` with your A-level labels and URLs
   - Set up Google Sheets credentials (optional, for sync functionality)

## Configuration

Edit `config.json` to specify:
- `a_level_labels`: List of A-level label names
- `a_level_label_urls`: Mapping of label names to Beatport URLs
- `exclude_labels`: Labels to exclude from B-level classification
- `tracks_per_page`: Number of tracks to fetch per page (default: 50)

## Environment Variables

Optional environment variables:
- `CONFIG_PATH`: Path to config file (default: `config.json`)
- `ARTISTS_CSV`: Path to artists CSV (default: `artists.csv`)
- `LABELS_CSV`: Path to labels CSV (default: `labels.csv`)
- `TRACKS_CSV`: Path to tracks CSV (default: `tracks.csv`)
- `GOOGLE_SERVICE_ACCOUNT_JSON`: Path to Google service account JSON (for Sheets sync)
- `GOOGLE_SHEET_URL`: URL of Google Sheet to sync to

## Usage

### Run Full Pipeline

Run all phases in sequence:
```bash
python run_full_pipeline.py
```

Run specific phases:
```bash
python run_full_pipeline.py --phases 1,2,3
```

### Run Individual Phases

1. **Seed artists from A-level labels:**
```bash
python seed_artists_from_labels.py
```

2. **Scrape artist tracks:**
```bash
python scrape_artist_tracks.py
```

3. **Classify B-level labels:**
```bash
python classify_b_labels.py
```

4. **Scrape B-level label tracks:**
```bash
python scrape_b_labels.py
```

5. **Clean and deduplicate:**
```bash
python clean_all.py
```

6. **Sync to Google Sheets:**
```bash
python sync_all_to_sheets.py
```

## Data Schemas

### artists.csv
- `artist_name`: Normalized artist name
- `beatport_url`: Canonical Beatport artist URL
- `source_label`: Initial A-level label that led to this artist
- `created_at`: ISO timestamp

### labels.csv
- `label_name`: Normalized label name
- `beatport_url`: Canonical Beatport label URL
- `tier`: "A", "B", or "unknown"
- `discovered_from_artist`: Optional artist info
- `created_at`: ISO timestamp

### tracks.csv
- `title`: Track title
- `artists`: Comma-separated artist names
- `label`: Label name
- `label_tier`: "A", "B", or "unknown"
- `genre`: Genre
- `bpm`: BPM (number)
- `key`: Musical key
- `released_date`: ISO date
- `track_url`: Beatport track URL
- `source_page_type`: "label_top10", "label_tracks", or "artist_tracks"
- `source_label`: A-level seed label if applicable
- `source_artist`: Artist name if applicable
- `created_at`: ISO timestamp

## Notes

- The scraper includes delays between requests to be respectful to Beatport
- All data is deduplicated before saving
- Google Sheets sync requires service account credentials
- The system handles errors gracefully and continues processing

