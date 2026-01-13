"""
知识库模型
"""

# 导入SQLAlchemy的字段类型和相关功能
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey

# 导入SQLAlchemy的SQL函数
from sqlalchemy.sql import func

# 导入uuid模块用于生成唯一ID
import uuid

# 导入基础模型类
from app.models.base import BaseModel


# 定义知识库模型，继承自基础模型
class Knowledgebase(BaseModel):
    # 指定模型对应的表名称
    __tablename__ = "knowledgebase"
    # 指定 __repr__ 方法显示的字段
    __repr_fields__ = ["id", "name"]
    # 主键id字段，类型为32位字符串，默认值为uuid的前32位
    id = Column(
        String(32),
        primary_key=True,
        default=lambda: uuid.uuid4().hex[:32],
    )
    # 用户id字段，外键关联到user表的id，删除用户时级联删除，不可为空，并且建有索引
    user_id = Column(
        String(32),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # 知识库名称字段，不可为空并建有索引，最大长度128
    name = Column(String(128), nullable=False, index=True)
    # 描述字段
    description = Column(Text, nullable=True)
    # 封面图片路径字段，类型微字符串，最大长度512，可以为空
    cover_image = Column(String(512), nullable=True, comment="封面图片路径")
    # 分块大小字段，类型为整数，不能为空，默认值为512
    chunk_size = Column(Integer, nullable=False, default=512)
    # 分块重叠大小字段，类型为整数，不能为空，默认值微50
    chunk_overlap = Column(Integer, nullable=False, default=50)
    # 创建时间字段，类型为DateTime，默认为当前时间，并建立索引
    created_at = Column(DateTime, default=func.now(), index=True)
    # 更新时间字段，类型为DateTime，默认为当前时间，更新时自动变为当前时间
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
