# 导入倒序排序工具
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
