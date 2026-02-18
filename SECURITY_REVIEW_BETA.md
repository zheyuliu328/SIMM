# 🔒 安全审查报告 (Beta)
## 三项目威胁模型、Guardrail、审计与回滚方案

**审查日期**: 2026-02-08  
**审查者**: Beta (安全/合规/可审计/回滚)  
**项目范围**: Credit One / FCT / NLP Factor

---

## 📋 执行摘要

| 项目 | 风险等级 | P0 安全项缺失数 | 关键问题 |
|------|----------|-----------------|----------|
| Credit One | 🟡 **中** | 4 | Secrets 管理、输入验证、审计日志 |
| FCT | 🟡 **中** | 3 | API Key 硬编码风险、审计完整性校验 |
| NLP Factor | 🟠 **中高** | 5 | API Key 暴露、无输入净化、依赖漏洞 |

---

## 1️⃣ Credit One (算法信用风险引擎)

### 1.1 威胁模型 (最小版)

| 威胁类别 | 风险描述 | 严重程度 | 证据位置 |
|----------|----------|----------|----------|
| **Secrets 泄露** | `.env.example` 存在但无 `.env` 在 `.gitignore` 中明确排除；`LENDING_CLUB_API_KEY` 可能意外提交 | 🔴 高 | `.env.example:7` |
| **危险操作** | `pipeline.py:33` 直接 `os.remove(DB_NAME)` 无确认机制；数据库可被任意删除 | 🔴 高 | `pipeline.py:33` |
| **数据泄露** | `app.py` Streamlit 缓存敏感数据 (`@st.cache_data`)，无访问控制；`fetch_real_market_data_safe` 可能暴露财务数据 | 🟡 中 | `app.py:88` |
| **误删风险** | `pipeline.py` 每次运行删除并重建数据库，无备份检查；`BACKUP_RETENTION=3` 仅配置未实现 | 🔴 高 | `pipeline.py:33`, `.env.example:28` |
| **注入攻击** | SQL 拼接在 `transform_logic.sql` 执行，虽为本地文件但无签名验证 | 🟢 低 | `pipeline.py:78` |

### 1.2 必须增加的 Guardrail (P0)

```python
# P0-1: 数据库删除保护 (pipeline.py)
def safe_database_init(db_name: str, force: bool = False):
    """带确认机制的数据库初始化"""
    if os.path.exists(db_name) and not force:
        backup_path = f"{db_name}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(db_name, backup_path)
        logger.info(f"Auto-backup created: {backup_path}")
    
    if os.path.exists(db_name) and force:
        raise ValueError("Use --force to delete existing database with backups")
```

```python
# P0-2: Secrets 扫描预提交钩子 (.pre-commit-config.yaml)
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    hooks:
      - id: detect-private-key
```

```python
# P0-3: 输入验证装饰器 (sme_credit_explainability.py)
from functools import wraps
import re

def validate_company_id(fn):
    @wraps(fn)
    def wrapper(company_id: str, *args, **kwargs):
        if not re.match(r'^HK_\d{5}$', company_id):
            raise ValueError(f"Invalid company_id format: {company_id}")
        return fn(company_id, *args, **kwargs)
    return wrapper
```

```python
# P0-4: 模型推理访问控制 (app.py)
def require_auth(role: str = "analyst"):
    """Streamlit 简易 RBAC"""
    if "user_role" not in st.session_state:
        st.session_state.user_role = st.sidebar.selectbox("Role", ["readonly", "analyst", "admin"])
    if st.session_state.user_role not in [role, "admin"]:
        st.error("Insufficient permissions")
        st.stop()
```

### 1.3 审计日志字段

```sql
-- audit_logs 表结构 (需新增)
CREATE TABLE audit_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    -- Who
    user_id TEXT NOT NULL,
    session_id TEXT,
    ip_address TEXT,
    -- What
    action_type TEXT NOT NULL,  -- MODEL_PREDICT, DATA_DELETE, CONFIG_CHANGE
    resource_type TEXT,         -- model, database, report
    resource_id TEXT,
    action_detail JSON,         -- 详细参数
    -- Context
    model_version TEXT,
    input_hash TEXT,            -- 输入数据哈希
    output_hash TEXT,           -- 输出数据哈希
    -- Risk
    risk_score REAL,
    anomaly_flags TEXT,
    -- Integrity
    log_hash TEXT,              -- 完整性校验
    prev_log_hash TEXT          -- 链式哈希
);

-- 创建索引
CREATE INDEX idx_audit_time ON audit_logs(timestamp);
CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_action ON audit_logs(action_type);
```

