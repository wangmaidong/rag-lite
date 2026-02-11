"""
聊天相关路由(视图+API)
"""

from pickle import FALSE

# 导入 Flask 的 Blueprint 和模板渲染函数
from flask import Blueprint, render_template, request, stream_with_context, Response
import json

from app.blueprints.utils import (
    handle_api_error,
    success_response,
    error_response,
    get_current_user_or_error,
    get_pagination_params,
    check_ownership,
)

# 导入知识库服务，用于后续业务逻辑
from app.services.knowledgebase_service import kb_service

# 导入聊天消息服务
from app.services.chat_service import chat_service

# 导入聊天会话服务
from app.services.chat_session_service import session_service

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
    current_user = get_current_user()
    # 获取所有知识库（通常用户不会有太多知识库，不需要分页）
    result = kb_service.list(user_id=current_user["id"], page=1, page_size=1000)
    # 渲染 chat.html 模板并传递空知识库列表
    return render_template("chat.html", knowledgebasees=result["items"])


# 注册 API 路由，处理聊天接口 POST 请求
@bp.route("/api/v1/chat", methods=["POST"])
@api_login_required
@handle_api_error
def api_chat():
    """普通聊天接口不支持知识库，支持流式输出"""
    # 获取当前用户和错误信息
    current_user, err = get_current_user_or_error()
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
    # 会话ID可以为空表示普通聊天
    session_id = data.get("session_id")
    # 获取 max_tokens 参数，默认 1000
    max_tokens = int(data.get("max_tokens", 1000))
    # 限制最大和最小值在 1~10000 之间
    max_tokens = max(1, min(max_tokens, 10000))

    # 从请求数据中获取'stream'字段，默认为True，表示启用流式输出
    stream = data.get("stream", True)
    # 初始化历史消息为None
    history = None
    # 如果请求中带有session_id 说明有现有会话
    if session_id:
        # 根据session_id和当前用户ID获取历史消息列表
        history_messages = session_service.get_message(session_id, current_user["id"])
        # 将历史消息转换为对话格式，仅保留最近10条
        history = [
            {"role": msg.get("role"), "content": msg.get("content")}
            for msg in history_messages[-10:]
        ]

    # 如果请求中没有session_id，说明是新对话，需要新建会话
    if not session_id:
        # 创建新会话，kb_id 设为None表示普通聊天
        chat_session = session_service.create_session(user_id=current_user["id"])
        # 使用新创建会话的ID作为本次会话
        session_id = chat_session["id"]

    # 将用户的问题消息保存到当前会话中
    session_service.add_message(session_id, "user", question)

    # 声明用于流式输出的生成器
    @stream_with_context
    def generate():
        try:
            # 用于缓存完整答案内容
            full_answer = ""
            # 调用服务进行流式对话
            for chunk in chat_service.chat_stream(
                question=question,
                temperature=None,
                max_tokens=max_tokens,
                history=history,
            ):
                # 如果是内容块，则拼接内容到full_answer
                if chunk.get("type") == "content":
                    full_answer += chunk.get("content", "")
                # 以 SSE 协议格式输出数据
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            # 输出对话完成信号
            yield "data: [DONE]\n\n"
            # 保存助手回复
            if full_answer:
                session_service.add_message(session_id, "assistant", full_answer)
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


# 路由装饰器，定义 GET 方法获取会话列表的接口
@bp.route("/api/v1/sessions", methods=["GET"])
@api_login_required
@handle_api_error
def api_list_sessions():
    """获取当前用户的会话列表"""
    # 获取当前用户，如有错误直接返回错误响应
    current_user, err = get_current_user_or_error()
    if err:
        return err
    # 获取分页参数（页码和每页数量），最大单页1000
    page, page_size = get_pagination_params(max_page_size=1000)
    # 调用会话服务获取当前用户的会话列表
    result = session_service.list_sessions(
        current_user["id"], page=page, page_size=page_size
    )
    # 以统一成功响应格式返回会话列表
    return success_response(result)


# 路由装饰器，定义 POST 方法创建会话的接口
@bp.route("/api/v1/sessions", methods=["POST"])
@api_login_required
@handle_api_error
def api_create_session():
    """创建新的聊天会话"""
    # 获取当前用户，如果有错误直接返回
    current_user, err = get_current_user_or_error()
    if err:
        return err
    # 获取请求体中的JSON数据，如无则返回空字典
    data = request.get_json() or {}
    # 获取会话标题
    title = data.get("title")
    # 调用服务创建会话，传入当前用户ID、知识库ID与标题
    session_obj = session_service.create_session(
        user_id=current_user["id"], title=title
    )
    # 返回成功响应及会话对象
    return success_response(session_obj)


