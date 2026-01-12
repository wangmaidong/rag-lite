# 数据库模型基类说明文档字符串
"""
数据库模型基类
"""

# 导入SQLAlchemy的declarative_base用于创建模型基类
from sqlalchemy.ext.declarative import declarative_base

# 导入inspect用于反射获取模型信息
from sqlalchemy.inspection import inspect

# 导入类型标注用的类型
from typing import Dict, Any, Optional

# 创建统一的Base类，所有ORM模型都应继承自该Base
Base = declarative_base()


# 定义所有模型的基类
class BaseModel(Base):
    # 说明此类为抽象类，不会创建表
    """
    模型基类，提供通用方法
    所有模型应该继承此类而不是直接继承 Base
    """
    __abstract__ = True  # 标记为抽象类，不会创建表

    # 将模型对象转为字典的方法
    def to_dict(self, exclude: Optional[list] = None, **kwargs) -> Dict[str, Any]:
        # 通用的to_dict方法说明文档
        """
        转换为字典（通用实现）

        Args:
            exclude: 要排除的字段列表（如 ['password_hash']）
            **kwargs: 额外的参数，用于特殊处理（如 include_password=True）

        Returns:
            字典格式的数据
        """
        # 如果没有传入exclude，则用空列表
        exclude = exclude or []
        # 初始化结果字典
        result = {}

        # 获取当前模型类的所有列定义
        mapper = inspect(self.__class__)
        for column in mapper.columns:
            # 获取列名
            col_name = column.name
            # 排除要忽略的字段
            if col_name in exclude:
                continue

            # 获取字段值
            value = getattr(self, col_name, None)
            # 如果是日期时间类型，调用isoformat转换为字符串
            if hasattr(value, "isoformat"):
                result[col_name] = value.isoformat() if value else None
            else:
                result[col_name] = value

        # 返回字典化后的结果
        return result

    # 统一的repr方法，便于调试打印
    def __repr__(self) -> str:
        # repr方法说明文档
        """
        通用 __repr__ 实现
        子类可以定义 __repr_fields__ 来指定要显示的字段
        如果没有定义，则显示 id 字段
        """
        # 如果子类定义了__repr_fields__，优先显示这些字段
        if hasattr(self, "__repr_fields__"):
            fields = getattr(self, "__repr_fields__")
            attrs = ", ".join(
                f"{field}={getattr(self, field, None)}" for field in fields
            )
        else:
            # 默认显示id字段
            attrs = f"id={getattr(self, 'id', None)}"

        # 返回格式化后的字符串
        return f"<{self.__class__.__name__}({attrs})>"
