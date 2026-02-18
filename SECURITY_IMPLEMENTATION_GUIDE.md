# 安全改造实施指南

## 概述

本文为 fct、nlp-factor、credit-one 三个项目提供完整的安全改造方案，包括：
- 最小威胁模型
- Guardrails 危险操作保护
- Secrets 统一管理
- 安全扫描（gitleaks + CI）
- 回滚与事故 SOP
- 数据边界校验

---

## 快速开始

### 1. 一键安装

```bash
cd /Users/zheyuliu/.openclaw/agents/main/workspace
./scripts/install_security.sh
```

### 2. 手动安装

#### 步骤 1: 安装依赖

```bash
# 安装 gitleaks
brew install gitleaks

# 安装 pre-commit
pip install pre-commit bandit safety
```

#### 步骤 2: 创建工具模块

```bash
# 为每个项目创建 utils 目录
mkdir -p fct/src/utils nlp-factor/src/utils credit-one/src/utils

# 复制工具模块
cp src/utils/*.py fct/src/utils/
cp src/utils/*.py nlp-factor/src/utils/
cp src/utils/*.py credit-one/src/utils/
```

#### 步骤 3: 配置 gitleaks

```bash
cp .gitleaks.toml fct/
cp .gitleaks.toml nlp-factor/
cp .gitleaks.toml credit-one/
```

#### 步骤 4: 配置 pre-commit

```bash
cd fct && pre-commit install
cd ../nlp-factor && pre-commit install
cd ../credit-one && pre-commit install
```

---

## 核心组件

### 1. Guardrails (`src/utils/guardrails.py`)

提供危险操作保护、审计日志和路径校验。

**使用示例**:

```python
from src.utils.guardrails import (
    DangerousOpGuard, AuditLogger, PathValidator,
    require_confirm, validate_path
)

# 危险操作保护
@require_confirm("database.delete")
def delete_database(db_path: str, confirm: bool = False):
    guard = DangerousOpGuard()
    if guard.check("database.delete", db_path, confirm_flag=confirm):
        os.remove(db_path)

# 审计日志
audit = AuditLogger()
audit.log("DB_QUERY", {"query": "SELECT * FROM loans"})

# 路径校验
validator = PathValidator(["./data", "./logs"])
safe_path = validator.validate("./data/loans.csv")
```

### 2. Secrets Manager (`src/utils/secrets.py`)

强制从环境变量读取 Secrets，禁止配置文件明文存储。

**使用示例**:

```python
from src.utils.secrets import get_secret, get_required_secret, check_secrets

# 获取 API Key
api_key = get_required_secret('ER_API_KEY')

# 获取可选配置
db_password = get_secret('DB_PASSWORD', default='')

# 验证所有必需 Secrets
check_secrets()
```

**环境变量设置**:

```bash
# nlp-factor
export ER_API_KEY=your_api_key

# credit-one
export KAGGLE_USERNAME=your_username
export KAGGLE_KEY=your_key
```

### 3. Data Boundary (`src/utils/data_boundary.py`)

提供输入数据校验，包括字段、类型、范围、缺失率。

**使用示例**:

```python
from src.utils.data_boundary import (
    DataBoundaryValidator, FieldSchema, FieldType,
    validate_loan_data, validate_news_data
)

# 使用预定义 schema 校验
df = pd.read_csv("loans.csv")
result = validate_loan_data(df)

if not result.is_valid:
    for error in result.errors:
        print(f"Error: {error}")
    raise ValueError("Data validation failed")

# 自定义 schema
validator = DataBoundaryValidator([
    FieldSchema(
        name="loan_amount",
        field_type=FieldType.FLOAT,
        required=True,
        min_value=0,
        max_value=100_000_000
    ),
])

result = validator.validate_dataframe(df)
```

---

## 项目特定改造

### FCT (financial-control-tower)

**修改文件**:
1. `src/data_engineering/db_connector.py` - 添加路径校验和审计日志
2. `main.py` - 添加 `--confirm` 和 `--dry-run` 参数
3. `pyproject.toml` - 添加 pre-commit 依赖

**验证命令**:
```bash
cd fct
python main.py --sample --dry-run
python main.py --sample --confirm
gitleaks detect --source . --verbose
```

### NLP-Factor

**修改文件**:
1. `src/data_pipe.py` - 使用 secrets.py 获取 API Key
2. `src/pipeline.py` - 添加数据校验
3. `.env.example` - 创建环境变量模板

**验证命令**:
```bash
cd nlp-factor
cp .env.example .env
# 编辑 .env 填入 ER_API_KEY
python src/data_pipe.py --symbols 0700.HK --recent_pages 1
gitleaks detect --source . --verbose
```

### Credit-One

**修改文件**:
1. `config/validator.py` - 添加配置校验（禁止 Secrets）
2. `pipeline.py` - 添加危险操作保护和数据校验
3. `main.py` - 添加 `--confirm` 参数

**验证命令**:
```bash
cd credit-one
cp .env.example .env
# 编辑 .env 填入 Kaggle 凭证
python main.py --dry-run
python main.py --confirm
gitleaks detect --source . --verbose
```

---

## CI/CD 集成

### GitHub Actions

`.github/workflows/security.yml`:

```yaml
name: Security Scan

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  gitleaks:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
      with:
        fetch-depth: 0
    - name: Run Gitleaks
      uses: gitleaks/gitleaks-action@v2
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Pre-commit Hooks

`.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks
  
  - repo: https://github.com/psf/black
    rev: 23.12.0
    hooks:
      - id: black
  
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.1.8
    hooks:
      - id: ruff
```

---

## 回滚与事故响应

### 数据库回滚

```bash
# 创建备份
./scripts/backup.sh

# 回滚到指定版本
./scripts/rollback_db.sh credit_risk.db 20240208_120000
```

### 事故响应流程

1. **发现**: 监控告警或用户反馈
2. **定级**: P0 (Critical) / P1 (High) / P2 (Medium) / P3 (Low)
3. **止损**: 停止服务、隔离问题
4. **修复**: 回滚或补丁
5. **复盘**: 文档更新、流程改进

详见 `docs/rollback.md`

---

## 验收清单

- [ ] gitleaks 无告警
- [ ] pre-commit hooks 安装成功
- [ ] 所有 Secrets 通过环境变量读取
- [ ] 危险操作需要 `--confirm`
- [ ] 审计日志正常记录
- [ ] 数据校验通过
- [ ] 回滚脚本可执行
- [ ] 事故 SOP 文档化

---

## 参考文档

- `docs/threat_model.md` - 威胁模型
- `docs/rollback.md` - 回滚与事故 SOP
- `fct/SECURITY_CHECKLIST.md` - FCT 改造清单
- `nlp-factor/SECURITY_CHECKLIST.md` - NLP-Factor 改造清单
- `credit-one/SECURITY_CHECKLIST.md` - Credit-One 改造清单
