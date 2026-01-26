"""
知识库相关路由（视图 + API）
"""

# 导入Flask中的相关模块
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    abort,
    send_file,
)

from io import BytesIO

# 导入logging模块
import logging

# 导入 mimetypes 模块用于判断类型
import mimetypes

# 导入os模块用于路径操作
import os

# 导入认证工具函数：登录认证装饰器、获取当前用户、API登录认证装饰器
from app.utils.auth import login_required, api_login_required, get_current_user

# 导入自定义工具函数：异常处理装饰器、错误响应、成功响应
from app.blueprints.utils import (
    success_response,
    error_response,
    handle_api_error,
    get_pagination_params,
    get_current_user_or_error,
    check_ownership,
)

# 导入知识库服务
from app.services.knowledgebase_service import kb_service

# 导入存储服务
from app.services.storage_service import storage_service

# 配置logger
logger = logging.getLogger(__name__)
# 创建Blueprint实例，注册在Flask应用下
bp = Blueprint("knowledgebase", __name__)

# 定义路由：POST请求到/api/v1/kb


@bp.route("/api/v1/kb", methods=["POST"])
# 应用API登录认证装饰器
@api_login_required
# 应用自定义异常处理装饰器
@handle_api_error
# 定义创建知识库的视图函数
def api_create():
    # 设置接口功能描述
    """创建知识库"""
    # 获取当前用户，如未返回则返回错误响应
    current_user, err = get_current_user_or_error()
    if err:
        return err
    user_id = current_user["id"]
    # 检查请求是否为multipart/form-data（用于文件上传的表单方式）
    if request.content_type and "multipart/form-data" in request.content_type:
        # 从表单数据中获取知识库名称
        name = request.form.get("name")
        # 如果为传入name参数，返回错误
        if not name:
            return error_response("name is required", 400)
        # 获取描述字段，没有则为None
        description = request.form.get("description") or None
        # 获取分块大小，默认为512
        chunk_size = int(request.form.get("chunk_size", 512))
        # 获取分块重叠，默认为50
        chunk_overlap = int(request.form.get("chunk_overlap", 50))
        # 设置封面图片数据变量初值为None
        cover_image_data = None
        # 设置封面图片文件名变量初值为None
        cover_image_filename = None
        # 判断请求中是否包含'cover_image'文件
        if "cover_image" in request.files:
            # 获取上传的封面图片文件对象
            cover_file = request.files["cover_image"]
            # 如果上传的封面图片存在且有文件名
            if cover_file and cover_file.filename:
                # 读取文件内容为二进制数据
                cover_image_data = cover_file.read()
                # 获取上传文件的文件名
                cover_image_filename = cover_file.filename
                # 记录封面图片上传的信息到日志，包括文件名、字节大小和内容类型
                logger.info(
                    f"收到新知识库的封面图片上传: 文件名={cover_image_filename}, 大小={len(cover_image_data)} 字节, 内容类型={cover_file.content_type}"
                )
    else:
        # 从请求中解析JSON数据
        data = request.get_json()
        # 校验数据是否存在以及name键是否存在
        if not data or "name" not in data:
            # 若校验失败，返回错误响应
            return error_response("name is required", 400)
        # 获取知识库名称
        name = data["name"]
        # 获取用户id, 可为空
        user_id = data.get("user_id")
        # 获取知识库描述，可为空
        description = data.get("description")
        # 获取分块大小，默认为512
        chunk_size = data.get("chunk_size", 512)
        # 获取分块重叠，默认为50
        chunk_overlap = data.get("chunk_overlap", 50)
        # 设置封面图片数据变量初值为None
        cover_image_data = None
        # 设置封面图片文件名变量初值为None
        cover_image_filename = None
    # 调用知识库服务创建知识库，返回信息字典
    kb_dict = kb_service.create(
        name=name,  # 知识库名称
        user_id=user_id,  # 用户ID
        description=description,  # 知识库描述
        chunk_size=chunk_size,  # 分块大小
        chunk_overlap=chunk_overlap,  # 分块重叠
        cover_image_data=cover_image_data,  # 封面图片数据
        cover_image_filename=cover_image_filename,  # 封面图片文件名
    )

    return success_response(kb_dict)


