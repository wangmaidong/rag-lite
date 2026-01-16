# 认证相关路由
"""
认证相关路由
"""

# 导入 Flask相关模块和方法
from flask import Blueprint, render_template, request, redirect, url_for, session, flash

# 导入用户服务
from app.services.user_service import user_service

# 导入日志模块
import logging

# 获取当前模块的 logger

logger = logging.getLogger(__name__)

# 创建名为 "auth" 的 Blueprint 实例
bp = Blueprint("auth", __name__)


# 定义根路径的路由和视图函数
@bp.route("/")
def home():
    # 首页视图，返回 home.html 模板
    """首页"""
    return render_template("home.html")


# 定义注册页面路由，支持 GET 和 POST 方法


@bp.route("/register", methods=["GET", "POST"])
def register():
    # 注册页面视图
    """注册页面"""
    # 判断请求方法是否为 POST
    if request.method == "POST":
        # 获取用户输入的用户名并去除首尾空格
        username = request.form.get("username", "").strip()
        # 获取用户输入的密码
        password = request.form.get("password", "")
        # 获取用户输入的确认密码
        password_confirm = request.form.get("password_confirm", "")
        # 获取用户输入的邮箱，并去除空格，如果为空则为 None
        email = request.form.get("email", "").strip() or None

        # 验证两次输入的密码是否一致
        if password_confirm != password:
            # 如果两次密码不一致
            flash("两次输入的密码不一致", "error")
            return render_template("register.html")

        try:
            # 调用用户服务进行注册
            user = user_service.register(username, password, email)
            # 注册成功提示并跳转到首页
            flash("注册成功！请登录", "success")
            return redirect(url_for("auth.home"))
        except ValueError as e:
            # 注册时业务逻辑报错，提示具体信息
            flash(str(e), "error")
        except Exception as e:
            # 捕获其他异常并写入日志，提示注册失败
            logger.error(f"Registration error: {e}")
            flash("注册失败，请稍后重试", "error")

    # 如果是 GET 或注册失败则渲染注册页面
    return render_template("register.html")


# 定义 "/login" 路由 支持 get 和 post 方法


@bp.route("/login", methods=["GET", "POST"])
# 定义登陆视图函数
def login():
    # 登录页说明
    """登录页面"""
    # 如果请求为POST方法，表示尝试登陆
    if request.method == "POST":
        # 获取表单中填写的用户名，并去除首位空格
        username = request.form.get("username", "").strip()
        # 获取表单中填写的密码
        password = request.form.get("password", "")
        # 获取登陆后重定向的目标页面（优先表单，其次URL参数）
        next_url = request.form.get("next") or request.args.get("next")
        try:
            user = user_service.login(username, password)
            # 这个session 是flask里的会话字典 和数据库的会话没关系
            # 当登录成功后，把用户ID放在了会话对象里
            session["user_id"] = user["id"]
            # 设置会话为永久有效，默认是31天
            session.permanent = True
            flash("登陆成功", "success")
            return redirect(next_url or url_for("auth.home"))
        except ValueError as e:
            logger.error(f"登录失败:{str(e)}")
            flash(str(e), "error")
        except Exception as e:
            logger.error(f"登录失败:{str(e)}")
            flash("登录失败,请稍后重试", "error")
    # 如果是Get请求或者登录失败，获取URL参数中的next
    next_url = request.args.get("next")
    return render_template("login.html", next_url=next_url)


@bp.route("/logout")
def logout():
    # 清除会话
    session.clear()
    flash("已成功退出", "success")
    return redirect(url_for("auth.home"))
