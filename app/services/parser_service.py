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
