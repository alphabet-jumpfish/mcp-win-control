from dao.sqlite.context.SystemUserContextMapper import SystemUserContextMapper
from dao.sqlite.context.SystemUserContextContentMapper import SystemUserContextContentMapper
from dao.sqlite.system.SystemUserMapper import SystemUserMapper
from dao.sqlite.rag.SystemUserLibraryMapper import SystemUserLibraryMapper


class EnvDAO:
    def __init__(self):
        self.system_user_mapper = SystemUserMapper()
        self.system_user_context_mapper = SystemUserContextMapper()
        self.system_user_context_content_mapper = SystemUserContextContentMapper()
        self.system_user_library = SystemUserLibraryMapper()
        pass

    def create_env(self):
        "环境配置"
        self.system_user_mapper.ddl_create_table()
        self.system_user_context_mapper.ddl_create_table()
        self.system_user_context_content_mapper.ddl_create_table()
        self.system_user_library.ddl_create_table()


if __name__ == '__main__':
    env = EnvDAO()
    env.create_env()
