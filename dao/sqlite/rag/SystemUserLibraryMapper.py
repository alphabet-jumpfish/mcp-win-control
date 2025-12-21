from typing import List, Optional, Dict, Any

from dao.sqlite.SQLiteDAOService import SQLiteDAO

const_system_user_library_table_name = "system_user_library"
const_system_user_library_table_columns = {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "user_id": "INTEGER NOT NULL",
    "name": "TEXT NOT NULL",
    "doc_ids": "TEXT NOT NULL",
    "content": "TEXT NOT NULL",
    "path": "TEXT NOT NULL",
    "create_time": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    "update_time": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    "deleted": "INTEGER DEFAULT 0"
}


class SystemUserLibraryMapper:
    def __init__(self):
        self.sqlite_dao = SQLiteDAO()

    def ddl_create_table(self):
        tables = self.sqlite_dao.list_tables()
        print(f"数据库中的表: {tables}")
        if const_system_user_library_table_name in tables:
            print(f"表 {const_system_user_library_table_name} 已存在")
            return

        is_success = self.sqlite_dao.create_table(const_system_user_library_table_name,
                                                  const_system_user_library_table_columns)
        print(f"用户知识库创建结果：{is_success}")

        self.sqlite_dao.create_table(const_system_user_library_table_name, const_system_user_library_table_columns)

    def insert(self, user_id: int, name: str, doc_ids: str, content: str, path: str) -> int:
        data = {
            "user_id": user_id,
            "name": name,
            "doc_ids": doc_ids,
            "content": content,
            "path": path
        }
        return self.sqlite_dao.insert(const_system_user_library_table_name, data)

    def delete(self, id: int) -> int:
        condition = {"id": id}
        return self.sqlite_dao.delete(const_system_user_library_table_name, condition)

    def update(self, id: int, data: Dict[str, Any]) -> int:
        condition = {"id": id}
        return self.sqlite_dao.update(const_system_user_library_table_name, data, condition)

    def query_by_user_id(self, user_id: int) -> List[Dict[str, Any]]:
        condition = {"user_id": user_id, "deleted": 0}
        return self.sqlite_dao.query(const_system_user_library_table_name, condition, order_by="update_time DESC")

    def query_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        condition = {"id": id, "deleted": 0}
        results = self.sqlite_dao.query(const_system_user_library_table_name, condition)
        return results[0] if results else None


if __name__ == "__main__":
    mapper = SystemUserLibraryMapper("test_system_library.db")

    print("=== 测试插入方法 ===")
    id1 = mapper.insert(
        user_id=1,
        name="测试库1",
        doc_ids="doc1,doc2,doc3",
        content="这是测试内容1",
        path="/path/to/library1"
    )
    print(f"插入记录1，ID: {id1}")

    id2 = mapper.insert(
        user_id=1,
        name="测试库2",
        doc_ids="doc4,doc5",
        content="这是测试内容2",
        path="/path/to/library2"
    )
    print(f"插入记录2，ID: {id2}")

    id3 = mapper.insert(
        user_id=2,
        name="测试库3",
        doc_ids="doc6,doc7",
        content="这是测试内容3",
        path="/path/to/library3"
    )
    print(f"插入记录3，ID: {id3}")

    print("\n=== 测试根据用户ID查询方法 ===")
    user1_records = mapper.query_by_user_id(1)
    print(f"用户1的记录数: {len(user1_records)}")
    for record in user1_records:
        print(f"  - ID: {record['id']}, 名称: {record['name']}, 路径: {record['path']}")

    user2_records = mapper.query_by_user_id(2)
    print(f"用户2的记录数: {len(user2_records)}")
    for record in user2_records:
        print(f"  - ID: {record['id']}, 名称: {record['name']}, 路径: {record['path']}")

    print("\n=== 测试根据ID查询方法 ===")
    record = mapper.query_by_id(id1)
    if record:
        print(f"查询ID {id1}: {record['name']}, 内容: {record['content']}")

    print("\n=== 测试更新方法 ===")
    update_count = mapper.update(id1, {
        "name": "更新后的测试库1",
        "content": "更新后的内容"
    })
    print(f"更新记录数: {update_count}")

    updated_record = mapper.query_by_id(id1)
    if updated_record:
        print(f"更新后的记录: {updated_record['name']}, 内容: {updated_record['content']}")

    print("\n=== 测试删除方法 ===")
    delete_count = mapper.delete(id2)
    print(f"删除记录数: {delete_count}")

    user1_records_after_delete = mapper.query_by_user_id(1)
    print(f"删除后用户1的记录数: {len(user1_records_after_delete)}")
    for record in user1_records_after_delete:
        print(f"  - ID: {record['id']}, 名称: {record['name']}")

    print("\n=== 测试完成 ===")
