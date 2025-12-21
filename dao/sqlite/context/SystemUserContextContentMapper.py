from typing import List

from dao.sqlite.SQLiteDAOService import SQLiteDAO

const_system_user_context_content_table_name = "system_user_context_content"
const_system_user_context_content_table_columns = {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "user_id": "INTEGER NOT NULL",
    "context_id": "TEXT NOT NULL",
    "content": "TEXT NOT NULL",
    "timestamp_id": "TEXT NOT NULL",
    "create_time": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    "update_time": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    "deleted": "INTEGER DEFAULT 0"
}


class SystemUserContextContentMapper:
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
        if const_system_user_context_content_table_name in tables:
            print(f"表 {const_system_user_context_content_table_name} 已存在")
            return
        is_success = self.sqlite_dao.create_table(const_system_user_context_content_table_name,
                                                  const_system_user_context_content_table_columns)
        print(f"用户表创建结果：{is_success}")

    def query_by_user_id_and_context_id(self, user_id: int, context_id: int) -> List[dict]:
        system_user_context_contents = self.sqlite_dao.select(
            table_name=const_system_user_context_content_table_name,
            columns=None,
            where={"user_id": ("=", user_id), "context_id": ("=", context_id), "deleted": ("=", 0)},
            order_by="create_time ASC"
        )
        return system_user_context_contents

    # dml 插入消息
    def insert_message(self, user_id: int, context_id: int, content: str) -> int:
        """
        插入单条消息
        content 格式: JSON字符串，包含 role 和 message
        例如: {"role": "user", "message": "你好"}
        """
        import time
        timestamp_id = str(int(time.time() * 1000))
        message_data = {
            "user_id": user_id,
            "context_id": str(context_id),
            "content": content,
            "timestamp_id": timestamp_id
        }
        last_id = self.sqlite_dao.insert(const_system_user_context_content_table_name, message_data)
        return last_id

    # dml 批量插入消息
    def insert_messages_batch(self, messages: List[dict]) -> bool:
        """
        批量插入消息
        messages 格式: [{"user_id": 1, "context_id": 1, "content": "{...}"}, ...]
        """
        import time
        for msg in messages:
            if "timestamp_id" not in msg:
                msg["timestamp_id"] = str(int(time.time() * 1000))
            if "context_id" in msg:
                msg["context_id"] = str(msg["context_id"])

        try:
            for msg in messages:
                self.sqlite_dao.insert(const_system_user_context_content_table_name, msg)
            return True
        except Exception as e:
            print(f"批量插入消息失败: {e}")
            return False


if __name__ == '__main__':
    pass
