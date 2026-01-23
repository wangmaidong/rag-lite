"""
知识库相关路由（视图 + API）
"""

# 导入Flask中的相关模块
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    abort,
    send_file,
)

from io import BytesIO

# 导入logging模块
import logging

# 导入自定义工具函数：异常处理装饰器、错误响应、成功响应
from app.blueprints.utils import success_response, error_response, handle_api_error

# 导入知识库服务
from app.services.knowledgebase_service import kb_service

# 配置logger
logger = logging.getLogger(__name__)
# 创建Blueprint实例，注册在Flask应用下
bp = Blueprint("knowledgebase", __name__)

# 定义路由：POST请求到/api/v1/kb


@bp.route("/api/v1/kb", methods=["POST"])
# 应用自定义异常处理装饰器
@handle_api_error
# 定义创建知识库的视图函数
def api_create():
    # 设置接口功能描述
    """创建知识库"""
    # 从请求中解析JSON数据
    data = request.get_json()
    # 校验数据是否存在以及name键是否存在
    if not data or "name" not in data:
        # 若校验失败，返回错误响应
        return error_response("name is required", 400)

    # 获取知识库名称
    name = data["name"]
    # 获取用户id, 可为空
    user_id = data.get("user_id")
    # 获取知识库描述，可为空
    description = data.get("description")
    # 获取分块大小，默认为512
    chunk_size = data.get("chunk_size", 512)
    # 获取分块重叠，默认为50
    chunk_overlap = data.get("chunk_overlap", 50)

    # 调用知识库服务创建知识库，返回信息字典
    kb_dict = kb_service.create(
        name=name,
        user_id=user_id,
        description=description,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    return success_response(kb_dict)
