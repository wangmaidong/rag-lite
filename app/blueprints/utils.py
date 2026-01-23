"""
路由工具函数
"""

# 导入Flask用于返回JSON响应
from flask import jsonify

# 导入装饰器工具，用来保持原函数信息
from functools import wraps

# 导入获取当前用户的工具函数
from app.utils.auth import get_current_user

# 导入日志模块
import logging

# 获取logger对象（当前模块名）
logger = logging.getLogger(__name__)


# 定义成功响应函数
def success_response(data=None, message="success"):
    """
    成功响应
    :param data:响应数据
    :param message:响应消息
    :return:JSON 响应
    """
    # 返回标准格式的JSON成功响应
    # 状态码200，表示成功
    # 响应消息
    # 响应数据
    return jsonify({"code": 200, "message": message, "data": data}), 200


# 定义错误响应函数
def error_response(message: str, code: int = 400):
    """
    错误响应

    Args:
        message: 错误消息
        code: HTTP 状态码

    Returns:
        JSON 响应和状态码
    """
    # 返回标准格式的JSON错误响应，以及相应的HTTP状态码
    return (
        jsonify(
            {
                "code": code,  # 错误码，对应HTTP状态码
                "message": message,  # 错误消息
                "data": None,  # 错误时无数据
            }
        ),
        code,
    )


# 定义API错误处理装饰器
def handle_api_error(func):
    """
    API错误处理装饰器
    :param func:
    :return:
    使用示例:
        @handle_api_error
        def my_api():
            # API 逻辑
            return success_response(data)
    """

    # 保留原函数信息并定义包装器
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            # 正常执行被装饰的API函数
            return func(*args, **kwargs)
        except ValueError as e:
            # 捕获ValueError, 日志记录warning信息并返回400错误响应
            logger.warning(f"ValueError in {func.__name__}: {e}")
            return error_response(str(e), 400)
        except Exception as e:
            # 捕获其他所有异常，日志记录error信息并返回500错误响应
            logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
            return error_response(str(e), 500)

    # 返回包装后的函数
    return wrapper
