#!/bin/bash
# Ollama 一键安装脚本 (Mac M4/M3)
# 位置: ~/.openclaw/agents/main/workspace/tools/install_ollama.sh

set -e

echo "🦙 OpenViking + Ollama 安装脚本"
echo "================================"
echo ""

# 检查系统
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ 此脚本仅适用于 macOS"
    exit 1
fi

echo "✅ 检测到 macOS"

# 检查内存
echo ""
echo "📊 检查系统配置..."
if command -v sysctl &> /dev/null; then
    MEM_GB=$(sysctl -n hw.memsize | awk '{print int($0/1024/1024/1024)}')
    echo "   内存: ${MEM_GB}GB"
    if [ "$MEM_GB" -lt 8 ]; then
        echo "⚠️  警告: 内存不足 8GB，可能影响性能"
        read -p "是否继续? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
fi

# 检查 Homebrew
echo ""
echo "🍺 检查 Homebrew..."
if ! command -v brew &> /dev/null; then
    echo "❌ 未检测到 Homebrew，请先安装:"
    echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi
echo "✅ Homebrew 已安装"

# 安装 Ollama
echo ""
echo "📦 安装 Ollama..."
if command -v ollama &> /dev/null; then
    echo "✅ Ollama 已安装: \$(ollama --version)"
else
    brew install ollama
    echo "✅ Ollama 安装完成"
fi

# 下载模型
echo ""
echo "🤖 下载模型 (这可能需要几分钟)..."
echo ""

echo "1. 下载 Embedding 模型 (~500MB)..."
ollama pull nomic-embed-text
echo "✅ nomic-embed-text 下载完成"

echo ""
echo "2. 下载 VLM 模型 (~3GB)..."
echo "   (用于图片理解，可选)"
ollama pull llava:7b
echo "✅ llava:7b 下载完成"

# 启动 Ollama 服务
echo ""
echo "🚀 启动 Ollama 服务..."
if pgrep -x "ollama" > /dev/null; then
    echo "✅ Ollama 服务已在运行"
else
    ollama serve &
    sleep 2
    if pgrep -x "ollama" > /dev/null; then
        echo "✅ Ollama 服务已启动"
    else
        echo "❌ Ollama 服务启动失败"
        exit 1
    fi
fi

# 测试模型
echo ""
echo "🧪 测试模型..."

# 测试 Embedding
echo "   测试 Embedding..."
if curl -s http://localhost:11434/api/embeddings \
    -H "Content-Type: application/json" \
    -d '{"model": "nomic-embed-text", "prompt": "test"}' | grep -q "embedding"; then
    echo "   ✅ Embedding 模型工作正常"
else
    echo "   ❌ Embedding 模型测试失败"
    exit 1
fi

# 更新 OpenViking 配置
echo ""
echo "⚙️  更新 OpenViking 配置..."

CONFIG_FILE="$HOME/.openviking/config.yaml"

if [ -f "$CONFIG_FILE" ]; then
    # 备份原配置
    cp "$CONFIG_FILE" "$CONFIG_FILE.backup.\$(date +%Y%m%d_%H%M%S)"
    
    # 写入新配置
    cat > "$CONFIG_FILE" <> 'EOF'
# OpenViking 配置 (本地 Ollama)
# 位置: ~/.openviking/config.yaml

models:
  vlm:
    provider: ollama
    model: llava:7b
    base_url: http://localhost:11434
  
  embedding:
    provider: ollama
    model: nomic-embed-text
    base_url: http://localhost:11434

storage:
  path: ~/.openviking/data
  vector_db: lancedb

server:
  host: 127.0.0.1
  port: 18888

retrieval:
  default_level: l1
  top_k: 5
  threshold: 0.7
  max_depth: 3

memory:
  auto_extract: true
  update_strategy: merge
  user_memory_path: viking://users/{user_id}/memory
  agent_memory_path: viking://agents/{agent_id}/memory

logging:
  level: INFO
  path: ~/.openviking/logs
  max_size: 100MB
  backup_count: 5

openclaw:
  enabled: true
  session_base: viking://sessions/openclaw
  sync_with_memory_md: true
  memory_md_path: ~/.openclaw/agents/main/workspace/MEMORY.md
  auto_save_interval: 5
EOF
    
    echo "✅ 配置已更新"
else
    echo "❌ 未找到 OpenViking 配置文件"
    exit 1
fi

# 测试 OpenViking
echo ""
echo "🧪 测试 OpenViking..."
if python3 "$HOME/.openclaw/agents/main/workspace/tools/viking_memory.py" stats; then
    echo "✅ OpenViking 工作正常"
else
    echo "⚠️  OpenViking 测试失败，可能需要手动安装 openviking 包"
    echo "   运行: pip install openviking"
fi

# 完成
echo ""
echo "================================"
echo "🎉 安装完成！"
echo ""
echo "📋 已安装模型:"
echo "   - nomic-embed-text (Embedding)"
echo "   - llava:7b (VLM，图片理解)"
echo ""
echo "📁 配置文件:"
echo "   $CONFIG_FILE"
echo ""
echo "🔧 常用命令:"
echo "   ollama list              # 查看模型"
echo "   ollama ps                # 查看运行中模型"
echo "   ollama stop              # 停止服务"
echo "   ollama serve             # 启动服务"
echo ""
echo "🧠 OpenViking 工具:"
echo "   python tools/viking_memory.py stats"
echo "   python tools/viking_memory.py store-memory --memory-type preference --content '测试'"
echo ""
echo "⚡ 性能和续航:"
echo "   - Embedding: 常驻内存 ~1GB，续航影响 < 5%"
echo "   - VLM: 按需加载 ~4GB，续航影响 < 10%"
echo ""
echo "💡 提示: Ollama 服务会在后台运行，重启电脑后需要重新启动:"
echo "   ollama serve &"
echo ""
echo "🎯 开始使用 OpenViking 吧！"
echo "================================"
