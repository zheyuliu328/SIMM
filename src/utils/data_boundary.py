"""
数据边界校验模块 - 输入数据校验
提供字段、类型、范围、缺失率校验
"""

import re
import pandas as pd
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum


class ValidationError(Exception):
    """数据校验错误"""
    pass


class ValidationResult:
    """校验结果"""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.stats: Dict[str, Any] = {}
    
    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0
    
    def add_error(self, message: str):
        self.errors.append(message)
    
    def add_warning(self, message: str):
        self.warnings.append(message)
    
    def merge(self, other: 'ValidationResult'):
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.stats.update(other.stats)


class FieldType(Enum):
    """字段类型"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    CATEGORICAL = "categorical"


@dataclass
class FieldSchema:
    """字段模式定义"""
    name: str
    field_type: FieldType
    required: bool = True
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    choices: Optional[List[Any]] = None
    allow_null: bool = False
    null_rate_threshold: float = 0.3  # 缺失率阈值
    custom_validator: Optional[Callable[[Any], bool]] = None
    description: str = ""


class DataBoundaryValidator:
    """数据边界校验器"""
    
    def __init__(self, schema: List[FieldSchema] = None):
        self.schema: Dict[str, FieldSchema] = {}
        if schema:
            for field in schema:
                self.schema[field.name] = field
    
    def add_field(self, field: FieldSchema):
        """添加字段定义"""
        self.schema[field.name] = field
    
    def validate_value(self, value: Any, field: FieldSchema) -> List[str]:
        """校验单个值"""
        errors = []
        
        # 空值检查
        if value is None or (isinstance(value, float) and pd.isna(value)):
            if field.required and not field.allow_null:
                errors.append(f"Field '{field.name}' is required but got null")
            return errors
        
        # 类型检查
        type_validators = {
            FieldType.STRING: lambda x: isinstance(x, str),
            FieldType.INTEGER: lambda x: isinstance(x, (int, float)) and float(x).is_integer(),
            FieldType.FLOAT: lambda x: isinstance(x, (int, float)),
            FieldType.BOOLEAN: lambda x: isinstance(x, bool),
        }
        
        if field.field_type in type_validators:
            if not type_validators[field.field_type](value):
                errors.append(
                    f"Field '{field.name}' expected {field.field_type.value}, "
                    f"got {type(value).__name__}"
                )
                return errors
        
        # 范围检查
        if field.field_type in (FieldType.INTEGER, FieldType.FLOAT):
            num_val = float(value)
            if field.min_value is not None and num_val < field.min_value:
                errors.append(
                    f"Field '{field.name}' value {num_val} is below minimum {field.min_value}"
                )
            if field.max_value is not None and num_val > field.max_value:
                errors.append(
                    f"Field '{field.name}' value {num_val} is above maximum {field.max_value}"
                )
        
        # 长度检查
        if field.field_type == FieldType.STRING:
            str_len = len(str(value))
            if field.min_length is not None and str_len < field.min_length:
                errors.append(
                    f"Field '{field.name}' length {str_len} is below minimum {field.min_length}"
                )
            if field.max_length is not None and str_len > field.max_length:
                errors.append(
                    f"Field '{field.name}' length {str_len} is above maximum {field.max_length}"
                )
        
        # 模式检查
        if field.pattern and field.field_type == FieldType.STRING:
            if not re.match(field.pattern, str(value)):
                errors.append(
                    f"Field '{field.name}' does not match pattern '{field.pattern}'"
                )
        
        # 枚举检查
        if field.choices is not None:
            if value not in field.choices:
                errors.append(
                    f"Field '{field.name}' value '{value}' is not in allowed choices: {field.choices}"
                )
        
        # 自定义校验
        if field.custom_validator is not None:
            try:
                if not field.custom_validator(value):
                    errors.append(f"Field '{field.name}' failed custom validation")
            except Exception as e:
                errors.append(f"Field '{field.name}' custom validation error: {e}")
        
        return errors
    
    def validate_dict(self, data: Dict[str, Any]) -> ValidationResult:
        """校验字典数据"""
        result = ValidationResult()
        
        # 检查必需字段
        for field_name, field in self.schema.items():
            if field.required and field_name not in data:
                result.add_error(f"Required field '{field_name}' is missing")
        
        # 校验每个字段
        for field_name, value in data.items():
            if field_name in self.schema:
                field = self.schema[field_name]
                errors = self.validate_value(value, field)
                for error in errors:
                    result.add_error(error)
            else:
                result.add_warning(f"Unknown field '{field_name}' in data")
        
        return result
    
    def validate_dataframe(self, df: pd.DataFrame) -> ValidationResult:
        """校验 DataFrame"""
        result = ValidationResult()
        
        if df.empty:
            result.add_error("DataFrame is empty")
            return result
        
        # 统计信息
        result.stats['total_rows'] = len(df)
        result.stats['total_columns'] = len(df.columns)
        
        # 检查必需字段
        for field_name, field in self.schema.items():
            if field.required and field_name not in df.columns:
                result.add_error(f"Required column '{field_name}' is missing")
        
        # 校验每个字段
        for field_name, field in self.schema.items():
            if field_name not in df.columns:
                continue
            
            column = df[field_name]
            
            # 缺失率检查
            null_rate = column.isna().sum() / len(df)
            if null_rate > field.null_rate_threshold:
                result.add_warning(
                    f"Column '{field_name}' has high null rate: {null_rate:.2%} "
                    f"(threshold: {field.null_rate_threshold:.2%})"
                )
            
            # 校验非空值
            valid_mask = column.notna()
            for idx, value in column[valid_mask].items():
                errors = self.validate_value(value, field)
                for error in errors:
                    result.add_error(f"Row {idx}: {error}")
        
        # 检查未知列
        known_columns = set(self.schema.keys())
        unknown_columns = set(df.columns) - known_columns
        if unknown_columns:
            result.add_warning(f"Unknown columns in DataFrame: {unknown_columns}")
        
        return result


# 预定义的校验模式

LOAN_SCHEMA = [
    FieldSchema(
        name="loan_id",
        field_type=FieldType.STRING,
        required=True,
        pattern=r"^[A-Z0-9_]+$",
        description="贷款唯一标识"
    ),
    FieldSchema(
        name="loan_amount",
        field_type=FieldType.FLOAT,
        required=True,
        min_value=0,
        max_value=100_000_000,
        description="贷款金额"
    ),
    FieldSchema(
        name="fico_score",
        field_type=FieldType.INTEGER,
        required=True,
        min_value=300,
        max_value=850,
        description="FICO信用评分"
    ),
    FieldSchema(
        name="dti_ratio",
        field_type=FieldType.FLOAT,
        required=True,
        min_value=0,
        max_value=1,
        description="债务收入比"
    ),
    FieldSchema(
        name="default_flag",
        field_type=FieldType.INTEGER,
        required=True,
        choices=[0, 1],
        description="违约标志"
    ),
]

NEWS_SCHEMA = [
    FieldSchema(
        name="uri",
        field_type=FieldType.STRING,
        required=True,
        description="文章唯一标识"
    ),
    FieldSchema(
        name="title",
        field_type=FieldType.STRING,
        required=True,
        max_length=500,
        description="文章标题"
    ),
    FieldSchema(
        name="date",
        field_type=FieldType.STRING,
        required=True,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="发布日期"
    ),
    FieldSchema(
        name="code",
        field_type=FieldType.STRING,
        required=True,
        pattern=r"^\d{4}\.HK$",
        description="股票代码"
    ),
    FieldSchema(
        name="sentiment_score",
        field_type=FieldType.FLOAT,
        required=False,
        min_value=-1,
        max_value=1,
        description="情感分数"
    ),
]


def validate_loan_data(df: pd.DataFrame) -> ValidationResult:
    """校验贷款数据"""
    validator = DataBoundaryValidator(LOAN_SCHEMA)
    return validator.validate_dataframe(df)


def validate_news_data(df: pd.DataFrame) -> ValidationResult:
    """校验新闻数据"""
    validator = DataBoundaryValidator(NEWS_SCHEMA)
    return validator.validate_dataframe(df)
