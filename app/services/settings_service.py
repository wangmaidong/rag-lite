"""
设置服务
"""

# 导入 Settings 模型
from app.models.settings import Settings

# 导入配置类
from app.config import Config

# 导入基础服务类
from app.services.base_service import BaseService

# 定义设置服务类，继承基础服务


class SettingsService(BaseService):
    """设置服务"""

    # 获取设置的方法
    def get(self) -> dict:
        """
        获取设置（单例模式）
        Returns:
            设置字典，如果不存在则返回默认值
        """
        # 打开会话
        with self.session() as session:
            # 查询主键为 'global' 的设置
            settings = session.query(Settings).filter_by(id="global").first()
            # 如果数据库中存在设置，返回其字典形式
            if settings:
                return settings.to_dict()
            else:
                # 如果不存在，返回默认设置
                return self._get_default_settings()

        # 获取默认设置的方法

    def _get_default_settings(self) -> dict:
        """获取默认设置"""
        return {
            "id": "global",  # 设置主键
            "embedding_provider": "huggingface",  # 默认 embedding provider
            "embedding_model_name": "sentence-transformers/all-MiniLM-L6-v2",  # 默认 embedding 模型
            "embedding_api_key": None,  # 默认无 embedding API key
            "embedding_base_url": None,  # 默认无 embedding base url
            "llm_provider": "deepseek",  # 默认 LLM provider
            "llm_model_name": Config.DEEPSEEK_CHAT_MODEL,  # 默认 LLM 模型
            "llm_api_key": Config.DEEPSEEK_API_KEY,  # 配置里的默认 LLM API key
            "llm_base_url": Config.DEEPSEEK_BASE_URL,  # 配置里的默认 LLM base url
            "llm_temperature": "0.7",  # 默认温度
            "chat_system_prompt": "你是一个专业的AI助手。请友好、准确地回答用户的问题。",  # 聊天系统默认提示词
            "rag_system_prompt": "你是一个专业的AI助手。请基于文档内容回答问题。",  # RAG系统提示词
            "rag_query_prompt": "文档内容：\n{context}\n\n问题：{question}\n\n请基于文档内容回答问题。如果文档中没有相关信息，请明确说明。",  # RAG查询提示词
            "retrieval_mode": "vector",  # 默认检索模式
            "vector_threshold": "0.2",  # 向量检索阈值
            "keyword_threshold": "0.5",  # 关键词检索阈值
            "vector_weight": "0.7",  # 检索混合权重
            "top_n": "5",  # 返回结果数量
            "created_at": None,  # 创建时间
            "updated_at": None,  # 更新时间
        }

    # 用于更新设置的方法
    def update(self, data: dict) -> dict:
        """
        更新设置
        Args:
            data:设置数据

        Returns:
            更新后的设置
        """
        # 启动事务会话
        with self.transaction() as session:
            # 查询主键为 global 的设置
            settings = session.query(Settings).filter_by(id="global").first()
            # 如果已存在设置，则逐项更新
            if settings:
                # 遍历提交的所有字段及其对应的值
                for key, value in data.items():
                    if hasattr(settings, key) and value is not None:
                        setattr(settings, key, value)
            else:
                # 不存在则新建一个 Settings 对象
                settings = Settings(id="global")
                # 设置各属性
                for key, value in data.items():
                    if hasattr(settings, key) and value is not None:
                        setattr(settings, key, value)
                # 添加到会话
                session.add(settings)
            # flush 保证所有更改同步到数据库会话（提交之前，保证主键自增/更新时间等有效）
            session.flush()
            # refresh 保证 settings 对象数据是数据库最新的内容（例如 updated_at 字段）
            session.refresh(settings)
            # 返回已更新的设置字典
            return settings.to_dict()


# 实例化设置服务
settings_service = SettingsService()
