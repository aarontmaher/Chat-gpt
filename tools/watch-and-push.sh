#!/usr/bin/env bash
# tools/watch-and-push.sh
#
# Watches ~/GrapplingMap/exports/ AND ~/Downloads/ for new .opml files.
# On detection:
#   1. Copies newest .opml to repo/grappling.opml  (canonical path)
#   2. Archives a timestamped copy in ~/GrapplingMap/exports/archive/
#   3. Runs opml_to_sections.py to update const SECTIONS in index.html
#   4. git add grappling.opml index.html && git commit && git push
#      (skips commit if no changes detected)
#
# Usage:
#   bash tools/watch-and-push.sh
#
# Stop: Ctrl-C

set -euo pipefail

# Configuration
EXPORTS_DIR="${HOME}/GrapplingMap/exports"
ARCHIVE_DIR="${HOME}/GrapplingMap/exports/archive"
DOWNLOADS_DIR="${HOME}/Downloads"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
CANONICAL_OPML="${REPO_ROOT}/grappling.opml"
CONVERTER="${SCRIPT_DIR}/opml_to_sections.py"

# Colour helpers
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
log()  { echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $*"; }
warn() { echo -e "${YELLOW}[$(date '+%H:%M:%S')] WARN:${NC} $*"; }
err()  { echo -e "${RED}[$(date '+%H:%M:%S')] ERROR:${NC} $*" >&2; }

# Pre-flight checks
if ! command -v fswatch &>/dev/null; then
    err "fswatch not found. Install with: brew install fswatch"
    exit 1
fi
if ! command -v python3 &>/dev/null; then
    err "python3 not found. Install from https://python.org or via Homebrew."
    exit 1
fi
if [[ ! -f "${CONVERTER}" ]]; then
    err "Converter not found: ${CONVERTER}"
    exit 1
fi
if [[ ! -d "${REPO_ROOT}/.git" ]]; then
    err "Not a git repo: ${REPO_ROOT}"
    exit 1
fi

mkdir -p "${EXPORTS_DIR}" "${ARCHIVE_DIR}"

echo ""
echo "----------------------------------------------------"
echo "  Grappling Map OPML Watcher"
echo "  Watching : ${EXPORTS_DIR}"
echo "           : ${DOWNLOADS_DIR}"
echo "  Repo     : ${REPO_ROOT}"
echo "  Press Ctrl-C to stop"
echo "----------------------------------------------------"
echo ""

handle_new_opml() {
    local changed_file="$1"

    # Only process .opml files
    [[ "${changed_file}" == *.opml ]] || return 0

    # Skip anything inside the archive folder
    [[ "${changed_file}" == "${ARCHIVE_DIR}"* ]] && return 0

    # Skip if it doesn't exist (e.g. delete events)
    [[ -f "${changed_file}" ]] || return 0

    log "Detected: ${changed_file}"

    # Use the file that was just saved (works for both exports + Downloads)
    local newest="${changed_file}"
    log "Processing: $(basename "${newest}")"

    # Archive timestamped copy
    local ts
    ts=$(date +"%Y%m%d_%H%M%S")
    local archive_name="grappling_${ts}.opml"
    cp "${newest}" "${ARCHIVE_DIR}/${archive_name}"
    log "Archived -> archive/${archive_name}"

    # Copy to canonical path in repo
    cp "${newest}" "${CANONICAL_OPML}"
    log "Copied to $(basename "${CANONICAL_OPML}")"

    # Run OPML to SECTIONS conversion
    log "Converting OPML -> updating index.html..."
    if ! python3 "${CONVERTER}"; then
        err "Conversion failed. Aborting commit."
        return 1
    fi

    # Auto-create live footage folders for new canonical positions (safe, additive-only)
    python3 "${HOME}/GrapplingMap/tools/live_folders_from_opml.py" >/dev/null 2>&1 || true

    # Git: detect changes, commit, push
    cd "${REPO_ROOT}"

    if git diff --quiet grappling.opml index.html 2>/dev/null \
       && ! git ls-files --others --exclude-standard -- grappling.opml index.html | grep -q .; then
        warn "No changes detected -- skipping commit"
        return 0
    fi

    git add grappling.opml index.html
    git commit -m "Update grappling map from Mindomo export [${ts}]"

    log "Pulling latest from GitHub (in case worktree pushed)..."
    if ! git pull --no-rebase origin main 2>/dev/null; then
        # Conflict — accept ours (watcher's pipeline output is latest)
        if git diff --name-only --diff-filter=U | grep -q .; then
            git checkout --ours index.html 2>/dev/null || true
            git add index.html
            git commit --no-edit 2>/dev/null || true
            log "Resolved merge conflict (accepted our pipeline output)"
        fi
    fi

    log "Pushing to GitHub..."
    if git push; then
        log "Done! GitHub Pages will update in ~30-60 seconds."
    else
        err "git push failed. Check credentials (see README for help)."
        return 1
    fi
    echo ""
}

# Watch both the exports folder AND Downloads
fswatch -0 --event Created --event Updated --event Renamed \
    "${EXPORTS_DIR}" "${DOWNLOADS_DIR}" \
    | while IFS= read -r -d '' changed_file; do
        handle_new_opml "${changed_file}" || true
    done
