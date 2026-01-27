# 导入os模块，用于处理文件和路径
import os

# 导入uuid模块，用于生成唯一ID
import uuid

# 导入BaseService基类
from app.services.base_service import BaseService

# 导入Document模型，重命名为DocumentModel
# from app.models.document import Document as DocumentModel

# 导入Knowledgebase知识库模型
from app.models.knowledgebase import Knowledgebase

# 导入存储服务
from app.services.storage_service import storage_service

# 导入配置项
from app.config import Config
