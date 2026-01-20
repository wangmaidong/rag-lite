# 基础服务类
"""
基础服务类
"""
# 导入日志库
import logging

# 导入可选类型、泛型、类型变量和类型别名
from typing import Optional, TypeVar, Generic, Dict, Any

# 导入数据库会话和事务管理工具
from app.utils.db import db_session, db_transaction

# 创建日志记录器
logger = logging.getLogger(__name__)

# 定义泛型的类型变量
T = TypeVar("T")


# 定义基础服务类，支持泛型
class BaseService(Generic[T]):
    # 基础服务类，提供通用的数据库操作方法
    # 初始化方法
    def __init__(self):
        # 初始化服务和日志记录器
        self.logger = logging.getLogger(self.__class__.__name__)

    # 数据库会话上下文管理器（只读）
    def session(self):
        """
        数据库会话上下文管理器（只读操作，不自动提交）
        使用示例:
            with self.session() as db:
                result = db.query(Model).all()
                # 不需要手动关闭 session
        """
        return db_session()

    # 数据库事务上下文管理器（自动提交）
    def transaction(self):
        """
        数据库事务上下文管理器（自动提交，出错时回滚）
        使用示例:
            with self.transaction() as db:
                obj = Model(...)
                db.add(obj)
                # 自动提交，出错时自动回滚
        """
        # 返回数据库事务
        return db_transaction()

    def get_by_id(self, model_class: T, entity_id: str):
        with self.session() as db_session:
            try:
                return (
                    db_session.query(model_class)
                    .filter(model_class.id == entity_id)
                    .first()
                )
            except Exception as e:
                self.logger.error("获取ID对应的对象失败:{e}")
                return None
