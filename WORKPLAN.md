# WORKPLAN.md - 三仓工程化工单队列

**日期**: 2026-02-08  
**状态**: 四里程碑全部完成

---

## 里程碑1：基线对齐 - ✅ COMPLETED

### 验收标准
- [x] D1: 三仓 `make verify` 通过
- [x] D2: src layout + pyproject.toml + Makefile
- [x] D3: .env.example + .gitignore
- [x] D4: LICENSE + README + docs/

### 证据

| 仓库 | 命令 | 输出 |
|:-----|:-----|:-----|
| credit-one | `make verify` | 15/15 PASS |
| fct | `make verify` | 14/14 PASS |
| nlp-factor | `make verify` | 14/14 PASS |

---

## 里程碑2：真实数据接入路径 (run-real) - ✅ COMPLETED

### 工单完成

| 编号 | 仓库 | 任务 | 验收命令 | 状态 |
|:-----|:-----|:-----|:---------|:-----|
| M2-1 | credit-one | run-real 路径 | `make run-real CSV=data/sample_input.csv` | ✅ |
| M2-2 | fct | run-real 路径 | `make run-real CSV=data/sample_erp.csv` | ✅ |
| M2-3 | nlp-factor | run-real 路径 | `make run-real CSV=data/sample_news.csv` | ✅ |
| M2-4 | credit-one | docs/real-data.md | 文件存在 | ✅ |
| M2-5 | fct | docs/real-data.md | 文件存在 | ✅ |
| M2-6 | nlp-factor | docs/real-data.md | 文件存在 | ✅ |

### 输出工件示例

```bash
# Credit One
python scripts/run_real.py data/sample_input.csv
# [OK] Report saved: artifacts/scoring_report_20260208_011426.json

# FCT
python scripts/run_real.py data/sample_erp.csv
# [OK] Report saved: artifacts/reconciliation_report_20260208_011527.json

# NLP Factor
python scripts/run_real.py data/sample_news.csv
# [OK] Report saved: reports/factor_report_20260208_011621.json
```

---

## 里程碑3：安全与回滚闭环 - ✅ COMPLETED

### 工单完成

| 编号 | 任务 | 证据 | 状态 |
|:-----|:-----|:-----|:-----|
| M3-1 | gitleaks 配置 | `.gitleaks.toml` 存在 | ✅ |
| M3-2 | pre-commit hooks | `.pre-commit-config.yaml` 存在 | ✅ |
| M3-3 | CI security workflow | `.github/workflows/security.yml` 存在 | ✅ |
| M3-4 | SECURITY.md | 文件存在 | ✅ |
| M3-5 | docs/rollback.md | 文件存在 + 演练记录 | ✅ |
| M3-6 | 回滚演练 | git checkout ae81296 && make verify 通过 | ✅ |

### 回滚演练证据

```bash
cd credit-one
git checkout ae81296
make verify
# [OK] All checks passed!
git checkout master
```

---

## 里程碑4：开源治理与发布 - ✅ COMPLETED

### 工单完成

| 编号 | 任务 | 文件路径 | 状态 |
|:-----|:-----|:---------|:-----|
| M4-1 | LICENSE | `LICENSE` (MIT) | ✅ |
| M4-2 | SECURITY.md | `SECURITY.md` | ✅ |
| M4-3 | CONTRIBUTING.md | `CONTRIBUTING.md` | ✅ |
| M4-4 | CODE_OF_CONDUCT.md | `CODE_OF_CONDUCT.md` | ✅ |
| M4-5 | CHANGELOG.md | `CHANGELOG.md` | ✅ |
| M4-6 | 免责声明 | `docs/legal.md` | ✅ |
| M4-7 | Tag v2.0.0 | `git tag --list` 显示 v2.0.0 | ✅ |

---

## 事实源审计记录

### 已删除的不受支持宣称

| 文件 | 原内容 | 修改后 | 事实源 |
|:-----|:-------|:-------|:-------|
| credit-one/pyproject.toml | "Basel III / IFRS 9 / SR 11-7 compliance" | "model validation and monitoring capabilities" | 简历未提及合规认证 |
| credit-one/pyproject.toml | keywords: "basel-iii, ifrs9" | "model-validation, pd-prediction" | 同上 |
| 三仓 README | 多处"合规"表述 | "面向...研究/演示工具" | 简历未提及合规认证 |

### 保留的准确表述
- "面向 Basel III 框架设计" (非合规声明)
- "参考 SR 11-7 模型风险管理框架" (非合规声明)
- "支持 IFRS 9 ECL 计算逻辑演示" (非合规声明)

---

## Git 提交记录

| 仓库 | 最新提交 | 说明 |
|:-----|:---------|:-----|
| credit-one | `275d535` | Add SECURITY, CONTRIBUTING, CODE_OF_CONDUCT, CHANGELOG, legal disclaimer |
| fct | `0dfe3ef` | Add SECURITY, CONTRIBUTING, CODE_OF_CONDUCT, CHANGELOG, legal disclaimer |
| nlp-factor | `24dcd2a` | Add SECURITY, CONTRIBUTING, CODE_OF_CONDUCT, CHANGELOG, legal disclaimer |

---

## 下一步 P0 工单

无。所有四里程碑已完成。

可选优化（非阻塞）：
1. 完善单元测试覆盖率
2. 添加 Docker 镜像构建
3. 完善文档中的配置示例
