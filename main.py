# 应用启动入口说明
"""
应用启动入口
"""

# 导入操作系统相关模块
import os

# 从 app 包导入创建 Flask 应用的工厂函数
from app import create_app

# 导入应用配置类
from app.config import Config

# 导入日志获取方法（日志系统会在首次使用时自动从 Config 获取配置并初始化）
from app.utils.logger import get_logger

# 获取当前模块日志记录器（会自动初始化日志系统）
logger = get_logger(__name__)


# 仅当直接运行该文件时才执行以下代码
if __name__ == "__main__":
    # 创建 Flask 应用对象
    app = create_app()

    # 记录应用启动的信息到日志
    logger.info(f"Starting  RAG Lite server on {Config.APP_HOST}:{Config.APP_PORT}")

    # 启动 Flask 应用，监听指定主机和端口，是否开启调试模式由配置决定
    app.run(host=Config.APP_HOST, port=Config.APP_PORT, debug=Config.APP_DEBUG)
