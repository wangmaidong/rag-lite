"""
问答服务
支持普通聊天和知识库聊天（RAG）
"""

# 导入日志模块
import logging

# 导入可选类型和迭代器类型注解
from typing import Optional, Iterator

# 导入 LLM 工厂，用于创建大语言模型实例
from app.utils.llm_factory import LLMFactory

# 导入 LangChain 的对话模板
from langchain_core.prompts import ChatPromptTemplate

# 导入设置服务，用于获取当前系统设置
from app.services.settings_service import settings_service


# 初始化日志记录器
logger = logging.getLogger(__name__)


class ChatService:
    # 类的初始化方法
    def __init__(self):
        """初始化问答服务"""
        self.settings = settings_service.get()

    # 定义流式普通聊天方法，不使用知识库
    def chat_stream(
        self,
        question: str,
        temperature: Optional[float] = None,
        max_tokens: int = 1000,
        history: Optional[list] = None,
    ) -> Iterator[dict]:
        """
        流式普通聊天接口（不使用知识库）
        Args:
            question: 问题
            temperature: LLM 温度参数（如果为 None，则从设置中读取）
            max_tokens: 最大生成 token 数
            history: 历史对话记录（可选）

        Returns:
            流式数据块

        """
        # 如果没有指定温度，则从设置中获取（默认为 0.7），并限制在 0-2 之间
        if temperature is None:
            temperature = float(self.settings.get("llm_temperature", "0.7"))
            temperature = max(0.0, min(temperature, 2.0))
        # 获取用于普通聊天的系统提示词
        chat_prompt_text = self.settings.get("chat_system_prompt")
        # 如果系统提示词不存在，则使用默认的提示词
        if not chat_prompt_text:
            chat_prompt_text = "你是一个专业的AI助手。请友好、准确地回答用户的问题。"
        # 创建支持流式输出的 LLM 实例
        llm = LLMFactory.create_llm(
            self.settings,
            temperature=temperature,
            max_tokens=max_tokens,
            streaming=True,
        )
        # 构造单轮对话消息格式，包含 system 提示和用户问题
        messages = [("system", chat_prompt_text), ("human", question)]
        # 从消息创建对话提示模板
        prompt = ChatPromptTemplate.from_messages(messages)
        # 组装 prompt 和 llm，形成链式调用
        chain = prompt | llm

        # 发送流式开头信号
        yield {"type": "start", "content": ""}
        # 初始化完整答案内容
        full_answer = ""
        try:
            # 遍历模型生成的每一段内容
            for chunk in chain.stream({}):
                # 如果chunk有内容，提取内容并累加到full_answer
                if hasattr(chunk, "content") and chunk.content:
                    content = chunk.content
                    full_answer += content
                    # 输出内容块
                    yield {"type": "content", "content": content}
        # 捕获生成过程中的异常，记录日志并产出错误类型的数据块
        except Exception as e:
            logger.error(f"流式生成时出错: {e}")
            yield {"type": "error", "content": f"生成答案时出错: {str(e)}"}
            return

        # 发送流式结束信号，附带元数据（此处无知识库相关内容）
        yield {
            "type": "done",
            "content": "",
            "sources": [],
            "metadata": {"question": question, "retrieved_chunks": 0, "used_chunks": 0},
        }


# 创建全局单例 chat_service 实例
chat_service = ChatService()
