"""
内存用户信息存储服务
提供当前登录用户信息的本地内存存储、清空和查询功能
用于管理用户登录会话状态
"""
from typing import Dict, Optional, Any, TypedDict
from datetime import datetime


class UserInfoType(TypedDict, total=False):
    id: Optional[int]
    username: str
    password: str
    email: str
    phone: str
    login_time: Optional[str]
    last_active_time: Optional[str]


class UserMemory:
    """
    用户信息内存存储访问对象
    用于存储和管理当前登录用户的信息
    """

    def __init__(self):
        """
        初始化用户内存存储
        存储当前登录用户的信息
        """
        self._current_user: Optional[UserInfoType] = None

    def save(self, user_info: UserInfoType) -> None:
        """
        用户登录时持久化用户信息
        
        Args:
            user_info: 用户信息字典，必须包含 username、email、phone 字段
                       例如：{"id": 1, "username": "alice", "email": "alice@example.com", "phone": "13800138000"}
        
        Raises:
            ValueError: 如果用户信息为空或缺少必填字段
        
        Example:
            # >>> from dao.memory.UserMemory import user_memory
            # >>> user_memory.login({"id": 1, "username": "alice", "email": "alice@example.com", "phone": "13800138000"})
        """
        if not user_info:
            raise ValueError("用户信息不能为空")
        # 验证必填字段
        if "username" not in user_info or not user_info.get("username"):
            raise ValueError("用户名不能为空")
        if "email" not in user_info or not user_info.get("email"):
            raise ValueError("邮箱不能为空")
        if "phone" not in user_info or not user_info.get("phone"):
            raise ValueError("电话不能为空")

        # 构建符合 UserInfoType 的用户信息
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        persisted_user_info: UserInfoType = {
            "id": user_info.get("id"),
            "username": user_info["username"],
            "email": user_info["email"],
            "phone": user_info["phone"],
            "login_time": current_time,
            "last_active_time": current_time
        }

        # 持久化用户信息
        self._current_user = persisted_user_info
        print(f"用户登录成功: {persisted_user_info['username']}")

    def logout(self) -> None:
        """
        用户登出时清空用户信息
        
        Example:
            # >>> from dao.memory.UserMemory import user_memory
            # >>> user_memory.logout()
        """
        if self._current_user:
            username = self._current_user.get('username', 'Unknown')
            # 清空用户信息
            self._current_user = None
            print(f"用户登出成功: {username}")
        else:
            print("当前没有登录用户")

    def get_current_user(self) -> Optional[UserInfoType]:
        """
        获取当前登录用户信息
        
        Returns:
            当前登录用户信息（UserInfoType 类型），如果未登录则返回 None
            返回的是用户信息的副本，避免外部修改影响内部数据
        
        Example:
            # >>> from dao.memory.UserMemory import user_memory
            # >>> user = user_memory.get_current_user()
            # >>> if user:
            # ...     print(f"当前用户: {user['username']}")
        """
        if self._current_user:
            # 返回用户信息的副本，确保类型为 UserInfoType
            return dict(self._current_user)
        return None


# 创建全局实例，供整个应用使用
# 使用方式：
#   from dao.memory.UserMemory import user_memory
#   user_memory.save(user_info)
#   current_user = user_memory.get_current_user()
#   user_memory.logout()
user_memory = UserMemory()

if __name__ == '__main__':
    # 测试示例
    print("=" * 60)
    print("UserMemory 测试")
    print("=" * 60)

    # 使用全局实例（推荐方式）
    # 在其他模块中：from dao.memory.UserMemory import user_memory
    from dao.memory.UserMemory import user_memory

    # 1. 用户登录
    print("\n1. 用户登录")
    user_info: UserInfoType = {
        "id": 1,
        "username": "alice",
        "email": "alice@example.com",
        "phone": "13800138000"
    }
    user_memory.save(user_info)

    # 2. 获取当前登录用户（返回 UserInfoType）
    print("\n2. 获取当前登录用户")
    current_user = user_memory.get_current_user()
    if current_user:
        print(f"   当前用户: {current_user}")
        print(f"   用户类型: {type(current_user)}")
        print(f"   用户名: {current_user['username']}")
        print(f"   登录时间: {current_user.get('login_time')}")
    else:
        print("   未登录")

    # 3. 用户登出（清空内容）
    print("\n3. 用户登出（清空内容）")
    user_memory.logout()

    # 4. 再次获取当前用户（应该为空）
    print("\n4. 登出后获取当前用户")
    current_user = user_memory.get_current_user()
    if current_user:
        print(f"   当前用户: {current_user}")
    else:
        print("   未登录（正确，内容已清空）")

    # 5. 演示全局实例的特性
    print("\n5. 演示全局实例特性")
    print("   在模块A中登录...")
    user_memory.save({
        "id": 2,
        "username": "bob",
        "email": "bob@example.com",
        "phone": "13900139000"
    })

    print("   在模块B中获取（应该是同一个实例）...")
    from dao.memory.UserMemory import user_memory as user_memory_b

    user_b = user_memory_b.get_current_user()
    if user_b:
        print(f"   模块B获取到的用户: {user_b['username']}")
    print(f"   是同一个实例: {user_memory is user_memory_b}")

    # 6. 测试必填字段验证
    print("\n6. 测试必填字段验证")
    try:
        user_memory.save({"username": "test"})  # 缺少 email 和 phone
    except ValueError as e:
        print(f"   预期错误: {e}")
