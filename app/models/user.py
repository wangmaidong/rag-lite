"""
用户模型
"""

# 从 SQLAlchemy 导入 Column、String、DateTime、Boolean 类型
from sqlalchemy import Column, String, DateTime, Boolean

# 从 SQLAlchemy 导入 func 用于处理时间戳
from sqlalchemy.sql import func

# 导入 uuid 模块用于生成唯一标识符
import uuid

# 从项目模型基类导入 BaseModel
from app.models.base import BaseModel


class User(BaseModel):
    """用户模型"""

    # 指定数据表名称为 'user'
    __tablename__ = "user"
    # 指定 __repr__ 时显示的字段为 id 和 username
    __repr_fields__ = ["id", "username"]
