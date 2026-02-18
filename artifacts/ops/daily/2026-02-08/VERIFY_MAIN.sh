#!/bin/bash
# VERIFY_MAIN.sh - 一键验收脚本
# 运行: bash VERIFY_MAIN.sh

echo "=== 运维验收 - 2026-02-08 ==="
echo ""

# 1. 检查今日目录结构
echo "1. 今日目录结构:"
ls -la ~/.openclaw/agents/main/workspace/artifacts/ops/daily/2026-02-08/
echo ""

# 2. 验证 RUN_EVIDENCE.json
echo "2. RUN_EVIDENCE.json 内容:"
cat ~/.openclaw/agents/main/workspace/artifacts/ops/daily/2026-02-08/RUN_EVIDENCE.json | jq '.'
echo ""

# 3. 检查三仓 CI 状态
echo "3. 三仓 CI 状态复核:"
echo "credit-one:"
cd ~/Documents/GitHub/credit-one && gh run list --limit 1 --json name,status,conclusion
echo "fct:"
cd ~/Documents/GitHub/fct && gh run list --limit 1 --json name,status,conclusion
echo "nlp-factor:"
cd ~/Documents/GitHub/nlp-factor && gh run list --limit 1 --json name,status,conclusion
echo ""

# 4. 检查三代理报告
echo "4. 三代理巡检报告:"
echo "Alpha:"
ls ~/.openclaw/agents/alpha/workspace/artifacts/ops/daily/2026-02-08/ 2>/dev/null || echo "未找到"
echo "Beta:"
ls ~/.openclaw/agents/beta/workspace/artifacts/ops/daily/2026-02-08/ 2>/dev/null || echo "未找到"
echo "Gamma:"
ls ~/.openclaw/agents/gamma/workspace/artifacts/ops/daily/2026-02-08/ 2>/dev/null || echo "未找到"
echo ""

echo "=== 验收完成 ==="
