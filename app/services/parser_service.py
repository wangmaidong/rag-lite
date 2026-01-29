"""
文档解析服务
使用 LangChain 的文档加载器
"""

# 导入日志模块
import logging

# 导入类型注解 List
from typing import List

# 导入 LangChain 的 Document 类型
from langchain_core.documents import Document

# 导入自定义的文档加载器
from app.utils.document_loader import DocumentLoader

# 获取日志记录器
logger = logging.getLogger(__name__)

# 定义文档解析服务类
class ParserService:
    """文档解析服务（使用 LangChain）"""
    # 统一解析接口，返回 LangChain Document 列表
    def parse(self, file_data:bytes, file_type:str) -> List[Document]:
        """
        统一解析接口（返回 LangChain Document 列表）
        Args:
            file_data: 文件数据（bytes）
            file_type: 文件类型（pdf/docx/txt/md）

        Returns:
            LangChain Document 列表
        """
        # 将文件类型转换成小写，便于统一处理
        file_type = file_type.lower()
        # 调用文档加载器，加载文档并返回 Document 列表
        return DocumentLoader.load(file_data, file_type)


# 创建 ParserService 的单例实例
parser_service = ParserService()