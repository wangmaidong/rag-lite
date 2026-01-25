# 从 app.services.storage.factory 导入 StorageFactory 类
from app.services.storage.factory import StorageFactory

#获取 StorageFactory 的单例实例，并赋值给storage_service

storage_service = StorageFactory.get_instance()
