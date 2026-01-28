"""
文档加载器
"""

# 导入日志模块
import logging

# 导入类型注解
from typing import List

# 导入LangChain社区的文档加载器
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader

# 导入LangChain核心Document类型
from langchain_core.documents import Document

# 导入临时文件工具
from tempfile import NamedTemporaryFile

# 导入os模块
import os

# 获取日志记录器
logger = logging.getLogger(__name__)


# 定义文档加载器类
class DocumentLoader:
    """文档加载器封装"""

    @staticmethod
    def load_pdf(file_data: bytes) -> List[Document]:
        """
        加载 PDF 文档
        :param file_data: PDF 文件数据（bytes）
        :return: Document 列表
        """
        # 异常捕获，避免加载出错崩溃
        try:
            # 创建一个临时pdf文件，内容写入
            with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(file_data)
                tmp_path = tmp_file.name
            # 内部try/finally保证文件最终被删除
            try:
                # 加载PDF文件为Document对象
                loader = PyPDFLoader(tmp_path)
                documents = loader.load()
                return documents
            finally:
                # 删除临时文件
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

            pass
        except Exception as e:
            # 打印并抛出加载错误
            logger.error(f"加载 PDF 时出错: {e}")
            raise ValueError(f"Failed to load PDF: {str(e)}")
