---
name: coding-agent-eval
description: Long-running coding agent evaluation suite based on Anthropic's eval methodology. Automated task execution with pass@k metrics and regression tracking.
metadata:
  {
    "openclaw": { "emoji": "🧪", "requires": { "anyBins": ["claude", "codex"] } },
  }
---

# Coding Agent Evaluation Suite

基于 Anthropic 评估方法论的 Coding Agent 自动化评估套件。

## 核心原则

- **评 outcome 而非路径**：只看结果，不看过程
- **多 grader 验证**：代码判定 + LLM rubric + 人工兜底
- **pass@k 指标**：k 次尝试成功率，衡量稳定性
- **回归保护**：防止升级后能力倒退

## 快速开始

```bash
# 运行完整评估
python tools/run_eval.py --suite all --trials 5

# 运行单个任务
python tools/run_eval.py --task feature_addition_1 --trials 3

# 运行回归套件
python tools/run_eval.py --suite regression

# 查看报告
cat reports/eval_report_$(date +%Y%m%d).json
```

## 评估套件结构

```
eval_suite/
├── tasks/              # 任务定义
│   ├── feature_addition_1.yaml
│   ├── integration_feature_2.yaml
│   └── regression_protection.yaml
├── graders/            # 评分器配置
│   ├── code_based.yml
│   ├── model_rubric.yml
│   └── human.yml
├── harness/            # 执行环境
│   ├── repo_setup.sh
│   └── verify.sh
└── reports/            # 评估报告
```

## 三类 Grader

### 1. Code-Based Grader（代码判定）
- 运行测试：`pytest test_*.py`
- 静态分析：`mypy`, `bandit`, `eslint`
- 文件检查：`logs/auth.log` 是否存在
- 结果：PASS/FAIL（硬判定）

### 2. Model-Based Grader（LLM Rubric）
- 评估代码是否符合 spec
- 检查边界情况和代码风格
- 输出：PASS/FAIL/UNKNOWN + confidence

### 3. Human Grader（人工兜底）
- 抽查不确定的案例
- 用于校准 rubric
- 模糊决策的最终仲裁

## 指标定义

| 指标 | 含义 | 阈值 |
|------|------|------|
| pass@1 | 1次尝试成功率 | ≥60% Feature, ≥50% Integration |
| pass^5 | 5次稳定过关率 | ≥25% Feature, ≥20% Integration |
| pass@1 regression | 回归任务成功率 | ≥80% |

## 报告示例

```json
{
  "timestamp": "2026-02-18T11:00:00Z",
  "summary": {
    "total_tasks": 3,
    "total_trials": 15,
    "overall_pass_at_1": 0.67,
    "overall_pass_at_5": 0.33
  },
  "tasks": [
    {
      "id": "feature_addition_1",
      "pass_at_1": 0.8,
      "pass_at_5": 0.4,
      "trials": [
        {"trial": 1, "result": "PASS", "duration": 120},
        {"trial": 2, "result": "FAIL", "duration": 45}
      ]
    }
  ]
}
```

## 添加新任务

1. 创建 `eval_suite/tasks/my_task.yaml`：

```yaml
id: "my_task"
desc: "Implement user auth with JWT"
env:
  repo_url: "https://github.com/template/backend-api.git"
  branch: "main"
  setup_cmd: "pip install -r requirements.txt"
task_input:
  spec: "Add JWT auth to /api/login endpoint"
success_criteria:
  run_tests: ["test_jwt_auth.py"]
  static_check: ["mypy", "bandit"]
  inspect_file: ["./logs/auth.log"]
trials: 5
```

2. 运行测试：

```bash
python tools/run_eval.py --task my_task --trials 5
```

## 配置

环境变量：

```bash
export EVAL_REPO_CACHE="~/.cache/coding-agent-eval"
export EVAL_REPORT_DIR="./reports"
export EVAL_MAX_PARALLEL=2
```

## 回归测试

定期运行：

```bash
# 添加到 cron
0 6 * * * cd ~/workspace && python tools/run_eval.py --suite regression --report
```

触发条件：
- 任何 regression 任务 pass^5 < 90% → 告警
- 任何能力指标下降 > 10% → 阻断发布

## 设计参考

- [Anthropic: Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
- [Build School: AI Agent Evaluation](https://learn.build-school.com/from-demo-to-production-ai-agent-evaluation/)