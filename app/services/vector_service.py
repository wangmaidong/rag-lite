"""
向量数据库服务
提供统一的向量数据库访问接口
"""
from app.services.vectordb.factory import get_vector_db_service

# 创建默认实例(使用全局设置)
vector_service = get_vector_db_service()
