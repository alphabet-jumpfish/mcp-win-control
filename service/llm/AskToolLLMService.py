import asyncio
import sys
from typing import AsyncIterator

from mcp import StdioServerParameters, ClientSession
from mcp.client.stdio import stdio_client

from util.McpConstant import Constant
from util.McpConfigUtil import ConfigUtil
from service.rag import EmbeddingUtil
from service.llm import AskLLmService


class AskToolLLM:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.server_script_path = Constant.SERVER_PATH
        self.askLLm = AskLLmService.AskLLM(self.model_path)  # 正确实例化
        self.embedding = EmbeddingUtil.EmbeddingUtil(self.model_path)  # 正确实例化
        self.server_params = StdioServerParameters(
            command=sys.executable,  # 使用当前 Python 解释器
            args=[self.server_script_path],
            env=None,
        )

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

    async def run(self, question: str = "你是谁?", stream: bool = False) -> AsyncIterator[str]:
        """
        根据 stream 标志返回一个 **异步可迭代器**，方便上层使用 `async for` 进行流式输出。
        """
        print("=" + "打印请求参数" + "=" * 20)
        print(question)

        # 建立链接
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # 初始化连接
                await session.initialize()
                print("=" + "初始化连接 成功" + "=" * 20)
                # 列出工具
                tools = await session.list_tools()
                print("可用工具:", tools.tools)
                s = self.transform_json(tools.tools) + "\n"
                # 根据是否流式输出选择不同的调用方式
                if stream:
                    # 包一层异步生成器，内部消费同步的 chat_stream 生成器
                    print("=" + "开始LLM-TOOL工具流式回复" + "=" * 20)
                    async def stream_iterator() -> AsyncIterator[str]:

                        # TODO
                        # 1、 根据提示词工程消费上下文 构建提示词
                        # 2、 针对于 askLLm 进行提问预处理

                        for piece in self.askLLm.chat_stream(question):
                            yield piece
                    return stream_iterator()
                else:
                    # 非流式：一次性拿到完整内容，再包装成只 yield 一次的异步生成器
                    content = self.askLLm.chat(question)
                    print("=" + "打印LLM-TOOL回复参数" + "=" * 20)
                    print(content)
                    async def single_content_iterator() -> AsyncIterator[str]:
                        yield content
                    return single_content_iterator()


if __name__ == "__main__":
    print("开始流程")
    model_path = ConfigUtil.load_model_path_from_config(Constant.CONFIG_PATH)
    askTool = AskToolLLM(model_path)

    async def runner(question: str = "你是谁?", stream: bool = False):
        result = await askTool.run(question, stream)
        async for chunk in result:
            print(chunk, end="", flush=True)

    asyncio.run(runner("你好", stream=True))
