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

    @staticmethod
    def load_docx(file_data: bytes) -> List[Document]:
        """
        加载 DOCX 文档
        Args:
            file_data:DOCX 文件数据（bytes）

        Returns:
            Document 列表
        """
        # 异常捕获
        try:
            # 再次导入本地模块，保险起见
            # 创建临时docx文件，写入内容
            with NamedTemporaryFile(delete=False, suffix=".docx") as tmp_file:
                tmp_file.write(file_data)
                tmp_path = tmp_file.name
            # 加载和清理临时文件
            try:
                # 加载DOCX为Document对象列表
                loader = Docx2txtLoader(tmp_path)
                documents = loader.load()
                return documents
            finally:
                # 删除临时文件
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        except Exception as e:
            # 日志抛出异常
            logger.error(f"加载DOCX时出错：{e}")
            raise ValueError(f"Failed to load DOCX: {str(e)}")

    @staticmethod
    def load_text(file_data: bytes, encoding: str = "utf-8") -> List[Document]:
        """
        加载文本文件
        Args:
            file_data:文本文件数据（bytes）
            encoding:文件编码

        Returns:
            Document 列表

        """
        # 总体异常捕获
        try:
            # 写入临时txt文件（二进制写模式）
            with NamedTemporaryFile(delete=False, suffix=".txt", mode="wb") as tmp_file:
                tmp_file.write(file_data)
                tmp_path = tmp_file.name
            # 加载过程及编码兜底
            try:
                # 优先尝试指定的编码
                loader = TextLoader(tmp_path, encoding=encoding)
                documents = loader.load()
                return documents
            except UnicodeDecodeError:
                # 编码失败自动用gbk重试
                try:
                    loader = TextLoader(tmp_path, encoding="gbk")
                    documents = loader.load()
                    return documents
                except Exception as e:
                    # 日志并抛错
                    logger.error(f"加载文本文件时出错: {e}")
                    raise ValueError(f"Failed to load text file: {str(e)}")
            finally:
                # 删除临时文件
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        except Exception as e:
            # 加载文本异常
            logger.error(f"加载文本时出错：{e}")
            raise ValueError(f"Failed to load text: {str(e)}")

    @staticmethod
    def load(file_data: bytes, file_type: str) -> List[Document]:
        """
        统一加载接口
        Args:
            file_data: 文件数据（bytes）
            file_type: 文件类型（pdf/docx/txt/md）

        Returns:
            Document 列表
        """
        # 文件类型小写化，统一处理
        file_type = file_type.lower()
        # PDF文件
        if file_type == "pdf":
            return DocumentLoader.load_pdf(file_data)
        # DOCX文件
        elif file_type == "docx":
            return DocumentLoader.load_docx(file_data)
        # 文本文件/markdown
        elif file_type in ["txt", "md"]:
            return DocumentLoader.load_text(file_data)
        else:
            # 不支持文件类型抛异常
            raise ValueError(f"Unsupported file type: {file_type}")