# 注册'/kb'路由，处理GET请求，显示知识库列表页面
@bp.route("/kb")
# 要求登录用户才能访问该视图，用于Web页面
@login_required
# 定义kb_list函数，渲染知识库列表页面
def kb_list():
    """
    知识库列表页面
    Returns:

    """
    # 获取当前登录用户信息
    current_user = get_current_user()
    # 获取分页参数（页码和每页大小），最大每页100
    page, page_size = get_pagination_params(max_page_size=100)
    # 获取搜索和排序参数
    search = request.args.get("search", "").strip() or None
    sort_by = request.args.get("sort_by", "created_at")
    sort_order = request.args.get("sort_order", "desc")
    # 验证排序参数
    if sort_by not in ["created_at", "name", "updated_at"]:
        sort_by = "created_at"
    if sort_order not in ["asc", "desc"]:
        sort_order = "desc"

    # 调用知识库服务，获取分页后的知识库列表结果
    result = kb_service.list(
        user_id=current_user["id"],  # 用户ID
        page=page,
        page_size=page_size,  # 每页大小
        search=search,  # 搜索关键词
        sort_by=sort_by,  # 排序字段
        sort_order=sort_order,  # 排序方向
    )
    return render_template(
        "kb_list.html",
        kbs=result["items"],
        pagination=result,
        search=search or "",
        sort_by=sort_by,
        sort_order=sort_order,
    )


# 删除知识库
@bp.route("/api/v1/kb/<kb_id>", methods=["DELETE"])
@api_login_required
@handle_api_error
def api_delete(kb_id):
    """删除知识库"""
    # 尝试获取当前用户
    current_user, err = get_current_user_or_error()
    if err:
        return err
    kb_dict = kb_service.get_by_id(kb_id)
    if not kb_dict:
        return error_response("未找到知识库", 404)
    # 验证用户是否有权限访问该知识库
    has_permission, err = check_ownership(
        kb_dict["user_id"], current_user["id"], "knowledgebase"
    )
    if not has_permission:
        return err
    success = kb_service.delete(kb_id)
    if not success:
        return error_response("未找到知识库", 404)
    return success_response("知识库删除成功")


# 更新知识库
# 注册PUT方法的API路由，用于更新知识库
@bp.route("/api/v1/kb/<kb_id>", methods=["PUT"])
@api_login_required
@handle_api_error
def api_update(kb_id):
    """
    更新知识库（支持封面图片更新）
    Args:
        kb_id: 知识库id

    Returns:

    """
    current_user, err = get_current_user_or_error()
    if err:
        return err
    # 获取并校验知识库是否存在
    kb_dict = kb_service.get_by_id(kb_id)
    if not kb_dict:
        return error_response("未找到知识库", 404)
    # 检查是否拥有操作该知识库的权限
    has_permission, err = check_ownership(
        kb_dict["user_id"], current_user["id"], "knowledgebase"
    )
    if not has_permission:
        return err
    # 检查请求内容类型是否为multipart/form-data（用于文件上传）
    if request.content_type and "multipart/form-data" in request.content_type:
        # 从表单数据获取字段
        name = request.form.get("name")
        description = request.form.get("description") or None
        chunk_size = request.form.get("chunk_size")
        chunk_overlap = request.form.get("chunk_overlap")
        # 初始化封面图片相关变量
        cover_image_data = None
        cover_image_filename = None
        # 获得delete_cover字段（类型字符串，需判断是否为'true'）
        delete_cover = request.form.get("delete_cover") == "true"
        if "cover_image" in request.files:
            # 获取上传的封面图片文件对象
            cover_file = request.files["cover_image"]
            # 如果上传的封面图片存在且有文件名
            if cover_file and cover_file.filename:
                # 读取文件内容为二进制数据
                cover_image_data = cover_file.read()
                # 获取上传文件的文件名
                cover_image_filename = cover_file.filename
                # 记录封面图片上传的信息到日志，包括文件名、字节大小和内容类型
                logger.info(
                    f"收到新知识库的封面图片上传: 文件名={cover_image_filename}, 大小={len(cover_image_data)} 字节, 内容类型={cover_file.content_type}"
                )
        # 组装待更新的数据字典
        update_data = {}
        if name:
            update_data["name"] = name
        if description:
            update_data["description"] = description
        if chunk_size:
            update_data["chunk_size"] = chunk_size
        if chunk_overlap:
            update_data["chunk_overlap"] = chunk_overlap
    else:
        # 如果不是form-data，则按JSON方式解析提交内容
        data = request.get_json()
        if not data:
            return error_response("请求体不能为空", 400)
        update_data = {}
        if "name" in data:
            update_data["name"] = data["name"]
        if "description" in data:
            update_data["description"] = data.get("description")
        if "chunk_size" in data:
            update_data["chunk_size"] = data["chunk_size"]
        if "chunk_overlap" in data:
            update_data["chunk_overlap"] = data["chunk_overlap"]
        # JSON请求时，cover_image相关变量置空
        cover_image_data = None
        cover_image_filename = None
        delete_cover = data.get("delete_cover", False)
    # 调用服务进行知识库更新
    updated_kb = kb_service.update(
        kb_id=kb_id,  # 知识库ID
        cover_image_data=cover_image_data,  # 封面图片的二进制内容
        cover_image_filename=cover_image_filename,  # 封面图片文件名
        delete_cover=delete_cover,  # 是否删除封面图片
        **update_data,
    )
    # 如果未找到知识库，返回404
    if not updated_kb:
        return error_response("未找到知识库", 404)
    return success_response(updated_kb, "知识库更新成功")


