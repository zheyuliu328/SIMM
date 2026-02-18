#!/bin/bash
# =============================================================================
# 安全回滚脚本 - 带完整确认流程和 dry-run 支持
# 用法: ./safe_rollback.sh [options] <repo-path>
# =============================================================================

set -euo pipefail

# 默认配置
DRY_RUN=false
TARGET_REF=""
REPO_PATH=""
AUTO_CONFIRM=false

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 帮助信息
usage() {
    cat << EOF
安全回滚脚本

用法: $0 [选项] <仓库路径>

选项:
    -t, --target <ref>     目标版本 (默认: HEAD~1)
    -d, --dry-run          模拟运行，不执行实际操作
    -y, --yes              自动确认，不提示
    -h, --help             显示帮助

示例:
    $0 /path/to/repo                    # 回滚到上一个版本
    $0 -t v1.2.3 /path/to/repo          # 回滚到指定标签
    $0 -d /path/to/repo                 # 模拟回滚
    $0 -t HEAD~3 -y /path/to/repo       # 回滚3个版本，自动确认

EOF
    exit 0
}

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--target)
            TARGET_REF="$2"
            shift 2
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -y|--yes)
            AUTO_CONFIRM=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        -*)
            echo -e "${RED}错误: 未知选项 $1${NC}"
            usage
            ;;
        *)
            REPO_PATH="$1"
            shift
            ;;
    esac
done

# 验证参数
if [ -z "$REPO_PATH" ]; then
    echo -e "${RED}错误: 请指定仓库路径${NC}"
    usage
fi

if [ -z "$TARGET_REF" ]; then
    TARGET_REF="HEAD~1"
    echo -e "${YELLOW}未指定目标版本，默认使用: $TARGET_REF${NC}"
fi

# 检查目录
cd "$REPO_PATH" 2>/dev/null || {
    echo -e "${RED}错误: 无法进入目录 $REPO_PATH${NC}"
    exit 1
}

# 检查 git
if [ ! -d ".git" ]; then
    echo -e "${RED}错误: $REPO_PATH 不是 git 仓库${NC}"
    exit 1
fi

echo "=========================================="
echo -e "${BLUE}🛡️  安全回滚工具${NC}"
echo "=========================================="

# 获取版本信息
CURRENT_SHA=$(git rev-parse HEAD)
CURRENT_MSG=$(git log -1 --pretty=format:"%h %s (%ci)")

echo ""
echo "📍 当前版本:"
echo "   $CURRENT_MSG"

# 验证目标版本
if ! git rev-parse --verify "$TARGET_REF" >/dev/null 2>&1; then
    echo -e "${RED}错误: 目标版本 '$TARGET_REF' 不存在${NC}"
    echo "可用标签:"
    git tag -l | tail -10
    exit 1
fi

TARGET_SHA=$(git rev-parse "$TARGET_REF")
TARGET_MSG=$(git log -1 --pretty=format:"%h %s (%ci)" "$TARGET_REF")

echo ""
echo "🎯 目标版本:"
echo "   $TARGET_MSG"

# 检查是否是祖先关系
if git merge-base --is-ancestor "$TARGET_SHA" "$CURRENT_SHA"; then
    echo -e "${GREEN}✓ 目标版本是当前版本的祖先，可以安全回滚${NC}"
else
    echo -e "${YELLOW}⚠ 警告: 目标版本不是当前版本的祖先${NC}"
    echo "   这将是一次非线性回滚 (可能丢失提交)"
fi

# 显示变更
echo ""
echo "📊 将要移除的提交:"
echo "------------------------------------------"
git log --oneline --color=always "$TARGET_REF..HEAD" 2>/dev/null | while read line; do
    echo "   $line"
done
echo "------------------------------------------"
COMMIT_COUNT=$(git rev-list --count "$TARGET_REF..HEAD" 2>/dev/null || echo "0")
echo "   总计: $COMMIT_COUNT 个提交将被移除"

# 检查是否有未推送的提交
LOCAL_COMMITS=$(git rev-list --count origin/HEAD..HEAD 2>/dev/null || echo "0")
if [ "$LOCAL_COMMITS" -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}⚠ 警告: 有 $LOCAL_COMMITS 个提交尚未推送到远程${NC}"
fi

# Dry-run 模式
if [ "$DRY_RUN" = true ]; then
    echo ""
    echo -e "${BLUE}========== DRY RUN 模式 ==========${NC}"
    echo "将要执行的操作:"
    echo "  1. git tag rollback-$(date +%Y%m%d-%H%M%S) $CURRENT_SHA"
    echo "  2. git reset --hard $TARGET_SHA"
    echo "  3. git push --force-with-lease origin HEAD"
    echo ""
    echo -e "${GREEN}✓ Dry-run 完成，未执行任何更改${NC}"
    exit 0
fi

# 最终确认
if [ "$AUTO_CONFIRM" = false ]; then
    echo ""
    echo -e "${YELLOW}⚠️  即将执行破坏性操作!${NC}"
    echo "   这将永久删除上述 $COMMIT_COUNT 个提交"
    echo ""
    read -p "输入 'ROLLBACK' 确认执行: " CONFIRM
    if [ "$CONFIRM" != "ROLLBACK" ]; then
        echo -e "${YELLOW}已取消${NC}"
        exit 0
    fi
fi

# 执行回滚
echo ""
echo "🔄 执行回滚..."

ROLLBACK_TAG="rollback-$(date +%Y%m%d-%H%M%S)"

# 创建标记
echo "  → 创建回滚标记..."
git tag -a "$ROLLBACK_TAG" -m "Rollback from $CURRENT_SHA to $TARGET_SHA" || {
    echo -e "${YELLOW}警告: 创建标记失败，继续回滚...${NC}"
}

# 执行重置
echo "  → 执行 git reset..."
git reset --hard "$TARGET_SHA"

# 推送
echo "  → 推送到远程..."
if git push --force-with-lease origin HEAD; then
    echo -e "${GREEN}✓ 推送成功${NC}"
else
    echo -e "${RED}✗ 推送失败${NC}"
    exit 1
fi

# 结果
echo ""
echo "=========================================="
echo -e "${GREEN}✓ 回滚完成${NC}"
echo "=========================================="
echo "回滚标记: $ROLLBACK_TAG"
echo "旧版本: ${CURRENT_SHA:0:7}"
echo "新版本: ${TARGET_SHA:0:7}"
echo "=========================================="

# 自动验证
echo ""
read -p "是否立即运行验证? [Y/n] " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    $(dirname "$0")/verify_rollback.sh "$REPO_PATH" "$CURRENT_SHA" "$TARGET_SHA"
fi

exit 0
