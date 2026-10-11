# AbletonMCP — Current Status

## ✅ Working End-to-End

Local MCP server controls Ableton Live 12 via TCP socket, integrated into Claude Code.

```
Claude Code → run_server.sh → MCP server (stdio) → socket :9877 → Ableton remote script
```

---

## Components

| Component | Location | Status |
|-----------|----------|--------|
| Ableton remote script | `~/Library/Preferences/Ableton/Live 12.4/User Remote Scripts/AbletonMCP/__init__.py` | ✅ Active, listening on port 9877 |
| Local MCP server (cloned repo) | `~/Documents/Workspace/music-production/mcp/ableton-mcp/` | ✅ Built (`uv sync`) |
| Server wrapper script | `~/Documents/Workspace/music-production/mcp/ableton-mcp/run_server.sh` | ✅ Bypasses py3.13 `.pth` issue |
| Claude Code MCP config | `~/.claude.json` (project scope) | ✅ Points to `run_server.sh` |
| Test client | `~/Documents/Workspace/music-production/mcp/test_mcp_client.py` | ✅ Verifies full MCP handshake |
| `uv` / `uvx` | Homebrew install | ✅ v0.11.16 |

---

## Verified Operations

- **MCP handshake:** `initialize` → server reports `AbletonMCP v1.4.0`
- **Tool discovery:** 16 tools enumerated via `tools/list`
- **Tool execution:** `get_session_info` returns live data (tempo, track count, master vol)
- **Direct socket queries:** Reading all 168 tracks, including names, types, clips
- **Source-cloned setup:** Editing `MCP_Server/server.py` then restarting Claude Code picks up changes

---

## 16 MCP Tools Available

| Category | Tools |
|----------|-------|
| **Session** | `get_session_info`, `set_tempo` |
| **Tracks** | `get_track_info`, `create_midi_track`, `set_track_name` |
| **Clips** | `create_clip`, `add_notes_to_clip`, `set_clip_name`, `fire_clip`, `stop_clip` |
| **Transport** | `start_playback`, `stop_playback` |
| **Browser/Devices** | `get_browser_tree`, `get_browser_items_at_path`, `load_instrument_or_effect`, `load_drum_kit` |

---

## Known Quirk

**Python 3.13 skips setuptools-generated editable `.pth` files** (security heuristic), so `uv run ableton-mcp` fails to import `MCP_Server`. The `run_server.sh` wrapper sidesteps this by running `python -m MCP_Server.server` from the project root so cwd is on `sys.path`.

## Activation Checklist (Each Session)

1. Ableton Live open
2. **Settings → Link, Tempo & MIDI → Control Surface = AbletonMCP** (status bar shows `Listening for commands on port 9877`)
3. Claude Code restart loads `mcp__ableton-mcp__*` tools natively

## Next Steps (Open)

- Add custom tools to `MCP_Server/server.py` (e.g. bulk `list_all_tracks`, arrangement-position reader, clip note reader)
- Optional: configure Claude Desktop with the same wrapper for desktop access
