"""
Track Library

A small “track library” layer on top of the existing 4-pillar analyzers.

Goals:
- Ingest a folder of favorite tracks (audio + optional Ableton projects)
- Store metadata + tags in a local SQLite DB
- Attach analysis artifacts using the unified `TrackAnalysis` schema
- Query common patterns by label/artist/tag groups
"""


