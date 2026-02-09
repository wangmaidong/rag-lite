"""
聊天相关路由(视图+API)
"""

# 导入 Flask 的 Blueprint 和模板渲染函数
from flask import Blueprint, render_template, request, stream_with_context, Response
import json

from app.blueprints.utils import (
    handle_api_error,
    success_response,
    error_response,
    get_current_user_or_error,
)

# 导入知识库服务，用于后续业务逻辑
from app.services.knowledgebase_service import kb_service

from app.services.chat_service import chat_service

# 导入登录保护装饰器和获取当前用户辅助方法
from app.utils.auth import login_required, get_current_user, api_login_required

# 导入日志模块
import logging

# 获取当前模块的日志记录器
logger = logging.getLogger(__name__)
# 创建名为 “chat” 的蓝图对象

bp = Blueprint("chat", __name__)


# 注册 /chat 路由，访问该路由需要先登录
@bp.route("/chat")
@login_required
def chat_view():
    """智能问答页面"""
    # 渲染 chat.html 模板并传递空知识库列表
    return render_template("chat.html", knowledgebasees=[])


# 注册 API 路由，处理聊天接口 POST 请求
@bp.route("/api/v1/knowledgebases/chat", methods=["POST"])
@api_login_required
@handle_api_error
def api_chat():
    """普通聊天接口不支持知识库，支持流式输出"""
    # 获取当前用户和错误信息
    current_user, err = get_current_user()
    # 如果有错误，直接返回错误响应
    if err:
        return err

    # 从请求体获取 JSON 数据
    data = request.get_json()
    # 如果数据为空或不存在，question 字段，返回错误
    if not data or "question" not in data:
        return error_response("question is required", 400)
    # 去除问题文本首尾空格
    question = data["question"].strip()
    # 如果问题内容为空，返回错误
    if not question:
        return error_response("question cannot be empty", 400)
    # 获取 max_tokens 参数，默认 1000
    max_tokens = int(data.get("max_tokens", 1000))
    # 限制最大和最小值在 1~10000 之间
    max_tokens = max(1, min(max_tokens, 10000))

    # 声明用于流式输出的生成器
    @stream_with_context
    def generate():
        try:
            # 用于缓存完整答案内容
            full_answer = ""
            # 调用服务进行流式对话
            for chunk in chat_service.chat_stream(
                question=question, temperature=None, max_tokens=max_tokens
            ):
                # 如果是内容块，则拼接内容到full_answer
                if chunk.get("type") == "content":
                    full_answer += chunk.get("content", "")
                # 以 SSE 协议格式输出数据
                yield f"data:{json.dumps(chunk, ensure_ascii=False)}\n\n"
            # 输出对话完成信号
            yield "data: [DONE]\n\n"
        except Exception as e:
            # 发生异常记录日志
            logger.error(f"流式输出时出错: {e}")
            # 构造错误数据块
            error_chunk = {"type": "error", "content": str(e)}
            # 输出错误数据块
            yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
        # 创建 Response 对象，设置必要的 SSE 响应头部
        response = Response(
            generate(),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Content-Type": "text/event-stream;charset=utf-8",
            },
        )
        return response