### 1.4 回滚与事故处理 SOP

```markdown
## Credit One 事故处理 SOP

### Level 1: 模型漂移检测 (PSI > 0.25)
1. 自动告警 → Slack #risk-alerts
2. 冻结模型推理 (维护模式)
3. 回滚到上一版本: `git checkout <prev_tag> -- models/`
4. 验证回滚: `python model_validation.py`
5. 通知业务方，记录事故时间线

### Level 2: 数据污染/误删
1. 立即停止所有写入操作
2. 从备份恢复: `cp ./backups/credit_risk.db.YYYYMMDD_HHMMSS ./credit_risk.db`
3. 数据完整性校验: `python validate_db_checksum.py`
4. 重跑 ETL: `python pipeline.py --validate-only`
5. 事故报告 24h 内提交

### Level 3: Secrets 泄露
1. 立即轮换 API Key: Lending Club Dashboard → Revoke → Generate New
2. 扫描提交历史: `gitleaks detect --source . -v`
3. 如已推送: `git filter-repo --path .env --invert-paths` (需 force push)
4. 通知安全团队，评估泄露范围
5. 更新所有部署环境的 Secrets

### 回滚检查清单
- [ ] 数据库备份存在且可读取
- [ ] 模型版本 tag 可 checkout
- [ ] 依赖版本锁定 (requirements.lock.txt)
- [ ] 配置文件未变更
- [ ] 验证脚本通过
```

### 1.5 安全扫描策略

```yaml
# .github/workflows/security-scan.yml
name: Security Scan
on: [push, pull_request]
jobs:
  gitleaks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  
  pip-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pypa/gh-action-pip-audit@v1
        with:
          inputs: requirements.txt
          ignore-vulns: |
            GHSA-xxx  # 已评估接受的低危漏洞
  
  bandit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install bandit
      - run: bandit -r . -f json -o bandit-report.json || true
```

---

## 2️⃣ FCT (财务控制塔)

### 2.1 威胁模型 (最小版)

| 威胁类别 | 风险描述 | 严重程度 | 证据位置 |
|----------|----------|----------|----------|
| **Secrets 泄露** | `erp_config.yaml` 可能包含 SAP/Oracle 密码，无加密存储说明 | 🔴 高 | `README.md:178` |
| **危险操作** | `financial_control_tower.py:39` 直接删除/修改审计日志无触发器保护 | 🟡 中 | `financial_control_tower.py` |
| **数据泄露** | 数据库文件 `.db` 未在 `.gitignore` 中排除，可能意外提交 | 🔴 高 | `.gitignore` |
| **误删风险** | 无数据库备份自动化，依赖手动 `setup_project.py` | 🟡 中 | 项目结构 |
| **权限绕过** | RBAC 仅文档定义，无实际代码实现 | 🟡 中 | `security_architecture.md` |

### 2.2 必须增加的 Guardrail (P0)

```python
# P0-1: 审计日志不可变触发器 (init_erp_databases.py)
IMMUTABLE_TABLES = ['audit_logs', 'fraud_metrics']

def create_immutable_trigger(conn, table_name: str):
    """创建防止更新/删除的触发器"""
    conn.execute(f"""
        CREATE TRIGGER IF NOT EXISTS prevent_{table_name}_update
        BEFORE UPDATE ON {table_name}
        BEGIN
            SELECT RAISE(ABORT, '审计表不可修改: {table_name}');
        END;
    """)
    conn.execute(f"""
        CREATE TRIGGER IF NOT EXISTS prevent_{table_name}_delete
        BEFORE DELETE ON {table_name}
        BEGIN
            SELECT RAISE(ABORT, '审计表不可删除: {table_name}');
        END;
    """)
```

