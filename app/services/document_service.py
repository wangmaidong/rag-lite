# 导入os模块，用于处理文件和路径
import os

# 导入uuid模块，用于生成唯一ID
import uuid

# 导入类型提示
from typing import List, Optional, Dict

# 导入线程池，用于异步处理文档
from concurrent.futures import ThreadPoolExecutor

# 导入BaseService基类
from app.services.base_service import BaseService

# 导入Document模型，重命名为DocumentModel
from app.models.document import Document as DocumentModel

# 导入Knowledgebase知识库模型
from app.models.knowledgebase import Knowledgebase

# 导入存储服务
from app.services.storage_service import storage_service

# 导入解析服务
from app.services.parser_service import ParserService, parser_service

# 导入配置项
from app.config import Config

# 导入文本分割器
from app.utils.text_splitter import TextSplitter

# 导入LangChain文档对象
from langchain_core.documents import Document

# 导入向量数据库服务
from app.services.vector_service import vector_service

# 定义DocumentService服务类，继承自BaseService


class DocumentService(BaseService[DocumentModel]):
    """文档服务"""

    def __init__(self):
        """初始化服务"""
        super().__init__()
        self.executor = ThreadPoolExecutor(max_workers=4)

    # 上传文档方法
    def upload(self, kb_id: str, file_data: bytes, filename: str) -> dict:
        """
        上传文档
        :param kb_id:知识库ID
        :param file_data:文件数据
        :param filename:文件名
        :return: 创建的文档字典
        """
        # 初始化变量，标识文件是否已经上传
        file_uploaded = False
        # 初始化文件路径
        file_path = None
        try:
            # 使用数据库会话，判断知识库是否存在
            with self.session() as session:
                kb = (
                    session.query(Knowledgebase)
                    .filter(Knowledgebase.id == kb_id)
                    .first()
                )
                # 如果知识库不存在，抛出异常
                if not kb:
                    raise ValueError(f"知识库{kb_id}不存在")
            # 检查文件名是否为空或者没有扩展名
            if not filename or "." not in filename:
                raise ValueError(f"文件名必须包含扩展名: {filename}")
            # 获取文件扩展名
            file_ext = os.path.splitext(filename)[1]
            # 如果有后缀，去掉点号并转为小写
            if file_ext:
                file_ext = file_ext[1:].lower()
            else:
                # 如果没有文件后缀，抛出异常
                raise ValueError(f"文件名必须包含扩展名: {filename}")
            # 检查文件类型是否合法
            if not file_ext or file_ext not in Config.ALLOWED_EXTENSIONS:
                raise ValueError(
                    f"不支持的文件类型: '{file_ext}'。允许类型: {', '.join(Config.ALLOWED_EXTENSIONS)}"
                )
            # 生成文档ID，用于标识唯一文档
            doc_id = uuid.uuid4().hex[:32]
            # 构建文件存储路径，便于后续文件操作
            file_path = f"documents/{kb_id}/{doc_id}/{filename}"
            # 优先将文件上传到本地/云存储，保证文件存在再创建记录
            try:
                storage_service.upload_file(file_path, file_data)
                file_uploaded = True
            except Exception as storage_error:
                # 上传存储失败时写入日志并抛出异常
                self.logger.error(f"上传文件到存储时发生错误: {storage_error}")
                raise ValueError(f"文件上传失败: {str(storage_error)}")
            # 在数据库中创建文档记录
            with self.transaction() as session:
                doc = DocumentModel(
                    id=doc_id,
                    kb_id=kb_id,
                    name=filename,
                    file_path=file_path,
                    file_type=file_ext,
                    file_size=len(file_data),
                    status="pending",
                )
                # 添加文档记录到会话
                session.add(doc)
                # Flush 保证数据同步到数据库
                session.flush()
                # 刷新文档对象，获取新写入的数据
                session.refresh(doc)
                # 对象转dict，避免对象分离后后续属性访问失败
                doc_dict = doc.to_dict()
                # 日志记录上传成功
                self.logger.info(f"文档上传成功：{doc.id}")
            # 返回新创建的文档字典信息

            return doc_dict
        except Exception as e:
            # 异常处理，如果文件已上传但事务失败，则尝试删除已上传的文件
            if file_uploaded and file_path:
                try:
                    storage_service.delete_file(file_path)
                except Exception as delete_error:
                    self.logger.warning(f"删除已上传文件时出错: {delete_error}")
            # 重新抛出异常
            raise

    # 定义根据知识库ID获取文档列表的方法
    def list_by_kb(
        self,
        kb_id: str,
        page: int = 1,
        page_size: int = 10,
        status: Optional[str] = None,
    ) -> Dict:
        """获取知识库的文档列表"""
        # 创建数据库会话
        with self.session() as session:
            # 查询指定知识库ID下的所有文档
            query = session.query(DocumentModel).filter(DocumentModel.kb_id == kb_id)
            # 如果设置了文档状态，则对状态进行过滤
            if status:
                query = query.filter(DocumentModel.status == status)
            # 使用分页方法返回结果，按创建时间倒序排列
            return self.paginate_query(
                query,
                page=page,
                page_size=page_size,
                order_by=DocumentModel.created_at.desc(),
            )

    # 定义处理单个文档的方法（手动触发处理）
    def process(self, doc_id: str):
        """
        处理文档（手动触发）
        :param doc_id: 文档ID
        :return:
        """
        # 创建数据库会话，检查文档是否存在
        with self.session() as session:
            # 根据doc_id查询文档对象
            doc = (
                session.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
            )
            # 如果文档不存在则抛出异常
            if not doc:
                raise ValueError(f"Document {doc_id} not found")
        # 记录已经提交文档处理任务的日志
        self.logger.info(f"提交文档处理任务: {doc_id}")
        # 在线程池中异步提交处理任务
        future = self.executor.submit(self._process_document, doc_id)

        # 定义异常回调函数，用于捕获子线程中的异常
        def exception_callback(future):
            try:
                # 获取异步线程的执行结果，发生异常会在此抛出
                future.result()
            except Exception as e:
                # 记录错误日志及异常堆栈信息
                self.logger.error(
                    f"文档处理任务异常: {doc_id}, 错误: {e}", exc_info=True
                )

        # 给future对象添加回调函数，任务结束时自动处理异常
        future.add_done_callback(exception_callback)

    # 文档实际处理方法（在子线程中执行，异步）
    def _process_document(self, doc_id: str):
        """
        处理文档（异步）
        Args:
            doc_id: 文档ID

        Returns:

        """
        try:
            # 日志：文档处理任务开始
            self.logger.info(f"开始处理文档：{doc_id}")
            # 首先开启事务，获取文档信息和知识库配置并更新文档初始状态
            with self.transaction() as session:
                # 查询文档对象
                doc: DocumentModel = (
                    session.query(DocumentModel)
                    .filter(DocumentModel.id == doc_id)
                    .first()
                )
                # 未找到文档则输出日志并返回
                if not doc:
                    self.logger.error(f"未找到文档{doc_id}")
                    return
                # 若文档已被处理过（完成或失败），则需重置状态
                need_cleanup = doc.status in ["completed", "failed"]
                if need_cleanup:
                    # 重置状态为待处理，分块数归零、错误信息清除
                    doc.status = "pending"
                    doc.chunk_count = 0
                    doc.error_message = None
                # 更新为正在处理状态
                doc.status = "processing"
                # 刷新到数据库(写入未提交)
                session.flush()
                # 提前取出相关数据，避免事务作用域外对象失效
                kb_id = doc.kb_id
                file_path = doc.file_path
                file_type = doc.file_type
                doc_name = doc.name
                collection_name = f"kb_{doc.kb_id}" if need_cleanup else None
                # 查询知识库配置
                kb: Knowledgebase = (
                    session.query(Knowledgebase)
                    .filter(Knowledgebase.id == kb_id)
                    .first()
                )
                # 未找到知识库抛出异常
                if not kb:
                    raise ValueError(f"知识库 {kb_id} 未找到")
                # 获取知识库分块参数
                kb_chunk_size = kb.chunk_size
                kb_chunk_overlap = kb.chunk_overlap

            # 如果需要清理旧分块和向量，则在事务作用域外先进行删除，避免占用数据库连接
            if need_cleanup:
                try:
                    # 调用向量服务，则删除指定集合、指定文档ID下的所有向量数据
                    vector_service.delete_documents(
                        collection_name=collection_name, filter={"doc_id": doc_id}
                    )
                    # 输出信息日志，标明文档的旧向量已被删除
                    self.logger.info(f"已删除文档 {doc_id} 的旧向量")
                except Exception as e:
                    # 如果删除操作出错，则记录警告日志
                    self.logger.warning(f"删除向量时出错: {e}")

            # 日志：文档已标记为处理中
            self.logger.info(f"文档 {doc_id} 状态已更新为 processing（处理中）")
            # 从存储中下载文件内容
            file_data = storage_service.download_file(file_path)
            # 解析文件，根据类型抽取原始文本内容
            langchain_docs = parser_service.parse(file_data, file_type)
            # 若抽取出的文本为空，则抛出异常
            if not langchain_docs:
                raise ValueError(f"未能抽取到任何文本内容")
            # 创建文本分块器，指定知识库参数
            splitter = TextSplitter(
                chunk_size=kb_chunk_size, chunk_overlap=kb_chunk_overlap
            )
            # 将文档内容分块
            chunks = splitter.split_documents(langchain_docs, doc_id=doc_id)
            # 如果分块失败，抛出异常
            if not chunks:
                raise ValueError("文档未能成功分块")
            # 初始化一个列表用于存放转换后的 LangChain Document 对象
            documents = []
            # 遍历所有分块，将每个分块转换为 LangChain Document 对象
            for chunk in chunks:
                # 创建一个 LangChain Document，包含文本内容和相关元数据
                doc_obj = Document(
                    page_content=chunk["text"],
                    metadata={
                        "doc_id": doc_id,
                        "doc_name": doc_name,
                        "chunk_index": chunk["chunk_index"],
                        "id": chunk["id"],
                        "chunk_id": chunk["id"],
                    },
                )
                # 将生成的 Document 对象加入到 documents 列表
                documents.append(doc_obj)
            # 构造向量库集合名称，格式为 kb_知识库ID
            collection_name = f"kb_{kb_id}"
            # 提取所有分块的ID,用于向量存储
            ids = [chunk["id"] for chunk in chunks]
            # 调用向量服务，将分块后的文档写入向量库
            vector_service.add_documents(
                collection_name=collection_name, documents=documents, ids=ids
            )
            # 再次开启事务，更新文档状态为完成，记录分块数
            with self.transaction() as session:
                doc = (
                    session.query(DocumentModel)
                    .filter(DocumentModel.id == doc_id)
                    .first()
                )
                if doc:
                    doc.status = "completed"  # 完成状态
                    doc.chunk_count = len(chunks)  # 分块数
            # 日志：处理完成，输出分块数
            self.logger.info(f"文档处理完成: {doc_id}, 分块数量: {len(chunks)}")
        except Exception as e:
            # 捕获异常后，更新文档状态为失败，并记录错误信息（限长）
            with self.transaction() as session:
                # 查询文档对象
                doc = (
                    session.query(DocumentModel)
                    .filter(DocumentModel.id == doc_id)
                    .first()
                )
                # 如果文档存在，则更新状态为失败，并记录错误信息（限长）
                if doc:
                    doc.status = "failed"
                    doc.error_message = str(e)[:500]
            # 记录处理失败的日志
            self.logger.error(f"处理文档 {doc_id} 时发生错误: {e}")

    def delete(self, doc_id):
        """
        删除文档
        包括：删除向量数据库中的向量数据、删除存储中的文件、删除数据库记录
        Args:
            doc_id:

        Returns:

        """
        with self.session() as session:
            doc = (
                session.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
            )
            if not doc:
                raise ValueError(f"文档{doc_id}不存在")

            # 保存需要删除的信息
            kb_id = doc.kb_id
            file_path = doc.file_path
            collection_name = f"kb_{kb_id}"
        # 1. 删除向量数据库中的相关向量数据
        try:
            vector_service.delete_documents(
                collection_name=collection_name, filter={"doc_id": doc_id}
            )
            self.logger.info(f"已删除文档{doc_id}的向量数据")
        except Exception as e:
            self.logger.warning(f"删除向量数据失败：{e}")
        # 2. 删除存储中的文件
        if file_path:
            try:
                storage_service.delete_file(file_path)
                self.logger.info(f"已删除文档{doc_id}的存储文件:{file_path}")
            except Exception as e:
                self.logger.warning(f"删除存储文件失败:{e}")
        # 3. 删除数据库记录
        with self.transaction() as session:
            doc = (
                session.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
            )
            if doc:
                session.delete(doc)
                self.logger.info(f"已删除文档{doc_id}的数据库记录")


# 实例化DocumentService
document_service = DocumentService()
