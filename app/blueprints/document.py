"""
文档相关路由（视图 + API）
"""

# 从 Flask 导入 Blueprint 和 request，用于定义蓝图和处理请求
from flask import Blueprint, request

# 导入 os 模块，用于文件名后缀等操作
import os

# 导入 logging 模块，用于日志记录
import logging

# 从工具模块导入通用的响应和错误处理函数
from app.blueprints.utils import success_response, error_response, handle_api_error

# 导入文档服务，用于处理文档业务逻辑
from app.services.document_service import document_service

# 导入配置文件，获取相关配置参数
from app.config import Config

# 设置日志对象
logger = logging.getLogger(__name__)
