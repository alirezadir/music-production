# How to Run

Due to system permission restrictions, please run the pipeline locally in your terminal.

## Quick Start

### Option 1: Use the setup script
```bash
cd /Users/alirezadirafzoon/GitHub/Deer-Code/music-production/analysis/bp-miner
./setup_and_run.sh
```

### Option 2: Manual steps

1. **Install dependencies:**
```bash
cd /Users/alirezadirafzoon/GitHub/Deer-Code/music-production/analysis/bp-miner

# Using uv (recommended):
uv pip install -r requirements.txt

# Or using pip:
pip3 install -r requirements.txt
```

2. **Verify config:**
```bash
cat config.json
```

3. **Run the full pipeline:**
```bash
python3 run_full_pipeline.py
```

4. **Or run phases individually:**
```bash
# Phase 1: Seed artists
python3 seed_artists_from_labels.py

# Phase 2: Scrape artist tracks  
python3 scrape_artist_tracks.py

# Phase 3: Classify B-level labels
python3 classify_b_labels.py

# Phase 4: Scrape B-level tracks
python3 scrape_b_labels.py

# Phase 5: Clean data
python3 clean_all.py

# Phase 6: Sync to Google Sheets (optional)
python3 sync_all_to_sheets.py
```

## What to Expect

The pipeline will:
1. ✅ Scrape A-level label pages to find artists
2. ✅ Search for artist Beatport URLs
3. ✅ Scrape tracks from artist pages
4. ✅ Identify B-level labels from artist releases
5. ✅ Scrape tracks from B-level labels
6. ✅ Clean and deduplicate all data
7. ✅ Optionally sync to Google Sheets

Output files will be created:
- `artists.csv`
- `labels.csv`  
- `tracks.csv`

## Troubleshooting

- **Import errors**: Make sure all dependencies are installed
- **Network errors**: Check your internet connection
- **Permission errors**: Try using `--user` flag with pip or use `uv`
- **Google Sheets errors**: Set `GOOGLE_SERVICE_ACCOUNT_JSON` and `GOOGLE_SHEET_URL` env vars, or skip Phase 6

