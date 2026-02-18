# OpenViking Skill - AI Agent 上下文数据库

**代号**: Viking Memory  
**功能**: OpenClaw + OpenViking 集成，三层记忆管理  
**状态**: ✅ 已激活

---

## 🎯 概述

OpenViking 是字节火山引擎开源的 **AI Agent 上下文数据库**，采用 **L0/L1/L2 三层渐进式加载** + **URI 文件系统** 架构。

**核心价值**:
- ✅ 解决传统 RAG 碎片化问题
- ✅ 三层按需加载，大幅节省 Token
- ✅ URI 定位，精准检索
- ✅ 自动记忆提取，Agent 越用越聪明

---

## 🏗️ 三层架构详解

```
┌─────────────────────────────────────────┐
│           L0 - 摘要层 (Abstract)         │
│         一句话概括, ~20 tokens           │
│            快速检索和识别                 │
└─────────────────────────────────────────┘
                    ↓ (按需加载)
┌─────────────────────────────────────────┐
│           L1 - 概览层 (Overview)         │
│     核心信息 + 使用场景, ~200 tokens      │
│         Agent 规划阶段决策                │
└─────────────────────────────────────────┘
                    ↓ (按需加载)
┌─────────────────────────────────────────┐
│           L2 - 完整层 (Full)             │
│            完整原文, 无限制               │
│            深入分析时使用                 │
└─────────────────────────────────────────┘
```

**对比传统 RAG**:

| 特性 | 传统 RAG | OpenViking |
|:-----|:---------|:-----------|
| 存储 | 平铺向量 | 分层文件系统 |
| 加载 | 全部加载 | 渐进按需 |
| Token | 浪费严重 | 精准控制 |
| 检索 | 黑箱语义 | URI + 语义混合 |

---

## 📁 URI 文件系统结构

```
viking://
├── users/
│   └── {user_id}/                    # 用户目录
│       ├── profile/                  # 用户画像
│       ├── preferences/              # 用户偏好
│       │   └── communication_style   # 沟通风格
│       ├── history/                  # 交互历史
│       └── memory/                   # 长期记忆
│           ├── preference/           # 偏好记忆
│           ├── event/                # 事件记忆
│           └── skill/                # 技能记忆
├── agents/
│   └── {agent_id}/                   # Agent 目录
│       ├── skills/                   # 技能记忆
│       ├── experiences/              # 任务经验
│       └── tools/                    # 工具使用记录
└── sessions/
    └── openclaw/
        └── {session_id}/             # 会话上下文
            ├── resources/            # 资源文件
            ├── context/              # 上下文
            └── memory/               # 提取的记忆
```

---

## 🛠️ 工具命令

### 记忆管理工具

**位置**: `tools/viking_memory.py`

```bash
# 查看统计
python tools/viking_memory.py stats

# 存储会话
python tools/viking_memory.py store-session --session-id 2026-02-15 --content '{"topic": "AI讨论"}'

# 检索会话
python tools/viking_memory.py retrieve-session --session-id 2026-02-15 --query "AI"

# 存储记忆
python tools/viking_memory.py store-memory --memory-type preference --content "用户喜欢简洁回答"

# 检索记忆
python tools/viking_memory.py retrieve-memory --query "用户偏好"

# 提取记忆（从会话）
python tools/viking_memory.py extract-memory --session-id 2026-02-15

# 同步到 MEMORY.md
python tools/viking_memory.py sync-to-md

# 列出所有会话
python tools/viking_memory.py list-sessions

# 列出用户记忆
python tools/viking_memory.py list-memory
```

---

## 🔧 配置说明

### 配置文件位置

- **OpenViking 配置**: `~/.openviking/config.yaml`
- **数据存储**: `~/.openviking/data/`
- **日志**: `~/.openviking/logs/`

### 模型配置

```yaml
# 当前配置 (OpenAI)
models:
  vlm:
    provider: openai
    model: gpt-4o-mini
    api_key: ${OPENAI_API_KEY}
  
  embedding:
    provider: openai
    model: text-embedding-3-small

# 推荐配置 (火山方舟 - 有免费额度)
models:
  vlm:
    provider: ark
    model: doubao-vision-pro
    api_key: ${ARK_API_KEY}
    base_url: https://ark.cn-beijing.volces.com/api/v3
  
  embedding:
    provider: ark
    model: doubao-embedding
```