```python
# P0-2: ERP 配置加密存储 (src/integration/erp_connector.py)
from cryptography.fernet import Fernet
import os

class SecureERPConfig:
    def __init__(self):
        self.key = os.environ.get('FCT_CONFIG_KEY')
        if not self.key:
            raise ValueError("FCT_CONFIG_KEY not set")
        self.cipher = Fernet(self.key)
    
    def load_config(self, path: str) -> dict:
        with open(path, 'rb') as f:
            encrypted = f.read()
        decrypted = self.cipher.decrypt(encrypted)
        return yaml.safe_load(decrypted)
```

```python
# P0-3: 数据库文件排除 (.gitignore 追加)
# Database files - NEVER commit
*.db
*.db-journal
*.db-wal
*.db-shm
data/*.db
!data/.gitkeep
```

### 2.3 审计日志字段

```sql
-- FCT 审计日志增强 (audit.db)
CREATE TABLE audit_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    -- Who
    user_id TEXT NOT NULL,
    role TEXT NOT NULL,           -- SYS_ADMIN, AUDITOR, etc.
    db_session_id TEXT,
    -- What
    action_category TEXT,         -- RECONCILE, FRAUD_CHECK, REPORT_GEN
    action_detail JSON,
    source_db TEXT,               -- operations/finance/audit
    target_db TEXT,
    records_affected INTEGER,
    -- Data Integrity
    source_checksum TEXT,         -- 源数据哈希
    result_checksum TEXT,         -- 结果哈希
    -- Compliance
    sox_control_id TEXT,          -- SOX 控制点编号
    gdpr_category TEXT,           -- 数据分类
    retention_until DATE,         -- 保留期限
    -- Chain of Custody
    log_hash TEXT,
    prev_log_hash TEXT,
    signature TEXT                -- 数字签名 (可选)
);

-- 欺诈检测专用审计
CREATE TABLE fraud_audit (
    audit_id INTEGER PRIMARY KEY,
    rule_id TEXT NOT NULL,
    triggered_at DATETIME,
    false_positive BOOLEAN,
    reviewer_id TEXT,
    reviewed_at DATETIME
);
```

### 2.4 回滚与事故处理 SOP

```markdown
## FCT 事故处理 SOP

### Level 1: 对账差异检测
1. 差异率 > 1% 触发告警
2. 冻结自动同步: `python sync_scheduler.py --pause`
3. 人工核查: 对比 `ops_vs_finance_reconciliation` 报告
4. 如为数据源问题 → 联系 ERP 管理员
5. 如为规则问题 → 回滚 `fraud_rule_metrics.py` 到上一版本

### Level 2: 审计日志损坏/篡改
1. 立即切换只读模式: `echo "readonly" > /tmp/fct_mode`
2. 从只读副本恢复: `rsync -av replica:audit.db ./`
3. 哈希链验证: `python verify_audit_chain.py`
4. 如链断裂 → 启动取证模式，保留现场
5. 通知合规官和 CISO

### Level 3: ERP 凭证泄露
1. 立即在 SAP/Oracle 端禁用对应 Service Account
2. 轮换所有 API Key 和密码
3. 检查审计日志中异常访问: `SELECT * FROM audit_logs WHERE timestamp > now() - interval '1 hour'`
4. 评估数据泄露范围 (哪些表被访问)
5. 按 GDPR/SOX 要求通知监管

### 灾难恢复清单
- [ ] 三个数据库的每日备份 (0:00 UTC)
- [ ] 备份加密存储 (AES-256)
- [ ] 异地备份 (S3 Glacier)
- [ ] RTO < 4h, RPO < 1h
```

### 2.5 安全扫描策略

```yaml
# FCT 安全扫描配置
scans:
  gitleaks:
    patterns:
      - SAP.*password
      - Oracle.*pwd
      - api[_-]?key
      - secret[_-]?key
  
  dependency-check:
    files:
      - requirements.txt
    fail-on-cvss: 7  # HIGH and CRITICAL
  
  custom-sql-check:
    rules:
      - id: SQL001
        pattern: "DELETE FROM.*audit"
        severity: CRITICAL
        message: "禁止直接删除审计表"
      - id: SQL002
        pattern: "DROP TABLE.*audit"
        severity: CRITICAL
        message: "禁止删除审计表"
```

---

## 3️⃣ NLP Factor (港股情绪因子)

### 3.1 威胁模型 (最小版)

