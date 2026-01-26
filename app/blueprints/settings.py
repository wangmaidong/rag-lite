"""
设置相关路由（视图 + API）
"""

from flask import Blueprint, render_template
from app.utils.auth import login_required
import logging

# 导入标准化响应、错误处理装饰器、请求JSON体校验工具
from app.blueprints.utils import error_response,success_response,handle_api_error

# 导入嵌入模型、LLM模型配置
from app.utils.models_config import EMBEDDING_MODELS,LLM_MODELS

# 导入设置服务
from app.services.settings_service import settings_service

logger = logging.getLogger(__name__)

bp = Blueprint("settings", __name__)


@bp.route("/settings")
@login_required
def settings_view():
    """设置页面"""
    return render_template("settings.html")
