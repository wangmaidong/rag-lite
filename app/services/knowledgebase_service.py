# 从基础服务导入BaseService类
from app.services.base_service import BaseService

# 从模型模块导入Knowledgebase类
from app.models.knowledgebase import Knowledgebase
# 从模型模块导入Document类
from app.models.document import Document as DocumentModel

# 导入类型说明
from typing import Optional, Dict

import os
from app.config import Config

# 导入存储服务
from app.services.storage_service import storage_service

# 导入向量服务
from app.services.vector_service import vector_service

from typing import List

# 定义KnowledgebaseService服务类，继承自BaseService，泛型参数为Knowledgebase
class KnowledgebaseService(BaseService[Knowledgebase]):
    """知识库服务"""

    # 定义创建知识库的方法
    def create(
        self,
        name: str,
        user_id: str,
        description: str = None,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        cover_image_data: bytes = None,
        cover_image_filename: str = None,
    ) -> dict:
        """
        创建知识库
        :param name: 知识库名称
        :param user_id: 用户ID
        :param description: 描述
        :param chunk_size: 分块大小
        :param chunk_overlap: 分块重叠
        :param cover_image_data: 封面图片数据（可选）
        :param cover_image_filename: 封面图片文件名（可选）
        :return:
            创建的知识库字典

        Args:
            cover_image_data:
        """
        cover_image_path = None
        # 处理封面图片上传
        if cover_image_data and cover_image_filename:
            # 验证文件类型
            file_ext_without_dot = (
                os.path.splitext(cover_image_filename)[1][1:].lower()
                if "." in cover_image_filename
                else ""
            )
            if not file_ext_without_dot:
                raise ValueError(f"文件名缺少扩展名: {cover_image_filename}")
            if file_ext_without_dot not in Config.ALLOWED_IMAGE_EXTENSIONS:
                raise ValueError(
                    f"不支持的图片格式: {file_ext_without_dot}。支持的格式: {', '.join(Config.ALLOWED_IMAGE_EXTENSIONS)}"
                )
            # 验证文件大小
            if len(cover_image_data) == 0:
                raise ValueError("上传的图片文件为空")
            if len(cover_image_data) > Config.MAX_IMAGE_SIZE:
                raise ValueError(
                    f"图片文件大小超过限制 {Config.MAX_IMAGE_SIZE / 1024 / 1024}MB"
                )
        # 启动数据库事务，上下文管理器自动处理提交或回滚
        with self.transaction() as session:
            # 先创建知识库对象
            kb = Knowledgebase(
                name=name,
                user_id=user_id,
                description=description,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
            # 将知识库对象添加到session
            session.add(kb)
            # 刷新session，生成知识库ID， 刷新以获取 ID，但不提交
            session.flush()
            # 上传封面图片（如果有）
            if cover_image_data and cover_image_filename:
                try:
                    # 构建封面图片路径（统一使用小写扩展名）
                    file_ext_with_dot = os.path.splitext(cover_image_filename)[
                        1
                    ].lower()
                    cover_image_path = f"covers/{kb.id}{file_ext_with_dot}"
                    self.logger.info(
                        f"正在为新知识库 {kb.id} 上传封面图片: "
                        f"文件名={cover_image_filename}, "
                        f"路径={cover_image_path}, "
                        f"大小={len(cover_image_data)} 字节"
                    )
                    # 上传到存储
                    storage_service.upload_file(cover_image_path, cover_image_data)
                    # 验证文件是否成功上传
                    if not storage_service.file_exists(cover_image_path):
                        raise ValueError(f"上传后文件不存在: {cover_image_path}")

                    self.logger.info(f"成功上传封面图片: {cover_image_path}")
                    # 更新知识库的封面路径
                    kb.cover_image = cover_image_path
                    session.flush()
                    pass
                except Exception as e:
                    self.logger.error(
                        f"上传知识库 {kb.id} 的封面图片时出错: {e}", exc_info=True
                    )
                    cover_image_path = None
            # 刷新kb对象的数据库状态
            session.refresh(kb)
            # 转换 kb 对象为字典，(在session内部，避免分离后出错)
            kb_dict = kb.to_dict()
            # 记录创建知识库的日志
            self.logger.info(f"创建了知识库，ID: {kb.id}")
            # 返回知识库字典信息
            return kb_dict

    # 定义获取知识库列表的方法
    def list(
        self,
        user_id: str = None,
        page: int = 1,
        page_size: int = 10,
        search: str = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Dict:
        """
        获取知识库列表
        Args:
            user_id: 用户ID（可选）
            page: 页码
            page_size: 每页数量
            search:搜索关键词（搜索名称和描述）
            sort_by: 排序字段
            sort_order:排序方向
        Returns:
            包含 items, total, page, page_size 的字典
        """
        # 使用数据库会话
        with self.session() as session:
            # 查询Knowledgebase表
            query = session.query(Knowledgebase)
            # 如果指定了user_id，则筛选属于该用户的知识库
            if user_id:
                query = query.filter(Knowledgebase.user_id == user_id)
            if search:
                # 构造模糊搜索的SQL模式
                search_pattern = f"%{search}%"
                # 通过SQLAlchemy的filter方法实现名称或描述字段的模糊查询
                query = query.filter(
                    # 名称模糊匹配
                    (Knowledgebase.name.like(search_pattern))
                    | (Knowledgebase.description.like(search_pattern))
                )
            # 排序逻辑
            # 初始化排序字段变量
            sort_field = None
            # 如果排序字段为 name ,按名称排序
            if sort_by == "name":
                sort_field = Knowledgebase.name
            # 如果排序字段为 updated_at ，按更新时间排序
            elif sort_by == "updated_at":
                sort_field = Knowledgebase.updated_at
            # 否则默认按创建时间排序
            else:
                sort_field = Knowledgebase.created_at
            # 根据排序顺序（升序或降序）添加排序
            if sort_order == "asc":
                # 升序排列
                query = query.order_by(sort_field.asc())
            else:
                # 默认降序排列
                query = query.order_by(sort_field.desc())
            # 统计总数
            total = query.count()
            # 计算分页偏移量
            offset = (page - 1) * page_size
            # 获取当前页的数据列表
            kbs = query.offset(offset).limit(page_size).all()
            # 初始化知识库字典列表
            items = []
            # 遍历查询结果，将每一项转为dict后添加到items列表
            for kb in kbs:
                kb_dict = kb.to_dict()
                items.append(kb_dict)
            # 返回包含分页信息和数据条目的字典
            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
            }

    def delete(self, kb_id: str) -> bool:
        """
        删除知识库
        Args:
            kb_id: 知识库ID

        Returns: 是否删除成功

        """
        # 1.获取知识库信息
        with self.session() as session:
            kb:Knowledgebase = session.query(Knowledgebase).filter(Knowledgebase.id == kb_id).first()
            if not kb:
                raise ValueError(f"知识库{kb_id}不存在")

            # 保存需要删除的信息
            kb_name = kb.name
            cover_image_path = kb.cover_image if kb.cover_image else None
            # 获取知识库下的所有文档
            documents:List[DocumentModel] = session.query(DocumentModel).filter(DocumentModel.kb_id == kb_id).all()
            doc_ids = [doc.id for doc in documents]
            doc_file_paths = [doc.file_path for doc in documents if doc.file_path]

        collection_name = f"kb_{kb_id}"
        # 2. 删除向量数据库集合中的所有向量数据
        if doc_ids:
            try:
                # 逐个删除每个文档的向量数据
                for doc_id in doc_ids:
                    try:
                        vector_service.delete_documents(
                            collection_name=collection_name,
                            filter={"doc_id":doc_id}
                        )
                    except Exception as e:
                        self.logger.warning(f"删除文档{doc_id}的向量数据失败:{e}")
                self.logger.info(f"已删除知识库{kb_id}的向量数据")
            except Exception as e:
                self.logger.warning(f"删除向量数据失败:{e}")
        # 3. 删除所有文档的存储文件
        for file_path in doc_file_paths:
            if file_path:
                try:
                    storage_service.delete_file(file_path)
                    self.logger.info(f"已删除文档存储文件:{file_path}")
                except Exception as e:
                    self.logger.warning(f"删除文档存储文件失败:{file_path}, 错误:{e}")
        # 4. 删除知识库的封面图片
        if cover_image_path:
            try:
                storage_service.delete_file(cover_image_path)
                self.logger.info(f"已删除知识库封面图片:{cover_image_path}")
            except Exception as e:
                self.logger.warning(f"删除封面图片失败:{e}")
        # 5. 删除知识库的数据库记录（由于 CASCADE，文档记录会自动删除）
        with self.transaction() as session:
            kb = session.query(Knowledgebase).filter(Knowledgebase.id == kb_id).first()
            if not kb:
                return False
            session.delete(kb)
            self.logger.info(f"已删除知识库:{kb_id} {kb_name}")
            return True

    def get_by_id(self, kb_id: str) -> Optional[dict]:
        """根据ID获取知识库"""
        with self.session() as session:
            kb = session.query(Knowledgebase).filter(Knowledgebase.id == kb_id).first()
            if kb:
                return kb.to_dict()
            return None

    # 定义 update 方法，用于更新知识库
    def update(
        self,
        kb_id: str,
        cover_image_data: bytes = None,
        cover_image_filename: str = None,
        delete_cover: bool = False,
        **kwargs,
    ) -> Optional[dict]:
        """
        更新知识库
        Args:
            kb_id: 知识库ID
            cover_image_data: 新的封面图片数据（可选）
            cover_image_filename: 新的封面图片文件名（可选）
            delete_cover: 是否删除封面图片（可选）
            **kwargs:

        Returns:

        """
        # 开启数据库事务
        with self.transaction() as session:
            # 查询指定ID的知识库对象
            kb = session.query(Knowledgebase).filter(Knowledgebase.id == kb_id).first()
            # 如果未找到知识库，则返回None
            if not kb:
                return None
            # 处理封面图片更新
            old_cover_path = kb.cover_image if kb.cover_image else None
            if delete_cover:
                # 删除封面图片
                if old_cover_path:
                    try:
                        storage_service.delete_file(old_cover_path)
                        self.logger.info(f"已删除封面图片: {old_cover_path}")
                    except Exception as e:
                        self.logger.warning(f"删除封面图片时出错: {e}")
                kwargs["cover_image"] = None
            elif cover_image_data and cover_image_filename:
                # 验证文件类型
                file_ext_without_dot = (
                    os.path.splitext(cover_image_filename)[1][1:].lower()
                    if "." in cover_image_filename
                    else ""
                )
                if not file_ext_without_dot:
                    raise ValueError(f"文件名缺少扩展名: {cover_image_filename}")
                if file_ext_without_dot not in Config.ALLOWED_IMAGE_EXTENSIONS:
                    raise ValueError(
                        f"不支持的图片格式: {file_ext_without_dot}。支持的格式: {', '.join(Config.ALLOWED_IMAGE_EXTENSIONS)}"
                    )
                # 验证文件大小
                if len(cover_image_data) == 0:
                    raise ValueError("上传的图片文件为空")
                if len(cover_image_data) > Config.MAX_IMAGE_SIZE:
                    raise ValueError(
                        f"图片文件大小超过限制 {Config.MAX_IMAGE_SIZE / 1024 / 1024}MB"
                    )
                try:
                    # 构建封面图片路径（统一使用小写扩展名）
                    file_ext_with_dot = os.path.splitext(cover_image_filename)[
                        1
                    ].lower()
                    new_cover_path = f"covers/{kb.id}{file_ext_with_dot}"
                    self.logger.info(
                        f"正在处理知识库 {kb_id} 的封面图片更新: 文件名={cover_image_filename}, "
                        f"扩展名={file_ext_without_dot}, "
                        f"大小={len(cover_image_data)} 字节, "
                        f"新路径={new_cover_path}, "
                        f"旧路径={old_cover_path}"
                    )
                    # 先上传新封面（确保上传成功后再删除旧封面）
                    storage_service.upload_file(new_cover_path, cover_image_data)
                    # 验证文件是否成功上传
                    if not storage_service.file_exists(new_cover_path):
                        raise ValueError(f"上传后文件不存在: {new_cover_path}")

                    self.logger.info(f"成功上传封面图片: {new_cover_path}")
                    # 删除旧封面（如果存在且与新封面路径不同）
                    if old_cover_path and old_cover_path != new_cover_path:
                        try:
                            storage_service.delete_file(old_cover_path)
                            self.logger.info(f"已删除旧封面图片: {old_cover_path}")
                        except Exception as e:
                            self.logger.warning(f"删除旧封面图片时出错: {e}")
                            # 继续执行，不因为删除旧文件失败而中断更新
                    # 更新数据库中的封面路径
                    kwargs["cover_image"] = new_cover_path
                except Exception as e:
                    self.logger.error(
                        f"上传知识库 {kb.id} 的封面图片时出错: {e}", exc_info=True
                    )
                    raise ValueError(f"上传封面图片失败: {str(e)}")
            # 遍历要更新的字段和值
            for key, value in kwargs.items():
                # 判断知识库对象是否有该字段，且值不为 None
                if hasattr(kb, key) and (key == "cover_image" or value is not None):
                    # 设置该字段的新值
                    setattr(kb, key, value)
            # 刷新session，保证对象属性为最新状态
            session.flush()
            # 刷新对象，避免未提交前读取到旧数据
            session.refresh(kb)
            # 在事务内部将对象转为字典，避免 session 关闭后访问失败
            kb_dict = kb.to_dict()
            # 如果本次更新包含'cover_image' 字段，记录详细日志
            if "cover_image" in kwargs:
                self.logger.info(
                    f"更新知识库 {kb_id}, 封面图片={kb_dict.get('cover_image')}"
                )
            else:
                # 否则仅记录知识库ID
                self.logger.info(f"更新知识库: {kb_id}")
            # 返回更新后的知识库字典
            return kb_dict


# 创建KnowledgebaseService的单例对象
kb_service = KnowledgebaseService()
