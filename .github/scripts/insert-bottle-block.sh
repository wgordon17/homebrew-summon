#!/usr/bin/env bash
# Parse bottle JSON artifacts and insert a `bottle do` block into the formula.
# Usage: insert-bottle-block.sh <artifact_dir>
#   Expects REPO and VERSION environment variables.
set -euo pipefail

ARTIFACT_DIR="$1"
FORMULA="Formula/summon-claude.rb"
ROOT_URL="https://github.com/${REPO}/releases/download/v${VERSION}"
BLOCK=$(mktemp)

# Header
printf '\n  bottle do\n    root_url "%s"\n' "$ROOT_URL" > "$BLOCK"

# Extract sha256 lines — jq handles cellar conversion and formatting
found=0
for json_file in "$ARTIFACT_DIR"/bottle-json-*/summon-claude-*.bottle.json; do
  [ -f "$json_file" ] || continue
  jq -r '
    .["summon-claude"].bottle as $b |
    ($b.cellar | if . == "any" or . == "any_skip_relocation" then ":" + . else "\"" + . + "\"" end) as $c |
    $b.tags | to_entries[] |
    "    sha256 cellar: \($c), \(.key): \"\(.value.sha256)\""
  ' "$json_file" >> "$BLOCK"
  found=$((found + 1))
done

[ "$found" -gt 0 ] || { echo "ERROR: No bottle JSONs in $ARTIFACT_DIR" >&2; rm "$BLOCK"; exit 1; }

echo "  end" >> "$BLOCK"

sed -i '/license "MIT"/r '"$BLOCK" "$FORMULA"
rm "$BLOCK"
echo "Inserted bottle block ($found platform(s))"
