# 用户服务
"""
用户服务
"""
# 导入哈希库
import hashlib

# 导入用户模型
from app.models.user import User

# 导入基础服务类
from app.services.base_service import BaseService


# 定义用户服务类，继承自基础服务
class UserService(BaseService[User]):
    # 用户服务的文档说明
    """用户服务"""

    # 静态方法，用于哈希密码
    @staticmethod
    def hash_password(password: str) -> str:
        # 对密码进行哈希处理
        """
        对密码进行哈希处理
        :param password: 原始密码
        :return: 哈希后的密码
        """
        # 使用 SHA256 进行哈希（实际生产环境建议使用 bcrypt）
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    # 注册新用户方法
    def register(self, username: str, password: str, email: str = None) -> dict:
        # 注册新用户
        """
        注册新用户
        :param username:用户名
        :param password:密码
        :param email:邮箱
        :return: 用户信息字典
        Raises:
            ValueError: 如果用户名已存在或其他验证错误
        """
        # 检查用户名和密码是否为空
        if not username or not password:
            raise ValueError("用户名和密码不能为空")
        # 检查用户名长度是否小于3
        if len(username) < 3:
            raise ValueError("用户名至少需要3个字符")
        # 检查密码长度是否小于6:
        if len(password) < 6:
            raise ValueError("密码至少需要6个字符")
        # 开启事务
        with self.transaction() as session:
            # 检查用户名是否已存在
            existing_user = session.query(User).filter_by(username=username).first()
            # 如果用户名已存在则抛出异常
            if existing_user:
                raise ValueError("用户名已存在")
            # 如果邮箱提供了，检查邮箱是否已被注册
            if email:
                existing_email = session.query(User).filter_by(email=email).first()
                # 如果邮箱已存在则抛出异常
                if existing_email:
                    raise ValueError("邮箱已被注册")
            password_hash = self.hash_password(password)
            # 创建用户对象
            user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                is_active=True,
            )
            # 添加新用户到会话
            session.add(user)
            # 刷新会话，获取用户id
            session.flush()
            # 刷新用户实例
            session.refresh(user)
            # 日志记录注册信息
            self.logger.info(f"User registered: {username}")
            # 返回用户信息字典
            return user.to_dict()

    def verify_password(self, password, password_hash):
        return self.hash_password(password) == password_hash

    def login(self, username, password):
        if not username or not password:
            raise ValueError("用户名和密码不能为空")
        with self.session() as db_session:
            existing_user = db_session.query(User).filter_by(username=username).first()
            if not existing_user:
                raise ValueError("此用户不存在")
            if not existing_user.is_active:
                raise ValueError("此用户已被封禁")
            if not self.verify_password(password, existing_user.password_hash):
                raise ValueError("密码错误")
            self.logger.info(f"用户{username}登陆成功")
            return existing_user.to_dict()

    def get_by_id(self, user_id):
        user: User = super().get_by_id(User, user_id)
        if user:
            return user.to_dict()
        else:
            return None


# 创建用户服务实例
user_service = UserService()
