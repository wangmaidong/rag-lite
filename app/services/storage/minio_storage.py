# MinIO 对象存储实现的说明文档
"""
MinIO 对象存储实现
"""
# 导入日志模块
import logging

# 导入可选类型提示
from typing import Optional

# 导入内存字节流处理
from io import BytesIO

# 导入存储接口基类
from app.services.storage.base import StorageInterface

# 导入minio 类和异常
from minio import Minio

# 导入minio 异常
from minio.error import S3Error

# 获取日志记录器
logger = logging.getLogger(__name__)

# 定义 MinioStorage 类，继承自StorageInterface


class MinIOStorage(StorageInterface):
    # MinIO 对象存储实现
    """MinIO 对象存储实现"""

    # 初始化方法，接受端点、密钥、桶名等参数
    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        secure: bool = False,
        region: Optional[str] = None,
    ):
        """
        初始化 MinIO 存储
        :param endpoint: MinIO 服务端点（如：localhost:9000）
        :param access_key: 访问密钥
        :param secret_key: 秘密密钥
        :param bucket_name:存储桶名称
        :param secure: 是否使用HTTPS
        :param region: 区域（可选）
        """
        # 创建 Minio 客户端实例
        self.client = Minio(
            endpoint,  # MinIO 服务端点（如：localhost:9000）
            access_key=access_key,  # 访问密钥
            secret_key=secret_key,  # 秘密密钥
            secure=secure,  # 是否使用HTTPS
            region=region,  # 区域（可选）
        )
        # 保存桶名称
        self.bucket_name = bucket_name
        # 检查桶是否存在，不存在则创建
        if not self.client.bucket_exists(bucket_name):
            # 创建存储桶
            self.client.make_bucket(bucket_name)
            # 记录桶创建日志
            logger.info(f"已创建桶：{bucket_name}")
        # 记录MinIO初始化完成日志
        logger.info(f"MinIO 存储初始化完成，桶名：{bucket_name}")

    # 上传文件到 MinIO
    def upload_file(
        self,
        file_path: str,
        file_data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """上传文件到MinIO"""
        try:
            # 创建BytesIO流用于上传
            data_stream = BytesIO(file_data)
            # 使用 put_object 方法上传文件
            self.client.put_object(
                self.bucket_name,
                file_path,
                data_stream,
                length=len(file_data),
                content_type=content_type,
            )
            # 上传成功，记录日志
            logger.info(f"已上传文件到 MinIO: {file_path}")
            # 返回文件路径
            return file_path
        except S3Error as e:
            # 上传时报错， 记录日志后抛出异常
            logger.error(f"上传文件到 MinIO 时报错: {e}")
            raise
        except Exception as e:
            # 上传时出现异常，记录日志并抛出
            logger.error(f"上传文件到 MinIO 时发生异常: {e}")
            raise

    # 下载文件方法
    def download_file(self, file_path: str) -> bytes:
        """从MinIO下载文件"""
        try:
            # 获取对象句柄
            response = self.client.get_object(self.bucket_name, file_path)
            # 读取数据
            data = response.read()
            # 关闭响应体
            response.close()
            # 释放连接
            response.release_conn()
            # 记录下载日志
            logger.info(f"已从 MinIO 下载文件: {file_path}")
            # 返回二进制数据
            return data
        except S3Error as e:
            # 如果对象不存在，抛出文件未找到异常
            if e.code == "NoSuchKey":
                raise FileNotFoundError(f"文件不存在：{file_path}")
            # 其他s3错误，记录日志后抛出
            logger.error(f"从MinIO 下载文件时报错：{e}")
            raise
        # 捕获其它异常
        except Exception as e:
            # 下载时发生其他异常，记录并抛出
            logger.error(f"从 MinIO 下载文件时发生异常：{e}")
            raise

    # 删除文件方法
    def delete_file(self, file_path: str) -> None:
        """从MinIO删除文件"""
        try:
            # 调用MinIO API删除文件
            self.client.remove_object(self.bucket_name, file_path)
            # 记录删除日志
            logger.info(f"已从 MinIO 删除文件: {file_path}")
        except S3Error as e:
            # 记录删除时报错日志
            logger.error(f"从 MinIO 删除文件时报错: {e}")
        except Exception as e:
            # 删除文件发生异常，记录并抛出
            logger.error(f"从 MinIO 删除文件时发生异常: {e}")
            raise

    # 判断文件是否存在方法
    def file_exists(self, file_path: str) -> bool:
        """检查文件是否存在于 MinIO"""
        try:
            # 检查对象状态（存在则无异常）
            self.client.stat_object(self.bucket_name, file_path)
            return True
        except S3Error as e:
            # 如果对象不存在，返回 False
            if e.code == "NoSuchKey":
                return False
            raise
        except Exception as e:
            # 检查文件存在时异常，记录并抛出
            logger.error(f"在 MinIO 检查文件是否存在时发生异常: {e}")
            raise

    # 获取文件访问URL方法
    def get_file_url(
        self, file_path: str, expires_in: Optional[int] = None
    ) -> Optional[str]:
        """获取 MinIO 文件的预签名URL"""
        try:
            # 如果未指定过期时间，默认为7天
            if expires_in in None:
                expires_in = 7 * 24 * 3600
            # 生成预签名URl
            url = self.client.presigned_get_object(
                self.bucket_name, file_path, expires=expires_in
            )
            return url
        except S3Error as e:
            # 生成URL时报错，记录日志返回None
            logger.error(f"生成 MinIO 文件预签名URL时报错: {e}")
            return None
        except Exception as e:
            # 发生其它异常，记录日志返回None
            logger.error(f"生成 MinIO 文件预签名URL时发生异常: {e}")
            return None
