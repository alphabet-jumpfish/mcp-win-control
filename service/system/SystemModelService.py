from typing import TypedDict, List

from dao.sqlite.system.SystemModelMapper import SystemModelMapper
from dao.sqlite.system.SystemModelMapper import SystemModelType


class SystemModelService:

    def __init__(self):
        self.system_model_mapper = SystemModelMapper()

    def create_model(self, save_system_model: SystemModelType) -> int:
        """
        创建模型
        """
        return self.system_model_mapper.dml_create_model_dict(save_system_model)

    def query_all_list_by_name(self, name: str) -> List[SystemModelType]:
        """
        查询所有模型
        """
        result = None
        if name:
            result = self.system_model_mapper.dml_query_by_name(name)
        else:
            result = self.system_model_mapper.dml_query_all_models()
        return result
