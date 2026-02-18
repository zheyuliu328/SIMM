# OpenClaw Browser Skill

**代号**: Browser Nexus  
**功能**: All-in-One 浏览器自动化与搜索中枢  
**优先级**: 🔴 最高（覆盖内置 web_search）

---

## 🎯 核心功能

### 1. 智能搜索 (Smart Search)

**触发**: 用户说"搜索 xxx"、"查一下 xxx"、"找 xxx"  
**行为**: 自动启动 Browser → 打开搜索引擎 → 输入查询 → 获取结果 → 必要时截图

```yaml
工作流:
  1. 检查 browser 状态 (openclaw browser status)
  2. 如未运行，启动 browser (openclaw browser start)
  3. 打开 Google/百度搜索页
  4. 输入搜索词
  5. 获取页面快照
  6. 提取关键结果
  7. 必要时截图验证
```

**示例对话**:
```
用户: 搜索 OpenAI 最新动态
AI:  [自动打开浏览器 → Google → 搜索 "OpenAI 最新动态" → 展示结果]
```

---

### 2. GitHub 联动 (GitHub Integration)

**触发**: 涉及 GitHub 仓库、PR、Issue 的查询  
**行为**: Browser 打开 GitHub 页面 → 读取内容 → 与 github skill 互补

```yaml
场景:
  - "查看这个 PR": browser open PR 页面 + 提取关键信息
  - "这个 Issue 什么情况": browser 打开 Issue + 总结内容
  - "看看这个仓库": browser 打开仓库主页 + 截图
```

**与 github skill 分工**:
- `github skill`: API 操作（搜索仓库、创建 Issue、合并 PR）
- `browser skill`: 页面浏览（查看详情、截图、阅读长内容）

---

### 3. 网页总结 (Web Summarize)

**触发**: "总结这个网页"、"这篇文章讲了什么"  
**行为**: Browser 抓取页面 → 提取文本 → LLM 总结

```yaml
工作流:
  1. browser open URL
  2. browser snapshot (获取页面结构)
  3. 提取主要文本内容
  4. LLM 总结要点
  5. 必要时截图关键部分
```

**与 summarize skill 联动**:
- summarize skill: 处理本地文件和已知 URL
- browser skill: 动态抓取 + 实时内容

---

### 4. Twitter/X 联动 (Bird Integration)

**触发**: "搜一下 Twitter 上的 xxx"、"看看 XX 的最新推文"  
**行为**: Browser 打开 Twitter → 搜索 → 提取推文

```yaml
场景:
  - "搜 Twitter AI": browser open twitter.com/search → 输入 AI
  - "看马斯克最新推文": browser 打开个人主页
```

**与 bird skill 分工**:
- `bird skill`: API 发推、点赞、关注
- `browser skill`: 浏览、搜索、阅读

---

### 5. RSS 联动 (Blogwatcher Integration)

**触发**: "看看 XX 博客的最新文章"  
**行为**: Browser 打开博客 → 获取最新文章列表

---

## 🛠️ 工具调用规范

### Browser 工具使用

```javascript
// 基本浏览
{
  "tool": "browser",
  "action": "open",
  "url": "https://..."
}

// 页面快照
{
  "tool": "browser", 
  "action": "snapshot",
  "targetId": "..."  // 可选，指定标签页
}

// 截图
{
  "tool": "browser",
  "action": "screenshot",
  "fullPage": true
}

// 点击元素
{
  "tool": "browser",
  "action": "act",
  "request": {
    "kind": "click",
    "ref": "e12"  // 来自 snapshot 的引用
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

---

## 📋 决策矩阵

| 用户需求 | 首选工具 | 辅助工具 | 说明 |
|:---------|:---------|:---------|:-----|
| "搜索 xxx" | **browser** | - | 打开搜索引擎，实时获取结果 |
| "查看 GitHub PR" | **browser** | github | browser 看内容，github 做操作 |
| "总结网页" | **browser** | - | 抓取 + LLM 总结 |
| "发 Tweet" | bird | - | bird skill 专门发推 |
| "搜索 Twitter" | **browser** | bird | browser 搜索浏览 |
| "查天气" | weather | - | weather skill 更直接 |
| "RSS 订阅" | blogwatcher | **browser** | blogwatcher 监控，browser 查看 |
| "运行代码" | coding-agent | - | 专用 skill |

---

## 🔧 配置要求

### OpenClaw 配置 (已配置)

```json
{
  "browser": {
    "enabled": true,
    "defaultProfile": "openclaw",
    "headless": false,
    "profiles": {
      "openclaw": {
        "cdpPort": 18800,
        "color": "#FF4500"
      }
    }
  }
}
```

### 环境检查清单

- [ ] Chrome/Brave/Chromium 已安装
- [ ] OpenClaw Gateway 运行中
- [ ] Browser 服务已启用
- [ ] 端口 18800 未被占用

---

## 🚀 快速开始

### 命令行测试

```bash
# 1. 检查状态
openclaw browser status

# 2. 启动浏览器
openclaw browser start

# 3. 打开搜索引擎
openclaw browser open "https://www.google.com"

# 4. 获取页面快照
openclaw browser snapshot

# 5. 截图
openclaw browser screenshot --full-page
```

### AI 对话中使用

```
用户: 搜索 "OpenClaw Browser 配置"

AI 内部流程:
1. browser status → 检查运行状态
2. browser start (如需要)
3. browser open "https://www.google.com/search?q=OpenClaw+Browser+配置"
4. browser snapshot → 获取结果
5. 提取并展示关键信息
6. 必要时 browser screenshot 验证
```

---

## 📝 使用示例

### 示例 1: 网页搜索

```
用户: 帮我搜一下 Kimi K2.5 的最新消息

AI:
[启动 browser]
[打开 Google]
[搜索 "Kimi K2.5 最新消息"]
[获取快照]

结果:
- Kimi K2.5 是 Moonshot AI 最新发布的大模型
- 支持 200K 上下文
- 代码能力显著提升
- [截图展示搜索结果]
```

### 示例 2: GitHub 查看

```
用户: 看看这个 PR https://github.com/.../pull/123

AI:
[browser open URL]
[snapshot 获取 PR 详情]

结果:
- PR 标题: Fix memory leak in worker
- 状态: Open, 3 commits, 2 comments
- 作者: @username
- 变更: +45/-12 行
- [截图展示 PR 页面]
```

### 示例 3: 网页总结

```
用户: 总结这篇文章 https://...

AI:
[browser open URL]
[snapshot 获取内容]
[提取正文]
[LLM 总结]

结果:
## 文章要点
1. ...
2. ...
3. ...

[截图关键段落]
```

---

## ⚠️ 注意事项

1. **优先使用 browser 而非 web_search**
   - 可以看到完整页面内容
   - 可以进一步交互（点击、滚动）
   - 可以截图验证

2. **browser 与系统 skills 的配合**
   - browser 负责"看"和"浏览"
   - 其他 skills 负责"操作"和"专用功能"

3. **性能考虑**
   - browser 启动需要 2-3 秒
   - 保持 browser 运行状态，避免频繁启停
   - 大页面 snapshot 可能较慢

4. **隐私安全**
   - 使用独立的 openclaw profile
   - 不访问个人浏览器数据
   - 敏感操作需用户确认

---

## 🔗 相关文件

- **配置文件**: `~/.openclaw/openclaw.json`
- **本 Skill**: `workspace/skills/openclaw-browser/SKILL.md`
- **整合文档**: `~/Documents/AI_SKILLS/Core_Skills/`

---

**版本**: 1.0  
**更新日期**: 2026-02-15  
**状态**: ✅ 已激活
