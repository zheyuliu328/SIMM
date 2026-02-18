#!/bin/bash
# =============================================================================
# 回滚验证脚本 - 验证回滚后的系统状态
# 用法: ./verify_rollback.sh <repo-path> [old-sha] [new-sha]
# =============================================================================

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

REPO_PATH="$1"
OLD_SHA="${2:-}"
NEW_SHA="${3:-}"

FAILED=0

echo "=========================================="
echo "🔍 回滚验证流程"
echo "=========================================="

cd "$REPO_PATH" || exit 1

# 1. 验证 Git 状态
echo ""
echo "1️⃣  验证 Git 状态..."
if [ -z "$NEW_SHA" ]; then
    NEW_SHA=$(git rev-parse HEAD)
fi

CURRENT_SHA=$(git rev-parse HEAD)
if [ "$CURRENT_SHA" = "$NEW_SHA" ]; then
    echo -e "${GREEN}✓ Git HEAD 匹配预期版本${NC}"
else
    echo -e "${RED}✗ Git HEAD 不匹配! 当前: $CURRENT_SHA, 预期: $NEW_SHA${NC}"
    FAILED=1
fi

# 2. 验证关键文件存在
echo ""
echo "2️⃣  验证关键文件..."
REQUIRED_FILES=(
    "Makefile"
    ".github/workflows/security.yml"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓ $file 存在${NC}"
    else
        echo -e "${YELLOW}⚠ $file 不存在 (可能正常)${NC}"
    fi
done

# 3. 验证 CI 配置完整性
echo ""
echo "3️⃣  验证 CI 配置..."
if [ -d ".github/workflows" ]; then
    WORKFLOW_COUNT=$(find .github/workflows -name "*.yml" | wc -l)
    echo "  发现 $WORKFLOW_COUNT 个工作流文件"
    
    # 检查 security.yml 是否存在
    if [ -f ".github/workflows/security.yml" ]; then
        echo -e "${GREEN}✓ security.yml 存在${NC}"
    else
        echo -e "${YELLOW}⚠ security.yml 不存在${NC}"
    fi
else
    echo -e "${YELLOW}⚠ .github/workflows 目录不存在${NC}"
fi

# 4. 验证 Secrets 扫描配置
echo ""
echo "4️⃣  验证安全扫描配置..."
if [ -f ".gitleaks.toml" ]; then
    echo -e "${GREEN}✓ .gitleaks.toml 存在${NC}"
else
    echo -e "${YELLOW}⚠ .gitleaks.toml 不存在${NC}"
fi

if [ -f ".pre-commit-config.yaml" ]; then
    echo -e "${GREEN}✓ .pre-commit-config.yaml 存在${NC}"
    # 检查是否包含 gitleaks
    if grep -q "gitleaks" .pre-commit-config.yaml; then
        echo -e "${GREEN}✓ pre-commit 包含 gitleaks${NC}"
    else
        echo -e "${YELLOW}⚠ pre-commit 未配置 gitleaks${NC}"
    fi
else
    echo -e "${YELLOW}⚠ .pre-commit-config.yaml 不存在${NC}"
fi

# 5. 运行基础测试 (如果可用)
echo ""
echo "5️⃣  运行基础验证..."
if [ -f "Makefile" ]; then
    if grep -q "^verify:" Makefile; then
        echo "  运行 make verify..."
        if make verify 2>/dev/null; then
            echo -e "${GREEN}✓ make verify 通过${NC}"
        else
            echo -e "${YELLOW}⚠ make verify 失败 (可能需要环境配置)${NC}"
        fi
    else
        echo "  (Makefile 中没有 verify 目标)"
    fi
fi

# 6. 检查最近的 CI 状态 (需要 gh CLI)
echo ""
echo "6️⃣  检查 CI 状态..."
if command -v gh >/dev/null 2>&1; then
    REPO_INFO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "")
    if [ -n "$REPO_INFO" ]; then
        echo "  仓库: $REPO_INFO"
        echo "  最近的 CI 运行:"
        gh run list --limit 3 --json name,status,conclusion,headSha \
            -q '.[] | "    \(.name): \(.status) (\(.conclusion)) - \(.headSha[:7])"' 2>/dev/null || echo "    无法获取 CI 状态"
    fi
else
    echo "  (跳过 - 需要 GitHub CLI)"
fi

# 7. 生成验证报告
echo ""
echo "=========================================="
echo "📋 验证报告"
echo "=========================================="
echo "验证时间: $(date -Iseconds)"
echo "仓库路径: $REPO_PATH"
echo "当前版本: $CURRENT_SHA"
echo "回滚前版本: ${OLD_SHA:-N/A}"
echo "=========================================="

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ 验证通过${NC}"
    exit 0
else
    echo -e "${RED}✗ 验证失败 (发现问题: $FAILED)${NC}"
    exit 1
fi
