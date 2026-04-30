#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

# Install system deps needed for native modules + AppImage
bash install-linux-deps.sh

cd app
npm install
npm run dist:linux

echo ""
echo "Build complete. Output: poeClient/app/dist/"
