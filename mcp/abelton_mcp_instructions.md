# AbletonMCP — Setup Guide (Verified Working)

Control Ableton Live directly via Claude Code over a local socket connection.  
Source: https://github.com/ahujasid/ableton-mcp

---

## What You Need
- Ableton Live 10+
- Terminal
- (Optional) `uv` if using Claude Desktop MCP integration

---

## Step 1 — Install the Ableton Remote Script

This is the only file you need from the repo — no cloning required.

```bash
# Create the folder and download the script in one step
mkdir -p ~/Library/Preferences/Ableton/Live\ 12.4/User\ Remote\ Scripts/AbletonMCP

curl -fsSL https://raw.githubusercontent.com/ahujasid/ableton-mcp/main/AbletonMCP_Remote_Script/__init__.py \
  -o ~/Library/Preferences/Ableton/Live\ 12.4/User\ Remote\ Scripts/AbletonMCP/__init__.py
```

> ⚠️ Replace `Live 12.4` with your actual Ableton version folder name.  
> Check with: `ls ~/Library/Preferences/Ableton/`

**Installed location:**
```
~/Library/Preferences/Ableton/Live 12.4/User Remote Scripts/AbletonMCP/__init__.py
```

---

## Step 2 — Activate in Ableton

1. **Quit and relaunch Ableton Live** (required to pick up new scripts)
2. Go to **Settings** → `⌘,` → **Link, Tempo & MIDI** tab
3. In any **Control Surface** slot set to `None` → select **AbletonMCP**
4. Set both **Input** and **Output** to **None**
5. Close Settings

✅ You should see in Ableton's status bar:
> `AbletonMCP: Listening for commands on port 9877`

---

## Step 3 — Verify the Connection

```bash
# Quick connection test
nc -z localhost 9877 && echo "✅ Connected" || echo "❌ Not reachable"

# Read session info
echo '{"type":"get_session_info","params":{}}' | nc -w 3 localhost 9877
```

Expected response:
```json
{"status": "success", "result": {"tempo": 125.0, "track_count": 158, ...}}
```

---

## How It Works

- The `__init__.py` remote script runs **inside Ableton** as a TCP socket server on **port 9877**
- No separate MCP server process needed — connect directly via socket
- Commands are JSON over TCP; no HTTP, no external dependencies

---

## Available Commands

| Command | Description |
|---------|-------------|
| `get_session_info` | Tempo, time sig, track count, master vol |
| `get_track_info` | Track name, type, clips, devices |
| `create_midi_track` | Add a new MIDI track |
| `set_track_name` | Rename a track |
| `create_clip` | Create a MIDI clip in a slot |
| `add_notes_to_clip` | Write MIDI notes into a clip |
| `set_clip_name` | Rename a clip |
| `set_tempo` | Change session BPM |
| `fire_clip` | Launch a clip (session view) |
| `stop_clip` | Stop a clip |
| `start_playback` | Start arrangement playback |
| `stop_playback` | Stop arrangement playback |
| `load_browser_item` | Load instrument/effect by URI |
| `get_browser_tree` | Browse available instruments/effects |
| `get_browser_items_at_path` | Drill into browser categories |

---

## Optional — Claude Desktop MCP Integration

If you want to use AbletonMCP as a proper MCP server in Claude Desktop:

### Install uv
```bash
brew install uv
```

### Add to Claude Desktop config
`~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "AbletonMCP": {
      "command": "uvx",
      "args": ["ableton-mcp"]
    }
  }
}
```
Restart Claude Desktop — you'll see a 🔨 hammer icon with Ableton tools.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Port 9877 not reachable | Ableton not running, or AbletonMCP not set as Control Surface |
| AbletonMCP not in dropdown | Restart Ableton after installing the script |
| Script installed but not showing | Check folder name is exactly `AbletonMCP` and file is `__init__.py` |
| Wrong Live version path | Check `ls ~/Library/Preferences/Ableton/` for correct folder name |
