#!/usr/bin/env bash
set -euo pipefail

REQ_FILE="vendor_requirements.txt"
OUT_DIR="vendor_modules"
ZIP_FILE="vendor_modules.zip"

# Choose a Python
if command -v python3 >/dev/null 2>&1; then
  PYTHON="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON="python"
else
  echo "Error: python not found on PATH." >&2
  exit 1
fi

# Ensure requirements file exists
if [[ ! -f "$REQ_FILE" ]]; then
  echo "Error: $REQ_FILE not found." >&2
  exit 1
fi

# Clean previous outputs
rm -f "$ZIP_FILE"

# Install into a target folder (includes transitive deps)
"$PYTHON" -m pip install \
  --upgrade \
  --no-cache-dir \
  -r "$REQ_FILE" \
  -t "$OUT_DIR"

# Optional: prune __pycache__ to slim the zip
find "$OUT_DIR" -type d -name "__pycache__" -exec rm -rf {} +

# Zip results (use system 'zip' if present, else pure-Python fallback)
if command -v zip >/dev/null 2>&1; then
  (cd "$OUT_DIR" && zip -r "../$ZIP_FILE" .)
else
  "$PYTHON" - <<'PY'
import os, zipfile
src = "vendor_modules"
dst = "vendor_modules.zip"
with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
    for root, _, files in os.walk(src):
        for f in files:
            p = os.path.join(root, f)
            z.write(p, os.path.relpath(p, src))
print(f"Created {dst}")
PY
fi
rm -rf "$OUT_DIR"
echo "Done:"
echo "  Zipped as:    $ZIP_FILE"