| 威胁类别 | 风险描述 | 严重程度 | 证据位置 |
|----------|----------|----------|----------|
| **Secrets 泄露** | `.env.example:9` 明文 `ER_API_KEY=your_api_key_here`，用户可能直接复制为 `.env` 并提交 | 🔴 高 | `.env.example:9` |
| **危险操作** | `data_pipe.py` 无输入验证直接写入文件系统，路径遍历风险 | 🟡 中 | `data_pipe.py:187` |
| **数据泄露** | 新闻数据可能包含非公开信息 (MNPI)，无数据分类 | 🟡 中 | 业务逻辑 |
| **误删风险** | `checkpoint.json` 可被任意覆盖，无版本控制 | 🟢 低 | `news_out/checkpoint.json` |
| **依赖漏洞** | `transformers`, `torch` 为大依赖面，需 CVE 监控 | 🟡 中 | `requirements.txt` |
| **API 滥用** | EventRegistry API 无调用限流，可能导致费用激增 | 🟡 中 | `data_pipe.py` |

### 3.2 必须增加的 Guardrail (P0)

```python
# P0-1: API Key 强制环境变量 (data_pipe.py)
import sys

def get_api_key() -> str:
    """强制从环境变量读取 API Key"""
    key = os.environ.get('ER_API_KEY')
    if not key or key == 'your_api_key_here':
        print("ERROR: ER_API_KEY must be set and not be placeholder", file=sys.stderr)
        sys.exit(1)
    return key
```

```python
# P0-2: 输入路径净化 (data_pipe.py)
import re
from pathlib import Path

def sanitize_path(user_input: str, base_dir: str = "./news_out") -> Path:
    """防止路径遍历攻击"""
    # 移除危险字符
    clean = re.sub(r'[^\w\-_./]', '', user_input)
    full_path = Path(base_dir) / clean
    
    # 确保在 base_dir 内
    try:
        full_path.relative_to(Path(base_dir).resolve())
    except ValueError:
        raise ValueError(f"Path traversal detected: {user_input}")
    
    return full_path
```

```python
# P0-3: API 调用限流 (data_pipe.py)
import time
from functools import wraps

def rate_limit(max_calls: int = 100, period: int = 3600):
    """每小时限流装饰器"""
    calls = []
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            now = time.time()
            calls[:] = [c for c in calls if now - c < period]
            if len(calls) >= max_calls:
                raise RuntimeError(f"Rate limit exceeded: {max_calls}/{period}s")
            calls.append(now)
            return fn(*args, **kwargs)
        return wrapper
    return decorator
```

```python
# P0-4: 数据分类标签 (clean_data.py)
DATA_CLASSIFICATION = {
    'public': ['published_date', 'source_name'],
    'internal': ['title', 'summary', 'sentiment_score'],
    'restricted': ['body_text', 'url']  # 可能含 MNPI
}

def tag_data_classification(df: pd.DataFrame) -> pd.DataFrame:
    """为数据添加分类标签"""
    df['data_classification'] = df.apply(
        lambda row: 'restricted' if 'earnings' in str(row.get('title', '')).lower() else 'internal',
        axis=1
    )
    return df
```

```python
# P0-5: Checkpoint 版本控制 (data_pipe.py)
import json
from datetime import datetime

def save_versioned_checkpoint(out_dir: str, state: dict):
    """保存带时间戳的 checkpoint"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    checkpoint_file = Path(out_dir) / f"checkpoint_{timestamp}.json"
    
    with open(checkpoint_file, 'w') as f:
        json.dump(state, f, indent=2)
    
    # 维护最近 10 个版本
    checkpoints = sorted(Path(out_dir).glob('checkpoint_*.json'))
    for old in checkpoints[:-10]:
        old.unlink()
    
    return checkpoint_file
```

### 3.3 审计日志字段

