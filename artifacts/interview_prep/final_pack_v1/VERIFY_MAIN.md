#!/bin/bash
# VERIFY_MAIN.md - 主控验收命令

echo "=== 面试冲刺材料验收 ==="
echo ""

echo "1. Alpha 交付验收:"
ls ~/.openclaw/agents/alpha/workspace/artifacts/interview_prep/alpha_project_story_v1/
echo ""

echo "2. Beta 交付验收:"
ls ~/.openclaw/agents/beta/workspace/artifacts/interview_prep/beta_jd_matrix_v1/
echo ""

echo "3. Gamma 交付验收:"
ls ~/.openclaw/agents/gamma/workspace/artifacts/interview_prep/gamma_script_v1/
echo ""

echo "4. Main 合并交付验收:"
ls ~/.openclaw/agents/main/workspace/artifacts/interview_prep/final_pack_v1/
echo ""

echo "5. 文件内容抽查:"
echo "Alpha project_facts_table.json 项目数:"
jq '.projects | length' ~/.openclaw/agents/alpha/workspace/artifacts/interview_prep/alpha_project_story_v1/project_facts_table.json 2>/dev/null || echo "N/A"
echo ""
echo "Beta qa_bank_zh.md 行数:"
wc -l ~/.openclaw/agents/beta/workspace/artifacts/interview_prep/beta_jd_matrix_v1/qa_bank_zh.md
echo ""
echo "Gamma block4_stories_zh.md 行数:"
wc -l ~/.openclaw/agents/gamma/workspace/artifacts/interview_prep/gamma_script_v1/block4_stories_zh.md

echo ""
echo "=== 验收完成 ==="
