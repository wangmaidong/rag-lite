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

# 导入配置项
from app.config import Config

# 定义DocumentService服务类，继承自BaseService


class DocumentService(BaseService[DocumentModel]):
    """文档服务"""

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


# 实例化DocumentService
document_service = DocumentService()
