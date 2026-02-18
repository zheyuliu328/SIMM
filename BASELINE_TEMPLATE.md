# OpenClaw Commercial Open Source Tool Baseline
# 商业化开源工具统一基线模板 v1.0

## 目录结构标准

```
project/
├── src/
│   └── package_name/          # 源代码
├── tests/
│   ├── unit/                  # 单元测试
│   ├── integration/           # 集成测试
│   └── e2e/                   # 端到端测试
├── docs/
│   ├── README.md              # 主文档
│   ├── QUICKSTART.md          # 快速开始
│   ├── CONFIGURATION.md       # 配置说明
│   ├── FAQ.md                 # 常见问题
│   └── ARCHITECTURE.md        # 架构设计
├── scripts/
│   ├── setup.sh               # 安装脚本
│   ├── validate.sh            # 验证脚本
│   └── release.sh             # 发布脚本
├── artifacts/                 # 输出目录
├── logs/                      # 日志目录
├── config/
│   ├── config.yaml            # 主配置
│   └── schema.json            # 配置schema
├── .github/
│   ├── workflows/
│   │   ├── ci.yml             # CI/CD
│   │   ├── security.yml       # 安全扫描
│   │   └── release.yml        # 发布工作流
│   └── ISSUE_TEMPLATE/        # Issue模板
├── pyproject.toml            # 项目配置
├── Makefile                  # 命令入口
├── Dockerfile                # 容器化
├── docker-compose.yml        # 编排（可选）
├── LICENSE                   # 许可证
├── NOTICE                    # 版权声明
├── CONTRIBUTING.md           # 贡献指南
├── CODE_OF_CONDUCT.md        # 行为准则
├── SECURITY.md               # 安全政策
└── CHANGELOG.md              # 变更日志

```

## 文档标准（3/10/30分钟路径）

### README.md 结构

```markdown
# Project Name

> 一句话定位（≤30字）

[![CI](...)](...) [![License](...)](...) [![Version](...)](...)

## 🚀 3分钟上手

```bash
# 1. 克隆
git clone <repo>
cd <project>

# 2. 安装
make install

# 3. 运行
make demo
```

**预期输出**：`artifacts/demo_report.json`

## 📊 10分钟跑通

### 核心功能
1. **功能A**：一句话说明
2. **功能B**：一句话说明
3. **功能C**：一句话说明

### 完整运行
```bash
make run
```

## 🔧 30分钟接入真实数据

### 配置
```bash
cp config/config.example.yaml config/config.yaml
# 编辑配置
make config-check
```

### 数据映射
| 你的数据字段 | 系统字段 | 说明 |
|-------------|---------|------|
| field_a | input_x | 说明 |

### 真实数据运行
```bash
make run --config config/config.yaml
```

## 📚 文档导航

- [快速开始](docs/QUICKSTART.md) ← 新手先看
- [配置说明](docs/CONFIGURATION.md)
- [FAQ](docs/FAQ.md)
- [架构设计](docs/ARCHITECTURE.md)

## ⚠️ 免责声明

本工具仅供学习和研究使用，不构成任何投资建议...
```

## 配置标准

### config.yaml 结构

```yaml
# config.yaml - 主配置文件
# 复制 config.example.yaml 并修改

version: "1.0.0"  # 配置版本

# 数据配置
data:
  input_path: "./data/input"
  output_path: "./artifacts"
  format: "csv"  # csv, json, parquet
  
# 模型配置（如适用）
model:
  name: "default"
  version: "v1.0"
  params:
    param1: value1
    
# 日志配置
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  format: "json"  # json, text
  output: "./logs"
  
# 运行配置
run:
  dry_run: false
  confirm: false
  verbose: false
  debug: false
```

### 配置校验

```python
# config/validator.py
import jsonschema
import yaml
from pathlib import Path

CONFIG_SCHEMA = {
    "type": "object",
    "required": ["version", "data", "logging"],
    "properties": {
        "version": {"type": "string"},
        "data": {
            "type": "object",
            "required": ["input_path", "output_path"],
            "properties": {
                "input_path": {"type": "string"},
                "output_path": {"type": "string"},
                "format": {"enum": ["csv", "json", "parquet"]}
            }
        },
        "logging": {
            "type": "object",
            "required": ["level"],
            "properties": {
                "level": {"enum": ["DEBUG", "INFO", "WARNING", "ERROR"]},
                "format": {"enum": ["json", "text"]}
            }
        }
    }
}

def validate_config(config_path: str) -> bool:
    """验证配置文件"""
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    try:
        jsonschema.validate(config, CONFIG_SCHEMA)
        print("✅ 配置验证通过")
        return True
    except jsonschema.ValidationError as e:
        print(f"❌ 配置错误: {e.message}")
        return False
```

## 日志标准

### 结构化日志格式

```python
import json
import logging
from datetime import datetime
from typing import Dict, Any

class StructuredLogFormatter(logging.Formatter):
    """结构化日志格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "run_id": getattr(record, "run_id", "unknown"),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 添加额外字段
        if hasattr(record, "metrics"):
            log_data["metrics"] = record.metrics
        if hasattr(record, "context"):
            log_data["context"] = record.context
            
        return json.dumps(log_data, ensure_ascii=False)

# 使用示例
logger = logging.getLogger(__name__)
logger.info("处理完成", extra={
    "run_id": "run_20240208_001",
    "metrics": {"records_processed": 1000, "success_rate": 0.99}
})
```

