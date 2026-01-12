"""
用户模型
"""
from typing import Optional, Dict, Any

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
    # 用户主键id, 使用uuid 生成， 字符串32位
    id = Column(String(32),primary_key=True,default=lambda: uuid.uuid4().hex[:32])
    # 邮箱字段，可以为空，唯一且建立索引，最大长度128
    email = Column(String(128), nullable=True, unique=True, index=True)
    # 密码哈希字段，必填，最大长度255
    password_hash = Column(String(255),nullable=False)
    # 用户是否激活，默认为激活，不可为空
    is_active = Column(Boolean,nullable=False,default=True)
    # 创建时间字段，默认当前时间，建立索引
    created_at = Column(DateTime,default=func.now(),index=True)
    # 更新时间字段，默认当前时间，更新时自动刷新
    update_at = Column(DateTime,default=func.now(), onupdate=func.now())

    # 将当前用户对象转换为字典
    def to_dict(self,include_password = False, **kwargs):
        """
        转换为字典
        Args:
            include_password: 是否包含密码，排除 password_hash 字段
            **kwargs:

        Returns:

        """
        exclude = ["password_hash"] if not include_password else []
        return super().to_dict(exclude=exclude,**kwargs)