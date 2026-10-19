#!/bin/sh
# Rebuild and mirror docs/ to the local preview folder (the preview server can't read ~/Documents).
cd "$(dirname "$0")/.." && python3 scripts/build.py "$@" && rsync -a --delete docs/ "${CCS_PREVIEW_DIR:-/private/tmp/claude-501/-Users-evanlopez--claude-spares-spare-wK8Mkn/aa835f5a-99a0-4dae-9f19-b0b7237f6bf8/scratchpad/site}/"
