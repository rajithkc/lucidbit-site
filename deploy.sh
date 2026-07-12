#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────
# deploy.sh — push local website changes to GitHub, which triggers the
# Actions workflow that deploys lucidbit.app.
#
# Usage:
#   ./deploy.sh                          # auto-generate a commit message
#   ./deploy.sh "your commit message"    # use a custom message
#
# What it does, in order:
#   1. Cleans junk (.DS_Store, sitemap.xml.bak, *.swp).
#   2. Refreshes <lastmod> in sitemap.xml to today's date so search
#      engines see fresh timestamps on every push.
#   3. Shows you what changed and asks for confirmation.
#   4. Commits with the chosen message and pushes to origin/main.
#   5. Prints the GitHub Actions URL and live-site URL so you can
#      verify the deploy.
#
# Run from anywhere — the script cds to its own directory first.
# ─────────────────────────────────────────────────────────────────────────

set -e

REPO_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$REPO_DIR"

GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
DIM="\033[2m"
RESET="\033[0m"

echo ""
echo -e "${DIM}→ Cleaning junk (.DS_Store, *.bak, *.swp)…${RESET}"
find . -name ".DS_Store"     -type f -not -path "./.git/*" -delete 2>/dev/null || true
find . -name "*.bak"         -type f -not -path "./.git/*" -delete 2>/dev/null || true
find . -name "*.swp"         -type f -not -path "./.git/*" -delete 2>/dev/null || true
find . -name "sitemap.xml.bak" -delete 2>/dev/null || true

# Sitemap lastmod refresh — only if sitemap.xml exists.
TODAY=$(date +%Y-%m-%d)
if [ -f sitemap.xml ]; then
    echo -e "${DIM}→ Refreshing sitemap.xml lastmod to ${TODAY}…${RESET}"
    sed -i.bak "s|<lastmod>[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}</lastmod>|<lastmod>${TODAY}</lastmod>|g" sitemap.xml
    rm -f sitemap.xml.bak
fi

# Bail if nothing to commit.
if [ -z "$(git status --porcelain)" ]; then
    echo ""
    echo -e "${GREEN}✓ Working tree clean — nothing to deploy.${RESET}"
    exit 0
fi

# Show what's changing.
echo ""
echo -e "${YELLOW}Changes since last commit:${RESET}"
git status --short
echo ""

# Build the commit message.
if [ -z "$1" ]; then
    # Auto-generate: take up to 5 changed files, comma-joined.
    CHANGED=$(
        { git diff --name-only HEAD 2>/dev/null;
          git diff --cached --name-only 2>/dev/null;
          git ls-files --others --exclude-standard 2>/dev/null; } \
        | sort -u | head -5 | tr '\n' ', ' | sed 's/, $//'
    )
    COMMIT_MSG="Update site: ${CHANGED}"
else
    COMMIT_MSG="$1"
fi

echo -e "Commit message:  ${GREEN}${COMMIT_MSG}${RESET}"
echo ""
read -p "Proceed with commit + push? [Y/N] " -n 1 -r
echo ""

# Default Yes: cancel only if the user explicitly answered N/n.
# Accepts: <Enter> (yes), y, Y, n, N. Anything else falls through to yes.
if [[ $REPLY =~ ^[Nn]$ ]]; then
    echo -e "${RED}✗ Cancelled. No changes pushed.${RESET}"
    echo -e "${DIM}  (Local files are still as they are; nothing was reverted.)${RESET}"
    exit 1
fi

echo ""
echo -e "${DIM}→ Staging all changes…${RESET}"
git add -A

echo -e "${DIM}→ Committing…${RESET}"
git commit -m "$COMMIT_MSG"

echo -e "${DIM}→ Pulling remote changes (rebase) before push…${RESET}"
git pull --rebase origin main

echo -e "${DIM}→ Pushing to origin/main…${RESET}"
git push origin main

echo ""
echo -e "${GREEN}✓ Pushed.${RESET}"
echo ""
echo "  Watch the deploy:   https://github.com/rajithkc/lucidbit-site/actions"
echo "  Live site:          https://lucidbit.app/"
echo ""
echo -e "${DIM}  Allow ~1-2 min for the Action to finish, then hard-refresh${RESET}"
echo -e "${DIM}  (Cmd+Shift+R on macOS) to bypass any cached pages.${RESET}"
echo ""
