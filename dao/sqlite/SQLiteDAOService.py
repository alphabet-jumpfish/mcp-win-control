"""
SQLite 数据库访问对象（DAO）服务
提供完整的数据库操作功能：
- 表管理：创建、查询、删除表
- 数据操作：增删改查（CRUD）
"""
import sqlite3
import os
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager
from util.McpConstant import Constant
from util.McpConfigUtil import ConfigUtil


class SQLiteDAO:
    """SQLite 数据库访问对象"""
    
    def __init__(self, db_path: Optional[str] = None):


        """
        初始化 SQLite DAO
        Args:
            db_path: 数据库文件路径，如果为 None 则从配置文件加载
        """
        if db_path is None:
            db_path = ConfigUtil.load_sqlite_db_path_from_config(Constant.CONFIG_PATH)
        
        self.db_path = db_path
        
        # 确保数据库目录存在
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        # 初始化时创建数据库连接（用于测试）
        self._init_database()
    
    def _init_database(self):
        """初始化数据库，确保数据库文件存在"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.close()
        except Exception as e:
            print(f"初始化数据库失败: {e}")
    
    @contextmanager
    def _get_connection(self):
        """
        获取数据库连接的上下文管理器
        
        Yields:
            sqlite3.Connection: 数据库连接对象
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    # ==================== 表管理方法 ====================
    
    def create_table(
        self, 
        table_name: str, 
        columns: Dict[str, str],
        if_not_exists: bool = True
    ) -> bool:
        """
        创建表
        
        Args:
            table_name: 表名
            columns: 列定义字典，格式：{"column_name": "column_type constraints"}
                    例如：{"id": "INTEGER PRIMARY KEY AUTOINCREMENT", "name": "TEXT NOT NULL"}
            if_not_exists: 如果表已存在是否跳过（默认 True）
            
        Returns:
            True 表示创建成功，False 表示失败
            
        Example:
            # >>> dao = SQLiteDAO()
            # >>> dao.create_table("users", {
            # ...     "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            # ...     "name": "TEXT NOT NULL",
            # ...     "age": "INTEGER"
            # ... })
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 构建 CREATE TABLE SQL
                columns_sql = ", ".join([f"{col} {defn}" for col, defn in columns.items()])
                if_exists_clause = "IF NOT EXISTS" if if_not_exists else ""
                
                sql = f"CREATE TABLE {if_exists_clause} {table_name} ({columns_sql})"
                cursor.execute(sql)
                
                print(f"表 '{table_name}' 创建成功")
                return True
        except Exception as e:
            print(f"创建表 '{table_name}' 失败: {e}")
            return False
    
    def list_tables(self) -> List[str]:
        """
        查询所有表名
        
        Returns:
            表名列表
            
        Example:
            # >>> tables = dao.list_tables()
            # >>> print(tables)  # ['users', 'orders', ...]
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                """)
                tables = [row[0] for row in cursor.fetchall()]
                return tables
        except Exception as e:
            print(f"查询表列表失败: {e}")
            return []
    
    def table_exists(self, table_name: str) -> bool:
        """
        检查表是否存在
        
        Args:
            table_name: 表名
            
        Returns:
            True 表示表存在，False 表示不存在
        """
        tables = self.list_tables()
        return table_name in tables
    
    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """
        获取表结构信息
        
        Args:
            table_name: 表名
            
        Returns:
            表结构信息列表，每个元素包含列信息
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = []
                for row in cursor.fetchall():
                    columns.append({
                        "cid": row[0],
                        "name": row[1],
                        "type": row[2],
                        "notnull": bool(row[3]),
                        "default_value": row[4],
                        "pk": bool(row[5])
                    })
                return columns
        except Exception as e:
            print(f"获取表 '{table_name}' 信息失败: {e}")
            return []
    
    def drop_table(self, table_name: str, if_exists: bool = True) -> bool:
        """
        删除表
        
        Args:
            table_name: 表名
            if_exists: 如果表不存在是否跳过（默认 True）
            
        Returns:
            True 表示删除成功，False 表示失败
            
        Example:
            # >>> dao.drop_table("users")
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if_exists_clause = "IF EXISTS" if if_exists else ""
                sql = f"DROP TABLE {if_exists_clause} {table_name}"
                cursor.execute(sql)
                print(f"表 '{table_name}' 删除成功")
                return True
        except Exception as e:
            print(f"删除表 '{table_name}' 失败: {e}")
            return False
    
    # ==================== 数据操作（CRUD）方法 ====================
    
    def insert(
        self, 
        table_name: str, 
        data: Dict[str, Any]
    ) -> Optional[int]:
        """
        插入数据（Create）
        
        Args:
            table_name: 表名
            data: 要插入的数据字典，格式：{"column_name": value}
            
        Returns:
            插入行的 ID（如果表有自增主键），否则返回 None
            
        Example:
            # >>> dao.insert("users", {"name": "Alice", "age": 30})
            1
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 构建 INSERT SQL
                columns = ", ".join(data.keys())
                placeholders = ", ".join(["?" for _ in data])
                values = list(data.values())
                
                sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                cursor.execute(sql, values)
                
                # 返回最后插入的行 ID
                last_id = cursor.lastrowid
                print(f"插入数据到表 '{table_name}' 成功，ID: {last_id}")
                return last_id
        except Exception as e:
            print(f"插入数据到表 '{table_name}' 失败: {e}")
            return None
    
    def select(
        self,
        table_name: str,
        columns: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        查询数据（Read）
        
        Args:
            table_name: 表名
            columns: 要查询的列名列表，如果为 None 则查询所有列
            where: 查询条件字典，格式：{"column": value} 或 {"column": ("operator", value)}
                   例如：{"age": 30} 或 {"age": (">", 25)}
            order_by: 排序字段，例如："age DESC" 或 "name ASC"
            limit: 限制返回行数
            
        Returns:
            查询结果列表，每个元素是一个字典
            
        Example:
            # >>> # 查询所有数据
            # >>> results = dao.select("users")
            #
            # >>> # 查询指定列
            # >>> results = dao.select("users", columns=["name", "age"])
            #
            # >>> # 带条件查询
            # >>> results = dao.select("users", where={"age": 30})
            #
            # >>> # 复杂条件查询
            # >>> results = dao.select("users", where={"age": (">", 25)}, order_by="age DESC", limit=10)
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 构建 SELECT SQL
                columns_sql = ", ".join(columns) if columns else "*"
                sql = f"SELECT {columns_sql} FROM {table_name}"
                
                # 添加 WHERE 子句
                params = []
                if where:
                    conditions = []
                    for col, value in where.items():
                        # 支持两种格式：
                        # 1. 简单等值查询：{"column": value}
                        # 2. 带操作符的查询：{"column": (operator, value)}
                        if isinstance(value, tuple) and len(value) == 2:
                            operator, val = value
                            if operator.upper() == "IN":
                                # 特殊处理IN操作符
                                placeholders = ",".join(["?" for _ in val])
                                conditions.append(f"{col} IN ({placeholders})")
                                params.extend(val)  # 注意这里是extend而不是append
                            else:
                                conditions.append(f"{col} {operator} ?")
                                params.append(val)
                        else:
                            # 简单等值查询
                            conditions.append(f"{col} = ?")
                            params.append(value)
                    sql += " WHERE " + " AND ".join(conditions)
                
                # 添加 ORDER BY 子句
                if order_by:
                    sql += f" ORDER BY {order_by}"
                
                # 添加 LIMIT 子句
                if limit:
                    sql += f" LIMIT {limit}"
                
                cursor.execute(sql, params)
                
                # 转换为字典列表
                rows = cursor.fetchall()
                results = [dict(row) for row in rows]
                
                print(f"从表 '{table_name}' 查询到 {len(results)} 条数据")
                return results
        except Exception as e:
            print(f"查询表 '{table_name}' 失败: {e}")
            return []
    
    def update(
        self,
        table_name: str,
        data: Dict[str, Any],
        where: Dict[str, Any]
    ) -> int:
        """
        更新数据（Update）
        
        Args:
            table_name: 表名
            data: 要更新的数据字典，格式：{"column_name": new_value}
            where: 更新条件字典，格式：{"column": value}
            
        Returns:
            受影响的行数
            
        Example:
            # >>> dao.update("users", {"age": 31}, {"name": "Alice"})
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 构建 UPDATE SQL
                set_clause = ", ".join([f"{col} = ?" for col in data.keys()])
                where_clause = " AND ".join([f"{col} = ?" for col in where.keys()])
                
                sql = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
                params = list(data.values()) + list(where.values())
                
                cursor.execute(sql, params)
                affected_rows = cursor.rowcount
                
                print(f"更新表 '{table_name}' 成功，影响 {affected_rows} 行")
                return affected_rows
        except Exception as e:
            print(f"更新表 '{table_name}' 失败: {e}")
            return 0
    
    def delete(
        self,
        table_name: str,
        where: Dict[str, Any]
    ) -> int:
        """
        删除数据（Delete）
        
        Args:
            table_name: 表名
            where: 删除条件字典，格式：{"column": value}
                   注意：为了安全，此方法必须提供 where 条件
                   如果要删除所有数据，请使用 delete_all 方法
            
        Returns:
            受影响的行数
            
        Example:
            # >>> dao.delete("users", {"id": 1})
            1
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 构建 DELETE SQL
                where_clause = " AND ".join([f"{col} = ?" for col in where.keys()])
                sql = f"DELETE FROM {table_name} WHERE {where_clause}"
                params = list(where.values())
                
                cursor.execute(sql, params)
                affected_rows = cursor.rowcount
                
                print(f"从表 '{table_name}' 删除成功，影响 {affected_rows} 行")
                return affected_rows
        except Exception as e:
            print(f"删除表 '{table_name}' 数据失败: {e}")
            return 0
    
    def delete_all(self, table_name: str) -> int:
        """
        删除表中所有数据（危险操作）
        
        Args:
            table_name: 表名
            
        Returns:
            受影响的行数
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                sql = f"DELETE FROM {table_name}"
                cursor.execute(sql)
                affected_rows = cursor.rowcount
                print(f"清空表 '{table_name}' 成功，删除 {affected_rows} 行")
                return affected_rows
        except Exception as e:
            print(f"清空表 '{table_name}' 失败: {e}")
            return 0
    
    def count(self, table_name: str, where: Optional[Dict[str, Any]] = None) -> int:
        """
        统计表中的记录数

        Args:
            table_name: 表名
            where: 查询条件字典（可选）

        Returns:
            记录数
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                sql = f"SELECT COUNT(*) FROM {table_name}"
                params = []

                if where:
                    conditions = []
                    for col, value in where.items():
                        if isinstance(value, tuple) and len(value) == 2:
                            operator, val = value
                            conditions.append(f"{col} {operator} ?")
                            params.append(val)
                        else:
                            conditions.append(f"{col} = ?")
                            params.append(value)
                    sql += " WHERE " + " AND ".join(conditions)

                cursor.execute(sql, params)
                count = cursor.fetchone()[0]
                return count
        except Exception as e:
            print(f"统计表 '{table_name}' 记录数失败: {e}")
            return 0

    def query(
        self,
        table_name: str,
        where: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        简化的查询方法（兼容旧代码）

        Args:
            table_name: 表名
            where: 查询条件字典，格式：{"column": value}
            order_by: 排序字段，例如："update_time DESC"
            limit: 限制返回行数

        Returns:
            查询结果列表，每个元素是一个字典
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                sql = f"SELECT * FROM {table_name}"
                params = []

                # 添加 WHERE 子句
                if where:
                    conditions = []
                    for col, value in where.items():
                        conditions.append(f"{col} = ?")
                        params.append(value)
                    sql += " WHERE " + " AND ".join(conditions)

                # 添加 ORDER BY 子句
                if order_by:
                    sql += f" ORDER BY {order_by}"

                # 添加 LIMIT 子句
                if limit:
                    sql += f" LIMIT {limit}"

                cursor.execute(sql, params)

                # 转换为字典列表
                rows = cursor.fetchall()
                results = [dict(row) for row in rows]

                return results
        except Exception as e:
            print(f"查询表 '{table_name}' 失败: {e}")
            return []


if __name__ == '__main__':
    # 测试示例
    print("=" * 60)
    print("SQLiteDAO 测试")
    print("=" * 60)
    
    # 初始化 DAO
    dao = SQLiteDAO()
    
    # 1. 创建表
    print("\n1. 创建表")
    dao.create_table("users", {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "name": "TEXT NOT NULL",
        "age": "INTEGER",
        "email": "TEXT"
    })
    
    # 2. 查询所有表
    print("\n2. 查询所有表")
    tables = dao.list_tables()
    print(f"数据库中的表: {tables}")
    
    # 3. 获取表信息
    print("\n3. 获取表结构信息")
    table_info = dao.get_table_info("users")
    for col in table_info:
        print(f"  列: {col['name']}, 类型: {col['type']}, 主键: {col['pk']}")
    
    # 4. 插入数据（Create）
    print("\n4. 插入数据")
    dao.insert("users", {"name": "Alice", "age": 30, "email": "alice@example.com"})
    dao.insert("users", {"name": "Bob", "age": 25, "email": "bob@example.com"})
    dao.insert("users", {"name": "Charlie", "age": 35, "email": "charlie@example.com"})
    
    # 5. 查询数据（Read）
    print("\n5. 查询所有数据")
    all_users = dao.select("users")
    for user in all_users:
        print(f"  {user}")
    
    print("\n5.1 查询指定列")
    names = dao.select("users", columns=["name", "age"])
    for user in names:
        print(f"  {user}")
    
    print("\n5.2 条件查询")
    young_users = dao.select("users", where={"age": ("<", 30)})
    for user in young_users:
        print(f"  {user}")
    
    # 6. 更新数据（Update）
    print("\n6. 更新数据")
    affected = dao.update("users", {"age": 31}, {"name": "Alice"})
    print(f"  更新了 {affected} 行")
    
    # 验证更新
    alice = dao.select("users", where={"name": "Alice"})
    print(f"  更新后的 Alice: {alice[0]}")
    
    # 7. 删除数据（Delete）
    print("\n7. 删除数据")
    deleted = dao.delete("users", {"name": "Bob"})
    print(f"  删除了 {deleted} 行")
    
    # 验证删除
    remaining = dao.select("users")
    print(f"  剩余用户数: {len(remaining)}")
    
    # 8. 统计记录数
    print("\n8. 统计记录数")
    total = dao.count("users")
    print(f"  总记录数: {total}")
    
    # 9. 删除表（可选，测试时注释掉）
    # print("\n9. 删除表")
    # dao.drop_table("users")

