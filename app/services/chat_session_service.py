# 导入倒序排序工具
from langchain_classic.chains.question_answering.map_reduce_prompt import messages
from sqlalchemy import desc

# 导入日期时间
from datetime import datetime

# 导入聊天会话ORM模型
from app.models.chat_session import ChatSession

# 导入导入聊天消息ORM模型
from app.models.chat_message import ChatMessage

# 导入基础服务类
from app.services.base_service import BaseService


# 聊天会话服务类，继承自基础服务
class ChatSessionService(BaseService[ChatSession]):
    """聊天会话服务"""

    # 创建新的聊天会话
    def create_session(
        self, user_id: str, kb_id: str = None, title: str = None
    ) -> dict:
        """
        创建新的聊天会话
        Args:
            user_id:用户ID
            kb_id:知识库ID（可选）
            title:会话标题（可选，如果不提供则使用默认标题）

        Returns:
            会话信息字典

        """
        # 启动数据事务
        with self.transaction() as session:
            # 如果没有传标题则用默认标题
            if not title:
                title = "新对话"
            # 构造会话对象
            chat_session = ChatSession(user_id=user_id, title=title)
            # 新会话入库
            session.add(chat_session)
            # 刷新以拿到自增ID
            session.flush()
            # 刷新会话对象，便于获取ID等字段
            session.refresh(chat_session)
            # 记录日志
            self.logger.info(f"已创建聊天会话: {chat_session.id}, 用户: {user_id}")
            # 返回会话字典格式
            return chat_session.to_dict()

    # 根据ID获取会话
    def get_session_by_id(self, session_id: str, user_id: str = None) -> dict:
        """
        根据ID获取会话
        Args:
            session_id:会话ID
            user_id:用户ID（可选，用于验证权限）

        Returns:
            会话信息字典，如果不存在或无权访问则返回 None
        """
        # 打开数据库只读session
        with self.session() as session:
            # 查询指定ID的会话
            query = session.query(ChatSession).filter_by(id=session_id)
            # 如果提供了user_id则额外限定归属
            if user_id:
                query = query.filter_by(user_id=user_id)
            # 拿到第一个会话记录
            chat_session = query.first()
            # 有则返回字典信息，没有返回None
            if chat_session:
                return chat_session.to_dict()
            return None

    # 获取用户的所有会话列表（分页）
    def list_sessions(self, user_id: str, page: int = 1, page_size: int = 1000) -> dict:
        """
        获取用户的会话列表
        Args:
            user_id:用户ID
            page:页码
            page_size:每页数量

        Returns:
            包含总数和会话列表的字典
        """
        # 打开数据库只读session
        with self.session() as session:
            # 查询当前用户的所有会话
            query = session.query(ChatSession).filter_by(user_id=user_id)
            # 用基类的分页方法返回结构化内容，按更新时间倒叙
            return self.paginate_query(
                query,
                page=page,
                page_size=page_size,
                order_by=desc(ChatSession.updated_at),
            )

    # 会话标题修改
    def update_session_title(self, session_id: str, user_id: str, title: str) -> dict:
        """
        更新会话标题
        Args:
            session_id:会话ID
            user_id:用户ID（用于验证权限）
            title:新标题

        Returns:
            更新后的会话信息字典
        """
        # 启动数据库事务
        with self.transaction() as session:
            # 查询拥有该会话的用户
            chat_session = (
                session.query(ChatSession)
                .filter_by(id=session_id, user_id=user_id)
                .first()
            )
            # 会话不存在则抛出异常
            if not chat_session:
                raise ValueError("Session not found or access denied")
            # 更新标题
            chat_session.title = title
            # 刷新会话对象(update不会提交，refresh刷新对象)
            session.refresh(chat_session)
            # 返回最新数据
            return chat_session.to_dict()

    # 删除指定会话
    def delete_session(self, session_id: str, user_id: str) -> bool:
        """
        删除会话（级联删除消息）
        Args:
            session_id:会话ID
            user_id:用户ID（用于验证权限）

        Returns:
            是否删除成功
        """
        # 开启数据事务
        with self.transaction() as session:
            # 查询该用户的指定会话
            chat_session = (
                session.query(ChatSession)
                .filter_by(id=session_id, user_id=user_id)
                .first()
            )
            # 未找到会话则返回False
            if not chat_session:
                return False
            # 删除会话（DB应有级联消息）
            session.delete(chat_session)
            # 记录日志
            self.logger.info(f"已删除聊天会话: {session_id}")
            # 返回True表示删除成功
            return True

    # 删除当前用户的所有会话
    def delete_all_sessions(self, user_id: str) -> int:
        """
        删除用户的所有会话

        Args:
            user_id: 用户ID

        Returns:
            删除的会话数量
        """
        # 开启数据库事务
        with self.transaction() as session:
            # 批量删除本用户所有会话
            count = session.query(ChatSession).filter_by(user_id=user_id).delete()
            # 记录日志
            self.logger.info(f"已删除用户 {user_id} 的 {count} 个聊天会话")
            # 返回删除数量
            return count

    # 添加消息到会话
    def add_message(self, session_id: str, role: str, content: str) -> dict:
        """
        添加消息到会话
        Args:
            session_id:会话ID
            role:角色（'user' 或 'assistant'）
            content:消息内容

        Returns:
            消息信息字典
        """
        # 开启数据事务
        with self.transaction() as session:
            # 构造消息对象
            message = ChatMessage(session_id=session_id, role=role, content=content)
            # 添加消息到数据库
            session.add(message)
            # 查询会话对象，用于更新时间/自动生成标题
            chat_session = session.query(ChatSession).filter_by(id=session_id).first()
            # 如果存在会话对象
            if chat_session:
                # 更新会话更新时间
                chat_session.updated_at = datetime.now()
                # 如果使用户发的第一条消息，并且还没有标题，则用内容自动命名
                if role == "user" and (
                    not chat_session.title or chat_session.title == "新对话"
                ):
                    # 会话标题截取前30字符，超长加省略号
                    title = content[:30] + ("..." if len(content) > 30 else "")
                    chat_session.title = title

            # 刷新确保message有ID
            session.flush()
            # 刷新消息对象
            session.refresh(message)
            return message.to_dict()

    # 获取会话的全部消息
    def get_message(self, session_id: str, user_id: str = None) -> list:
        """
        获取会话的所有消息
        Args:
            session_id:会话ID
            user_id:用户ID（可选，用于验证权限）

        Returns:
            消息列表
        """
        # 打开只读session
        with self.session() as session:
            # 如指定user_id，须先验证此会话是否属于该用户，不属则不给查
            if user_id:
                chat_session = (
                    session.query(ChatSession)
                    .filter_by(id=session_id, user_id=user_id)
                    .first()
                )
                # 如果会话不存在则返回空列表
                if not chat_session:
                    return []
            # 查询该会话下所有消息，按创建时间升序排序
            messages = (
                session.query(ChatMessage)
                .filter_by(session_id=session_id)
                .order_by(ChatMessage.created_at)
                .all()
            )
            # 返回所有消息的字典列表
            return [m.to_dict() for m in messages]


# 单例: 聊天会话服务对象
session_service = ChatSessionService()
