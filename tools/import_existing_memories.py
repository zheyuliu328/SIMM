#!/usr/bin/env python3
"""
导入现有记忆到 OpenViking
将 MEMORY.md 和 memory/ 目录导入 OpenViking
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime

# 路径
MEMORY_MD = Path.home() / ".openclaw" / "agents" / "main" / "workspace" / "MEMORY.md"
MEMORY_DIR = Path.home() / ".openclaw" / "agents" / "main" / "workspace" / "memory"
VIKING_DATA = Path.home() / ".openviking" / "data"

class MemoryImporter:
    """记忆导入器"""
    
    def __init__(self):
        self.imported = []
        
    def parse_memory_md(self):
        """解析 MEMORY.md"""
        if not MEMORY_MD.exists():
            print("❌ MEMORY.md 不存在")
            return []
        
        print(f"📖 读取 {MEMORY_MD}...")
        content = MEMORY_MD.read_text(encoding='utf-8')
        
        # 简单解析：按 ## 分割章节
        sections = re.split(r'\n## ', content)
        
        memories = []
        for section in sections[1:]:  # 跳过第一个（标题）
            lines = section.strip().split('\n')
            title = lines[0].strip()
            content_text = '\n'.join(lines[1:]).strip()
            
            if content_text:
                memories.append({
                    "title": title,
                    "content": content_text,
                    "source": "MEMORY.md",
                    "type": "key_decision",
                    "imported_at": datetime.now().isoformat()
                })
        
        print(f"✅ 解析到 {len(memories)} 条关键记忆")
        return memories
    
    def parse_daily_memories(self):
        """解析 daily memory 文件"""
        if not MEMORY_DIR.exists():
            print("❌ memory/ 目录不存在")
            return []
        
        print(f"📖 读取 {MEMORY_DIR}...")
        
        memories = []
        for md_file in sorted(MEMORY_DIR.glob("*.md")):
            date_str = md_file.stem
            content = md_file.read_text(encoding='utf-8')
            
            # 提取关键信息（简化处理）
            memories.append({
                "title": f"Daily log {date_str}",
                "content": content[:1000] + "..." if len(content) > 1000 else content,
                "source": str(md_file.name),
                "type": "daily_log",
                "date": date_str,
                "imported_at": datetime.now().isoformat()
            })
        
        print(f"✅ 解析到 {len(memories)} 个 daily memory 文件")
        return memories
    
    def create_l0_l1_l2(self, memory):
        """创建 L0/L1/L2 三层结构"""
        content = memory["content"]
        
        # L0: 一句话摘要
        # 取第一句话或前 50 字符
        first_sentence = content.split('.')[0] if '.' in content else content[:50]
        l0 = first_sentence[:100]
        
        # L1: 概览（前 200 字符 + 关键信息）
        l1 = content[:500] if len(content) > 500 else content
        
        # L2: 完整内容
        l2 = content
        
        return {
            "uri": f"viking://users/main/memory/imported/{memory.get('type', 'general')}/{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "l0_abstract": l0,
            "l1_overview": l1,
            "l2_full": l2,
            "metadata": {
                "title": memory.get("title", ""),
                "source": memory.get("source", ""),
                "type": memory.get("type", "general"),
                "date": memory.get("date", ""),
                "imported_at": memory["imported_at"]
            }
        }
    
    def save_to_viking_format(self, memories):
        """保存为 OpenViking 格式"""
        VIKING_DATA.mkdir(parents=True, exist_ok=True)
        
        imported_dir = VIKING_DATA / "imported_memories"
        imported_dir.mkdir(exist_ok=True)
        
        print(f"💾 保存到 {imported_dir}...")
        
        for i, memory in enumerate(memories):
            viking_memory = self.create_l0_l1_l2(memory)
            
            # 保存为 JSON
            filename = f"memory_{i:04d}_{memory.get('type', 'general')}.json"
            filepath = imported_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(viking_memory, f, indent=2, ensure_ascii=False)
            
            self.imported.append(viking_memory)
        
        # 创建索引
        index = {
            "imported_at": datetime.now().isoformat(),
            "total_count": len(memories),
            "types": {}
        }
        
        for m in memories:
            t = m.get("type", "general")
            index["types"][t] = index["types"].get(t, 0) + 1
        
        index_file = imported_dir / "index.json"
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2)
        
        print(f"✅ 已导入 {len(memories)} 条记忆")
        print(f"   位置: {imported_dir}")
        print(f"   索引: {index_file}")
        
        return index
    
    def import_all(self):
        """导入所有记忆"""
        print("=" * 60)
        print("OpenViking 记忆导入工具")
        print("=" * 60)
        print()
        
        all_memories = []
        
        # 导入 MEMORY.md
        mem_md = self.parse_memory_md()
        all_memories.extend(mem_md)
        
        # 导入 daily memories
        mem_daily = self.parse_daily_memories()
        all_memories.extend(mem_daily)
        
        if not all_memories:
            print("⚠️  没有找到可导入的记忆")
            return
        
        print()
        print(f"总计: {len(all_memories)} 条记忆")
        print()
        
        # 保存
        index = self.save_to_viking_format(all_memories)
        
        print()
        print("=" * 60)
        print("导入完成！")
        print("=" * 60)
        print()
        print("统计:")
        for t, count in index["types"].items():
            print(f"  - {t}: {count} 条")
        print()
        print("这些记忆现在可以在 OpenViking 中检索！")
        print()
        print("使用方法:")
        print("  python tools/viking_memory.py retrieve-memory")
        print("    --query \"你的查询\" --memory-type key_decision")


def main():
    importer = MemoryImporter()
    importer.import_all()


if __name__ == "__main__":
    main()
