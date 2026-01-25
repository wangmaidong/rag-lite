"""
配置管理模块
"""

# 导入操作系统相关模块
import os

# 导入Path模块处理路径
from pathlib import Path

# 导入 dotenv 用于加载 .env 文件中的环境变量
from dotenv import load_dotenv

# 加载 .env文件中的环境变量到系统变量中
load_dotenv()


# 定义应用配置类
class Config:
    """应用配置类"""

    # 基础配置
    # 项目根目录路径（取上级目录）
    BASE_DIR = Path(__file__).parent.parent
    # 加载环境变量 SECRET_KEY，若未设置则使用默认开发密钥
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

    # 应用配置
    # 读取应用监听的主机地址，默认为本地所有地址
    APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
    # 读取应用监听的端口，默认为5000端口
    APP_PORT = os.getenv("APP_PORT", 5000)
    # 读取debug模式配置，字符串转小写等于true，则为True
    APP_DEBUG = os.getenv("APP_DEBUG", "false").lower() == "true"
    # 读取允许上传的最大文件大小，默认为 100MB,类型为int
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 104857600))
    # 允许上传的文件扩展名集合
    ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "md"}
    # 允许上传的图片扩展名集合
    ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
    # 允许上传的图片最大大小，默认为 5MB，类型为 int
    MAX_IMAGE_SIZE = int(os.environ.get('MAX_IMAGE_SIZE', 5242880))  # 5MB

    # 日志配置
    # 日志目录，默认 './logs'
    LOG_DIR = os.environ.get("LOG_DIR", "./logs")
    # 日志文件名，默认 'rag_lite.log'
    LOG_FILE = os.environ.get("LOG_FILE", "rag_lite.log")
    # 日志等级，默认 'INFO'
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    # 是否启用控制台日志，默认 True
    LOG_ENABLE_CONSOLE = os.environ.get("LOG_ENABLE_CONSOLE", "true").lower() == "true"
    # 是否启用文件日志，默认 True
    LOG_ENABLE_FILE = os.environ.get("LOG_ENABLE_FILE", "true").lower() == "true"

    # 数据库配置
    # 数据库主机地址，默认为 'localhost'
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    # 数据库端口号，默认为 3306
    DB_PORT = int(os.environ.get("DB_PORT", 3306))
    # 数据库用户名，默认为 'root'
    DB_USER = os.environ.get("DB_USER", "root")
    # 数据库密码，默认为 'root'
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "root")
    # 数据库名称，默认为 'rag-lite'
    DB_NAME = os.environ.get("DB_NAME", "rag-lite")
    # 数据库字符集，默认为 'utf8mb4'
    DB_CHARSET = os.environ.get("DB_CHARSET", "utf8mb4")


    # 存储配置
    STORAGE_TYPE = os.environ.get('STORAGE_TYPE', 'local')  # 'local' 或 'minio'
    STORAGE_DIR = os.environ.get('STORAGE_DIR', './storage')