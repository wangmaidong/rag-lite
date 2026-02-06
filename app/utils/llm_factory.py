"""
LLM 模型工厂
根据设置动态创建 LLM 模型，支持扩展
"""

# 导入日志模块
import logging

# 导入类型注解：可选、字典、可调用、任意类型
from typing import Optional, Dict, Callable, Any

# 导入设置服务，用于获取当前设置
from app.services.settings_service import settings_service

# 导入配置类
from app.config import Config

# 获取当前模块的日志记录器
logger = logging.getLogger(__name__)


class LLMFactory:
    """LLM 模型工厂（支持扩展）"""

    # 注册的LLM提供者，用于存储各Provider的构造函数
    _providers: Dict[str, Callable] = {}

    # 注册新的LLM提供者方法
    @classmethod
    def register_provider(cls, provider_name: str, provider_func: Callable):
        """
        注册新的LLM提供者
        Args:
            provider_name:提供者名称
            provider_func:创建LLM的函数，签名应为:
                func(settings: dict, temperature: float, max_tokens: int, streaming: bool) -> LLM
        Returns:

        """
        # 将提供者函数存入_providers字典，键为小写名称
        cls._providers[provider_name.lower()] = provider_func
        # 日志打印已注册信息
        logger.info(f"已注册LLM提供商：{provider_name}")

    # 创建LLM实例方法
    @classmethod
    def create_llm(
        cls,
        settings: Optional[dict] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        streaming: bool = False,
    ):
        """
        根据设置创建 LLM 模型
        Args:
            settings:设置字典，如果为 None 则从数据库读取
            temperature:温度参数
            max_tokens:最大 token 数
            streaming:是否启用流式输出

        Returns:
            LLM 对象

        """
        # 如果未传入settings，从setting_service获取全局设置
        if settings is None:
            settings = settings_service.get()
        # 获取llm_provider的名称(默认为deepseek)
        provider = settings.get("llm_provider", "deepseek").lower()
        # 优先检查是否用户注册的 Provider
        if provider in cls._providers:
            # 使用自定义注册的Provider创建llm对象
            return cls._providers[provider](
                settings, temperature, max_tokens, streaming
            )
        # 若非自定义Provider，则按内置Provider处理
        if provider == "deepseek":
            # 创建 DeepSeek LLM
            return cls._create_deepseek(settings, temperature, max_tokens, streaming)
        elif provider == "openai":
            # 创建 OpenAI LLM
            return cls._create_openai(settings, temperature, max_tokens, streaming)
        elif provider == "ollama":
            # 创建 Ollama LLM
            return cls._create_ollama(settings, temperature, max_tokens, streaming)
        else:
            # 不支持的Provider,抛出错误
            raise ValueError(
                f"Unsupported LLM provider: {provider}. "
                f"Available providers: {list(cls._providers.keys()) + ['deepseek', 'openai', 'ollama']}"
            )

    # DeepSeek LLM创建方法
    @classmethod
    def _create_deepseek(
        cls, settings: dict, temperature: float, max_tokens: int, streaming: bool
    ):
        """创建 DeepSeek LLM"""
        # 导入 DeepSeek LLM 的类
        from langchain_deepseek import ChatDeepSeek

        # 获取模型名，优先用settings里的值，否则用默认配置
        model_name = settings.get("llm_model_name") or Config.DEEPSEEK_CHAT_MODEL
        # 获取API Key，优先用settings里的值，否则用默认配置
        api_key = settings.get("llm_api_key") or Config.DEEPSEEK_API_KEY
        # 获取Base URL，优先用settings里的值，否则用默认配置
        base_url = settings.get("llm_base_url") or Config.DEEPSEEK_BASE_URL
        # 实例化 DeepSeek LLM 对象
        llm = ChatDeepSeek(
            model=model_name,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
            streaming=streaming,
        )
        # 日志打印创建成功的信息
        logger.info(f"已创建DeepSeek LLM: {model_name}")
        # 返回 DeepSeek LLM实例
        return llm

    # OpenAI LLM 创建方法
    @classmethod
    def _create_openai(
        cls, settings: dict, temperature: float, max_tokens: int, streaming: bool
    ):
        # 创建 OpenAI LLM
        """创建 OpenAI LLM"""
        # 导入OpenAI LLM的类
        from langchain_openai import ChatOpenAI

        # 从settings中获取API Key
        api_key = settings.get("llm_api_key")
        # 如果未设置API Key则报错
        if not api_key:
            raise ValueError("OpenAI API key is required")

        # 获取模型名称，优先用用户配置，否则用默认gpt-4o
        model_name = settings.get("llm_model_name") or "gpt-4o"
        # 实例化OpenAI LLM对象
        llm = ChatOpenAI(
            model=model_name,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            streaming=streaming,
        )
        # 日志打印创建成功的信息
        logger.info(f"已创建 OpenAI LLM: {model_name}")
        # 返回OpenAI LLM实例
        return llm

    # Ollama LLM 创建方法
    @classmethod
    def _create_ollama(
        cls, settings: dict, temperature: float, max_tokens: int, streaming: bool
    ):
        # 创建 Ollama LLM
        """创建 Ollama LLM"""
        # 导入Ollama LLM相关类
        from langchain_community.chat_models import ChatOllama

        # 获取基础URL（优先用setting，否则用默认本地地址）
        base_url = settings.get("llm_base_url") or "http://localhost:11434"
        # 获取模型名，优先用用户配置
        model_name = settings.get("llm_model_name") or "llama2"

        # 实例化Ollama LLM对象
        llm = ChatOllama(
            model=model_name,
            base_url=base_url,
            temperature=temperature,
            num_predict=max_tokens,
        )
        # 日志打印Ollama创建信息
        logger.info(f"已创建 Ollama LLM: {model_name}, 地址: {base_url}")
        # 返回 Ollama LLM 实例
        return llm


# 注册内置提供者（可选，用于统一管理）
def _register_builtin_provider():
    """注册内置提供者"""
    # 注册deepseek provider
    LLMFactory.register_provider("deepseek", LLMFactory._create_deepseek)
    # 注册openai provider
    LLMFactory.register_provider("openai", LLMFactory._create_openai)
    # 注册ollama provider
    LLMFactory.register_provider("ollama", LLMFactory._create_ollama)


# 自动注册内置提供者
_register_builtin_provider()
