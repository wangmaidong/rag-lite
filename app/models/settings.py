# 设置模型的文档字符串
"""
设置模型
"""
# 引入 SQLAlchemy 的 Column、String、Text、DateTime 类型
from sqlalchemy import Column, String, Text, DateTime

# 引入 SQLAlchemy 的 func，用于时间戳
from sqlalchemy.sql import func

# 引入自定义的 BaseModel 作为父类
from app.models.base import BaseModel


# 定义设置模型类，继承自 BaseModel
class Settings(BaseModel):
    # 设置模型说明（单例模式，只存储一条记录）
    """设置模型（单例模式，只存储一条记录）"""
    # 指定数据表名为 settings
    __tablename__ = "settings"
    # 指定 __repr__ 方法显示的字段为 id
    __repr_fields__ = ["id"]  # 指定 __repr__ 显示的字段

    # 主键，类型为 String(32)，默认值为 'global'
    id = Column(String(32), primary_key=True, default="global")

    # Embedding 配置
    embedding_provider = Column(
        String(64), nullable=False, default="huggingface"
    )  # huggingface, openai, ollama
    embedding_model_name = Column(String(255), nullable=True)  # 模型名称或路径
    embedding_api_key = Column(String(255), nullable=True)  # API Key（OpenAI 需要）
    embedding_base_url = Column(String(512), nullable=True)  # Base URL（Ollama 需要）

    # LLM 配置
    # LLM 提供商，类型为 String(64)，不能为空，默认值为 'deepseek'
    llm_provider = Column(
        String(64), nullable=False, default="deepseek"
    )  # deepseek, openai, ollama
    # LLM 模型名称，类型为 String(255)，可为空
    llm_model_name = Column(String(255), nullable=True)  # 模型名称
    # LLM API Key，类型为 String(255)，可为空
    llm_api_key = Column(String(255), nullable=True)  # API Key
    # LLM Base URL，类型为 String(512)，可为空
    llm_base_url = Column(String(512), nullable=True)  # Base URL
    # LLM 温度参数，类型为 String(16)，可为空，默认值为 '0.7'
    llm_temperature = Column(String(16), nullable=True, default="0.7")  # LLM 温度参数

    # 提示词配置
    # 普通聊天系统提示词，类型为 Text，可为空
    chat_system_prompt = Column(Text, nullable=True)  # 普通聊天系统提示词
    # 知识库聊天系统提示词，类型为 Text，可为空（会话开始时设置）
    rag_system_prompt = Column(
        Text, nullable=True
    )  # 知识库聊天系统提示词（会话开始时设置）
    # 知识库聊天查询提示词，类型为 Text，可为空（每次提问时使用，可包含{context}和{question}）
    rag_query_prompt = Column(
        Text, nullable=True
    )  # 知识库聊天查询提示词（每次提问时使用，可包含{context}和{question}）

    # 检索配置
    # 检索模式，类型为 String(32)，不能为空，默认值为 'vector'（可选值：vector, keyword, hybrid）
    retrieval_mode = Column(
        String(32), nullable=False, default="vector"
    )  # vector, keyword, hybrid
    # 向量检索阈值，类型为 String(16)，可为空，默认值为 '0.2'
    vector_threshold = Column(String(16), nullable=True, default="0.2")  # 向量检索阈值
    # 全文检索阈值，类型为 String(16)，可为空，默认值为 '0.5'
    keyword_threshold = Column(String(16), nullable=True, default="0.5")  # 全文检索阈值
    # 向量检索权重，类型为 String(16)，可为空，默认值为 '0.7'（混合检索时使用）
    vector_weight = Column(
        String(16), nullable=True, default="0.7"
    )  # 向量检索权重（混合检索时使用）
    # TopN 结果数量，类型为 String(16)，可为空，默认值为 '5'
    top_n = Column(String(16), nullable=True, default="5")  # TopN 结果数量

    # 创建时间，类型为 DateTime，默认值为当前时间
    created_at = Column(DateTime, default=func.now())
    # 更新时间，类型为 DateTime，默认值为当前时间，更新时自动更改
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