```python
# NLP Factor 审计日志 (JSON Lines 格式)
{
    "timestamp": "2026-02-08T00:42:00Z",
    "who": {
        "user_id": "quant_researcher_001",
        "api_key_hash": "sha256:abc123...",  # API Key 哈希，非明文
        "client_ip": "10.0.0.5"
    },
    "what": {
        "action": "news_ingestion",
        "symbols": ["0700.HK", "9988.HK"],
        "date_range": ["2024-01-01", "2024-12-31"],
        "articles_fetched": 15234,
        "tokens_consumed": 2450,
        "output_files": ["news_out/articles_2024.jsonl"]
    },
    "data_quality": {
        "duplicates_filtered": 123,
        "cleaning_rules_applied": ["html_strip", "dedup"],
        "validation_errors": 0
    },
    "compliance": {
        "data_retention_days": 2555,  # 7 years
        "gdpr_category": "legitimate_interest",
        "mnpi_flag": false
    },
    "performance": {
        "duration_ms": 45230,
        "api_latency_p99": 850
    }
}
```

### 3.4 回滚与事故处理 SOP

```markdown
## NLP Factor 事故处理 SOP

### Level 1: API 配额耗尽/费用异常
1. 监控告警: tokens_consumed > 10,000/小时
2. 暂停采集: `touch news_out/PAUSE`
3. 检查异常调用模式: `grep "symbols.*count" audit.log`
4. 如为代码 bug → 修复后恢复
5. 如为攻击 → 轮换 API Key，限制 IP

### Level 2: 数据污染 (重复/脏数据)
1. 识别污染批次: `python identify_bad_batch.py --date 2024-01-15`
2. 标记受影响因子: `UPDATE factors SET status='contaminated' WHERE date='2024-01-15'`
3. 回滚到上一干净 checkpoint: `cp checkpoint_20240114.json checkpoint.json`
4. 重跑 pipeline: `bash run.sh --from-date 2024-01-14`
5. 验证 IC 一致性: `python validate_factor.py`

### Level 3: MNPI 泄露风险
1. 立即停止所有新闻采集
2. 隔离相关数据: `mv news_out/2024-01-15 news_out/quarantine/2024-01-15`
3. 评估泄露范围: 哪些文章含未公开信息
4. 通知合规团队和法律顾问
5. 按监管要求披露 (如需要)

### 因子失效回滚
- [ ] 保留历史因子版本 (daily_sentiment_factors_v{YYYYMMDD}.csv)
- [ ] 模型版本锁定 (sentiment_model_v{version}.pkl)
- [ ] 回滚命令: `python backtest.py --factor-version 20240101`
```

### 3.5 安全扫描策略

```yaml
# NLP Factor 安全扫描
scans:
  gitleaks:
    enabled: true
    patterns:
      - ER_API_KEY
      - eventregistry.*key
    allowlist:
      paths:
        - ".env.example"  # 允许示例文件中的占位符
      regexes:
        - "your_api_key_here"
  
  pip-audit:
    enabled: true
    ignore:
      - GHSA-xxx  # torch 相关，已评估
    
  bandit:
    enabled: true
    skips: [B101]  # 跳过 assert 检查
  
  safety:
    enabled: true
    fail_on: high
```

---

## 📊 汇总对比表

| 维度 | Credit One | FCT | NLP Factor |
|------|------------|-----|------------|
| **主要风险** | 数据库误删、Secrets | 审计完整性、ERP 凭证 | API Key、MNPI |
| **P0 项数** | 4 | 3 | 5 |
| **审计粒度** | 模型级 | 交易级 | 批次级 |
| **回滚复杂度** | 中 (DB + Model) | 高 (多 DB 一致性) | 低 (文件系统) |
| **合规要求** | Basel III / IFRS 9 | SOX / GDPR | GDPR / 证券法 |

---

## 🎯 优先行动清单

### 立即执行 (本周)
1. [ ] 三项目均添加 `.env` 到 `.gitignore` 并安装 gitleaks
2. [ ] Credit One: 实现数据库删除保护机制
3. [ ] NLP: 强制 ER_API_KEY 从环境变量读取
4. [ ] FCT: 添加审计表不可变触发器

### 短期 (本月)
1. [ ] 建立统一的审计日志 schema
2. [ ] 实现自动备份和恢复测试
3. [ ] 部署依赖 CVE 监控 (Dependabot/Snyk)
4. [ ] 编写并演练事故处理 SOP

### 中期 (本季度)
1. [ ] 统一 Secrets 管理 (AWS Secrets Manager / Vault)
2. [ ] 实现审计日志链式哈希
3. [ ] 通过渗透测试验证 RBAC
4. [ ] 建立 SOC2 合规基线

---

**报告完成** ✅
*Beta - 安全审查专员*
