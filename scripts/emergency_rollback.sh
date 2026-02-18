#!/bin/bash
# =============================================================================
# 紧急回滚脚本 - 用于 P0 级事故快速恢复
# 用法: ./emergency_rollback.sh <repo-path> <target-ref>
# 示例: ./emergency_rollback.sh /path/to/repo HEAD~1
# =============================================================================

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 参数检查
if [ $# -lt 2 ]; then
    echo -e "${RED}错误: 参数不足${NC}"
    echo "用法: $0 <repo-path> <target-ref>"
    echo "示例: $0 /path/to/repo HEAD~1"
    exit 1
fi

REPO_PATH="$1"
TARGET_REF="$2"
DRY_RUN="${3:-false}"
ROLLBACK_TAG="rollback-$(date +%Y%m%d-%H%M%S)"

echo "=========================================="
echo "🚨 紧急回滚脚本"
echo "=========================================="
echo "仓库路径: $REPO_PATH"
echo "目标版本: $TARGET_REF"
echo "Dry Run: $DRY_RUN"
echo "=========================================="

# 进入仓库目录
cd "$REPO_PATH" || { echo -e "${RED}错误: 无法进入目录 $REPO_PATH${NC}"; exit 1; }

# 检查 git 状态
if [ ! -d ".git" ]; then
    echo -e "${RED}错误: 不是 git 仓库${NC}"
    exit 1
fi

# 获取当前版本
CURRENT_SHA=$(git rev-parse HEAD)
CURRENT_MSG=$(git log -1 --pretty=format:"%h %s")
echo -e "${YELLOW}当前版本: $CURRENT_MSG${NC}"

# 验证目标版本存在
if ! git rev-parse --verify "$TARGET_REF" >/dev/null 2>&1; then
    echo -e "${RED}错误: 目标版本 $TARGET_REF 不存在${NC}"
    exit 1
fi

TARGET_SHA=$(git rev-parse "$TARGET_REF")
TARGET_MSG=$(git log -1 --pretty=format:"%h %s" "$TARGET_REF")
echo -e "${GREEN}目标版本: $TARGET_MSG${NC}"

# 显示变更摘要
echo ""
echo "📊 将要回滚的变更:"
echo "------------------------------------------"
git log --oneline "$TARGET_REF..HEAD" 2>/dev/null || echo "无法获取变更列表"
echo "------------------------------------------"

# Dry-run 模式
if [ "$DRY_RUN" = "true" ]; then
    echo -e "${YELLOW}[DRY RUN] 模式 - 不会执行实际回滚${NC}"
    echo "将要执行的操作:"
    echo "  1. git tag $ROLLBACK_TAG $CURRENT_SHA"
    echo "  2. git reset --hard $TARGET_SHA"
    echo "  3. git push --force-with-lease origin HEAD"
    echo ""
    echo -e "${GREEN}✓ Dry-run 完成，未执行任何更改${NC}"
    exit 0
fi

# 确认提示
echo ""
read -p "⚠️  确认执行回滚? [y/N] " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}已取消回滚${NC}"
    exit 0
fi

# 执行回滚
echo ""
echo "🔄 执行回滚..."

# 1. 标记当前版本 (用于追踪)
echo "  → 创建回滚标记: $ROLLBACK_TAG"
git tag -a "$ROLLBACK_TAG" -m "Rollback marker from $CURRENT_SHA to $TARGET_SHA" || true

# 2. 执行硬重置
echo "  → 重置到目标版本..."
git reset --hard "$TARGET_SHA"

# 3. 强制推送 (需要权限)
echo "  → 推送到远程..."
if git push --force-with-lease origin HEAD; then
    echo -e "${GREEN}✓ 回滚成功${NC}"
else
    echo -e "${RED}✗ 推送失败，请检查权限${NC}"
    exit 1
fi

echo ""
echo "=========================================="
echo -e "${GREEN}✓ 回滚完成${NC}"
echo "=========================================="
echo "回滚标记: $ROLLBACK_TAG"
echo "旧版本: $CURRENT_SHA"
echo "新版本: $TARGET_SHA"
echo "=========================================="

# 触发验证
echo ""
echo "🔍 触发验证流程..."
$(dirname "$0")/verify_rollback.sh "$REPO_PATH" "$CURRENT_SHA" "$TARGET_SHA" || true

exit 0
