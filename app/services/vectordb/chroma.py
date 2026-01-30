"""
ChromaDB 向量数据库实现
"""
# 导入日志模块
import logging
# 导入需要的类型提示
from typing import List, Dict, Optional, Any
# 导入LangChain 的 Chroma类
from langchain_chroma import Chroma
# 导入Document类
from langchain_core.documents import Document
# 导入向量数据库接口基类
from app.services.vectordb.base import VectorDBInterface
# 导入全局配置
from app.config import Config
# 导入嵌入模型工厂
from app.utils.embedding_factory import EmbeddingFactory
# 获取日志记录器
logger = logging.getLogger(__name__)

# 定义 Chroma 向量数据库实现类
class ChromaVectorDB(VectorDBInterface):
    # 初始化方法
    def __init__(
            self,
            persist_directory:Optional[str]=None
    ):
        """
        初始化 ChromaDB 服务
        Args:
            persist_directory: 持久化目录，如果为None则使用配置中的值
        """
        # 如果持久化目录为 None，则从配置读取
        if persist_directory is None:
            persist_directory = Config