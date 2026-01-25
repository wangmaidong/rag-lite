"""
存储服务工厂
"""
# 导入日志模块
import logging
# 导入可选类型提示
from typing import Optional
# 导入存储服务接口
from app.services.storage.base import StorageInterface
# 导入本地存储服务实现
from app.services.storage.local_storage import LocalStorage
# 导入配置
from app.config import Config

# 获取logger实例
logger = logging.getLogger(__name__)


# 定义存储服务工厂类
class StorageFactory:
    """存储服务工厂"""

    # 定义用于实现单例的静态属性
    _instance: Optional[StorageInterface] = None

    # 定义创建存储服务实例的类方法
    @classmethod
    def create_storage(cls, storage_type: Optional[str] = None, **kwargs) -> StorageInterface:
        """
        创建存储服务实例

        Args:
            storage_type: 存储类型 ('local' 或 'minio')，如果为None则从配置读取
            **kwargs: 存储服务的初始化参数

        Returns:
            存储服务实例
        """
        # 如果没有传递storage_type，则优先从配置读取（默认local）
        if storage_type is None:
            storage_type = getattr(Config, 'STORAGE_TYPE', 'local')

        # 统一转为小写
        storage_type = storage_type.lower()

        # 判断存储类型，如果是local则返回本地存储实例
        if storage_type == 'local':
            # 获取可选的存储目录参数
            storage_dir = kwargs.get('storage_dir')
            return LocalStorage(storage_dir=storage_dir)
        else:
            # 不支持的类型抛出异常
            raise ValueError(f"Unsupported storage type: {storage_type}")

    # 定义获取实例的类方法（用于单例懒加载）
    @classmethod
    def get_instance(cls) -> StorageInterface:
        """
        获取单例存储服务实例（懒加载）

        Returns:
            存储服务实例
        """
        # 如果还未创建实例，则创建一个
        if cls._instance is None:
            cls._instance = cls.create_storage()
        # 返回单例
        return cls._instance