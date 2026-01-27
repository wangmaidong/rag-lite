"""
设置相关路由（视图 + API）
"""

from flask import Blueprint, render_template
from app.utils.auth import login_required
import logging

# 导入标准化响应、错误处理装饰器、请求JSON体校验工具
from app.blueprints.utils import (
    error_response,
    success_response,
    handle_api_error,
    require_json_body,
)

# 导入嵌入模型、LLM模型配置
from app.utils.models_config import EMBEDDING_MODELS, LLM_MODELS

# 导入设置服务
from app.services.settings_service import settings_service

logger = logging.getLogger(__name__)

bp = Blueprint("settings", __name__)


@bp.route("/settings")
@login_required
def settings_view():
    """设置页面"""
    return render_template("settings.html")


# 注册 API 路由：获取可用模型列表
@bp.route("/api/v1/settings/models", methods=["GET"])
@handle_api_error
def api_get_available_models():
    """获取可用的模型列表"""
    # 返回嵌入模型与LLM可用模型数据
    return success_response(
        {"embedding_models": EMBEDDING_MODELS, "llm_models": LLM_MODELS}
    )


# 注册API路由：更新设置
@bp.route("/api/v1/settings", methods=["PUT"])
@handle_api_error
def api_update_settings():
    """更新设置"""
    # 校验请求体并获取数据
    data, err = require_json_body()
    # 如果有错误，直接返回错误响应
    if err:
        return err
    # 调用设置服务进行更新
    settings = settings_service.update(data)
    # 返回更新后的设置
    return success_response(settings, "Settings updated successfully")


# 注册 API 路由：获取当前设置
@bp.route("/api/v1/settings", methods=["GET"])
@handle_api_error
def api_get_settings():
    """获取设置"""
    # 从设置服务获取当前设置
    settings = settings_service.get()
    return success_response(settings)
