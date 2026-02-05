"""
聊天相关路由(视图+API)
"""

# 导入 Flask 的 Blueprint 和模板渲染函数
from flask import Blueprint, render_template

# 导入知识库服务，用于后续业务逻辑
from app.services.knowledgebase_service import kb_service

# 导入登录保护装饰器和获取当前用户辅助方法
from app.utils.auth import login_required, get_current_user

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
