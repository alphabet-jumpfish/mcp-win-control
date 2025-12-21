from typing import List

from dao.sqlite.SQLiteDAOService import SQLiteDAO

const_system_user_context_table_name = "system_user_context"
const_system_user_context_table_columns = {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "user_id": "INTEGER NOT NULL",
    "context_name": "TEXT NOT NULL",
    "timestamp_id": "TEXT NOT NULL",
    "create_time": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    "update_time": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    "deleted": "INTEGER DEFAULT 0"
}


class SystemUserContextMapper:
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
        # 查看表是否存在
        tables = self.sqlite_dao.list_tables()
        print(f"数据库中的表: {tables}")
        if const_system_user_context_table_name in tables:
            print(f"表 {const_system_user_context_table_name} 已存在")
            return
        is_success = self.sqlite_dao.create_table(const_system_user_context_table_name,
                                                  const_system_user_context_table_columns)
        print(f"用户上下文表创建结果：{is_success}")

    # dml 创建用户上下文
    def dml_create_user_context(self, user_id: int, context_name: str) -> int:
        import time
        timestamp_id = str(int(time.time() * 1000))
        user_context_data = {
            "user_id": user_id,
            "context_name": context_name,
            "timestamp_id": timestamp_id
        }
        last_id = self.sqlite_dao.insert(const_system_user_context_table_name, user_context_data)
        return last_id

    # dml 查询用户上下文[最近]
    def query_recent_context_by_user_id(self, user_id: int) -> List[dict]:
        """
                根据用户ID查询用户上下文
                """
        system_user_contexts = self.sqlite_dao.select(
            table_name=const_system_user_context_table_name,
            columns=None,
            where={"user_id": ("=", user_id)},
            order_by="update_time DESC",
            limit=1
        )
        if system_user_contexts:
            return system_user_contexts[0]
        return None

    # dml 查询用户上下文
    def query_by_user_id(self, user_id: int) -> List[dict]:
        """
        根据用户ID查询用户上下文
        """
        system_user_contexts = self.sqlite_dao.select(
            table_name=const_system_user_context_table_name,
            columns=None,
            where={"user_id": ("=", user_id), "deleted": ("=", 0)},
            order_by="update_time DESC"
        )
        return system_user_contexts

    # dml 更新上下文名称
    def update_context_name(self, context_id: int, new_name: str) -> bool:
        """
        更新上下文名称
        """
        update_data = {"context_name": new_name}
        rows_affected = self.sqlite_dao.update(
            table_name=const_system_user_context_table_name,
            data=update_data,
            where={"id": context_id}
        )
        return rows_affected > 0

    # dml 删除上下文（软删除）
    def delete_context(self, context_id: int) -> bool:
        """
        删除上下文（软删除）
        """
        update_data = {"deleted": 1}
        rows_affected = self.sqlite_dao.update(
            table_name=const_system_user_context_table_name,
            data=update_data,
            where={"id": context_id}
        )
        return rows_affected > 0

    # dml 按名称搜索上下文
    def search_context_by_name(self, user_id: int, keyword: str) -> List[dict]:
        """
        按名称搜索上下文
        """
        system_user_contexts = self.sqlite_dao.select(
            table_name=const_system_user_context_table_name,
            columns=None,
            where={"user_id": ("=", user_id), "deleted": ("=", 0)},
            order_by="update_time DESC"
        )
        # 手动过滤包含关键词的上下文
        if keyword:
            system_user_contexts = [ctx for ctx in system_user_contexts if keyword.lower() in ctx.get("context_name", "").lower()]
        return system_user_contexts

    # dml 更新上下文的更新时间
    def update_context_time(self, context_id: int) -> bool:
        """
        更新上下文的更新时间（用于标记最近使用）
        """
        import time
        from datetime import datetime
        update_data = {"update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        rows_affected = self.sqlite_dao.update(
            table_name=const_system_user_context_table_name,
            data=update_data,
            where={"id": context_id}
        )
        return rows_affected > 0


if __name__ == '__main__':
    pass
