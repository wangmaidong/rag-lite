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

# 导入MinIO存储服务实现
from app.services.storage.minio_storage import MinIOStorage

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
    def create_storage(
        cls, storage_type: Optional[str] = None, **kwargs
    ) -> StorageInterface:
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
            storage_type = getattr(Config, "STORAGE_TYPE", "local")

        # 统一转为小写
        storage_type = storage_type.lower()

        # 判断存储类型，如果是local则返回本地存储实例
        if storage_type == "local":
            # 获取可选的存储目录参数
            storage_dir = kwargs.get("storage_dir")
            return LocalStorage(storage_dir=storage_dir)
        elif storage_type == "minio":
            # 优先从参数中获取 endpoint，否则从配置中获取 MINIO_ENDPOINT，没有则为''
            endpoint = kwargs.get("endpoint") or getattr(Config, "MINIO_ENDPOINT", "")
            # 优先从参数中获取 access_key,否则从配置中获取MINIO_ACCESS_KEY ，没有则为“”
            access_key = kwargs.get("access_key") or getattr(
                Config, "MINIO_ACCESS_KEY", ""
            )
            # 优先从参数中获取 secret_key，否则从配置中获取 MINIO_SECRET_KEY，没有则为''
            secret_key = kwargs.get("secret_key") or getattr(
                Config, "MINIO_SECRET_KEY", ""
            )
            # 优先从参数中获取 bucket_name，否则从配置中获取 MINIO_BUCKET_NAME，默认值为 'rag-lite'
            bucket_name = kwargs.get("bucket_name") or getattr(
                Config, "MINIO_BUCKET_NAME", "rag-lite"
            )
            # 优先从参数中获取 secure，否则从配置中获取 MINIO_SECURE，默认值为 False
            secure = kwargs.get("secure", getattr(Config, "MINIO_SECURE", False))
            # 优先从参数中获取 region，否则从配置中获取 MINIO_REGION，默认值为 None
            region = kwargs.get("region", getattr(Config, "MINIO_REGION", None))
            # 如果 endpoint、access_key 或 secret_key 其中任一为空，则抛出 ValueError 异常
            if not endpoint or not access_key or not secret_key:
                raise ValueError(
                    "MinIO 存储需要提供 endpoint、access_key 和 secret_key，请在环境变量中配置或通过参数传递。"
                )
            # 创建并返回 MinIOStorage 实例
            return MinIOStorage(
                endpoint=endpoint,
                access_key=access_key,
                secret_key=secret_key,
                bucket_name=bucket_name,
                secure=secure,
                region=region,
            )
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
