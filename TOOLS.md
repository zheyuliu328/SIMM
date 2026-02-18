# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.

---

## 🌐 Browser (OpenClaw Browser Skill)

### 配置状态
- **Profile**: `openclaw` (独立浏览器)
- **状态**: ✅ 已启用
- **CDP 端口**: 18800
- **浏览器**: Google Chrome

### 命令速查

```bash
# 状态检查
openclaw browser status

# 启动/停止
openclaw browser start
openclaw browser stop

# 打开网页
openclaw browser open https://example.com

# 页面快照
openclaw browser snapshot

# 截图
openclaw browser screenshot --full-page

# 生成 PDF
openclaw browser pdf
```

### AI 工具调用

```javascript
// 打开网页
{
  "tool": "browser",
  "action": "open",
  "url": "https://..."
}

// 获取快照
{
  "tool": "browser",
  "action": "snapshot"
}

// 截图
{
  "tool": "browser",
  "action": "screenshot"
}

// 点击元素
{
  "tool": "browser",
  "action": "act",
  "request": {
    "kind": "click",
    "ref": "e12"
  }
}

// 输入文本
{
  "tool": "browser",
  "action": "act",
  "request": {
    "kind": "type",
    "ref": "e5",
    "text": "搜索关键词"
  }
}
```

### 使用场景

| 场景 | 操作 |
|:-----|:-----|
| 搜索信息 | Browser → 搜索引擎 → 输入 → 获取结果 |
| 查看 GitHub | Browser → 打开 PR/Issue → 截图/总结 |
| 总结网页 | Browser → 抓取 → LLM 总结 |
| 查 Twitter | Browser → twitter.com → 搜索 |

### 优先策略

**说"搜索 xxx" → 用 Browser，不用 web_search**

原因:
- ✅ 看到完整页面内容
- ✅ 可以进一步交互
- ✅ 截图验证结果
- ✅ 实时内容

### 相关文件

- **Skill**: `workspace/skills/openclaw-browser/SKILL.md`
- **配置**: `~/.openclaw/openclaw.json`
- **文档**: `~/Documents/AI_SKILLS/`

---

## 🧠 OpenViking Memory (AI 上下文数据库)

### 简介

**OpenViking**: 字节火山引擎开源的 AI Agent 上下文数据库  
**核心**: L0/L1/L2 三层渐进式加载 + URI 文件系统

### 三层架构

```
L0 (摘要层)    → 一句话, ~20 tokens
L1 (概览层)    → 核心信息, ~200 tokens
L2 (完整层)    → 完整原文, 按需加载
```

### 位置

- **Skill**: `workspace/skills/openviking/SKILL.md`
- **工具**: `tools/viking_memory.py`
- **配置**: `~/.openviking/config.yaml`
- **数据**: `~/.openviking/data/`

### 命令速查

```bash
# 查看状态
python tools/viking_memory.py stats

# 存储记忆
python tools/viking_memory.py store-memory \
  --memory-type preference \
  --content "用户喜欢简洁回答"

# 检索记忆
python tools/viking_memory.py retrieve-memory --query "用户偏好"

# 会话管理
python tools/viking_memory.py store-session --session-id 2026-02-15
python tools/viking_memory.py retrieve-session --session-id 2026-02-15

# 提取记忆
python tools/viking_memory.py extract-memory --session-id 2026-02-15

# 同步到 MEMORY.md
python tools/viking_memory.py sync-to-md

# 列出所有
python tools/viking_memory.py list-sessions
python tools/viking_memory.py list-memory
```

### 环境变量

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# 或火山方舟（推荐，有免费额度）
export ARK_API_KEY="..."
```

### 使用流程

```
会话开始 → 加载记忆 → 实时存储 → 提取记忆 → 同步 MEMORY.md
```

### 与 MEMORY.md 的关系

| 系统 | 用途 | 说明 |
|:-----|:-----|:-----|
| **OpenViking** | 大规模上下文、自动记忆提取 | 技术实现层 |
| **MEMORY.md** | 关键决策、用户偏好 | 人工维护层 |

### 相关文件

- **Skill**: `workspace/skills/openviking/SKILL.md`
- **详细报告**: `~/Documents/AI_SKILLS/Reports/11_OPENVIKING_RESEARCH.md`
