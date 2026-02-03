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
from test import vectorstore

# 获取日志记录器
logger = logging.getLogger(__name__)


# 定义 Chroma 向量数据库实现类
class ChromaVectorDB(VectorDBInterface):
    # 初始化方法
    def __init__(self, persist_directory: Optional[str] = None):
        """
        初始化 ChromaDB 服务
        Args:
            persist_directory: 持久化目录，如果为None则使用配置中的值
        """
        # 如果持久化目录为 None，则从配置读取
        if persist_directory is None:
            persist_directory = Config.CHROMA_PERSIST_DIRECTORY
        # 设置持久化目录属性
        self.persist_directory = persist_directory
        # 动态创建Embedding模型
        self.embeddings = EmbeddingFactory.create_embeddings()
        # 记录 ChromaDB 初始化信息
        logger.info(f"ChromaDB 已初始化, 持久化目录: {persist_directory}")

    # 获取或创建集合（向量存储）
    def get_or_create_collection(self, collection_name: str) -> Chroma:
        # 获取或创建向量存储对象
        vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory,
        )
        return vectorstore

    # 向向量存储添加文档
    def add_documents(
        self,
        collection_name: str,
        documents: List[Document],
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        # 获取集合
        vectorstore = self.get_or_create_collection(collection_name)
        # 如果指定了ids
        if ids:
            # # 添加文档，指定 ids
            result_ids = vectorstore.add_documents(documents=documents, ids=ids)
        else:
            # 添加文档，不指定ids
            result_ids = vectorstore.add_documents(documents=documents)
        # 记录日志，添加文档
        logger.info(
            f"已向 ChromaDB 集合 {collection_name} 添加 {len(documents)} 个文档"
        )
        # 返回已添加文档的id列表
        return result_ids

    # 删除文档
    def delete_documents(
        self,
        collection_name: str,
        ids: Optional[List[str]] = None,
        filter: Optional[Dict] = None,
    ) -> None:
        vectorstore = self.get_or_create_collection(collection_name)
        if ids:
            vectorstore.delete(ids)
        elif filter:
            # ChromaDB 不支持直接使用 filter 参数删除
            # 需要先查询出符合条件的文档 IDs，然后删除
            try:
                collectin = vectorstore._collection
                # 使用 where 条件查询匹配的文档
                # filter 格式: {"doc_id": "xxx"}
                where = filter
                results = collectin.get(where=where)
                if results and "ids" in results and results["ids"]:
                    matched_ids = results["ids"]
                    vectorstore.delete(ids=matched_ids)
                    logger.info(f"已通过filter条件删除{len(matched_ids)}个文档")
                else:
                    logger.info(f"未找到匹配filter条件的文档，无需删除")
            except Exception as e:
                logger.error(f"使用filter删除文档时出错: {e}", exc_info=True)
                raise
        else:
            raise ValueError(f"你既没有传ids,也没有传filter")
        logger.info(f"已经从ChromDB集合{collection_name}删除文档")

    def similarity_search(
        self,
        collection_name: str,
        query: str,
        k: int = 5,
        filter: Optional[Dict] = None,
    ) -> List[Document]:
        """相似度搜索"""
        # 获取或创建集合对应的向量存储对象
        vectorstore = self.get_or_create_collection(collection_name)
        # 如果指定了过滤条件
        if filter:
            # 带过滤条件地执行相似度搜索
            results = vectorstore.similarity_search(query=query, k=k, filter=filter)
        else:
            # 不带过滤条件地执行相似度搜索
            results = vectorstore.similarity_search(query=query, k=k)
        # 返回搜索结果
        return results

    # 定义带分数地相似度搜索方法
    def similarity_search_with_score(
        self,
        collection_name: str,
        query: str,
        k: int = 5,
        filter: Optional[Dict] = None,
    ) -> List[tuple]:
        """用于执行带分数的相似度搜索"""
        vectorstore = self.get_or_create_collection(collection_name)
        if filter:
            results = vectorstore.similarity_search_with_score(
                query=query, k=k, filter=filter
            )
        else:
            results = vectorstore.similarity_search_with_score(query=query, k=k)
        return results
