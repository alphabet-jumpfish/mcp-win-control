import flet as ft
import asyncio
from service.rag import EmbeddingUtil
from service.llm import AskLLmService
from service.llm import AskToolLLMService

from util.McpConfigUtil import ConfigUtil
from util.McpConstant import Constant

model_path = ConfigUtil.load_model_path_from_config(Constant.CONFIG_PATH)


def register_llm():
    askLLm = AskLLmService.AskLLM(model_path)
    askToolLLm = AskToolLLMService.AskToolLLM(model_path)
    return askLLm, askToolLLm


# 实例化
askLLm, askToolLLm = register_llm()


def create_streaming_ai_response(query: str, page: ft.Page):
    """
    创建并返回流式输出的 AI 回复容器
    
    Args:
        query: 用户查询文本
        page: Flet 页面对象
        
    Returns:
        AI 回复容器组件和 Markdown 组件
    """
    # 创建 Markdown 组件用于显示流式文本
    ai_markdown = ft.Markdown(
        "",
        selectable=True,
        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB
    )

    # 创建 AI 回复容器
    ai_container = ft.Container(
        content=ft.Column([
            ft.Text("Gemini", weight="bold", size=12, color=ft.Colors.BLUE_200),
            ai_markdown,
        ]),
        bgcolor="#1E1E1E",
        padding=15,
        border_radius=10,
        margin=ft.margin.only(right=50),
    )

    # 异步流式输出函数
    async def stream_response():
        try:
            # 工具逻辑
            current_text = ""
            result = await askToolLLm.run(query, stream=True)  # 添加 await
            async for chunk in result:
                print(chunk, end="", flush=True)
                current_text += chunk
                ai_markdown.value = current_text
                page.update()
                await asyncio.sleep(0.01)  # 短暂延迟，让 UI 有机会更新

            # 大模型逻辑
            # current_text = ""
            # for chunk in askLLm.chat_stream(query):
            #     current_text += chunk
            #     ai_markdown.value = current_text
            #     page.update()
            #     await asyncio.sleep(0.01)  # 短暂延迟，让 UI 有机会更新
        except Exception as ex:
            # 如果流式输出失败，回退到普通输出
            print(f"流式输出错误: {ex}")
            try:
                response = askLLm.chat(query)
                ai_markdown.value = response
                page.update()
            except Exception as ex2:
                ai_markdown.value = f"错误: {str(ex2)}"
                page.update()

    # 启动异步流式输出
    page.run_task(stream_response)

    return ai_container


