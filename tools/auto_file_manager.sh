#!/bin/zsh
set -euo pipefail

HOME_DIR="$HOME"
HUB="$HOME_DIR/Documents/UnifiedHub"
LOG_DIR="$HUB/_logs"
LOG_FILE="$LOG_DIR/auto_file_manager.log"
TS="$(date '+%Y-%m-%d %H:%M:%S')"

mkdir -p "$LOG_DIR" "$HUB/OpenClaw" "$HUB/Claude" "$HUB/Archive"

log(){
  echo "[$TS] $*" | tee -a "$LOG_FILE"
}

# ---------------------------
# 1) Mirror key workspaces
# ---------------------------
mirror(){
  local src="$1"
  local dst="$2"
  mkdir -p "$dst"
  if [[ -d "$src" || -f "$src" ]]; then
    rsync -a --delete "$src" "$dst" >> "$LOG_FILE" 2>&1 || true
    log "Mirrored: $src -> $dst"
  else
    log "Skip missing source: $src"
  fi
}

mirror "$HOME_DIR/.openclaw/agents/main/workspace/" "$HUB/OpenClaw/workspace/"
mirror "$HOME_DIR/.claude/" "$HUB/Claude/.claude/"
mirror "$HOME_DIR/.claude.json" "$HUB/Claude/"
mirror "$HOME_DIR/.claude.json.backup" "$HUB/Claude/"

# ---------------------------
# 2) Auto-archive older loose files from Desktop/Downloads
# conservative rules: older than 21 days, non-hidden regular files
# ---------------------------
archive_from_dir(){
  local src_root="$1"
  local label="$2"
  local archive_month
  archive_month="$(date '+%Y-%m')"
  local dst_root="$HUB/Archive/$archive_month/$label"
  mkdir -p "$dst_root"

  find "$src_root" -maxdepth 1 -type f -mtime +21 ! -name '.*' | while IFS= read -r f; do
    local base ext subdir dst
    base="$(basename "$f")"
    ext="${base##*.}"
    ext="${ext:l}"

    case "$ext" in
      pdf|md|txt|doc|docx|xls|xlsx|ppt|pptx|csv|json|html|js|ts|py|ipynb|zip|7z|rar|jpg|jpeg|png|webp|gif|mp4|mov|mp3|wav)
        ;;
      *)
        subdir="other"
        ;;
    esac

    if [[ -z "${subdir:-}" ]]; then
      subdir="$ext"
    fi

    dst="$dst_root/$subdir"
    mkdir -p "$dst"

    if [[ ! -e "$dst/$base" ]]; then
      mv "$f" "$dst/"
      log "Archived: $f -> $dst/$base"
    else
      # avoid overwrite, append timestamp
      local stamped
      stamped="${base:r}_$(date '+%H%M%S').${base:e}"
      mv "$f" "$dst/$stamped"
      log "Archived (renamed): $f -> $dst/$stamped"
    fi
    unset subdir
  done
}

archive_from_dir "$HOME_DIR/Desktop" "Desktop"
archive_from_dir "$HOME_DIR/Downloads" "Downloads"

log "Run completed"
