from typing import List

from dao.sqlite.SQLiteDAOService import SQLiteDAO

const_system_user_table_name = "system_user"
const_system_user_table_columns = {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "username": "TEXT NOT NULL",
    "password": "TEXT NOT NULL",
    "email": "TEXT",
    "phone": "TEXT",
    "create_time": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    "update_time": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    "deleted": "INTEGER DEFAULT 0"
}


class SystemUserMapper:
    """
    系统用户映射器
    """

    def __init__(self):
        """
        初始化系统用户映射器
        """
        self.sqlite_dao = SQLiteDAO()

    # DDL 创建表结构
    def ddl_create_table(self):
        """
        创建系统用户表
        """
        tables = self.sqlite_dao.list_tables()
        print(f"数据库中的表: {tables}")
        if const_system_user_table_name in tables:
            print(f"表 {const_system_user_table_name} 已存在")
            return

        is_success = self.sqlite_dao.create_table(const_system_user_table_name, const_system_user_table_columns)
        print(f"用户表创建结果：{is_success}")

    # 根据用户名查询
    def dml_query_by_username(self, usernames: str):
        """
        查询用户表数据
        """
        system_user = self.sqlite_dao.select(
            table_name=const_system_user_table_name,
            columns=None,
            where={"username": ("=", usernames)},
            order_by="update_time DESC",
            limit=1
        )
        print(f"查询用户表数据：{system_user}")
        if len(system_user) > 0:
            system_user = system_user[0]
        return system_user

    # 新增用户
    def dml_create_user(self,
                        username: str,
                        password: str,
                        email: str,
                        phone: str) -> int:
        """
        新增用户
        """
        user_data = {k: v for k, v in locals().items() if k != 'self' and v}

        system_users = self.sqlite_dao.select(
            table_name=const_system_user_table_name,
            columns=None,
            where={"username": ("=", username)},
            order_by="update_time DESC",
            limit=1
        )
        if system_users:
            raise ValueError("用户已存在")

        # 确保必要字段存在
        if "username" not in user_data or "password" not in user_data:
            raise ValueError("用户名和密码不能为空")
        last_id = self.sqlite_dao.insert(const_system_user_table_name, user_data)
        print(f"用户表数据插入结果：{last_id}")
        return last_id

    def dml_delete_user_by_id(self, id: int):
        """
        删除用户
        """
        is_success = self.sqlite_dao.delete(const_system_user_table_name, {"id": id})
        print(f"用户表数据删除结果：{is_success}")
        return is_success


if __name__ == '__main__':
    system_user_mapper = SystemUserMapper()
    # system_user_mapper.ddl_create_table()

    # 查询所有表
    tables = system_user_mapper.sqlite_dao.list_tables()
    print(f"所有表：{tables}")
    # 查询表结构
    columns = system_user_mapper.sqlite_dao.get_table_info(const_system_user_table_name)
    print(f"表字段：{columns}")
    # 插入用户数据
    try:
        system_user_mapper.dml_create_user(username="wangjiawen",
                                           password="123456",
                                           email="wangjiawen@qq.com",
                                           phone="13675831750")
    except ValueError as e:
        print(e)

    # system_user_mapper.sqlite_dao.insert(const_system_user_table_name,
    #                                      {
    #                                          "username": "wangjiawen",
    #                                          "password": "123456",
    #                                          "email": "wangjiawen@qq.com",
    #                                          "phone": "13675831750",
    #                                          "deleted": 1
    #                                      })

    # dml 查询用户数据
    # system_user_mapper.dml_query_by_usernames(usernames=["wangjiawen"])
