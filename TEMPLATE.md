# OpenClaw Project Template
# 统一工程标准与验收规范

## 目录结构标准

```
project/
├── src/
│   └── package_name/          # 源代码
├── tests/                     # 测试
├── artifacts/ 或 reports/     # 输出目录（固定命名）
├── data/                      # 数据目录
├── docs/                      # 文档
├── .github/workflows/         # CI/CD
├── pyproject.toml            # 项目配置
├── Makefile                  # 命令入口
├── Dockerfile                # 容器化
├── .env.example              # 配置模板
├── README.md                 # 快速开始
└── run.py 或 cli.py          # 统一入口

```

## Makefile 标准命令

```makefile
.PHONY: help install lint test quickstart docker-build docker-run

help:                           # 显示帮助
install:                        # 安装依赖
lint:                           # 代码检查
test:                           # 运行测试
quickstart:                     # 一键运行（默认离线）
docker-build:                   # 构建镜像
docker-run:                     # 运行容器
```

## pyproject.toml 标准配置

```toml
[project]
name = "project-name"
version = "1.0.0"
requires-python = ">=3.9"
dependencies = []

[project.scripts]
project-cli = "package.cli:main"

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--cov=package --cov-report=term-missing"
```

## README Quickstart 模板

```markdown
# Project Name

> 一句话价值主张

## 🚀 Quickstart (1分钟)

```bash
# 本地运行
make quickstart

# 或 Docker
docker build -t project .
docker run project
```

## 📦 输出

运行后生成：
- `artifacts/report.json` - 分析报告
- `artifacts/chart.png` - 可视化图表

## ⚙️ 配置

```bash
cp .env.example .env
# 编辑 .env 填入 API Key（可选，默认离线模式）
```
```

## 验收检查清单

### P0 - 入口闭环
- [ ] `make quickstart` 单命令跑通
- [ ] 默认离线可跑，无需API Key
- [ ] 输出到 artifacts/ 或 reports/ 固定路径
- [ ] 清理后可复现

### P1 - 工程骨架
- [ ] pyproject.toml + src layout
- [ ] Makefile 标准命令
- [ ] pytest 集成测试覆盖 quickstart
- [ ] GitHub Actions CI (lint+test)
- [ ] 失败显式报错

### P2 - Docker
- [ ] Dockerfile 可构建
- [ ] `docker run` 执行 quickstart
- [ ] 服务类项目提供 /health

### 安全
- [ ] .env.example 配置模板
- [ ] 危险操作需 --confirm 或 --dry-run
- [ ] 默认禁止破坏性操作
