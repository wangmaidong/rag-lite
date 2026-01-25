"""
存储服务抽象接口
"""
# 导入抽象基类和抽象方法装饰器
from abc import ABC, abstractmethod
# 导入可选类型提示
from typing import Optional

# 定义存储服务抽象接口类，继承自ABC
class StorageInterface(ABC):
    """存储服务抽象接口"""

    # 定义抽象方法：上传文件
    @abstractmethod
    def upload_file(self, file_path: str, file_data: bytes,
                   content_type: str = 'application/octet-stream') -> str:
        """
        上传文件

        Args:
            file_path: 文件路径（相对路径）
            file_data: 文件数据（bytes）
            content_type: 内容类型

        Returns:
            文件路径
        """
        # 方法体由子类实现
        pass

    # 定义抽象方法：下载文件
    @abstractmethod
    def download_file(self, file_path: str) -> bytes:
        """
        下载文件

        Args:
            file_path: 文件路径

        Returns:
            文件数据（bytes）
        """
        # 方法体由子类实现
        pass

    # 定义抽象方法：删除文件
    @abstractmethod
    def delete_file(self, file_path: str) -> None:
        """
        删除文件

        Args:
            file_path: 文件路径
        """
        # 方法体由子类实现
        pass

    # 定义抽象方法：检查文件是否存在
    @abstractmethod
    def file_exists(self, file_path: str) -> bool:
        """
        检查文件是否存在

        Args:
            file_path: 文件路径

        Returns:
            是否存在
        """
        # 方法体由子类实现
        pass

    # 定义抽象方法：获取文件访问URL，可选
    @abstractmethod
    def get_file_url(self, file_path: str, expires_in: Optional[int] = None) -> Optional[str]:
        """
        获取文件访问URL（可选，某些存储后端支持）

        Args:
            file_path: 文件路径
            expires_in: URL过期时间（秒），None表示永久

        Returns:
            文件URL，如果不支持则返回None
        """
        # 方法体由子类实现
        pass