def main(page: ft.Page):
    # --- 1. 页面全局设置 ---
    page.title = "Gemini Pro Studio Clone"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.bgcolor = "#131314"

    # --- 2. 定义组件 ---

    # 左侧侧边栏
    sidebar = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=72,
        min_extended_width=200,
        group_alignment=-0.9,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icons.ADD,  # 修复: Icons (大写)
                selected_icon=ft.Icons.ADD,  # 修复: Icons (大写)
                label="New Chat"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.LIBRARY_BOOKS_OUTLINED,  # 修复: 使用 icon 参数
                selected_icon=ft.Icons.LIBRARY_BOOKS,
                label="Library",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.SETTINGS_OUTLINED,
                selected_icon=ft.Icons.SETTINGS,
                label="Settings",  # 修复: 以前是 label_content，现在直接用 label
            ),
        ],
        on_change=lambda e: print("Selected destination:", e.control.selected_index),
    )

    # 输出模式状态（True=流式输出，False=批量输出）
    is_streaming_mode = ft.Ref[ft.Switch]()

    # 中间：聊天历史显示区域
    chat_history = ft.ListView(
        expand=True,
        spacing=10,
        padding=20,
        auto_scroll=True,
    )

    # 模拟 AI 欢迎语
    chat_history.controls.append(
        ft.Container(
            content=ft.Column([
                # 修复: ft.Colors (大写)
                ft.Text("Gemini 1.5 Pro", weight="bold", size=14, color=ft.Colors.BLUE_200),
                ft.Markdown(
                    "你好！我是 Gemini。今天有什么我可以帮你的吗？\n\n你可以尝试问我：\n- 写一段 Python 代码\n- 解释量子物理\n- 生成创意文案",
                    selectable=True, extension_set=ft.MarkdownExtensionSet.GITHUB_WEB),
            ]),
            bgcolor="#1E1E1E",
            padding=15,
            border_radius=10,
        )
    )

    # 中间：底部输入框
    user_input = ft.TextField(
        hint_text="在这里输入提示词...",
        border_color="transparent",
        bgcolor="#1E1E1E",
        filled=True,
        expand=True,
        multiline=True,
        min_lines=1,
        max_lines=5,
        border_radius=25,
        content_padding=ft.padding.symmetric(horizontal=20, vertical=15),
    )

    def send_message(e):
        if not user_input.value:
            return

        user_query = user_input.value
        user_input.value = ""
        page.update()

        # 添加用户消息
        chat_history.controls.append(
            ft.Container(
                content=ft.Text(user_query, size=16),
                alignment=ft.alignment.center_right,
                bgcolor="#2B2D31",
                padding=15,
                border_radius=10,
                margin=ft.margin.only(left=50),
            )
        )

        # 根据输出模式选择流式或批量输出
        if is_streaming_mode.current.value:
            # 流式输出模式
            ai_container = create_streaming_ai_response(user_query, page)
            chat_history.controls.append(ai_container)
        else:
            # 批量输出模式
            try:
                response = askLLm.chat(user_query)
                chat_history.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Gemini", weight="bold", size=12, color=ft.Colors.BLUE_200),
                            ft.Markdown(
                                response,
                                selectable=True,
                                extension_set=ft.MarkdownExtensionSet.GITHUB_WEB
                            ),
                        ]),
                        bgcolor="#1E1E1E",
                        padding=15,
                        border_radius=10,
                        margin=ft.margin.only(right=50),
                    )
                )
            except Exception as ex:
                chat_history.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Gemini", weight="bold", size=12, color=ft.Colors.BLUE_200),
                            ft.Text(f"错误: {str(ex)}", size=16),
                        ]),
                        bgcolor="#1E1E1E",
                        padding=15,
                        border_radius=10,
                        margin=ft.margin.only(right=50),
                    )
                )

        page.update()

    send_button = ft.IconButton(
        icon=ft.Icons.SEND_ROUNDED,  # 修复: Icons (大写)
        icon_color=ft.Colors.BLUE_400,  # 修复: Colors (大写)
        icon_size=30,
        on_click=send_message
    )

    # 中间区域布局
    center_layout = ft.Container(
        expand=True,
        padding=ft.padding.only(top=20, bottom=20, right=20),
        content=ft.Column(
            controls=[
                # 顶部模型选择和输出模式切换
                ft.Container(
                    content=ft.Row([
                        # 修复: ft.Colors (大写)
                        ft.Text("Model:", size=16, color=ft.Colors.GREY_400),
                        ft.Dropdown(
                            options=[ft.dropdown.Option("Gemini 1.5 Pro"), ft.dropdown.Option("Gemini 1.5 Flash")],
                            value="Gemini 1.5 Pro",
                            border_width=0,
                            text_size=16,
                            width=160,
                        ),
                        ft.VerticalDivider(width=1, color=ft.Colors.GREY_800),
                        ft.Text("输出模式:", size=16, color=ft.Colors.GREY_400),
                        ft.Switch(
                            ref=is_streaming_mode,
                            label="流式输出",
                            value=True,  # 默认开启流式输出
                            active_color=ft.Colors.BLUE_400,
                        ),
                    ]),
                    padding=ft.padding.only(left=20)
                ),
                # 修复: ft.Colors (大写)
                ft.Divider(color=ft.Colors.GREY_800),
                chat_history,
                ft.Row([user_input, send_button], alignment="center"),
            ]
        )
    )

    # 右侧参数栏
    right_panel = ft.Container(
        width=300,
        bgcolor="#1E1E1E",
        padding=20,
        content=ft.Column([
            ft.Text("Run settings", size=18, weight="bold"),
            # 修复: ft.Colors (大写)
            ft.Divider(color=ft.Colors.GREY_800),

            ft.Text("Temperature", size=14),
            # 修复: ft.Colors (大写)
            ft.Slider(min=0, max=1, divisions=10, value=0.7, active_color=ft.Colors.BLUE_400),

            ft.Text("Top K", size=14),
            # 修复: ft.Colors (大写)
            ft.Slider(min=1, max=100, divisions=100, value=40, active_color=ft.Colors.BLUE_400),

            # 修复: ft.Colors (大写)
            ft.Text("Safety settings", size=14, weight="bold", color=ft.Colors.GREY_400),
            # 修复: ft.Colors (大写)
            ft.Switch(label="Block Harassment", value=True, active_color=ft.Colors.BLUE_400),
            ft.Switch(label="Block Hate Speech", value=True, active_color=ft.Colors.BLUE_400),
        ])
    )

    # 布局组装
    layout = ft.Row(
        controls=[
            sidebar,
            ft.VerticalDivider(width=1, color="#2D2D2D"),
            center_layout,
            ft.VerticalDivider(width=1, color="#2D2D2D"),
            right_panel,
        ],
        expand=True,
        spacing=0
    )

    page.add(layout)


if __name__ == "__main__":
    ft.app(target=main)
