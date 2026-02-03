# Milvus 向量数据库实现说明
"""
Milvus 向量数据库实现
"""
# 导入日志模块
import logging

# 导入Milvus类
from langchain_milvus import Milvus

# 导入类型提示相关模块
from typing import List, Dict, Optional, Any

# 导入LangChain的文档类型
from langchain_core.documents import Document

# 导入向量数据库接口基类
from app.services.vectordb.base import VectorDBInterface

# 导入Embedding工厂方法
from app.utils.embedding_factory import EmbeddingFactory
from test import vectorstore

# 获取日志记录器
logger = logging.getLogger(__name__)


# 定义 Milvus 向量数据库实现类，继承接口基类
class MilvusVectorDB(VectorDBInterface):
    """Milvus 向量数据库实现"""

    # 初始化方法，设置连接参数和embedding模型
    def __init__(self, connection_args: Optional[Dict] = None):
        """
        初始化 Milvus 服务

        Args:
            connection_args: Milvus连接参数，例如：
                {'host': 'localhost', 'port': '19530'}
        """
        # 如果没有传递连接参数，则使用默认主机和端口
        if connection_args is None:
            connection_args = {"uri": "http://localhost:19530", "db_name": "default"}
        # 保存连接参数到实例
        self.connection_args = connection_args

        # 动态创建 Embedding 模型
        self.embeddings = EmbeddingFactory.create_embeddings()
        # 打印初始化日志
        logger.info(f"Milvus 已初始化, 连接参数: {connection_args}")

    # 获取或创建 Milvus 向量集合的方法
    def get_or_create_collection(self, collection_name: str) -> Any:
        """获取或创建向量存储"""
        # 拷贝一份连接参数，检查端口类型
        connection_args = self.connection_args.copy()
        # 创建 Milvus 向量存储对象，如果集合不存在会自动创建
        # LangChain Milvus 会自动处理集合、索引创建和加载
        vectorstore = Milvus(
            collection_name=collection_name,  # 集合名称
            embedding_function=self.embeddings,  # embedding模型
            connection_args=connection_args,  # 连接参数
        )

        # 如果集合对象有 _collection 属性，尝试加载已有集合（如果已经存在）
        if hasattr(vectorstore, "_collection"):
            try:
                # 尝试加载集合
                vectorstore._collection.load()
                logger.debug(f"已加载 Milvus 集合 {collection_name}")
            except Exception as e:
                # 集合不存在或为空时输出Debug日志
                logger.debug(f"集合 {collection_name} 可能不存在或为空: {e}")

        # 返回vectorstore对象
        return vectorstore

    # 添加文档到 Milvus 的方法
    def add_documents(
        self,
        collection_name: str,
        documents: List[Document],
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """添加文档到向量存储"""
        # 获取（或创建）对应的集合
        vectorstore = self.get_or_create_collection(collection_name)

        try:
            # 指定了ID则传入，否则直接添加
            if ids:
                result_ids = vectorstore.add_documents(documents=documents, ids=ids)
            else:
                result_ids = vectorstore.add_documents(documents=documents)

            # 确保数据写入并刷新到磁盘
            # 通过内部 _collection 对象手动刷新
            if hasattr(vectorstore, "_collection"):
                vectorstore._collection.flush()  # 刷新集合
                logger.debug(f"已刷新 Milvus 集合 {collection_name}")

            # 记录添加文档的日志
            logger.info(
                f"已向 Milvus 集合 {collection_name} 添加 {len(documents)} 个文档"
            )
            return result_ids  # 返回结果
        except Exception as e:
            # 添加失败时打印错误日志并抛出异常
            logger.error(
                f"向 Milvus 集合 {collection_name} 添加文档时出错: {e}", exc_info=True
            )
            raise

    # 删除文档的方法
    def delete_documents(
        self,
        collection_name: str,
        ids: Optional[List[str]] = None,
        filter: Optional[Dict] = None,
    ) -> None:
        """删除文档"""
        # 获取（或创建）指定名称的向量集合
        vectorstore = self.get_or_create_collection(collection_name)
        # 如果传入了ids，按id删除文档
        if ids:
            vectorstore.delete(ids=ids)
        # 如果传入了filter，根据过滤条件删除文档
        elif filter:
            # 构造Milvus的表达式字符串，这里只处理doc_id的情况
            expr = f'doc_id=="{filter["doc_id"]}"'
            vectorstore.delete(expr=expr)
        # ids和filter都未传，抛出异常
        else:
            raise ValueError(f"你既没有传ids,也没有传filter")
        # 如果集合对象有_collection属性，则刷新集合，保证删除操作落盘
        if hasattr(vectorstore, "_collection"):
            vectorstore._collection.flush()
        # 记录删除操作的日志
        logger.info(f"已经从ChromDB集合{collection_name}删除文档")

    # 定义相似度搜索方法
    def similarity_search(
        self,
        collection_name: str,
        query: str,
        k: int = 5,
        filter: Optional[Dict] = None,
    ) -> List[Document]:
        """相似度搜索"""
        vectorstore = self.get_or_create_collection(collection_name)
        # 检查集合是否已被加载（LangChain Milvus 一般自动处理，这里显式保证）
        if hasattr(vectorstore, "_collection"):
            try:
                # 显式加载集合
                vectorstore._collection.load()
            except Exception as e:
                # 如果加载失败或已加载，记录到 debug 日志
                logger.debug(f"集合可能已加载或加载失败: {e}")
        # 如果指定了过滤条件
        if filter:
            # 使用过滤条件表达式地相似度搜索
            results = vectorstore.similarity_search(query=query, k=k, expr=filter)
        else:
            # 不带过滤条件，直接搜索
            results = vectorstore.similarity_search(query=query, k=k)
        # 返回搜索结果
        return results

    # 定义带分数的相似度搜索方法
    def similarity_search_with_score(
        self,
        collection_name: str,
        query: str,
        k: int = 5,
        filter: Optional[Dict] = None,
    ) -> List[tuple]:
        """带分数的相似度搜索方法"""
        vectorstore = self.get_or_create_collection(collection_name)
        # 检查集合是否已被加载（LangChain Milvus 一般自动处理，这里显式保证）
        if hasattr(vectorstore, "_collection"):
            try:
                # 显式加载集合
                vectorstore._collection.load()
            except Exception as e:
                # 如果加载失败或已加载，记录到 debug 日志
                logger.debug(f"集合可能已加载或加载失败: {e}")
        # 如果传递了过滤条件
        if filter:
            # 根据过滤条件构造Milvus的过滤表达式，只支持doc_id精准查询
            expr = f'doc_id == "{filter["doc_id"]}"'
            # 带过滤表达式执行相似度检索，并拿到分数
            results = vectorstore.similarity_search_with_score(
                query=query, k=k, expr=expr
            )
            print("filter_results", len(results))
        else:
            # 如果没有过滤条件，直接执行检索
            results = vectorstore.similarity_search_with_score(query=query, k=k)
        return results
