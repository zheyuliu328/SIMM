# 长期运维模式 - 执行报告

## A. 固化 CI 不确定性 ✅

### timeout-minutes 已添加
- lint: 5 minutes
- test: 15 minutes
- e2e: 15 minutes
- verify: 10 minutes

### 追踪与取证命令
```bash
# 追踪
gh run watch <run_id> --compact --exit-status

# 取证
gh run view <run_id> --log-failed
```

## B. 测试分层与外部依赖隔离 ✅

### pytest 配置已添加
- `pytest.ini` 三仓统一
- markers: integration, e2e
- 默认跳过 integration: `pytest -m "not integration"`

## C. 文档化作战协议 ✅

### 文档已创建
- `docs/CI-RUNBOOK.md` - 红灯分流、修复口径、gh 命令
- `docs/RELEASE-CHECKLIST.md` - tag/release/分支保护/验收顺序

## D. 补充证据报告 ✅

### 新 CI Run ID
| 仓库 | Security Run | CI Run |
|:-----|:-------------|:-------|
| credit-one | 21792136451 | (等待) |
| fct | 21792136723 | (等待) |
| nlp-factor | (等待) | 21792136898 |

### 文档路径
- `docs/CI-RUNBOOK.md`
- `docs/RELEASE-CHECKLIST.md`

### 提交记录
- credit-one: cc48eb3
- fct: 6d0cf2b
- nlp-factor: ef80920

## 状态
- 5 of 5 required status checks are expected
- 长期运维制度已固化
