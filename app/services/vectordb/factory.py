"""
向量数据库工厂
"""
# 导入日志模块
import logging
# 导入可选类型提示
from typing import Optional
# 导入向量数据库接口基类
from app.services.vectordb.base import VectorDBInterface
# 导入 Chroma 的向量数据库实现
from app.services.vectordb.chroma import ChromaVectorDB
# 导入 Milvus 的向量数据库实现
from app.services.vectordb.milvus import MilvusVectorDB
# 导入全局配置
from app.config import Config

# 获取日志记录器
logger = logging.getLogger(__name__)

# 定义向量数据库工厂类
class VectorDBFactory:
    """向量数据库工厂"""
    # 类属性：用于保存单例实例
    _instance:Optional[VectorDBInterface]=None
    # 类方法：创建向量数据库实例
    @classmethod
    def create_vector_db(
            cls,
            vectordb_type:Optional[str] =None,
            **kwargs
    ) -> VectorDBInterface:
        """
        创建向量数据库实例
        Args:
            vectordb_type: 向量数据库类型 ('chroma' 或 'milvus')，如果为None则从配置读取
            **kwargs: 向量数据库的初始化参数

        Returns:
            向量数据库实例
        """
        # 如果未传入 vectordb_type，则从配置读取，默认 'chroma'
        if vectordb_type is None:
            vectordb_type = getattr(Config,"VECTORDB_TYPE","chroma")

        # 转为小写，统一判断
        vectordb_type = vectordb_type.lower()
        # 如果选择的是 Chroma
        if vectordb_type == "chroma":
            # 获取持久化目录（可选参数）
            persist_directory = kwargs.get("persist_directory")
            # 创建 ChromaVectorDB实例并返回
            return ChromaVectorDB(
                persist_directory=persist_directory
            )
        elif vectordb_type == "milvus":
            # 从 kwargs 获取连接参数，如果没有则使用配置中的默认值

            connection_args = kwargs.get("connection_args")
            if connection_args is None:
                host = getattr(Config,"MILVUS_HOST","localhost")
                port = getattr(Config,"MILVUS_PORT","19530")
                db_name = getattr(Config,"MILVUS_DB_NAME","default")
                uri = f"http://{host}:{port}"
                connection_args = {
                    "uri": uri,
                    "db_name": db_name
                }
            # 创建 MilvusVectorDB 实例，并传入连接参数
            return MilvusVectorDB(connection_args)
        else:
             # 其他类型暂不支持，抛出异常
             raise ValueError(f"Unsupported vector database type: {vectordb_type}")

    # 类方法：获取单例向量数据库实例（懒加载）
    @classmethod
    def get_instance(cls) -> VectorDBInterface:
        """
        获取单例向量数据库实例（懒加载）
        Returns:
            向量数据库实例

        """
        # 如果单例实例为空，则创建
        if cls._instance is None:
            cls._instance = cls.create_vector_db()
        return cls._instance



# 工厂方法：便捷获取向量数据库服务实例
def get_vector_db_service():
    """
    便捷函数：获取向量数据库服务实例
    Returns:
        向量数据库服务实例

    """
    # 返回单例向量数据库实例
    return VectorDBFactory.get_instance()



