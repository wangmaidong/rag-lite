"""
文档相关路由（视图 + API）
"""

# 从 Flask 导入 Blueprint 和 request，用于定义蓝图和处理请求
from flask import Blueprint, request, flash, redirect, url_for, render_template

# 导入 os 模块，用于文件名后缀等操作
import os

# 导入 logging 模块，用于日志记录
import logging

# 从工具模块导入通用的响应和错误处理函数
from app.blueprints.utils import success_response, error_response, handle_api_error

# 导入文档服务，用于处理文档业务逻辑
from app.services.document_service import document_service
from app.models.document import Document as DocumentModel

# 导入知识库服务
from app.services.knowledgebase_service import kb_service


# 导入配置文件，获取相关配置参数
from app.config import Config
from app.utils.auth import login_required

# 设置日志对象
logger = logging.getLogger(__name__)

# 创建一个名为 'document' 的蓝图
bp = Blueprint("document", __name__)


# 定义一个检查文件扩展名是否合法的辅助函数
def allowed_file(filename):
    # 检查文件名中有小数点并且扩展名在允许的扩展名列表中
    return (
        "." in filename
        and os.path.splitext(filename)[1][1:].lower() in Config.ALLOWED_EXTENSIONS
    )


# 定义上传文档的 API 路由，POST 方法
@bp.route("/api/v1/knowledgebases/<kb_id>/documents", methods=["POST"])
# 使用装饰器统一捕获和处理 API 错误
def api_upload(kb_id):
    """
    上传文档
    :param kb_id: 知识库id
    :return:
    """
    # 如果请求中没有 'file' 字段，返回参数错误
    if "file" not in request.files:
        return error_response("No file part", 400)
    # 从请求中获取上传的文件对象
    file = request.files["file"]
    # 如果用户未选择文件（文件名为空），返回错误
    if file.filename == "":
        return error_response("No file selected", 400)

    # 如果文件类型不被允许（扩展名校验），返回错误
    if not allowed_file(file.filename):
        return error_response(
            f"File type not allowed. Allowed: {', '.join(Config.ALLOWED_EXTENSIONS)}",
            400,
        )
    # 读取上传的文件内容
    file_data = file.read()
    # 检查文件大小是否超过上限
    if len(file_data) > Config.MAX_FILE_SIZE:
        return error_response(
            f"File size exceeds maximum {Config.MAX_FILE_SIZE} bytes", 400
        )
    # 获取前端自定义的文件名（可选）
    custom_name = request.form.get("name")
    # 如果指定了自定义文件名：
    if custom_name:
        # 获取原始文件扩展名
        original_ext = os.path.splitext(file.filename)[1]
        # 如果自定义文件名没有扩展名，自动补上原扩展名
        if not os.path.splitext(custom_name)[1] and original_ext:
            filename = custom_name + original_ext
        else:
            filename = custom_name
    else:
        filename = file.filename
    # 校验最终得到的文件名：为空或只包含空白则报错
    if not filename or not filename.strip():
        return error_response("Filename is required", 400)

    # 校验最终文件名是否包含扩展名
    if "." not in filename:
        return error_response("Filename must have an extension", 400)
    # 调用文档服务上传，返回文档信息字典
    doc_dict = document_service.upload(kb_id, file_data, filename)
    # 返回成功响应及新文档信息
    return success_response(doc_dict)


# 定义路由，处理 POST 请求，API 路径包含待处理文档的ID
@bp.route("/api/v1/documents/<doc_id>/process", methods=["POST"])
@handle_api_error
def api_process(doc_id):
    # 处理文档（API接口），doc_id是传入的文档ID
    try:
        # 调用文档服务方法，提交文档处理任务（异步）
        document_service.process(doc_id)
        # 返回成功响应信息，提示任务已提交
        return success_response({"message": "文档处理任务已提交"})
    except ValueError as e:
        # 捕获业务异常
        return error_response(str(e), 404)
    except Exception as e:
        logger.error(f"处理文档时出错: {e}", exc_info=True)
        # 返回500通用错误响应，附带错误原因
        return error_response(f"处理文档失败: {str(e)}", 500)


# 路由：文档分块列表页面，URL中包含doc_id
@bp.route("/documents/<doc_id>/chunks")
# 需要用户登录
@login_required
def documents_chunks(doc_id):
    # 文档分块列表页面
    """文档分块列表页面"""
    # 根据文档ID获取文档对象
    doc = document_service.get_by_id(DocumentModel, doc_id)
    # 如果文档不存在，提示错误并跳转到知识库列表页面
    if not doc:
        flash("文档不存在", "error")
        return redirect(url_for("knowledgebase.kb_list"))
    # 根据文档的kb_id获取对应的知识库对象
    kb = kb_service.get_by_id(doc.kb_id)
    # 如果知识库不存在，提示错误并跳转到知识库列表页面
    if not kb:
        flash("知识库不存在", "error")
        return redirect(url_for("knowledgebase.kb_list"))
    # 获取分块数据
    try:
        # 动态导入向量数据库服务工厂方法
        from app.services.vectordb.factory import get_vector_db_service

        # 组合向量数据库中的 collection 名称
        collection_name = f"kb_{doc.kb_id}"
        # 获取向量数据库服务实例
        vectordb = get_vector_db_service()
        # 构建过滤条件，只获取当前文档的分块
        filter_dict = {"doc_id": doc_id}
        # 通过similarity_search_with_score方法，检索所有属于该文档的分块
        results = vectordb.similarity_search_with_score(
            collection_name=collection_name, query="", k=10000, filter=filter_dict
        )
        # 提取查询结果中的Document对象，准备排序
        chunks = [doc for doc, _ in results]
        # 按chunk_index进行排序，保证顺序和原始文档一致
        chunks.sort(key=lambda d: d.metadata.get("chunk_index", 0))
        # 初始化分块列表
        chunks_data = []
        # 遍历所有分块对象，整理为前端模板使用的字典格式
        for chunk in chunks:
            chunks_data.append(
                {
                    # 分块ID，如果不存在则尝试兼容chunk_id字段
                    "id": chunk.metadata.get("id")
                    or chunk.metadata.get("chunk_id", ""),
                    # 分块文本内容
                    "content": chunk.page_content,
                    # 分块在文档中的序号
                    "chunk_index": chunk.metadata.get("chunk_index", 0),
                    # 分块的原始数据
                    "metadata": chunk.metadata,
                }
            )
    except Exception as e:
        logger.error(f"获取分块数据失败: {e}")
        chunks_data = []
    # 渲染模板，传递知识库、文档及分块列表数据给页面
    return render_template(
        "document_chunks.html", kb=kb, document=doc.to_dict(), chunks=chunks_data
    )


@bp.route("/api/v1/documents/<doc_id>", methods=["DELETE"])
@handle_api_error
def api_delete(doc_id):
    """删除文档API"""
    try:
        document_service.delete(doc_id)
        return success_response({"message": "文档删除成功"})
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        logger.error(f"删除文档失败：{e}", exc_info=True)
        return error_response(f"删除文档失败:{str(e)}", 500)