### 关键指标日志

```python
def log_metrics(run_id: str, metrics: Dict[str, Any]):
    """记录关键指标"""
    logger.info(
        "运行指标",
        extra={
            "run_id": run_id,
            "metrics": {
                "duration_ms": metrics.get("duration_ms"),
                "records_in": metrics.get("records_in"),
                "records_out": metrics.get("records_out"),
                "success_count": metrics.get("success_count"),
                "error_count": metrics.get("error_count"),
                "success_rate": metrics.get("success_rate"),
            }
        }
    )
```

## CI/CD 标准

### .github/workflows/ci.yml

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.9'
      - run: pip install ruff black mypy
      - run: ruff check .
      - run: black --check .
      - run: mypy .

  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.9', '3.10', '3.11']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[dev]"
      - run: pytest --cov=src --cov-report=xml
      - uses: codecov/codecov-action@v3

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: gitleaks/gitleaks-action@v2
      - run: pip install bandit safety
      - run: bandit -r src/
      - run: safety check

  e2e:
    runs-on: ubuntu-latest
    needs: [lint, test]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.9'
      - run: pip install -e "."
      - run: make demo  # E2E测试

  build:
    runs-on: ubuntu-latest
    needs: [test, security]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.9'
      - run: pip install build
      - run: python -m build
      - uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/
```

### .github/workflows/release.yml

```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Generate Changelog
        uses: github-changelog-generator/github-changelog-generator@v1
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Build Package
        run: |
          pip install build
          python -m build
      
      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          files: dist/*
          body_path: CHANGELOG.md
          generate_release_notes: true
```

## 版本与回滚

### SemVer 规范

- **MAJOR**：破坏性变更（BREAKING CHANGE）
- **MINOR**：新功能，向后兼容
- **PATCH**：Bug修复，向后兼容

### 版本文件

```python
# src/package_name/__version__.py
__version__ = "1.2.3"
__version_info__ = (1, 2, 3)
```

### 回滚指南

```markdown
# 回滚指南

## 回滚到上一版本

```bash
# 查看版本历史
git log --oneline --tags

# 回滚到 v1.2.2
git checkout v1.2.2

# 或使用 pip
pip install package-name==1.2.2
```

## Docker 回滚

```bash
# 拉取上一版本
docker pull package-name:v1.2.2

# 运行
docker run package-name:v1.2.2
```
```

## 法务与开源治理

### LICENSE 模板（MIT）

```
MIT License

Copyright (c) 2024 [Author Name]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### DISCLAIMER 模板

```markdown
# 免责声明

本工具仅供学习、研究和演示使用，不构成任何投资建议、专业意见或担保。

1. **数据准确性**：工具使用的数据可能来自第三方，不保证实时性或准确性
2. **投资风险**：基于本工具输出做出的任何决策，风险由使用者自行承担
3. **合规责任**：使用者需自行确保使用场景符合当地法律法规
4. **无担保**：按"原样"提供，不提供任何明示或暗示的担保

使用本工具即表示您同意以上条款。
```

### SECURITY.md

```markdown
# 安全政策

## 支持的版本

| 版本 | 支持状态 |
|------|----------|
| 1.x | ✅ 支持 |
| 0.x | ❌ 不再支持 |

## 报告漏洞

如发现安全漏洞，请通过以下方式报告：

- 邮箱：security@example.com
- 标题格式：[SECURITY] 简要描述
- 请勿在公开 issue 中披露漏洞细节

我们会在 48 小时内回复，并在修复后公开致谢（如允许）。
```

## Makefile 标准命令

```makefile
.PHONY: help install install-dev test test-cov lint format clean \
        config-check demo run docker-build docker-run release

help: ## 显示帮助
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## 安装依赖
	pip install -r requirements.txt

install-dev: ## 安装开发依赖
	pip install -e ".[dev]"

test: ## 运行测试
	pytest

test-cov: ## 运行测试（带覆盖率）
	pytest --cov=src --cov-report=html

lint: ## 代码检查
	ruff check .
	black --check .
	mypy .

format: ## 格式化代码
	black .
	ruff check --fix .

config-check: ## 检查配置
	python -c "from config.validator import validate_config; validate_config('config/config.yaml')"

demo: ## 运行演示
	python -m src.cli demo

run: ## 运行（生产模式）
	python -m src.cli run

docker-build: ## 构建 Docker 镜像
	docker build -t $(PROJECT_NAME):latest .

docker-run: ## 运行 Docker 容器
	docker run -v $(PWD)/data:/app/data $(PROJECT_NAME):latest

clean: ## 清理构建产物
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +

release: ## 发布新版本（需要设置 VERSION）
	@echo "发布版本: $(VERSION)"
	git tag -a $(VERSION) -m "Release $(VERSION)"
	git push origin $(VERSION)
```

---

**模板版本**: v1.0  
**最后更新**: 2026-02-08  
**维护者**: OpenClaw Team
