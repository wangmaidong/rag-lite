"""
文本分割器
"""
# 导入日志模块
import logging
# 导入类型提示
from typing import List
# 导入递归字符切分器
from langchain_text_splitters import RecursiveCharacterTextSplitter
# 导入文档对象
from langchain_core.documents import Document

# 定义日志记录器
logger = logging.getLogger(__name__)

# 定义文本分割器类
class TextSplitter:
    """文本分割器封装"""
    def __init__(
            self,
            chunk_size:int=512,
            chunk_overlap:int=50
    ):
        """
        初始化文本分割器
        Args:
            chunk_size:每个块的最大字符数
            chunk_overlap:块之间的重叠字符数
        """
        # 设置块的大小
        self.chunk_size = chunk_size
        # 设置块之间的重叠字符数
        self.chunk_overlap = chunk_overlap
        # 创建递归字符分割器实例，并设置分割参数
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", ". ", "! ", "? ", " ", ""]#分隔符
        )

    # 分割文档列表为若干块
    def split_documents(
            self,
            documents:List[Document],
            doc_id:str=None
    ) -> List[dict]:
        """
        分割文档列表
        Args:
            documents: Document 列表
            doc_id: 文档ID（用于生成块ID）

        Returns:
            块列表，每个块包含 id, text, chunk_index, metadata
        """
        # 如果文档为空，直接返回空列表
        if not documents:
            return []
        # 使用分割器分割文档
        chunks = self.splitter.split_documents(documents)

        # 结果列表
        result = []
        # 遍历每个分割快
        for i, chunk in enumerate(chunks):
            # 生成块ID，包含文档ID和序号
            chunk_id = f"{doc_id}_{i}" if doc_id else str(i)
            # 把快信息添加到结果中
            result.append({
                "id": chunk_id,# 块ID
                "text": chunk.page_content,# 块文本内容
                "chunk_index": i,# 块索引
                "metadata": chunk.metadata# 块元数据
            })
        return result
