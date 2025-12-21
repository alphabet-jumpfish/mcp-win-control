from typing import List

from dao.sqlite.context.SystemUserContextContentMapper import SystemUserContextContentMapper


class SystemUserContextContentService:
    def __init__(self):
        self.system_user_context_content_mapper = SystemUserContextContentMapper()

    # 用来查询用户上下文内容
    def query_by_user_id_and_context_id(self, user_id: int, context_id: int) -> List[dict]:
        system_user_context_contents = self.system_user_context_content_mapper.query_by_user_id_and_context_id(user_id,
                                                                                                               context_id)
        return system_user_context_contents

    # 插入消息
    def insert_message(self, user_id: int, context_id: int, content: str) -> int:
        """
        插入单条消息
        content 格式: JSON字符串，包含 role 和 message
        """
        return self.system_user_context_content_mapper.insert_message(user_id, context_id, content)

    # 批量插入消息
    def insert_messages_batch(self, messages: List[dict]) -> bool:
        """
        批量插入消息
        """
        return self.system_user_context_content_mapper.insert_messages_batch(messages)
