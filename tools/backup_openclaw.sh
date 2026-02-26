#!/bin/zsh
set -euo pipefail

# OpenClaw Daily Backup Script
# Usage: backup_openclaw.sh [manual|daily]

HOME_DIR="$HOME"
BACKUP_ROOT="$HOME_DIR/Documents/OpenClaw_Backups"
DROPBOX_ROOT="$HOME_DIR/Dropbox/A_dropbox/OpenClaw_Archive"
WORKSPACE="$HOME_DIR/.openclaw/agents/main/workspace"
DATE_STR="$(date '+%Y-%m-%d')"
DATETIME_STR="$(date '+%Y-%m-%d_%H%M%S')"
TS="$(date '+%Y-%m-%d %H:%M:%S')"

# Determine backup type and category
if [[ "${1:-}" == "manual" ]]; then
    BACKUP_TYPE="manual"
    # Try to detect task category from recent git commits or memory files
    CATEGORY="manual_backup"
    if git -C "$WORKSPACE" log -1 --oneline 2>/dev/null | grep -qiE '(feat|feature|新功能|开发)'; then
        CATEGORY="01_NewFeature_Development"
    elif git -C "$WORKSPACE" log -1 --oneline 2>/dev/null | grep -qiE '(fix|bug|修复|维护)'; then
        CATEGORY="02_Maintenance_Repair"
    elif git -C "$WORKSPACE" log -1 --oneline 2>/dev/null | grep -qiE '(chore|ops|备份|同步|后勤)'; then
        CATEGORY="03_Logistics_Operations"
    elif git -C "$WORKSPACE" log -1 --oneline 2>/dev/null | grep -qiE '(test|qa|验证|审查)'; then
        CATEGORY="04_Testing_QA"
    elif git -C "$WORKSPACE" log -1 --oneline 2>/dev/null | grep -qiE '(doc|文档|报告)'; then
        CATEGORY="05_Documentation_Reports"
    else
        CATEGORY="06_Daily_Activity"
    fi
else
    BACKUP_TYPE="daily"
    CATEGORY="06_Daily_Activity"
fi

# Create backup directories
BACKUP_DIR="$BACKUP_ROOT/$DATE_STR"
DROPBOX_DIR="$DROPBOX_ROOT/$CATEGORY/$DATE_STR"
mkdir -p "$BACKUP_DIR" "$DROPBOX_DIR"

# Log function
log(){
    echo "[$TS] $*" | tee -a "$BACKUP_ROOT/backup.log"
}

log "=== OpenClaw Backup Started ==="
log "Type: $BACKUP_TYPE | Category: $CATEGORY | Date: $DATE_STR"

# Create backup archive
ARCHIVE_NAME="openclaw_backup_${DATETIME_STR}.tar.gz"
ARCHIVE_PATH="$BACKUP_DIR/$ARCHIVE_NAME"

log "Creating backup archive: $ARCHIVE_NAME"
tar -czf "$ARCHIVE_PATH" \
    --exclude='.git/objects' \
    --exclude='__pycache__' \
    --exclude='node_modules' \
    --exclude='.pytest_cache' \
    -C "$HOME_DIR/.openclaw" \
    "agents/main/workspace" \
    "agents/main/config" \
    2>&1 || log "Warning: Some paths may not exist"

# Create metadata file
META_FILE="$BACKUP_DIR/backup_${DATETIME_STR}_metadata.json"
cat > "$META_FILE" <<EOF
{
  "backup_date": "$DATE_STR",
  "backup_datetime": "$DATETIME_STR",
  "backup_type": "$BACKUP_TYPE",
  "category": "$CATEGORY",
  "workspace_path": "$WORKSPACE",
  "archive_name": "$ARCHIVE_NAME",
  "archive_size_bytes": $(stat -f%z "$ARCHIVE_PATH" 2>/dev/null || echo 0),
  "git_commit": "$(git -C "$WORKSPACE" rev-parse --short HEAD 2>/dev/null || echo 'none')",
  "git_message": "$(git -C "$WORKSPACE" log -1 --pretty=%s 2>/dev/null | tr '"' "'" || echo 'none')",
  "memory_files": $(ls "$WORKSPACE/memory/"*.md 2>/dev/null | wc -l | tr -d ' '),
  "source": "OpenClaw main agent workspace"
}
EOF

