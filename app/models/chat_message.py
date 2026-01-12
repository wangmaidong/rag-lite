"""
聊天消息模型
"""

# 导入 SQLAlchemy 的列类型、外键约束、JSON 类型等
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON

# 导入 SQLAlchemy 的时间函数
from sqlalchemy.sql import func

# 导入 uuid 用于生成唯一的主键
import uuid

# 导入自定义的基础模型 BaseModel
from app.models.base import BaseModel


# 定义ChatMessage类，继承自BaseModel
class ChatMessage(BaseModel):
    """聊天消息模型"""

    # 指定在数据库中的表名为 chat_message
    __tablename__ = "chat_message"
    # 指定 __repr__ 时显示的字段为 id, session_id, role
    __repr_fields__ = ["id", "session_id", "role"]
    # 定义主键 id，使用 32 位字符串，默认值为 uuid 的前 32 位
    id = Column(
        String(32),
        ForeignKey("chat_session.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # 定义角色 role，为字符串类型，不可为空，区分 'user' 或 'assistant'
    role = Column(String(16), nullable=False)
    # 定义消息内容content, 为 Text类型， 不可为空
    content = Column(Text, nullable=False)
    # 定义引用来源source,为JSON类型，可以为空
    sources = Column(JSON, nullable=True)
    # 定义创建时间 created_at, 默认为当前时间，加索引
    created_at = Column(DateTime, default=func.now(), index=True)
