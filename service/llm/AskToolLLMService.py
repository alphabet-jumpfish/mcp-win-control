import asyncio
import sys
from typing import AsyncIterator

from mcp import StdioServerParameters, ClientSession
from mcp.client.stdio import stdio_client

from util.McpConstant import Constant
from util.McpConfigUtil import ConfigUtil
# 持久层
from dao.chroma.ChromaDocumentDAO import ChromaDocumentDAO
from service.rag import EmbeddingUtil
from service.llm import AskLLmService
from service.promat import PromptEngineeringService
from service.retrieval import RetrievalSystemService
from service.tool.ToolSelectorService import ToolSelector
from service.tool.ToolService import ToolService


class AskToolLLM:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.server_script_path = Constant.SERVER_PATH
        self.askLLm = AskLLmService.AskLLM(self.model_path)  # 正确实例化
        self.embedding = EmbeddingUtil.EmbeddingUtil(self.model_path)  # 正确实例化
        self.prompt_engineering = PromptEngineeringService.PromptEngineering(
            role="专业的AI助手",
            enable_boundary_control=True,
            enable_citation=True
        )
        chroma_save_path = ConfigUtil.load_chroma_save_path_from_config(Constant.CONFIG_PATH)
        # TODO schema
        schema = "schema"
        self.chroma_document_dao = ChromaDocumentDAO(
            collection_name=schema,
            persist_directory=chroma_save_path
        )
        self.retrieval_system = RetrievalSystemService.RetrievalSystem(self.askLLm, self.embedding, self.chroma_document_dao)
        self.server_params = StdioServerParameters(
            command=sys.executable,  # 使用当前 Python 解释器
            args=[self.server_script_path],
            env=None,
        )
        self.tool_selector = ToolSelector(embedding_util=self.embedding)  # 仅使用规则匹配测试
        self.tool_service = ToolService()

    @staticmethod
    def transform_json(tools) -> str:
        s = "MCP服务器提供的工具如下："
        for tool in tools:
            s = s + f"""
                tool_name: {tool.name},
                tool_description: {tool.description},
                - input tile: {tool.inputSchema['title']},
                - input properties: "{tool.inputSchema['properties']}
        """
        return s

    # 构建提示词
    def prompt(self, question: str, context_id: str):
        contexts = self.chroma_document_dao.get_by_context_ids(context_id)
        messages = self.prompt_engineering.build_rag_prompt(query=question, contexts=contexts)
        print("=" * 50)
        print("系统提示词：")
        print(messages[0]["content"])
        print("\n" + "=" * 50)
        print("用户提示词：")
        print(messages[1]["content"])
        print("\n" + "=" * 50)
        return messages

    # 查询预处理
    def retrieval(self, query: str):
        original_query = query
        rewritten = self.retrieval_system.query_rewrite(original_query)
        print(f"开始LLM-TOOL 原始查询: {original_query}")
        print(f"开始LLM-TOOL 改写后: {rewritten}\n")
        return rewritten

    def match_tool(self, question: str):
        tool_name, score, method = self.tool_selector.select_tool(question)
        if tool_name:
            print(f"\n问题: {question}")
            print(f"匹配工具: {tool_name}")
            print(f"置信度: {score:.2f}")
            print(f"匹配方式: {method}")
            print(f"工具描述: {self.tool_selector.get_tool_description(tool_name)}")
        else:
            print(f"\n问题: {question}")
            print("未找到匹配的工具（可能需要直接使用 LLM 回答）")
            return None
        return {
            "tool_name": tool_name,
            "score": score,
            "method": method
        }

    # 工具调用
    async def invoke_tool(self,
                          session,
                          question,
                          tool_name: str,
                          tool_input: str) -> str:
        # 根据工具名称准备参数
        tool_arguments = self.tool_service.prepare_tool_arguments(tool_name, question)
        # 调用工具
        tool_result = await session.call_tool(tool_name, tool_arguments)
        # 处理工具结果
        processed_result = self.tool_service.process_tool_result(tool_result)
        return processed_result

    def process(self, question: str, stream: bool = False):
        # 根据是否流式输出选择不同的调用方式
        if stream:
            # 包一层异步生成器，内部消费同步的 chat_stream 生成器
            print("=" + "开始LLM-TOOL工具流式回复" + "=" * 20)

            async def stream_iterator() -> AsyncIterator[str]:
                # TODO
                # 1、 context上下文查询
                # 2、 根据提示词工程消费上下文 构建提示词
                # 3、 针对于 askLLm 进行提问预处理
                # 4、 保存文档信息
                context_id = "20251219_context_id"
                # context = self.prompt(question, context_id)
                messages = []
                # if len(context) > 0:
                #     messages.append({"role": "system", "content": context[0]["content"]})
                #     # user_context_message = self.retrieval(context[1]["content"])
                #     messages.append({"role": "user", "content": context[1]["content"]})
                # else:
                #     pass
                # user_question = self.retrieval(question)
                # 直接使用原始问题
                message = {"role": "user", "content": question}
                messages.append(message)

                print("=" + "开始LLM-TOOL工具messages最终入参" + "=" * 20)
                print(f"{messages}")
                for piece in self.askLLm.chat_stream(messages):
                    yield piece

            return stream_iterator()
        else:
            # 非流式：一次性拿到完整内容，再包装成只 yield 一次的异步生成器
            # TODO: 构建完整的 messages 用于非流式调用
            context_id = "20251219_context_id"
            context = self.prompt(question, context_id)
            messages = []
            if len(context) > 0:
                messages.append({"role": "system", "content": context[0]["content"]})
                messages.append({"role": "user", "content": context[1]["content"]})
            user_question = self.retrieval(question)
            message = {"role": "user", "content": user_question}
            messages.append(message)
            content = self.askLLm.chat(messages)
            print("=" + "打印LLM-TOOL回复参数" + "=" * 20)
            print(content)

            async def single_content_iterator() -> AsyncIterator[str]:
                yield content

            return single_content_iterator()

    async def run(self, question: str = "你是谁?", stream: bool = False) -> AsyncIterator[str]:
        """
        根据 stream 标志返回一个 **异步可迭代器**，方便上层使用 `async for` 进行流式输出。
        """
        print("=" + "打印请求参数" + "=" * 20)
        print(question)

        try:
            # 建立链接
            async with stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # 初始化连接
                    await session.initialize()
                    print("=" + "初始化连接 成功" + "=" * 20)
                    # 列出工具
                    tools = await session.list_tools()
                    print("可用工具:", tools.tools)
                    format_s = self.transform_json(tools.tools) + "\n"
                    print(f"可用工具格式化输出:{format_s}")
                    # 匹配工具
                    tool_result = self.match_tool(question)
                    # # TODO 调用工具
                    # if tool_result is not None:
                    #     processed_result = await self.invoke_tool(question, tool_result["tool_name"], tool_result["tool_input"])
                    #     print(f"\n工具返回结果: {processed_result}")

                    # 返回处理结果
                    return self.process(question, stream)
        except Exception as e:
            # 连接失败时的处理
            print(f"=" + "MCP服务器连接失败，使用直接回复模式" + "=" * 20)
            print(f"错误信息: {e}")
            # 直接使用 LLM 回复，不使用工具
            return self.process(question, stream)

    def cleanup(self):
        """
        清理 AskToolLLM 资源，释放内存
        """
        print("正在清理 AskToolLLM 资源...")
        try:
            # 清理 askLLm
            if hasattr(self, 'askLLm') and self.askLLm is not None:
                if hasattr(self.askLLm, 'cleanup'):
                    self.askLLm.cleanup()
                del self.askLLm
                self.askLLm = None
                print("- askLLm 已释放")

            # 清理 embedding
            if hasattr(self, 'embedding') and self.embedding is not None:
                if hasattr(self.embedding, 'cleanup'):
                    self.embedding.cleanup()
                del self.embedding
                self.embedding = None
                print("- embedding 已释放")

            # 清理其他组件
            if hasattr(self, 'retrieval_system') and self.retrieval_system is not None:
                del self.retrieval_system
                self.retrieval_system = None

            if hasattr(self, 'chroma_document_dao') and self.chroma_document_dao is not None:
                del self.chroma_document_dao
                self.chroma_document_dao = None

            if hasattr(self, 'tool_selector') and self.tool_selector is not None:
                del self.tool_selector
                self.tool_selector = None

            print("AskToolLLM 资源清理完成")
        except Exception as e:
            print(f"清理 AskToolLLM 资源时出错: {e}")


if __name__ == "__main__":
    print("开始流程")
    model_path = ConfigUtil.load_model_path_from_config(Constant.CONFIG_PATH)
    askTool = AskToolLLM(model_path)


    async def runner(question: str = "你是谁?", stream: bool = False):
        result = await askTool.run(question, stream)
        async for chunk in result:
            print(chunk, end="", flush=True)


    asyncio.run(runner("你好", stream=True))
