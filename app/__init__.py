# RAG Lite 应用模块说明
""" "
RAG Lite Application
"""

# 导入操作系统的相关模块
import os

# 从flask包导入Flask应用对象
from flask import Flask

# 导入Flask跨域资源共享支持
from flask_cors import CORS

# 导入应用配置类
from app.config import Config

# 导入日志工具，用于获取日志记录器
from app.utils.logger import get_logger

# 导入数据库初始化函数
from app.utils.db import init_db


# 定义创建 Flask 应用的工厂函数
def create_app(config_class=Config):
    # 获取名为当前模块的日志记录器（在函数内部获取，避免模块导入时过早初始化
    logger = get_logger(__name__)
    # 尝试初始化数据库
    try:
        # 输出日志
        logger.info("初始化数据库...")
        # 执行数据库初始化函数
        init_db()
        # 输出日志，表示数据库初始化成功
        logger.info("数据库初始化成功")
    except Exception as e:
        # 输出警告日志，提示数据库初始化失败，并输出异常信息
        logger.warning(f"数据库初始化失败：{e}")
        # 输出警告日志，提示检查数据库是否已存在，并建议手动创建数据表
        logger.warning("请确认数据库已存在，或手动创建数据表")
        pass
    # 创建Flask 应用对象， 并指定模板和静态文件目录
    base_dir = os.path.abspath(os.path.dirname(__file__))
    print("app的__name__", __name__)
    app = Flask(
        __name__,
        # 指定模板文件目录
        template_folder=os.path.join(base_dir, "templates"),
        # 静态文件目录
        static_folder=os.path.join(base_dir, "static"),
    )
    # 从给定配置类加载配置信息到应用
    app.config.from_object(config_class)
    # 启用跨域请求支持
    CORS(app)
    # 记录应用创建日志信息
    logger.info("Flask 应用已创建")

    # 定义首页路由
    @app.route("/")
    def index():
        return "Hello, World!"

    # 返回已配置的 Flask 应用对象
    return app
