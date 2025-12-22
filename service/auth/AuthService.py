from typing import Optional
from datetime import datetime

from dao.memory.UserMemory import UserInfoType
from dao.memory.UserMemory import user_memory
from dao.sqlite.system.SystemUserMapper import SystemUserMapper


class AuthService:
    """
    认证服务
    提供用户登录、登出和获取当前登录用户信息的功能
    """

    def __init__(self):
        self.system_user_mapper = SystemUserMapper()
        pass

    def login(self, user_info: UserInfoType) -> None:
        """
        用户登录
        Args:
            user_info: 用户信息字典，必须包含 username、email、phone 字段
                       例如：{"id": 1, "username": "alice", "email": "alice@example.com", "phone": "13800138000"}

        Raises:
            ValueError: 如果用户信息为空或缺少必填字段
        """
        if not user_info:
            raise ValueError("用户信息不能为空")
            # 验证必填字段
        if "username" not in user_info or not user_info.get("username"):
            raise ValueError("用户名不能为空")
        if "password" not in user_info or not user_info.get("password"):
            raise ValueError("密码不能为空")

        query_system_user = self.system_user_mapper.dml_query_by_username(user_info.get("username"))
        if not user_info:
            raise ValueError("数据库中用户不存在")
        if query_system_user["password"] != user_info.get("password"):
            raise ValueError("密码错误")

        memory_user_info: UserInfoType = {
            "id": query_system_user["id"],
            "username": query_system_user["username"],
            "email": query_system_user["email"],
            "phone": query_system_user["phone"],
            "login_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        user_memory.save(memory_user_info)
        current_user = user_memory.get_current_user()
        return current_user

    @staticmethod
    def logout():
        current_user = user_memory.get_current_user()
        if current_user:
            print("    用户登出（清空内容）")
            print(f"   当前用户: {current_user}")
            print(f"   用户类型: {type(current_user)}")
            print(f"   用户名: {current_user['username']}")
            print(f"   登录时间: {current_user.get('login_time')}")
        user_memory.logout()

    @staticmethod
    def get_current_user() -> Optional[UserInfoType]:
        """
        获取当前登录用户信息
        Returns:
            当前登录用户信息（UserInfoType 类型），如果未登录则返回 None
            返回的是用户信息的副本，避免外部修改影响内部数据
        """
        current_user = user_memory.get_current_user()
        return current_user
