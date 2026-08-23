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
#   2. Regenerates the generated assets and STOPS if any were stale.
#   3. Refreshes <lastmod> in sitemap.xml to today's date so search
#      engines see fresh timestamps on every push.
#   4. Shows you what changed and asks for confirmation.
#   5. Commits with the chosen message and pushes to origin/main.
#   6. Prints the GitHub Actions URL and live-site URL so you can
#      verify the deploy.
#
# Run from anywhere — the script cds to its own directory first.
#
#   --skip-build   deploy without regenerating (see the note in stage 2)
#
# ── Why stage 2 exists ───────────────────────────────────────────────────
# Some files in this repo are OUTPUT, not source:
#
#   favicon.png, favicon.ico, apple-touch-icon.png,
#   Images/lucidbit-logo-*.png          ← from Images/favicon.svg
#   Images/og/og-*.png                  ← from index.html + app icons
#
# Nothing stops you editing a source file, forgetting the generator, and
# pushing yesterday's PNGs. That is not hypothetical: the root favicons sat
# stale through several deploys because the palette had been updated in the
# SVG and nowhere else, and a favicon is exactly the kind of thing nobody
# re-checks. So the script regenerates them every time and refuses to push
# if the regeneration changed anything — a stale asset becomes a blocked
# deploy with a diff to look at, instead of a silent wrong file on the CDN.
# ─────────────────────────────────────────────────────────────────────────

set -e

REPO_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$REPO_DIR"

# Strip --skip-build out of the arguments so "$1" is still the commit message.
SKIP_BUILD=0
ARGS=()
for arg in "$@"; do
    if [ "$arg" = "--skip-build" ]; then SKIP_BUILD=1; else ARGS+=("$arg"); fi
done
set -- "${ARGS[@]+"${ARGS[@]}"}"

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

# ── Stage 2: regenerate generated assets, and stop if any were stale ─────
#
# The staleness test is "did regenerating change the file?", which is only
# meaningful if the generators are deterministic — same inputs, byte-identical
# output. Both are: no timestamps, no randomness, no PNG metadata that varies
# per run. If that ever stops being true this check will cry wolf on every
# deploy, and the fix is to make the generator deterministic again rather than
# to delete the check.
#
# Only tracked files are compared. Untracked output (a brand-new card, say) is
# not "stale" — it's new, and stage 4 will show it to you like any other change.
if [ "$SKIP_BUILD" = "1" ]; then
    echo -e "${YELLOW}⚠ Skipping asset regeneration (--skip-build).${RESET}"
    echo -e "${DIM}  Generated files will be pushed exactly as they are on disk.${RESET}"
elif ! command -v python3 >/dev/null 2>&1; then
    # Don't fail the deploy over a missing interpreter — say so and move on,
    # so a machine without python3 can still push a text-only change.
    echo -e "${YELLOW}⚠ python3 not found — skipping asset regeneration.${RESET}"
else
    echo -e "${DIM}→ Regenerating assets…${RESET}"

    # Fingerprint the generated files BEFORE regenerating. `git stash list`-free
    # approach: just ask git what differs afterwards.
    GENERATED_PATHS=(
        favicon.png favicon.ico apple-touch-icon.png
        Images/lucidbit-logo-192.png Images/lucidbit-logo-512.png
        Images/og
    )
    BEFORE=$(git diff --name-only -- "${GENERATED_PATHS[@]}" 2>/dev/null || true)

    # A generator that can't run is not a reason to ship silently, so this
    # aborts — but it aborts with the two ways out, because the usual cause is
    # a missing dependency on a new machine rather than anything wrong with
    # the assets themselves.
    generator_failed() {
        echo ""
        echo -e "${RED}✗ $1 failed. Nothing pushed.${RESET}"
        echo ""
        echo -e "${YELLOW}  Most likely Pillow isn't installed for this python3:${RESET}"
        echo -e "      python3 -m pip install --user Pillow"
        echo -e "${DIM}      (add --break-system-packages if macOS refuses)${RESET}"
        echo ""
        echo -e "${DIM}  Or skip the check if the assets are already current:${RESET}"
        echo -e "${DIM}      ./deploy.sh \"your message\" --skip-build${RESET}"
        echo ""
        exit 1
    }

    ( cd Images     && python3 make-logo.py >/dev/null ) \
        || generator_failed "Images/make-logo.py"
    ( cd Images/og  && python3 make-og.py  >/dev/null ) \
        || generator_failed "Images/og/make-og.py"

    AFTER=$(git diff --name-only -- "${GENERATED_PATHS[@]}" 2>/dev/null || true)

    # Anything that changed as a RESULT of this run — i.e. present in AFTER but
    # not in BEFORE — was stale on disk and would have shipped wrong.
    STALE=$(comm -13 <(echo "$BEFORE" | sort -u) <(echo "$AFTER" | sort -u) | sed '/^$/d')

    if [ -n "$STALE" ]; then
        echo ""
        echo -e "${RED}✗ Stale generated assets found and rebuilt:${RESET}"
        echo "$STALE" | sed 's/^/    /'
        echo ""
        echo -e "${YELLOW}  These were out of date with their source files.${RESET}"
        echo -e "${DIM}  Review them (git diff), then re-run ./deploy.sh to push.${RESET}"
        echo -e "${DIM}  To push anyway without rebuilding: ./deploy.sh --skip-build${RESET}"
        echo ""
        exit 1
    fi
    echo -e "${DIM}  All generated assets were already current.${RESET}"
fi

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