### 环境变量

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# 或火山方舟
export ARK_API_KEY="..."
```

---

## 🔄 使用流程

### 典型会话流程

```
会话开始
    ↓
1. 加载用户记忆
   python tools/viking_memory.py retrieve-memory --query "用户偏好"
    ↓
2. 实时存储上下文
   python tools/viking_memory.py store-session --session-id 2026-02-15
    ↓
会话进行中... (自动保存)
    ↓
3. 会话结束，提取记忆
   python tools/viking_memory.py extract-memory --session-id 2026-02-15
    ↓
4. 同步关键记忆到 MEMORY.md
   python tools/viking_memory.py sync-to-md
    ↓
记忆闭环完成
```

### 与 OpenClaw MEMORY.md 的协作

| 系统 | 职责 | 同步方式 |
|:-----|:-----|:---------|
| **OpenViking** | 大规模上下文、自动记忆提取、三层检索 | 提取的洞察 → MEMORY.md |
| **MEMORY.md** | 关键决策、用户偏好、重要事件 | 手动维护，参考 Viking |

---

## 💡 使用示例

### 示例 1: 存储当前会话

```bash
# 存储今天会话
python tools/viking_memory.py store-session \
  --session-id $(date +%Y-%m-%d) \
  --content '{"topic": "OpenViking配置", "tasks": ["安装", "配置", "测试"]}'
```

### 示例 2: 检索用户偏好

```bash
# 查找用户喜欢的沟通风格
python tools/viking_memory.py retrieve-memory \
  --query "用户喜欢的回答风格" \
  --memory-type preference
```

### 示例 3: 自动记忆提取

```bash
# 从昨天会话提取记忆
python tools/viking_memory.py extract-memory \
  --session-id $(date -v-1d +%Y-%m-%d)

# 同步到 MEMORY.md
python tools/viking_memory.py sync-to-md
```

---

## 🚀 高级功能

### 1. 三层检索

```python
# L0 - 快速识别
client.retrieve(query="AI项目", level="l0")

# L1 - 决策支持
client.retrieve(query="OpenViking配置步骤", level="l1")

# L2 - 深度分析
client.retrieve(query="详细配置说明", level="l2")
```

### 2. 目录递归检索

```python
# 自动递归搜索子目录
client.retrieve(
    query="用户偏好",
    uri="viking://users/main/memory",
    recursive=True
)
```

### 3. 可视化检索轨迹

```python
# 获取检索过程详情
trace = client.get_retrieval_trace(uri="viking://...")
# 可以看到检索路径、停留点、跳转逻辑
```

---

## 📊 性能优化

### Token 节省估算

| 场景 | 传统 RAG | OpenViking | 节省 |
|:-----|:---------|:-----------|:-----|
| 快速检索 | 1000 tokens | 20 tokens (L0) | **98%** |
| 决策支持 | 2000 tokens | 200 tokens (L1) | **90%** |
| 深度分析 | 4000 tokens | 4000 tokens (L2) | 按需加载 |

### 本地缓存

- 向量数据库: LanceDB (默认)
- 文件系统缓存: `~/.openviking/data/`
- 索引缓存: 自动维护

---

## ⚠️ 注意事项

### 成本控制

| 模型 | 费用 | 建议 |
|:-----|:-----|:-----|
| GPT-4o-mini | $0.0006/1K tokens | 推荐，性价比高 |
| 火山方舟 | 有免费额度 | 新用户首选 |
| GPT-4V | $0.005/1K tokens | 只在需要图像理解时使用 |

### 隐私安全

- ✅ 数据本地存储 (`~/.openviking/data/`)
- ✅ 仅调用 API 时上传文本片段
- ✅ 敏感数据可使用本地 Embedding 模型

---

## 🔗 相关资源

- **GitHub**: https://github.com/volcengine/OpenViking
- **官网**: https://www.openviking.ai
- **详细报告**: `~/Documents/AI_SKILLS/Reports/11_OPENVIKING_RESEARCH.md`
- **本 Skill**: `~/.openclaw/agents/main/workspace/skills/openviking/SKILL.md`

---

## ✅ 验证安装

```bash
# 检查 OpenViking
python3 -c "import openviking; print('✅ OpenViking 已安装')"

# 检查配置
cat ~/.openviking/config.yaml | head -20

# 测试工具
python tools/viking_memory.py stats
```

---

*Skill 版本: 1.0*  
*更新日期: 2026-02-15*  
*状态: ✅ 已激活*
