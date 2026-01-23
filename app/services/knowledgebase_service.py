# 从基础服务导入BaseService类
from app.services.base_service import BaseService

# 从模型模块导入Knowledgebase类
from app.models.knowledgebase import Knowledgebase


# 定义KnowledgebaseService服务类，继承自BaseService，泛型参数为Knowledgebase
class KnowledgebaseService(BaseService[Knowledgebase]):
    """知识库服务"""

    # 定义创建知识库的方法
    def create(
        self,
        name: str,
        user_id: str,
        description: str = None,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
    ) -> dict:
        """
        创建知识库
        :param name: 知识库名称
        :param user_id: 用户ID
        :param description: 描述
        :param chunk_size: 分块大小
        :param chunk_overlap: 分块重叠
        :return: 创建的知识库字典
        """
        # 启动数据库事务，上下文管理器自动处理提交或回滚
        with self.transaction() as session:
            # 先创建知识库对象
            kb = Knowledgebase(
                name=name,
                user_id=user_id,
                description=description,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
            # 将知识库对象添加到session
            session.add(kb)
            # 刷新session，生成知识库ID， 刷新以获取 ID，但不提交
            session.flush()
            # 刷新kb对象的数据库状态
            session.refresh()
            # 转换 kb 对象为字典，(在session内部，避免分离后出错)
            kb_dict = kb.to_dict()
            # 记录创建知识库的日志
            self.logger.info(f"创建了知识库，ID: {kb.id}")
            # 返回知识库字典信息
            return kb_dict


# 创建KnowledgebaseService的单例对象
kb_service = KnowledgebaseService()
