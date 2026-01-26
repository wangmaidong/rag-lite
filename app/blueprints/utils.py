"""
路由工具函数
"""

# 导入Flask用于返回JSON响应
from flask import jsonify, request

# 导入装饰器工具，用来保持原函数信息
from functools import wraps

# 导入获取当前用户的工具函数
from app.utils.auth import get_current_user

# 导入类型提示
from typing import Tuple, Optional

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


# 定义获取分页参数的函数，允许指定最大每页数量
def get_pagination_params(max_page_size: int = 1000) -> Tuple[int, int]:
    """
    获取分页参数
    Args:
        max_page_size: 最大每页数量
    Returns:
        (page, page_size) 元组
    """
    # 获取请求中的 'page' 参数，默认为1，并将其转换为整数
    page = int(request.args.get("page", 1))
    # 获取请求中的 'page_size' 参数，默认为10，并将其转换为整数
    page_size = int(request.args.get("page_size", 10))
    # 保证page 至少为1
    page = max(1, page)
    # 保证 page_size 至少为1且不超过 max_page_size
    page_size = max(1, min(page_size, max_page_size))

    # 返回分页的(page, page_size)元组
    return page, page_size


# 定义获取当前用户或返回错误的函数
def get_current_user_or_error():
    """
    获取当前用户，如果未登录则返回错误响应
    Returns:
        如果成功返回 (user_dict, None)，如果失败返回 (None, error_response)
    """
    # 调用get_current_user()获取当前用户对象
    current_user = get_current_user()
    # 如果没有获取到用户，则返回（None，错误相应）
    if not current_user:
        return None, error_response("Unauthorized", 401)
    # 如果获取到用户，则返回(用户对象,None)
    return current_user, None


# 定义检查资源所有权的函数，判断当前用户是否为资源所有者
def check_ownership(
    entity_user_id: str, current_user_id: str, entity_name: str = "资源"
) -> Tuple[bool, Optional[Tuple]]:
    # 检查所有资源所属用户ID是否与当前用户ID相同
    if entity_user_id != current_user_id:
        # 如果不同，返回False，并返回403未授权的错误响应
        return False, error_response(f"Unauthorized to access this {entity_name}", 403)
    # 如果相同，则有权限，返回True和None
    return True, None
