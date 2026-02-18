#!/usr/bin/env python3
"""
OpenViking Memory Manager for OpenClaw
位置: ~/.openclaw/agents/main/workspace/tools/viking_memory.py

功能:
- 管理 OpenClaw 会话记忆
- 与 OpenViking 上下文数据库集成
- 自动提取和更新长期记忆
"""

import os
import sys
import json
import asyncio
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# 尝试导入 openviking
try:
    import openviking as ov
except ImportError:
    print("⚠️  OpenViking 未安装，请先运行: pip install openviking")
    sys.exit(1)

# ==================== 配置 ====================
VIKING_PATH = Path.home() / ".openviking" / "data"
CONFIG_PATH = Path.home() / ".openviking" / "config.yaml"
MEMORY_MD_PATH = Path.home() / ".openclaw" / "agents" / "main" / "workspace" / "MEMORY.md"

class OpenClawVikingManager:
    """OpenClaw + OpenViking 记忆管理器"""
    
    def __init__(self):
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """初始化 OpenViking 客户端"""
        try:
            # 使用同步客户端
            self.client = ov.SyncOpenViking(
                path=str(VIKING_PATH),
                config_path=str(CONFIG_PATH) if CONFIG_PATH.exists() else None
            )
            self.client.initialize()
            print(f"✅ OpenViking 初始化成功")
            print(f"   数据路径: {VIKING_PATH}")
        except Exception as e:
            print(f"❌ 初始化失败: {e}")
            raise
    
    # ==================== 会话管理 ====================
    
    def store_session(self, session_id: str, context: Dict[str, Any]) -> str:
        """
        存储会话上下文到 OpenViking
        
        Args:
            session_id: 会话 ID (如: 2026-02-15)
            context: 会话上下文数据
        
        Returns:
            URI of stored resource
        """
        try:
            # 构建 URI
            uri = f"viking://sessions/openclaw/{session_id}"
            
            # 将上下文转换为资源
            context_json = json.dumps(context, ensure_ascii=False, indent=2)
            
            # 添加资源
            result = self.client.add_resource(
                path=f"memory://{context_json}",
                uri=uri,
                metadata={
                    "type": "session",
                    "agent": "openclaw",
                    "timestamp": datetime.now().isoformat(),
                    "session_id": session_id
                }
            )
            
            print(f"✅ 会话已存储: {uri}")
            return result.get('root_uri', uri)
            
        except Exception as e:
            print(f"❌ 存储失败: {e}")
            raise
    
    def retrieve_session(self, session_id: str, query: str = "", level: str = "l1") -> Dict:
        """
        检索会话上下文
        
        Args:
            session_id: 会话 ID
            query: 检索查询（可选）
            level: 检索层级 (l0, l1, l2)
        
        Returns:
            检索结果
        """
        try:
            uri = f"viking://sessions/openclaw/{session_id}"
            
            if query:
                # 语义检索
                result = self.client.retrieve(
                    query=query,
                    uri=uri,
                    level=level
                )
            else:
                # 列出目录结构
                result = self.client.ls(uri)
            
            return result
            
        except Exception as e:
            print(f"❌ 检索失败: {e}")
            return {}
    
    # ==================== 记忆管理 ====================
    
    def store_memory(self, user_id: str, memory_type: str, content: str, metadata: Dict = None) -> str:
        """
        存储长期记忆
        
        Args:
            user_id: 用户 ID
            memory_type: 记忆类型 (preference, event, skill)
            content: 记忆内容
            metadata: 额外元数据
        
        Returns:
            URI of stored memory
        """
        try:
            uri = f"viking://users/{user_id}/memory/{memory_type}/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            result = self.client.add_resource(
                path=f"memory://{content}",
                uri=uri,
                metadata={
                    "type": "memory",
                    "memory_type": memory_type,
                    "timestamp": datetime.now().isoformat(),
                    **(metadata or {})
                }
            )
            
            print(f"✅ 记忆已存储: {uri}")
            return uri
            
        except Exception as e:
            print(f"❌ 记忆存储失败: {e}")
            raise
    
    def retrieve_memory(self, user_id: str, query: str, memory_type: Optional[str] = None) -> list:
        """
        检索长期记忆
        
        Args:
            user_id: 用户 ID
            query: 查询内容
            memory_type: 记忆类型过滤（可选）
        
        Returns:
            相关记忆列表
        """
        try:
            if memory_type:
                uri = f"viking://users/{user_id}/memory/{memory_type}"
            else:
                uri = f"viking://users/{user_id}/memory"
            
            result = self.client.retrieve(
                query=query,
                uri=uri,
                level="l1"  # 使用概览层
            )
            
            return result if isinstance(result, list) else [result]
            
        except Exception as e:
            print(f"❌ 记忆检索失败: {e}")
            return []
    
    def extract_memory(self, session_id: str) -> Dict:
        """
        从会话中提取长期记忆
        
        Args:
            session_id: 会话 ID
        
        Returns:
            提取的记忆
        """
        try:
            uri = f"viking://sessions/openclaw/{session_id}"
            
            # 触发记忆提取
            result = self.client.extract_memory(uri=uri)
            
            print(f"✅ 记忆提取完成")
            return result
            
        except Exception as e:
            print(f"❌ 记忆提取失败: {e}")
            return {}
    
    # ==================== MEMORY.md 同步 ====================
    
    def sync_to_memory_md(self, user_id: str = "main") -> bool:
        """
        将关键记忆同步到 MEMORY.md
        
        Args:
            user_id: 用户 ID
        
        Returns:
            是否成功
        """
        try:
            if not MEMORY_MD_PATH.exists():
                print(f"⚠️  MEMORY.md 不存在: {MEMORY_MD_PATH}")
                return False
            
            # 检索重要记忆
            important_memories = self.retrieve_memory(
                user_id=user_id,
                query="重要决策 关键事件 用户偏好",
                memory_type="event"
            )
            
            # 构建同步内容
            sync_content = f"\n\n## OpenViking 同步记忆 ({datetime.now().strftime('%Y-%m-%d')})\n\n"
            
            for memory in important_memories[:5]:  # 只同步最重要的 5 条
                sync_content += f"- {memory.get('content', '')}\n"
            
            # 追加到 MEMORY.md
            with open(MEMORY_MD_PATH, 'a', encoding='utf-8') as f:
                f.write(sync_content)
            
            print(f"✅ 已同步到 MEMORY.md")
            return True
            
        except Exception as e:
            print(f"❌ 同步失败: {e}")
            return False
    
    # ==================== 实用工具 ====================
    
    def list_sessions(self) -> list:
        """列出所有存储的会话"""
        try:
            result = self.client.ls("viking://sessions/openclaw")
            return result.get('entries', [])
        except Exception as e:
            print(f"❌ 列表获取失败: {e}")
            return []
    
    def list_user_memory(self, user_id: str = "main") -> list:
        """列出用户的所有记忆"""
        try:
            result = self.client.ls(f"viking://users/{user_id}/memory")
            return result.get('entries', [])
        except Exception as e:
            print(f"❌ 记忆列表获取失败: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        try:
            return {
                "data_path": str(VIKING_PATH),
                "config_path": str(CONFIG_PATH),
                "memory_md_path": str(MEMORY_MD_PATH),
                "sessions": len(self.list_sessions()),
                "memory_entries": len(self.list_user_memory())
            }
        except Exception as e:
            print(f"❌ 统计获取失败: {e}")
            return {}


# ==================== CLI 接口 ====================

def main():
    parser = argparse.ArgumentParser(description='OpenViking Memory Manager for OpenClaw')
    parser.add_argument('action', choices=[
        'store-session', 'retrieve-session', 
        'store-memory', 'retrieve-memory',
        'extract-memory', 'sync-to-md',
        'list-sessions', 'list-memory', 'stats'
    ])
    parser.add_argument('--session-id', help='Session ID')
    parser.add_argument('--user-id', default='main', help='User ID')
    parser.add_argument('--query', help='Search query')
    parser.add_argument('--content', help='Memory content')
    parser.add_argument('--memory-type', choices=['preference', 'event', 'skill'], help='Memory type')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    args = parser.parse_args()
    
    # 初始化管理器
    manager = OpenClawVikingManager()
    
    # 执行操作
    if args.action == 'stats':
        result = manager.get_stats()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif args.action == 'store-session':
        if not args.session_id:
            print("❌ 需要 --session-id")
            sys.exit(1)
        context = json.loads(args.content) if args.content else {"test": True}
        uri = manager.store_session(args.session_id, context)
        print(f"URI: {uri}")
    
    elif args.action == 'retrieve-session':
        if not args.session_id:
            print("❌ 需要 --session-id")
            sys.exit(1)
        result = manager.retrieve_session(args.session_id, args.query or "")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif args.action == 'store-memory':
        if not args.content or not args.memory_type:
            print("❌ 需要 --content 和 --memory-type")
            sys.exit(1)
        uri = manager.store_memory(args.user_id, args.memory_type, args.content)
        print(f"URI: {uri}")
    
    elif args.action == 'retrieve-memory':
        if not args.query:
            print("❌ 需要 --query")
            sys.exit(1)
        result = manager.retrieve_memory(args.user_id, args.query, args.memory_type)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif args.action == 'extract-memory':
        if not args.session_id:
            print("❌ 需要 --session-id")
            sys.exit(1)
        result = manager.extract_memory(args.session_id)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif args.action == 'sync-to-md':
        success = manager.sync_to_memory_md(args.user_id)
        sys.exit(0 if success else 1)
    
    elif args.action == 'list-sessions':
        sessions = manager.list_sessions()
        for session in sessions:
            print(session)
    
    elif args.action == 'list-memory':
        memories = manager.list_user_memory(args.user_id)
        for memory in memories:
            print(memory)


if __name__ == '__main__':
    main()