# 路由装饰器，定义 GET 方法获取单个会话详情的接口（带 session_id）
@bp.route("/api/v1/sessions/<session_id>", methods=["GET"])
@api_login_required
@handle_api_error
def api_get_session(session_id):
    """获取会话详情和消息"""
    current_user, err = get_current_user_or_error()
    if err:
        return err
    # 根据 session_id 获取会话对象，校验所属当前用户
    session_obj = session_service.get_session_by_id(session_id, current_user["id"])
    # 如果没有找到会话，返回 404 错误
    if not session_obj:
        return error_response("Session not found", 404)

    # 获取该会话下的所有消息
    message = session_service.get_message(session_id, current_user["id"])
    # 返回会话详情及消息列表
    return success_response({"session": session_obj, "messages": message})


# 路由装饰器，定义 DELETE 方法删除单个会话接口
@bp.route("/api/v1/sessions/<session_id>", methods=["DELETE"])
@api_login_required
@handle_api_error
def api_delete_session(session_id):
    """删除会话"""
    # 获取当前用户，如有错误直接返回
    current_user, err = get_current_user_or_error()
    if err:
        return err
    # 调用服务删除会话，校验归属当前会话
    success = session_service.delete_session(session_id, current_user["id"])
    # 若删除成功，返回成功响应，否则返回 404
    if success:
        return success_response(None, "Session deleted")
    else:
        return error_response("Session not found", 404)


# 路由装饰器，定义 DELETE 方法清空所有会话的接口
@bp.route("/api/v1/sessions", methods=["DELETE"])
@api_login_required
@handle_api_error
def api_delete_all_sessions():
    """清空所有会话"""
    # 获取当前用户，如果有错误直接返回
    current_user, err = get_current_user_or_error()
    if err:
        return err
    # 调用服务删除所有属于当前用户的会话，返回删除数量
    count = session_service.delete_all_sessions(current_user["id"])
    # 返回成功响应及被删除会话数
    return success_response({"deleted_count": count}, f"Deleted {count} sessions")


# 路由装饰器，指定POST方法用于知识库问答接口
@bp.route("/api/v1/knowledgebases/<kb_id>/chat", methods=["POST"])
@api_login_required
@handle_api_error
def api_ask(kb_id):
    """知识库问答接口（支持流式输出）"""
    # 获取当前用户和错误信息
    current_user, err = get_current_user_or_error()
    if err:
        return err
    # 获取指定id的知识库
    kb = kb_service.get_by_id(kb_id)
    # 检查当前用户是否有权限访问该知识库
    has_permission, err = check_ownership(
        kb["user_id"], current_user["id"], "knowledgebase"
    )
    # 如果没有权限，直接返回错误
    if not has_permission:
        return err
    # 获取请求中的json数据
    data = request.get_json()
    # 获取并去除问题字符串首尾空白
    question = data["question"].strip()

    # 从请求数据获取session_id,如果没有则为None
    session_id = data.get("session_id")
    # 获取最大token数，默认为1000
    max_tokens = int(data.get("max_tokens", 1000))
    # 限制max_tokens在1到10000之间
    max_tokens = max(1, min(max_tokens, 10000))
    # 如果没有提供session_id，则为用户和知识库创建一个新会话
    if not session_id:
        chat_session = session_service.create_session(
            user_id=current_user["id"], kb_id=kb_id
        )
        # 获取新会话的会话ID
        session_id = chat_session["id"]
    # 保存用户输入的问题到消息列表
    session_service.add_message(session_id, "user", question)

    # 内部函数：生成流式响应内容
    @stream_with_context
    def generate():
        try:
            # 初始化完整回复内容
            full_answer = ""
            # 初始化引用信息
            source = None
            # 迭代 chat_service.ask_stream的每个数据块
            for chunk in chat_service.ask_stream(kb_id=kb_id, question=question):
                # 如果块类型为内容，则将内容追加到full_answer
                if chunk.get("type") == "content":
                    full_answer += chunk.get("content", "")
                # 如果块类型为done，则获取sources
                elif chunk.get("type") == "done":
                    sources = chunk.get("sources")
                # 以SSE格式输出该块内容
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            # 所有内容输出后发送结束标志
            yield "data: [DONE]\n\n"
            # 如果有回复内容，则保存机器人助手的回复和引用
            session_service.add_message(session_id, "assistant", full_answer)
        except Exception as e:
            # 如果流式输出出错，在日志中记录错误信息
            logger.error(f"流式输出时出错：{e}")
            # 构造错误信息块
            error_chunk = {"type": "error", "content": str(e)}
            # 以SSE格式输出错误信息
            yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"

    # 构造SSE（服务端事件）响应对象，携带合适的头部信息
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
