"""
存储服务模块
提供统一的存储接口，支持多种存储后端
"""
from app.services.storage.factory import StorageFactory

__all__ = [
    'StorageFactory'
]