"""
RAG 服务
"""

# 导入日志模块
import logging

# 导入Langchain的对话提示模板模块
from langchain_core.prompts import ChatPromptTemplate

# 导入自定义 LLM 工厂
from app.utils.llm_factory import LLMFactory

# 导入设置服务
from app.services.settings_service import settings_service

# 设置日志对象
logger = logging.getLogger(__name__)


# 定义 RAGService 类
class RAGService:
    """RAG 服务"""

    # 初始化函数
    def __init__(self):
        """
        初始化服务
        Args:
            settings: 设置字典，如果为 None 则从数据库读取
        """
        # 从设置服务中获取配置信息
        self.settings = settings_service.get()
        # 定义默认系统消息提示词
        default_rag_system_prompt = "你是一个专业的AI助手，请基于文档内容回答问题"
        # 定义默认查询提示词，包含content 和 question 占位符
        default_rag_query_prompt = """文档内容：
        {context}
        
        问题：{question}
        
        请基于文档内容回答问题。如果文档中没有相关信息，请明确说明。
        """
        # 从设置中获取自定义系统消息提示词
        rag_system_prompt_text = self.settings.get("rag_system_prompt")
        # 如果没有设置，使用默认系统提示词
        if not rag_system_prompt_text:
            rag_system_prompt_text = default_rag_system_prompt

        # 从设置中获取自定义查询提示词
        rag_query_prompt_text = self.settings.get("rag_query_prompt")
        # 如果没有设置，使用默认查询提示词
        if not rag_query_prompt_text:
            rag_query_prompt_text = default_rag_query_prompt

        # 构建 RAG 的提示模板，包含系统消息和用户查询部分
        self.rag_prompt = ChatPromptTemplate.from_messages(
            [("system", rag_system_prompt_text), ("human", rag_query_prompt_text)]
        )

    # 定义流式问答接口
    def ask_stream(self, kb_id: str, question: str):
        """
        流式问答接口
        Args:
            kb_id:知识库ID
            question:问题

        Returns:
            流式数据块
        """
        # 创建带流式输出能力的 LLM 实例
        llm = LLMFactory.create_llm(self.settings)
        # 文档过滤后的结果，暂时为空列表
        filtered_docs = []
        # 发送流式开始信号
        yield {"type": "start", "content": ""}
        # 构造用于传递给 LLM 的上下文字符串，将所有文档整合为字符串
        context = "\n\n".join(
            [
                f"文档 {i+1} ({doc.metadata.get('doc_name', '未知')}):\n{doc.page_content}"
                for i, doc in enumerate(filtered_docs)
            ]
        )
        # 创建 Rag Prompt 到 LLM 的处理链
        chain = self.rag_prompt | llm
        # 初始化完整答案的字符串
        full_answer = ""
        # 逐块流式生成答案
        for chunk in chain.stream({"context": context, "question": question}):
            # 获取当前输出块内容
            content = chunk.content
            # 如果有内容则累加并 yield 输出内容块
            if content:
                full_answer += content
                yield {"type": "content", "content": content}

        # 所有内容输出结束后，发送完成信号和相关元数据
        yield {
            "type": "done",
            "content": "",
            "metadata": {
                "kb_id": kb_id,
                "question": question,
                "retrieved_chunks": len(filtered_docs),
            },
        }


# 实例化 rag_service，供外部调用
rag_service = RAGService()
