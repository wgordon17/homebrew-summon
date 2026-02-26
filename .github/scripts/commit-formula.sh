#!/usr/bin/env bash
# Stage Formula/summon-claude.rb, commit with the given message, and push.
# Expects GH_TOKEN and REPO environment variables.
# Usage: commit-formula.sh "commit message"
set -euo pipefail

MSG="$1"

git remote set-url origin "https://x-access-token:${GH_TOKEN}@github.com/${REPO}.git"
git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
git add Formula/summon-claude.rb

if git diff --cached --quiet; then
  echo "No changes to formula"
  exit 0
fi

git commit -m "$MSG"
git push origin main
