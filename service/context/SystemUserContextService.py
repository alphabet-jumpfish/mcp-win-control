from typing import List

from dao.sqlite.context.SystemUserContextMapper import SystemUserContextMapper


class SystemUserContextService:
    """
    系统用户上下文服务
    """
    def __init__(self):
        self.system_user_context_mapper = SystemUserContextMapper()

    # dml 创建用户上下文
    def create_user_context(self, user_id: int, context_name: str) -> int:
        last_id = self.system_user_context_mapper.dml_create_user_context(user_id, context_name)
        return last_id

    # dml 查询用户上下文[最近]
    def query_recent_context_by_user_id(self, user_id: int) -> List[dict]:
        recent_user_context = self.system_user_context_mapper.query_recent_context_by_user_id(user_id)
        return recent_user_context

    # dml 查询用户上下文
    def query_by_user_id(self, user_id: int) -> List[dict]:
        user_contexts = self.system_user_context_mapper.query_by_user_id(user_id)
        return user_contexts

    # dml 更新上下文名称
    def update_context_name(self, context_id: int, new_name: str) -> bool:
        return self.system_user_context_mapper.update_context_name(context_id, new_name)

    # dml 删除上下文
    def delete_context(self, context_id: int) -> bool:
        return self.system_user_context_mapper.delete_context(context_id)

    # dml 搜索上下文
    def search_context_by_name(self, user_id: int, keyword: str) -> List[dict]:
        return self.system_user_context_mapper.search_context_by_name(user_id, keyword)

    # dml 更新上下文时间
    def update_context_time(self, context_id: int) -> bool:
        return self.system_user_context_mapper.update_context_time(context_id)
