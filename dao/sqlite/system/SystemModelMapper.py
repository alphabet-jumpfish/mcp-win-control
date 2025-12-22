from typing import TypedDict, List

from dao.sqlite.SQLiteDAOService import SQLiteDAO

const_system_model_table_name = "system_model"
const_system_model_table_columns = {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
    "description": "TEXT NOT NULL",
    "path": "TEXT NOT NULL",
    "type": "TEXT NOT NULL",
    "create_time": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    "update_time": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    "deleted": "INTEGER DEFAULT 0"
}


class SystemModelType(TypedDict, total=False):
    id: int
    name: str
    description: str
    path: str
    type: str
    create_time: str
    update_time: str
    deleted: int


class SystemModelMapper:
    def __init__(self):
        self.sqlite_dao = SQLiteDAO()

    # DDL 创建表结构
    def ddl_create_table(self):
        """
        创建系统模型表
        """
        tables = self.sqlite_dao.list_tables()
        print(f"数据库中的表: {tables}")
        if const_system_model_table_name in tables:
            print(f"表 {const_system_model_table_name} 已存在")
            return

        is_success = self.sqlite_dao.create_table(const_system_model_table_name, const_system_model_table_columns)
        print(f"模型表创建结果：{is_success}")

    # 根据模型名称查询
    def dml_query_by_name(self, name: str) -> List[SystemModelType]:
        """
        根据名称模糊查询模型数据
        """
        system_models = self.sqlite_dao.select(
            table_name=const_system_model_table_name,
            columns=None,
            where={"name": ("LIKE", f"%{name}%")},
            order_by="update_time DESC"
        )
        print(f"查询模型表数据：{system_models}")
        return system_models

    # 根据模型ID查询
    def dml_query_by_id(self, id: int) -> SystemModelType:
        """
        根据ID查询模型数据
        """
        system_model = self.sqlite_dao.select(
            table_name=const_system_model_table_name,
            columns=None,
            where={"id": ("=", id)},
            order_by="update_time DESC",
            limit=1
        )
        print(f"查询模型表数据：{system_model}")
        if len(system_model) > 0:
            system_model = system_model[0]
        return system_model

    def dml_create_model_dict(self, save_system_model: SystemModelType) -> int:
        """
        保存模型
        """
        result = self.dml_create_model(name=save_system_model.get("name"),
                                       description=save_system_model.get("description"),
                                       path=save_system_model.get("path"),
                                       type=save_system_model.get("type"))
        return result

    # 新增模型
    def dml_create_model(self,
                         name: str,
                         description: str,
                         path: str,
                         type: str) -> int:
        """
        新增模型
        """
        model_data = {k: v for k, v in locals().items() if k != 'self' and v}

        # 检查模型是否已存在
        system_models = self.sqlite_dao.select(
            table_name=const_system_model_table_name,
            columns=None,
            where={"name": ("=", name)},
            order_by="update_time DESC",
            limit=1
        )
        if system_models:
            raise ValueError("模型已存在")

        # 确保必要字段存在
        if "name" not in model_data or "description" not in model_data or "path" not in model_data or "type" not in model_data:
            raise ValueError("模型名称、描述、路径和类型不能为空")

        last_id = self.sqlite_dao.insert(const_system_model_table_name, model_data)
        print(f"模型表数据插入结果：{last_id}")
        return last_id

    # 更新模型
    def dml_update_model(self,
                         id: int,
                         name: str = None,
                         description: str = None,
                         path: str = None,
                         type: str = None) -> int:
        """
        更新模型
        """
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
        if path is not None:
            update_data["path"] = path
        if type is not None:
            update_data["type"] = type

        if not update_data:
            raise ValueError("至少需要更新一个字段")

        affected_rows = self.sqlite_dao.update(
            table_name=const_system_model_table_name,
            data=update_data,
            where={"id": id}
        )
        print(f"模型表数据更新结果：{affected_rows}")
        return affected_rows

    # 删除模型
    def dml_delete_model_by_id(self, id: int) -> int:
        """
        删除模型
        """
        is_success = self.sqlite_dao.delete(const_system_model_table_name, {"id": id})
        print(f"模型表数据删除结果：{is_success}")
        return is_success

    # 查询所有模型
    def dml_query_all_models(self) -> List[SystemModelType]:
        """
        查询所有模型数据
        """
        system_models = self.sqlite_dao.select(
            table_name=const_system_model_table_name,
            columns=None,
            where={"deleted": 0},  # 排除已删除的记录
            order_by="update_time DESC"
        )
        print(f"查询所有模型表数据：{system_models}")
        return system_models
