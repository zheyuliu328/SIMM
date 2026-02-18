"""
Guardrails - 安全护栏模块
提供危险操作保护、审计日志和输入校验
"""

import os
import sys
import json
import logging
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from functools import wraps
from contextlib import contextmanager


class SecurityError(Exception):
    """安全相关异常"""
    pass


class GuardrailsError(Exception):
    """Guardrails 异常基类"""
    pass


class ConfirmationRequiredError(GuardrailsError):
    """需要确认错误"""
    pass


class PathTraversalError(SecurityError):
    """路径遍历攻击检测"""
    pass


class AuditLogger:
    """审计日志记录器"""
    
    def __init__(self, log_dir: str = "./logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True, parents=True)
        
        # 设置文件日志
        log_file = self.log_dir / f"audit_{datetime.now().strftime('%Y%m%d')}.log"
        self.logger = logging.getLogger("guardrails.audit")
        self.logger.setLevel(logging.INFO)
        
        # 避免重复添加 handler
        if not self.logger.handlers:
            handler = logging.FileHandler(log_file, encoding='utf-8')
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def log(self, action: str, details: Dict[str, Any], user: str = "system"):
        """记录审计日志"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "user": user,
            "action": action,
            "details": details
        }
        self.logger.info(json.dumps(entry, ensure_ascii=False))
    
    def log_dangerous_op(self, operation: str, target: str, confirmed: bool, 
                         user: str = "system", extra: Dict = None):
        """记录危险操作"""
        self.log("DANGEROUS_OPERATION", {
            "operation": operation,
            "target": target,
            "confirmed": confirmed,
            "extra": extra or {}
        }, user)


class PathValidator:
    """路径校验器 - 防止路径遍历攻击"""
    
    def __init__(self, allowed_base_paths: List[str] = None):
        self.allowed_base_paths = [Path(p).resolve() for p in (allowed_base_paths or ["."])]
    
    def validate(self, path: str, check_exists: bool = False) -> Path:
        """
        校验路径是否在允许范围内
        
        Args:
            path: 待校验路径
            check_exists: 是否检查文件存在
            
        Returns:
            规范化后的 Path 对象
            
        Raises:
            PathTraversalError: 路径遍历攻击检测
        """
        try:
            # 解析路径
            target = Path(path).resolve()
            
            # 检查是否在允许的基路径下
            is_allowed = any(
                str(target).startswith(str(base))
                for base in self.allowed_base_paths
            )
            
            if not is_allowed:
                raise PathTraversalError(
                    f"Path traversal detected: {path} is outside allowed directories"
                )
            
            # 检查符号链接
            if target.is_symlink():
                real_target = target.resolve()
                is_allowed = any(
                    str(real_target).startswith(str(base))
                    for base in self.allowed_base_paths
                )
                if not is_allowed:
                    raise PathTraversalError(
                        f"Symlink traversal detected: {path} -> {real_target}"
                    )
            
            if check_exists and not target.exists():
                raise FileNotFoundError(f"Path does not exist: {path}")
            
            return target
            
        except PathTraversalError:
            raise
        except Exception as e:
            raise PathTraversalError(f"Invalid path: {path}, error: {e}")


class DangerousOpGuard:
    """危险操作保护器"""
    
    DANGEROUS_OPERATIONS = {
        'database.delete': {'confirm': True, 'backup': True},
        'database.drop_table': {'confirm': True, 'backup': True},
        'file.delete': {'confirm': True, 'backup': False},
        'file.overwrite': {'confirm': True, 'backup': True},
        'config.modify': {'confirm': True, 'backup': True},
        'model.deploy': {'confirm': True, 'backup': True},
    }
    
    def __init__(self, audit_logger: AuditLogger = None):
        self.audit = audit_logger or AuditLogger()
        self._confirm_override = os.getenv('GUARDRAILS_CONFIRM', 'false').lower() == 'true'
        self._dry_run = os.getenv('GUARDRAILS_DRY_RUN', 'false').lower() == 'true'
    
    def check(self, operation: str, target: str, 
              confirm_flag: bool = False,
              interactive: bool = True) -> bool:
        """
        检查危险操作
        
        Args:
            operation: 操作类型
            target: 操作目标
            confirm_flag: 是否已提供 --confirm 标志
            interactive: 是否允许交互式确认
            
        Returns:
            True 如果允许执行
            
        Raises:
            ConfirmationRequiredError: 需要确认但未提供
        """
        config = self.DANGEROUS_OPERATIONS.get(operation, {})
        
        # Dry run 模式
        if self._dry_run:
            self.audit.log_dangerous_op(operation, target, False, extra={"dry_run": True})
            print(f"[DRY RUN] Would execute: {operation} on {target}")
            return False
        
        # 检查是否需要确认
        if config.get('confirm', False):
            if not confirm_flag and not self._confirm_override:
                self.audit.log_dangerous_op(operation, target, False, extra={"reason": "confirmation_required"})
                
                if interactive:
                    # 交互式确认
                    response = input(f"\n⚠️  Dangerous operation: {operation} on {target}\nConfirm? [y/N]: ")
                    if response.lower() != 'y':
                        print("Operation cancelled.")
                        return False
                    self.audit.log_dangerous_op(operation, target, True, extra={"method": "interactive"})
                    return True
                else:
                    raise ConfirmationRequiredError(
                        f"Operation '{operation}' on '{target}' requires --confirm flag"
                    )
            
            self.audit.log_dangerous_op(operation, target, True, extra={"method": "flag"})
        
        return True


class InputValidator:
    """输入校验器"""
    
    @staticmethod
    def validate_string(value: Any, field_name: str, 
                       min_len: int = 1, max_len: int = 1000,
                       pattern: str = None) -> str:
        """校验字符串"""
        if not isinstance(value, str):
            raise ValueError(f"{field_name} must be a string, got {type(value)}")
        
        if len(value) < min_len:
            raise ValueError(f"{field_name} must be at least {min_len} characters")
        
        if len(value) > max_len:
            raise ValueError(f"{field_name} must be at most {max_len} characters")
        
        if pattern and not re.match(pattern, value):
            raise ValueError(f"{field_name} does not match required pattern")
        
        return value
    
    @staticmethod
    def validate_number(value: Any, field_name: str,
                       min_val: float = None, max_val: float = None,
                       allow_none: bool = False) -> Optional[float]:
        """校验数值"""
        if value is None:
            if allow_none:
                return None
            raise ValueError(f"{field_name} cannot be None")
        
        try:
            num = float(value)
        except (TypeError, ValueError):
            raise ValueError(f"{field_name} must be a number, got {value}")
        
        if min_val is not None and num < min_val:
            raise ValueError(f"{field_name} must be >= {min_val}")
        
        if max_val is not None and num > max_val:
            raise ValueError(f"{field_name} must be <= {max_val}")
        
        return num
    
    @staticmethod
    def validate_choice(value: Any, field_name: str, choices: List[Any]) -> Any:
        """校验枚举值"""
        if value not in choices:
            raise ValueError(f"{field_name} must be one of {choices}, got {value}")
        return value


# 便捷装饰器

def require_confirm(operation: str):
    """危险操作确认装饰器"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, confirm: bool = False, **kwargs):
            guard = DangerousOpGuard()
            # 尝试从参数中提取 target
            target = kwargs.get('target', kwargs.get('path', kwargs.get('db_path', 'unknown')))
            if guard.check(operation, str(target), confirm_flag=confirm):
                return func(*args, **kwargs)
            return None
        return wrapper
    return decorator


def audit_log(action: str):
    """审计日志装饰器"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = AuditLogger()
            start_time = datetime.now()
            
            try:
                result = func(*args, **kwargs)
                logger.log(action, {
                    "function": func.__name__,
                    "args": str(args),
                    "kwargs": {k: str(v) for k, v in kwargs.items()},
                    "duration_ms": (datetime.now() - start_time).total_seconds() * 1000,
                    "status": "success"
                })
                return result
            except Exception as e:
                logger.log(action, {
                    "function": func.__name__,
                    "error": str(e),
                    "status": "error"
                })
                raise
        return wrapper
    return decorator


def validate_path(allowed_base_paths: List[str] = None):
    """路径校验装饰器"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            validator = PathValidator(allowed_base_paths)
            # 检查参数中的 path 或 file_path
            for key in ['path', 'file_path', 'db_path', 'target_path']:
                if key in kwargs:
                    kwargs[key] = str(validator.validate(kwargs[key]))
            return func(*args, **kwargs)
        return wrapper
    return decorator


# 导入 re 模块用于正则
import re


# 全局实例
default_guard = DangerousOpGuard()
default_audit = AuditLogger()
default_path_validator = PathValidator()
