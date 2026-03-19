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
CANONICAL_OPML="${HOME}/GrapplingMap/exports/grappling.opml"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_OPML="${REPO_ROOT}/grappling.opml"
CONVERTER="${SCRIPT_DIR}/opml_to_sections.py"
LIVE_FOLDER_GEN="${HOME}/GrapplingMap/tools/live_folders_from_opml.py"

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
    local ts
    ts=$(date +"%Y%m%d_%H%M%S")

    # ── STEP 1: Ensure canonical OPML is up-to-date ──────────────────
    # Find newest Downloads export
    local latest_dl
    latest_dl=$(ls -t "${DOWNLOADS_DIR}"/grappling*.opml 2>/dev/null | head -n 1)

    if [[ -n "${latest_dl}" && -f "${latest_dl}" ]]; then
        # Stale-guard: always copy newest Downloads → canonical
        cp "${latest_dl}" "${CANONICAL_OPML}"
        log "OPML_SOURCE=downloads:${latest_dl}"
    elif [[ -f "${CANONICAL_OPML}" ]]; then
        log "OPML_SOURCE=exports:${CANONICAL_OPML} (no newer download)"
    else
        err "No OPML found in Downloads or exports. Checked:"
        err "  Downloads: ${DOWNLOADS_DIR}/grappling*.opml"
        err "  Canonical: ${CANONICAL_OPML}"
        return 1
    fi

    log "OPML_SOURCE=exports:${CANONICAL_OPML}"
    log "OPML_MTIME=$(stat -f '%Sm' -t '%Y-%m-%dT%H:%M:%S' "${CANONICAL_OPML}" 2>/dev/null || date -r "${CANONICAL_OPML}" '+%Y-%m-%dT%H:%M:%S' 2>/dev/null || echo 'unknown')"

    # Archive timestamped copy
    local archive_name="grappling_${ts}.opml"
    cp "${CANONICAL_OPML}" "${ARCHIVE_DIR}/${archive_name}"
    log "Archived -> archive/${archive_name}"

    # Copy canonical to repo working copy (for git tracking)
    cp "${CANONICAL_OPML}" "${REPO_OPML}"

    # ── STEP 2: Run pipeline from canonical OPML ─────────────────────
    log "Running opml_to_sections.py ${CANONICAL_OPML}"
    if ! python3 "${CONVERTER}" "${CANONICAL_OPML}"; then
        err "Conversion failed. Aborting commit."
        return 1
    fi

    # ── STEP 3: Live-footage folder generation from same canonical ───
    log "LIVE_OPML=${CANONICAL_OPML}"
    python3 "${LIVE_FOLDER_GEN}" "${CANONICAL_OPML}" >/dev/null 2>&1 || true

    # ── STEP 4: Git commit + push ────────────────────────────────────
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
        # Write result to results.md feed
        local commit_hash
        commit_hash=$(git log -1 --format='%h')
        local edge_count no_dest_count in_network_count
        edge_count=$(python3 -c "
import re, sys
with open('${REPO_OPML}') as f: t = f.read()
arrows = re.findall(r'.+\s*(?:->|→|â†')\s*.+', t)
print(len([a for a in arrows if re.match(r'.+\S\s*(?:->|→|â†')\s*\S', a)]))" 2>/dev/null || echo "null")
        no_dest_count=$(python3 -c "
import re
with open('${REPO_OPML}') as f: t = f.read()
bare = [a for a in re.findall(r'(?:->|→|â†')\s*\S+', t) if not re.match(r'\S+\s*(?:->|→|â†')', a)]
print(len(bare))" 2>/dev/null || echo "null")
        in_network_count="null"
        if [[ -f "${SCRIPT_DIR}/write-result.sh" ]]; then
            bash "${SCRIPT_DIR}/write-result.sh" \
                "PIPELINE-AUTO" \
                "OPML pipeline auto-run: ${edge_count} edges, ${no_dest_count} NO_DEST" \
                "${commit_hash}" \
                "${edge_count}" \
                "${no_dest_count}" \
                "${in_network_count}" || true
        fi
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
