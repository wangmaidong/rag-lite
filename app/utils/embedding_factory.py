"""
Embedding 模型工厂
支持多种Embedding 模型提供商
"""
# 导入日志模块
import logging
# 导入 Huggingface Embeddings 类
from langchain_huggingface import HuggingFaceEmbeddings
# 导入Open AI Embeddings 类
from langchain_openai import OpenAIEmbeddings
# 导入 Ollama Embeddings 类
from langchain_community.embeddings import OllamaEmbeddings
from openai import embeddings

# 导入全局设置服务
from app.services.settings_service import  settings_service
# 获取logger对象
logger = logging.getLogger(__name__)

# 定义 Embedding 工厂类
class EmbeddingFactory:
    """Embedding 模型工厂"""
    # 默认模型名称
    DEFAULT_MODEL_NAME = 'sentence-transformers/all-MiniLM-L6-v2'
    # 定义静态方法，用于创建 embedding 对象
    @staticmethod
    def create_embeddings():
        """
        创建 Embedding 模型
        Returns:
            Embeddings 对象
        """
        # 从 settings_service 获取嵌入设置
        settings = settings_service.get()
        # 获取 embedding 提供商，默认为 huggingface
        provider = settings.get("embedding_provider", "huggingface")
        # 获取embedding 模型名称
        model_name = settings.get("embedding_model_name")
        # 获取 embedding api key
        api_key = settings.get("embedding_api_key")
        # 获取 embedding base url
        base_url = settings.get("embedding_base_url")
        try:
            # 如果提供商为 huggingface
            if provider == "huggingface":
                # 创建 HuggingFace Embeddings 对象
                embeddings = HuggingFaceEmbeddings(
                    model_name=model_name,
                    model_kwargs={"device": "cpu"},
                    encode_kwargs={"normalize_embeddings":True}
                )
                # 记录日志
                logger.info(f"创建 HuggingFace Embeddings: {model_name}")
            # 如果提供商为 openai
            elif provider == "openai":
                # 如果没有api_key抛出异常
                if not api_key:
                    raise ValueError("OpenAI Embeddings 需要 API Key")
                # 创建 OpenAI Embeddings 对象
                embeddings = OpenAIEmbeddings(
                    model=model_name,
                    openai_api_key=api_key
                )
                # 记录日志
                logger.info(f"创建 OpenAI Embeddings: {model_name}")
            elif provider == "ollama":
                # 如果没有 base_url 抛出异常
                if not base_url:
                    raise ValueError(f"Ollama Embeddings 需要 Base URL")
                # 创建 Ollama Embeddings对象
                embeddings = OllamaEmbeddings(
                    model=model_name,
                    base_url=base_url
                )
                # 记录日志
                logger.info(f"创建 Ollama Embeddings: {model_name}, base_url: {base_url}")
            else:
                # 未知的提供商，警告日志，使用默认 huggingface
                logger.warning(f"未知的 Embedding 提供商: {provider}，使用默认的 HuggingFace")
                embeddings = HuggingFaceEmbeddings(
                    model_name=EmbeddingFactory.DEFAULT_MODEL_NAME,
                    model_kwargs={"device": "cpu"},
                    encode_kwargs={"normalize_embeddings": True}
                )
            return embeddings
        except Exception as e:
            # 出现异常时记录错误日志
            logger.error(f"创建 Embedding 模型失败: {e}", exc_info=True)
            # 失败时回退到默认模型并记录警告
            logger.warning(f"回退到默认 HuggingFace 模型: {EmbeddingFactory.DEFAULT_MODEL_NAME}")
            return HuggingFaceEmbeddings(
                model_name=EmbeddingFactory.DEFAULT_MODEL_NAME,
                model_kwargs={"device":"cpu"},
                encode_kwargs={"normalize_embeddings": True}
            )