#!/usr/bin/env bash
# Fetch sdist info from PyPI and write version/url/sha256 to GITHUB_OUTPUT.
# Usage: pypi-info.sh [expected_version]
#   If expected_version is provided, fails when PyPI doesn't match.
set -euo pipefail

EXPECTED="${1:-}"

INFO=$(curl -sf https://pypi.org/pypi/summon-claude/json)
VERSION=$(echo "$INFO" | jq -r '.info.version')
URL=$(echo "$INFO" | jq -r '.urls[] | select(.packagetype=="sdist") | .url')
SHA256=$(echo "$INFO" | jq -r '.urls[] | select(.packagetype=="sdist") | .digests.sha256')

if [ -n "$EXPECTED" ] && [ "$VERSION" != "$EXPECTED" ]; then
  echo "ERROR: PyPI version ($VERSION) does not match expected ($EXPECTED). PyPI may not have propagated yet."
  exit 1
fi

echo "version=$VERSION" >> "$GITHUB_OUTPUT"
echo "url=$URL" >> "$GITHUB_OUTPUT"
echo "sha256=$SHA256" >> "$GITHUB_OUTPUT"
