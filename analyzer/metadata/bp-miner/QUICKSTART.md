# Quick Start Guide

## Setup

1. **Install dependencies:**
```bash
cd /Users/alirezadirafzoon/GitHub/Deer-Code/music-production/analysis/bp-miner
pip install -r requirements.txt
```

2. **Configure your A-level labels:**
Edit `config.json` to add your A-level labels and their Beatport URLs.

Example:
```json
{
  "a_level_labels": ["Afterlife Records", "Anjunadeep"],
  "a_level_label_urls": {
    "Afterlife Records": "https://www.beatport.com/label/afterlife-records/56958",
    "Anjunadeep": "https://www.beatport.com/label/anjunadeep/8871"
  },
  "exclude_labels": ["Afterlife Records", "Anjunadeep"],
  "tracks_per_page": 50
}
```

3. **Optional: Set up Google Sheets sync:**
```bash
export GOOGLE_SERVICE_ACCOUNT_JSON="/path/to/service-account.json"
export GOOGLE_SHEET_URL="https://docs.google.com/spreadsheets/d/..."
```

## Running the Pipeline

### Option 1: Run Full Pipeline
```bash
python run_full_pipeline.py
```

This will run all phases:
1. Seed artists from A-level labels
2. Scrape artist tracks
3. Classify B-level labels
4. Scrape B-level label tracks
5. Clean and deduplicate
6. Sync to Google Sheets (if configured)

### Option 2: Run Individual Phases

```bash
# Phase 1: Seed artists
python seed_artists_from_labels.py

# Phase 2: Scrape artist tracks
python scrape_artist_tracks.py

# Phase 3: Classify B-level labels
python classify_b_labels.py

# Phase 4: Scrape B-level tracks
python scrape_b_labels.py

# Phase 5: Clean data
python clean_all.py

# Phase 6: Sync to Google Sheets
python sync_all_to_sheets.py
```

## Output Files

After running, you'll have:
- `artists.csv` - All discovered artists
- `labels.csv` - All labels (A and B tier)
- `tracks.csv` - All discovered tracks

## Notes

- The scraper includes delays between requests to be respectful
- All data is automatically deduplicated
- If Google Sheets credentials aren't set, Phase 6 will skip gracefully
- You can re-run phases individually to update data

