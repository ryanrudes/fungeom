#!/usr/bin/env bash
# Sync wiki/*.md to the GitHub wiki. The wiki must already be INITIALIZED: create the first page
# once at https://github.com/ryanrudes/fungeom/wiki (any content), then run this. Re-run to sync.
set -euo pipefail
REPO_WIKI="https://github.com/ryanrudes/fungeom.wiki.git"
HERE="$(cd "$(dirname "$0")" && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
git clone "$REPO_WIKI" "$TMP"
cp "$HERE"/*.md "$TMP"/
rm -f "$TMP/README.md"   # the staging explainer is not a wiki page
cd "$TMP"
git add -A
git commit -m "Sync wiki from repo wiki/" || { echo "wiki already up to date"; exit 0; }
git push
echo "Wiki updated: https://github.com/ryanrudes/fungeom/wiki"
