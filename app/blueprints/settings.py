"""
设置相关路由（视图 + API）
"""

from flask import Blueprint, render_template
from app.utils.auth import login_required
import logging

logger = logging.getLogger(__name__)

bp = Blueprint("settings", __name__)


@bp.route("/settings")
@login_required
def settings_view():
    """设置页面"""
    return render_template("settings.html")
