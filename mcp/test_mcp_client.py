"""Quick MCP client to test the local ableton-mcp server end-to-end via stdio."""
import json
import subprocess
import sys

PROC = subprocess.Popen(
    ["/Users/alirezadir/Documents/Workspace/music-production/mcp/ableton-mcp/run_server.sh"],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    text=True, bufsize=1,
)

def send(req):
    PROC.stdin.write(json.dumps(req) + "\n")
    PROC.stdin.flush()
    return json.loads(PROC.stdout.readline())

# 1. Initialize MCP session
init = send({
    "jsonrpc": "2.0", "id": 1, "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "test", "version": "0.1"},
    },
})
print(f"✅ Initialized: {init['result']['serverInfo']}")

# Required: send initialized notification
PROC.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
PROC.stdin.flush()

# 2. List tools
tools = send({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
print(f"\n📦 Available MCP tools ({len(tools['result']['tools'])}):")
for t in tools["result"]["tools"]:
    print(f"  • {t['name']}")

# 3. Call get_session_info
print("\n🎵 Calling get_session_info tool...")
result = send({
    "jsonrpc": "2.0", "id": 3, "method": "tools/call",
    "params": {"name": "get_session_info", "arguments": {}},
})
print(result["result"]["content"][0]["text"])

PROC.terminate()
