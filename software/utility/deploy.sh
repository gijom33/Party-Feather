#!/bin/bash
# === deploy_feather.sh ===

# Change this to your project path
PROJECT_DIR="./software/src"
# CIRCUITPY drive (macOS path; on Linux use /media/$USER/CIRCUITPY)
BOARD_PATH="/Volumes/CIRCUITPY"

# Safety check
if [ ! -d "$BOARD_PATH" ]; then
  echo "❌ CIRCUITPY drive not found. Is the board connected?"
  exit 1
fi

echo "🚀 Deploying code to Feather board..."
rsync -av --exclude='.git*' \
    --exclude='*.DS_Store' \
    "$PROJECT_DIR"/ "$BOARD_PATH"/

# Optional: small beep on success
afplay /System/Library/Sounds/Glass.aiff 2>/dev/null || true
echo "✅ Done!"
