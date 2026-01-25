"""
本地文件系统存储实现
"""
# 导入os模块
import os
# 导入日志模块
import logging
# 导入路径操作类
from pathlib import Path
# 导入可选类型提示
from typing import Optional
# 导入存储接口基类
from app.services.storage.base import StorageInterface
# 导入配置信息
from app.config import Config

# 获取logger实例
logger = logging.getLogger(__name__)


class LocalStorage(StorageInterface):
    """本地文件系统存储实现"""

    # 初始化本地存储
    def __init__(self, storage_dir: Optional[str] = None):
        """
        初始化本地存储

        Args:
            storage_dir: 存储目录，如果为None则使用配置中的值
        """
        # 如果没有传入存储目录，则用配置中的存储目录
        if storage_dir is None:
            storage_dir = Config.STORAGE_DIR

        # 判断路径是否为绝对路径
        if os.path.isabs(storage_dir):
            # 如果是绝对路径，直接用
            self.storage_dir = Path(storage_dir)
        else:
            # 如果是相对路径，则以项目根目录为基准
            base_dir = Path(__file__).parent.parent.parent.parent
            self.storage_dir = base_dir / storage_dir

        # 确保存储目录存在，创建多级目录
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        # 记录初始化日志
        logger.info(f"本地存储已初始化，目录：{self.storage_dir}")

    # 获取文件的完整路径
    def _get_full_path(self, file_path: str) -> Path:
        """获取文件的完整路径"""
        # 拼接存储目录和文件路径
        return self.storage_dir / file_path

    # 上传文件到本地存储
    def upload_file(self, file_path: str, file_data: bytes,
                   content_type: str = 'application/octet-stream') -> str:
        """上传文件到本地存储"""
        try:
            # 获取文件完整路径
            full_path = self._get_full_path(file_path)
            # 创建父目录（如果不存在）
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # 写入文件内容
            with open(full_path, 'wb') as f:
                f.write(file_data)

            # 记录日志
            logger.info(f"文件已上传：{file_path}")
            # 返回文件相对路径
            return file_path
        except Exception as e:
            # 上传失败，记录错误日志，继续抛出异常
            logger.error(f"上传文件出错：{e}")
            raise

    # 从本地存储下载文件
    def download_file(self, file_path: str) -> bytes:
        """从本地存储下载文件"""
        try:
            # 获取文件完整路径
            full_path = self._get_full_path(file_path)
            # 文件不存在则抛出异常
            if not full_path.exists():
                raise FileNotFoundError(f"文件不存在：{file_path}")

            # 读取文件内容
            with open(full_path, 'rb') as f:
                data = f.read()

            # 记录日志
            logger.info(f"文件已下载：{file_path}")
            # 返回文件数据
            return data
        except Exception as e:
            # 下载出现异常，记录日志并抛出异常
            logger.error(f"下载文件出错：{e}")
            raise

    # 删除本地存储文件
    def delete_file(self, file_path: str) -> None:
        """删除文件"""
        try:
            # 获取文件完整路径
            full_path = self._get_full_path(file_path)
            # 如果文件存在则删除
            if full_path.exists():
                full_path.unlink()
                # 记录日志
                logger.info(f"文件已删除：{file_path}")

                # 尝试删除父目录（为空才能删，主要防止目录冗余）
                try:
                    full_path.parent.rmdir()
                except OSError:
                    # 如果目录不为空，忽略该异常
                    pass
        except Exception as e:
            # 删除文件时出错
            logger.error(f"删除文件出错：{e}")
            raise

    # 检查文件是否存在
    def file_exists(self, file_path: str) -> bool:
        """检查文件是否存在"""
        # 获取文件完整路径
        full_path = self._get_full_path(file_path)
        # 判断文件是否存在
        return full_path.exists()

    # 获取文件URL，本地存储不支持直接返回None
    def get_file_url(self, file_path: str, expires_in: Optional[int] = None) -> Optional[str]:
        """本地存储不支持URL，返回None"""
        return None