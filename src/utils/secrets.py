"""
Secrets Manager - 统一的 Secrets 管理模块
强制从环境变量读取，禁止配置文件明文存储
"""

import os
import json
from typing import Optional, Dict, Any
from pathlib import Path


class SecretsError(Exception):
    """Secrets 相关异常"""
    pass


class SecretNotFoundError(SecretsError):
    """Secret 未找到"""
    pass


class SecretsManager:
    """
    Secrets 管理器
    
    规则：
    1. 所有敏感信息必须从环境变量读取
    2. 禁止从配置文件读取敏感信息
    3. 提供清晰的错误提示
    """
    
    # 必需的 Secrets
    REQUIRED_SECRETS = {
        'ER_API_KEY': 'Event Registry API Key (nlp-factor)',
        'KAGGLE_USERNAME': 'Kaggle username (credit-one)',
        'KAGGLE_KEY': 'Kaggle API key (credit-one)',
    }
    
    # 可选的 Secrets
    OPTIONAL_SECRETS = {
        'DB_PASSWORD': 'Database password',
        'AWS_ACCESS_KEY_ID': 'AWS Access Key',
        'AWS_SECRET_ACCESS_KEY': 'AWS Secret Key',
        'SMTP_PASSWORD': 'SMTP password',
    }
    
    def __init__(self):
        self._cache: Dict[str, str] = {}
        self._loaded = False
    
    def get(self, key: str, default: Any = None, required: bool = False) -> Optional[str]:
        """
        获取 Secret
        
        Args:
            key: 环境变量名
            default: 默认值（仅当 required=False 时有效）
            required: 是否为必需
            
        Returns:
            Secret 值或默认值
            
        Raises:
            SecretNotFoundError: 当 required=True 且未找到时
        """
        # 先查缓存
        if key in self._cache:
            return self._cache[key]
        
        # 从环境变量读取
        value = os.getenv(key)
        
        if value is None:
            if required:
                raise SecretNotFoundError(
                    f"Required secret '{key}' not found in environment variables.\n"
                    f"Please set it with: export {key}=your_value"
                )
            return default
        
        # 缓存并返回
        self._cache[key] = value
        return value
    
    def get_required(self, key: str) -> str:
        """获取必需的 Secret"""
        return self.get(key, required=True)
    
    def check_all(self) -> Dict[str, bool]:
        """检查所有必需 Secrets 是否存在"""
        return {
            key: os.getenv(key) is not None
            for key in self.REQUIRED_SECRETS.keys()
        }
    
    def validate(self) -> bool:
        """
        验证所有必需 Secrets 是否已设置
        
        Returns:
            True 如果全部存在
            
        Raises:
            SecretNotFoundError: 如果有缺失
        """
        missing = []
        for key, description in self.REQUIRED_SECRETS.items():
            if os.getenv(key) is None:
                missing.append(f"  - {key}: {description}")
        
        if missing:
            raise SecretNotFoundError(
                "Missing required secrets:\n" + "\n".join(missing) + "\n\n"
                "Please set them in your environment or .env file.\n"
                "Example:\n"
                "  export ER_API_KEY=your_api_key\n"
                "  export KAGGLE_USERNAME=your_username\n"
                "  export KAGGLE_KEY=your_key"
            )
        
        return True
    
    def load_env_file(self, env_path: str = ".env", required: bool = False):
        """
        从 .env 文件加载环境变量（仅用于开发）
        
        ⚠️ 警告：生产环境禁止提交 .env 文件到版本控制！
        
        Args:
            env_path: .env 文件路径
            required: 是否必需
        """
        env_file = Path(env_path)
        
        if not env_file.exists():
            if required:
                raise SecretNotFoundError(f"Env file not found: {env_path}")
            return
        
        # 读取 .env 文件
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')  # 去除引号
                    
                    # 只在未设置时才设置（环境变量优先级更高）
                    if os.getenv(key) is None:
                        os.environ[key] = value
    
    def mask(self, value: str, visible_chars: int = 4) -> str:
        """脱敏显示"""
        if not value or len(value) <= visible_chars * 2:
            return "***"
        return f"{value[:visible_chars]}...{value[-visible_chars:]}"
    
    def get_masked(self, key: str, default: str = "***") -> str:
        """获取脱敏后的值"""
        value = self.get(key)
        if value is None:
            return default
        return self.mask(value)


# 全局实例
secrets_manager = SecretsManager()


def get_secret(key: str, default: Any = None) -> Optional[str]:
    """便捷函数：获取 Secret"""
    return secrets_manager.get(key, default)


def get_required_secret(key: str) -> str:
    """便捷函数：获取必需的 Secret"""
    return secrets_manager.get_required(key)


def check_secrets() -> bool:
    """便捷函数：检查 Secrets"""
    return secrets_manager.validate()


# 项目特定的 Secrets 获取函数

def get_er_api_key() -> str:
    """获取 Event Registry API Key (nlp-factor)"""
    return secrets_manager.get_required('ER_API_KEY')


def get_kaggle_credentials() -> Dict[str, str]:
    """获取 Kaggle 凭证 (credit-one)"""
    return {
        'username': secrets_manager.get_required('KAGGLE_USERNAME'),
        'key': secrets_manager.get_required('KAGGLE_KEY'),
    }
