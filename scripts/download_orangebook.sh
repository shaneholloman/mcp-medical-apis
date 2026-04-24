#!/usr/bin/env bash
# Download FDA Orange Book flat files (patent, exclusivity, product listings).
# https://www.fda.gov/drugs/drug-approvals-and-databases/orange-book-data-files
#
# Usage: ./scripts/download_orangebook.sh [TARGET_DIR]
#   TARGET_DIR defaults to ./data/orangebook (relative to repo root)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TARGET_DIR="${1:-$REPO_ROOT/data/orangebook}"
ZIP_URL="https://www.fda.gov/media/76860/download?attachment"

mkdir -p "$TARGET_DIR"

TMPZIP=$(mktemp)
trap 'rm -f "$TMPZIP"' EXIT

echo "Downloading FDA Orange Book data..."
curl -sL "$ZIP_URL" -o "$TMPZIP"
unzip -oq "$TMPZIP" -d "$TARGET_DIR"

echo "Orange Book files:"
wc -l "$TARGET_DIR"/*.txt
echo "Saved to $TARGET_DIR"
