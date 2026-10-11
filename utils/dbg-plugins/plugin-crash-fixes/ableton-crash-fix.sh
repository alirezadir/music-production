#!/bin/bash

ABLETON_VERSION="Live 12.3.5"
PREFS_DIR=~/Library/Preferences/Ableton/"$ABLETON_VERSION"
REMOTE_SCRIPTS_DIR="$PREFS_DIR/User Remote Scripts"

echo "=== Ableton Live $ABLETON_VERSION Crash Fix ==="
echo ""

# Step 1: Fix broken Remote Script folder names (hyphens -> underscores)
echo "[1/4] Fixing broken Remote Script names..."
for dir in "$REMOTE_SCRIPTS_DIR"/*/; do
    dirname=$(basename "$dir")
    if [[ "$dirname" == *-* ]]; then
        newname="${dirname//-/_}"
        echo "  Renaming '$dirname' -> '$newname'"
        mv "$dir" "$REMOTE_SCRIPTS_DIR/$newname"
    fi
done
echo "  Done."
echo ""

# Step 2: Clear the plugin scan cache (forces a clean rescan)
echo "[2/4] Clearing plugin scan cache..."
rm -f "$PREFS_DIR/PluginScanDb.txt"
echo "  Removed PluginScanDb.txt"
echo ""

# Step 3: Clear crash detection state
echo "[3/4] Clearing crash detection state..."
rm -f "$PREFS_DIR/CrashDetection.cfg"
rm -f "$PREFS_DIR/CrashRecoveryInfo.cfg"
echo "  Cleared CrashDetection.cfg and CrashRecoveryInfo.cfg"
echo ""

# Step 4: Clear Undo/recovery locks
echo "[4/4] Clearing undo locks..."
rm -f "$PREFS_DIR/Undo.lock"
echo "  Cleared Undo.lock"
echo ""

echo "=== Fix applied! ==="
echo ""
echo "Next steps:"
echo "  1. Open Ableton Live"
echo "  2. When prompted, DO NOT open the last project"
echo "  3. Instead, start with an empty project first"
echo "  4. Then open the Kafan-Deer-Remix project -- missing plugins"
echo "     will show as 'missing' but won't crash."
echo ""
echo "The crash was caused by these missing plugins in your project:"
echo "  - Pro-Q 3 / Pro-MB (FabFilter)"
echo "  - NLS Buss (Waves) -- on nearly every bus channel"
echo "  - soothe2 (oeksound)"
echo "  - Neutron 4 Transient Shaper (iZotope)"
echo "  - SplitEQ (Eventide)"
echo "  - bx_limiter (Plugin Alliance)"
echo "  - Sugar (Plugin Alliance)"
echo "  - FUSER (Native Instruments)"
echo "  - ValhallaShimmer (Valhalla DSP)"
echo "  - LFOTool (Xfer/Cableguys)"
echo ""
echo "Install these plugins or remove them from the project to prevent issues."