# Sync to Dropbox with category structure
log "Syncing to Dropbox: $DROPBOX_DIR"

# Create task summary for Dropbox
SUMMARY_FILE="$DROPBOX_DIR/TASK_SUMMARY_${DATETIME_STR}.md"

cat > "$SUMMARY_FILE" <<EOF
# OpenClaw 工作报告 - $DATE_STR

## 📋 备份信息
- **备份日期**: $DATE_STR
- **备份时间**: $(date '+%H:%M:%S')
- **任务类别**: $CATEGORY
- **备份类型**: ${BACKUP_TYPE/daily/每日自动备份}${BACKUP_TYPE/manual/手动触发备份}
- **来源**: OpenClaw Main Agent Workspace

## 📝 工作摘要
$(git -C "$WORKSPACE" log --oneline -3 2>/dev/null || echo "无提交记录")

## 📂 文件清单
- 工作区: \`~/.openclaw/agents/main/workspace\`
- 最新提交: $(git -C "$WORKSPACE" rev-parse --short HEAD 2>/dev/null || echo 'none')
- 提交信息: $(git -C "$WORKSPACE" log -1 --pretty=%s 2>/dev/null || echo 'none')

## 🔗 相关文件
- 完整备份: \`$ARCHIVE_NAME\`
- 元数据: \`backup_${DATETIME_STR}_metadata.json\`

## 📊 文件统计
\`\`\`
$(du -sh "$WORKSPACE" 2>/dev/null || echo "无法计算大小")
$(find "$WORKSPACE" -type f -name '*.md' | wc -l | xargs -I {} echo "Markdown 文档: {} 个")
$(find "$WORKSPACE" -type f -name '*.py' | wc -l | xargs -I {} echo "Python 文件: {} 个")
$(find "$WORKSPACE" -type f -name '*.json' | wc -l | xargs -I {} echo "JSON 配置: {} 个")
\`\`\`

---
*由 OpenClaw 自动生成*
EOF

# Copy archive to Dropbox
cp "$ARCHIVE_PATH" "$DROPBOX_DIR/"
cp "$META_FILE" "$DROPBOX_DIR/"

# Sync key workspace folders to Dropbox (unpacked for easy access)
log "Syncing unpacked workspace to Dropbox..."
rsync -av --delete \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='node_modules' \
    --exclude='.pytest_cache' \
    "$WORKSPACE/" "$DROPBOX_DIR/workspace/" >> "$BACKUP_ROOT/backup.log" 2>&1

# Cleanup old backups (keep 30 days)
log "Cleaning up backups older than 30 days..."
find "$BACKUP_ROOT" -type f -name "*.tar.gz" -mtime +30 -delete 2>/dev/null || true
find "$BACKUP_ROOT" -type f -name "*_metadata.json" -mtime +30 -delete 2>/dev/null || true

# Cleanup old Dropbox archives (keep 90 days)
find "$DROPBOX_ROOT" -type d -name "20*" -mtime +90 -exec rm -rf {} + 2>/dev/null || true

# Report
ARCHIVE_SIZE=$(du -h "$ARCHIVE_PATH" | cut -f1)
WORKSPACE_SIZE=$(du -sh "$WORKSPACE" | cut -f1)

log "=== Backup Completed ==="
log "Archive: $ARCHIVE_PATH ($ARCHIVE_SIZE)"
log "Dropbox: $DROPBOX_DIR"
log "Category: $CATEGORY"
log "Workspace: $WORKSPACE_SIZE"

echo ""
echo "✅ OpenClaw 备份完成"
echo "📦 备份文件: $ARCHIVE_PATH ($ARCHIVE_SIZE)"
echo "☁️  Dropbox: $DROPBOX_DIR"
echo "📁 任务类别: $CATEGORY"
echo "📝 工作报告: $SUMMARY_FILE"