# 定义路由，获取指定知识库ID的封面图片，仅限登录用户访问
@bp.route("/kb/<kb_id>/cover")
@login_required
@handle_api_error
def kb_cover(kb_id):
    """获取知识库封面图片"""
    current_user, error = get_current_user_or_error()
    if error:
        return error
    kb_dict = kb_service.get_by_id(kb_id)
    if not kb_dict:
        return error_response("知识库未找到", 404)
    # 验证用户是否有删除此知识库的权限
    has_permission, err = check_ownership(
        kb_dict["user_id"], current_user["id"], "knowledgebase"
    )
    if not has_permission:
        return err
    # covers/2324bcd410ae433790de1b63eae9aba8.png
    cover_path = kb_dict.get("cover_image")
    if not cover_path:
        logger.info(f"知识库没有设置封面图片")
        abort(404)
    try:
        # 通过存储服务下载封面图片数据
        image_data = storage_service.download_file(cover_path)
        # 如果未能获取到图片数据，记录错误日志并返回404
        if not image_data:
            logger.error(f"从路径下载封面图片失败: {cover_path}")
            abort(404)
        # 根据文件扩展名判断图片MIME类型
        file_ext = os.path.splitext(cover_path)[1].lower()
        # 自定义映射，优先根据文件扩展名判断图片MIME类型
        mime_type_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        # 优先根据自定义映射获取MIME类型
        mime_type = mime_type_map.get(file_ext)
        if not mime_type:
            # 如果没有命中自定义映射，则使用mimetypes猜测类型
            mime_type = mimetypes.guess_type(cover_path)
            if not mime_type:
                # 如果还未识别出类型，则默认用JPEG
                mime_type = "image/jpeg"
        # 通过send_file响应图片数据和MIME类型，不以附件形式发送
        return send_file(
            BytesIO(image_data),  # 图片数据
            mimetype=mime_type,  # MIME类型
            as_attachment=False,  # 不以附件形式发送
        )
    except FileNotFoundError as e:
        # 捕获文件未找到异常，记录错误日志
        logger.error(f"封面图片文件未找到: {cover_path}, 错误: {e}")
        abort(404)
    except Exception as e:
        # 捕获其他未预期异常，记录错误日志（包含堆栈信息）
        logger.error(
            f"提供知识库 {kb_id} 的封面图片时出错, 路径: {cover_path}, 错误: {e}",
            exc_info=True,
        )
        abort(404)
