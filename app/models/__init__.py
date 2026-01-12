"""
数据模型模块
"""

# 导入数据库模型基类和自定义基类
from app.models.base import Base, BaseModel


# 定义当前模块对外可用的成员列表
__all__ = ["Base", "BaseModel"]
