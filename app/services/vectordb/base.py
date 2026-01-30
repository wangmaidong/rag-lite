"""
向量数据库抽象接口
"""
# 导入 abc 库，定义抽象基类和抽象方法
from abc import ABC, abstractmethod
# 导入类型提示：列表、字典、可选和任意类型
from typing import List, Dict, Optional, Any
# 导入 LangChain 的 Document 类，用于文档对象
from langchain_core.documents import Document

# 定义一个向量数据库的抽象接口，继承自 ABC 抽象基类
class VectorDBInterface(ABC):
    """向量数据库抽象接口"""

    # 定义抽象方法：获取或创建集合
    @abstractmethod
    def get_or_create_collection(self, collection_name: str) -> Any:
        """
        获取或创建集合

        Args:
            collection_name: 集合名称

        Returns:
            向量存储对象
        """
        # 子类需要实现具体逻辑
        pass

    # 定义抽象方法：向向量存储中添加文档
    @abstractmethod
    def add_documents(self, collection_name: str, documents: List[Document],
                     ids: Optional[List[str]] = None) -> List[str]:
        """
        添加文档到向量存储

        Args:
            collection_name: 集合名称
            documents: Document 列表
            ids: 文档ID列表（可选）

        Returns:
            添加的文档ID列表
        """
        # 子类需要实现具体逻辑
        pass
    # 定义抽象方法：删除指定的文档
    @abstractmethod
    def delete_documents(self, collection_name: str, ids: Optional[List[str]] = None,
                        filter: Optional[Dict] = None) -> None:
        """
        删除文档

        Args:
            collection_name: 集合名称
            ids: 要删除的文档ID列表（可选）
            filter: 过滤条件（可选）
        """
        # 子类需要实现具体逻辑
        pass
