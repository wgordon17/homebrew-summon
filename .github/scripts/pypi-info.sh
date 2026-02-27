#!/usr/bin/env bash
# Fetch sdist info from PyPI and write version/url/sha256 to GITHUB_OUTPUT.
# Usage: pypi-info.sh [expected_version]
#   If expected_version is provided, retries until PyPI matches (up to 5 min).
set -euo pipefail

EXPECTED="${1:-}"
MAX_ATTEMPTS=10
DELAY=30

for attempt in $(seq 1 "$MAX_ATTEMPTS"); do
  INFO=$(curl -sf https://pypi.org/pypi/summon-claude/json)
  VERSION=$(echo "$INFO" | jq -r '.info.version')
  URL=$(echo "$INFO" | jq -r '.urls[] | select(.packagetype=="sdist") | .url')
  SHA256=$(echo "$INFO" | jq -r '.urls[] | select(.packagetype=="sdist") | .digests.sha256')

  if [ -z "$EXPECTED" ] || [ "$VERSION" = "$EXPECTED" ]; then
    echo "version=$VERSION" >> "$GITHUB_OUTPUT"
    echo "url=$URL" >> "$GITHUB_OUTPUT"
    echo "sha256=$SHA256" >> "$GITHUB_OUTPUT"
    exit 0
  fi

  echo "Attempt $attempt/$MAX_ATTEMPTS: PyPI has $VERSION, waiting for $EXPECTED (${DELAY}s)"
  sleep "$DELAY"
done

echo "ERROR: PyPI version ($VERSION) did not match expected ($EXPECTED) after $((MAX_ATTEMPTS * DELAY))s"
exit 1
