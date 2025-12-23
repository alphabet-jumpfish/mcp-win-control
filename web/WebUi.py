from datetime import datetime

import flet as ft
import asyncio
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from service.rag import EmbeddingUtil
from service.llm import AskLLmService
from service.llm import AskToolLLMService

from util.McpConfigUtil import ConfigUtil
from util.McpConstant import Constant

from service.auth.AuthService import AuthService
from dao.memory.UserMemory import UserInfoType
from service.context.SystemUserContextService import SystemUserContextService
from service.context.SystemUserContextContentService import SystemUserContextContentService
from service.rag.SystemUserLibraryService import SystemUserLibraryService
from service.system.SystemModelService import SystemModelService
from service.system.SystemModelService import SystemModelType
import json

model_path = ConfigUtil.load_model_path_from_config(Constant.CONFIG_PATH)
local_load_system_model: SystemModelType = {
    "name": "Qwen3本地配置模型",
    "path": model_path,
    "type": "local",
    "description": "本地配置文件加载",
    #"create_time": datetime.now(),
    #"update_time": datetime.now(),
    "deleted": 0
}


def register_llm(model_path_param=None):
    """
    注册 LLM 服务
    """
    askLLm = AskLLmService.AskLLM(model_path_param)
    askToolLLm = AskToolLLMService.AskToolLLM(model_path_param)
    return askLLm, askToolLLm


# 实例化
library_service = SystemUserLibraryService(local_load_system_model.get("path"))  # 全局知识库服务实例
askLLm, askToolLLm = register_llm(local_load_system_model.get("path"))
auth_service = AuthService()
context_service = SystemUserContextService()
context_content_service = SystemUserContextContentService()
model_service = SystemModelService()  # 全局模型服务实例

def create_streaming_ai_response(query: str, page: ft.Page, save_callback=None):
    """
    创建并返回流式输出的 AI 回复容器

    Args:
        query: 用户查询文本
        page: Flet 页面对象
        save_callback: 保存消息的回调函数，接收 (role, message) 参数

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
            ft.Row([
                ft.Container(
                    content=ft.Icon(ft.Icons.SMART_TOY, size=20, color=ft.Colors.BLUE_400),
                    bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.BLUE_400),
                    border_radius=20,
                    padding=8,
                ),
                ft.Text("Gemini", weight="bold", size=15, color=ft.Colors.BLUE_300),
            ], spacing=10),
            ai_markdown,
        ], spacing=12),
        bgcolor="#1E1E1E",
        padding=20,
        border_radius=16,
        margin=ft.margin.only(right=80),
        border=ft.border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.BLUE_400)),
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=10,
            color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
            offset=ft.Offset(0, 2),
        ),
    )

    # 异步流式输出函数
    async def stream_response():
        current_text = ""
        try:
            # 工具逻辑
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
                current_text = response
                ai_markdown.value = response
                page.update()
            except Exception as ex2:
                current_text = f"错误: {str(ex2)}"
                ai_markdown.value = current_text
                page.update()

        # 流式输出完成后，保存消息
        if save_callback and current_text:
            save_callback("assistant", current_text)

    # 启动异步流式输出
    page.run_task(stream_response)

    return ai_container


def show_login_dialog(page: ft.Page, on_login_success):
    """
    显示登录对话框

    Args:
        page: Flet 页面对象
        on_login_success: 登录成功后的回调函数
    """
    # 创建输入框
    username_field = ft.TextField(
        label="用户名",
        hint_text="请输入用户名",
        prefix_icon=ft.Icons.PERSON,
        border_color=ft.Colors.BLUE_400,
        focused_border_color=ft.Colors.BLUE_600,
        border_radius=12,
        filled=True,
        bgcolor="#2B2D31",
        width=350,
        height=60,
    )

    password_field = ft.TextField(
        label="密码",
        hint_text="请输入密码",
        prefix_icon=ft.Icons.LOCK,
        password=True,
        can_reveal_password=True,
        border_color=ft.Colors.BLUE_400,
        focused_border_color=ft.Colors.BLUE_600,
        border_radius=12,
        filled=True,
        bgcolor="#2B2D31",
        width=350,
        height=60,
    )

    error_text = ft.Text("", color=ft.Colors.RED_400, size=13, weight="w500")

    def handle_login(e):
        """处理登录逻辑"""
        username = username_field.value
        password = password_field.value

        # 验证输入
        if not username or not password:
            error_text.value = "用户名和密码不能为空"
            page.update()
            return

        user_info: UserInfoType = {
            "username": username,
            "password": password
        }

        try:
            # 调用 AuthService 登录
            print(f"调用 AuthService 登录")
            current_user = auth_service.login(user_info)
            print(f"调用 AuthService 登录获取当前用户信息{current_user}")
            # 关闭对话框
            dialog.open = False
            page.update()

            # 调用成功回调
            if on_login_success:
                on_login_success(current_user)

        except Exception as ex:
            error_text.value = f"登录失败: {str(ex)}"
            page.update()

    def handle_cancel(e):
        """取消登录"""
        dialog.open = False
        page.update()

    # 创建对话框
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Row([
            ft.Icon(ft.Icons.LOGIN, color=ft.Colors.BLUE_400, size=28),
            ft.Text("用户登录", size=22, weight="bold"),
        ], spacing=10),
        content=ft.Container(
            content=ft.Column([
                username_field,
                password_field,
                error_text,
            ], tight=True, spacing=20),
            width=350,
            padding=ft.padding.only(top=10, bottom=10),
        ),
        actions=[
            ft.TextButton(
                "取消",
                on_click=handle_cancel,
                style=ft.ButtonStyle(
                    color=ft.Colors.GREY_400,
                    overlay_color=ft.Colors.with_opacity(0.1, ft.Colors.GREY_400),
                ),
            ),
            ft.ElevatedButton(
                "登录",
                on_click=handle_login,
                bgcolor=ft.Colors.BLUE_500,
                color=ft.Colors.WHITE,
                height=45,
                width=100,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=10),
                ),
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        shape=ft.RoundedRectangleBorder(radius=15),
        bgcolor="#1E1E1E",
    )

    page.overlay.append(dialog)
    dialog.open = True
    page.update()


def show_user_menu(page: ft.Page, user_info: UserInfoType, on_logout):
    """
    显示用户菜单对话框

    Args:
        page: Flet 页面对象
        user_info: 当前登录用户信息
        on_logout: 登出后的回调函数
    """

    def handle_logout(e):
        """处理登出逻辑"""
        try:
            # 调用 AuthService 登出
            auth_service.logout()

            # 关闭对话框
            dialog.open = False
            page.update()

            # 调用登出回调
            if on_logout:
                on_logout()

        except Exception as ex:
            print(f"登出失败: {str(ex)}")

    def handle_close(e):
        """关闭菜单"""
        dialog.open = False
        page.update()

    # 创建用户信息显示
    user_info_content = ft.Column([
        # 用户头像和基本信息
        ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Icon(ft.Icons.ACCOUNT_CIRCLE, size=80, color=ft.Colors.BLUE_400),
                    alignment=ft.alignment.center,
                ),
                ft.Text(
                    user_info.get("username", "未知用户"),
                    size=22,
                    weight="bold",
                    text_align=ft.TextAlign.CENTER,
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            padding=ft.padding.only(bottom=15),
        ),

        ft.Divider(color=ft.Colors.GREY_800, height=1),

        # 详细信息卡片
        ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.EMAIL, size=20, color=ft.Colors.BLUE_400),
                    ft.Column([
                        ft.Text("邮箱", size=11, color=ft.Colors.GREY_500),
                        ft.Text(user_info.get('email', 'N/A'), size=14, weight="w500"),
                    ], spacing=2),
                ], spacing=12),

                ft.Row([
                    ft.Icon(ft.Icons.PHONE, size=20, color=ft.Colors.BLUE_400),
                    ft.Column([
                        ft.Text("手机", size=11, color=ft.Colors.GREY_500),
                        ft.Text(user_info.get('phone', 'N/A'), size=14, weight="w500"),
                    ], spacing=2),
                ], spacing=12),

                ft.Row([
                    ft.Icon(ft.Icons.ACCESS_TIME, size=20, color=ft.Colors.BLUE_400),
                    ft.Column([
                        ft.Text("登录时间", size=11, color=ft.Colors.GREY_500),
                        ft.Text(user_info.get('login_time', 'N/A'), size=14, weight="w500"),
                    ], spacing=2),
                ], spacing=12),
            ], spacing=18),
            padding=ft.padding.only(top=15),
        ),
    ], spacing=0)

    # 创建对话框
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Row([
            ft.Icon(ft.Icons.PERSON, color=ft.Colors.BLUE_400, size=28),
            ft.Text("用户信息", size=22, weight="bold"),
        ], spacing=10),
        content=ft.Container(
            content=user_info_content,
            width=380,
            padding=ft.padding.symmetric(horizontal=10, vertical=10),
        ),
        actions=[
            ft.TextButton(
                "关闭",
                on_click=handle_close,
                style=ft.ButtonStyle(
                    color=ft.Colors.GREY_400,
                    overlay_color=ft.Colors.with_opacity(0.1, ft.Colors.GREY_400),
                ),
            ),
            ft.ElevatedButton(
                "登出",
                on_click=handle_logout,
                bgcolor=ft.Colors.RED_500,
                color=ft.Colors.WHITE,
                height=45,
                width=100,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=10),
                ),
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        shape=ft.RoundedRectangleBorder(radius=15),
        bgcolor="#1E1E1E",
    )

    page.overlay.append(dialog)
    dialog.open = True
    page.update()


def main(page: ft.Page):
    # --- 1. 页面全局设置 ---
    page.title = "Gemini Pro Studio Clone"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.bgcolor = "#131314"

    # --- 登录状态管理 ---
    current_user = ft.Ref[dict]()  # 存储当前登录用户信息
    current_user.current = None

    # --- 上下文状态管理 ---
    current_context_id = ft.Ref[int]()  # 当前活跃的上下文ID
    current_context_id.current = None
    current_context_name = ft.Ref[str]()  # 当前活跃的上下文名称
    current_context_name.current = "新对话"
    context_list_data = ft.Ref[list]()  # 上下文列表数据
    context_list_data.current = []
    sidebar_expanded = ft.Ref[bool]()  # 侧边栏展开状态
    sidebar_expanded.current = False

    # --- 模型状态管理 ---
    current_model_id = ft.Ref[int]()  # 当前选中的模型ID
    current_model_id.current = None
    current_model_name = ft.Ref[str]()  # 当前选中的模型名称
    current_model_name.current = "默认模型"
    current_model_path = ft.Ref[str]()  # 当前选中的模型路径
    current_model_path.current = model_path
    model_list_data = ft.Ref[list]()  # 模型列表数据
    model_list_data.current = []
    model_panel_expanded = ft.Ref[bool]()  # 模型面板展开状态
    model_panel_expanded.current = False

    # --- 2. 定义组件 ---

    # 当前对话名称显示组件
    context_name_text = ft.Ref[ft.Text]()

    # 模型名称显示组件
    current_model_display_text = ft.Ref[ft.Text]()  # 右侧面板的模型显示
    center_model_display_text = ft.Ref[ft.Text]()  # 中间顶部的模型显示

    def update_model_display():
        """更新右侧模型名称显示"""
        if current_model_display_text.current:
            current_model_display_text.current.value = current_model_name.current
            page.update()

    def update_center_model_display():
        """更新中间模型名称显示"""
        if center_model_display_text.current:
            center_model_display_text.current.value = current_model_name.current
            page.update()

    def update_context_name_display():
        """更新对话名称显示"""
        if context_name_text.current:
            context_name_text.current.value = current_context_name.current
            page.update()

    def on_context_name_click(e):
        """点击对话名称时，弹出重命名对话框"""
        if not current_context_id.current:
            return

        show_rename_dialog(current_context_id.current, current_context_name.current)

    # 上下文管理函数
    def load_user_contexts():
        """加载用户的所有上下文"""
        if not current_user.current:
            return

        user_id = current_user.current.get("id")
        contexts = context_service.query_by_user_id(user_id)
        context_list_data.current = contexts

        # 如果没有上下文，创建默认上下文
        if not contexts:
            context_name = "新对话"
            new_context_id = context_service.create_user_context(user_id, context_name)
            current_context_id.current = new_context_id
            # 重新加载
            contexts = context_service.query_by_user_id(user_id)
            context_list_data.current = contexts
        else:
            # 加载最近的上下文
            recent_context = context_service.query_recent_context_by_user_id(user_id)
            if recent_context:
                current_context_id.current = recent_context.get("id")

    def create_new_context():
        """创建新的上下文 - 弹出输入框让用户输入名称"""
        if not current_user.current:
            return

        # 生成默认名称建议
        existing_contexts = context_list_data.current
        context_count = len([c for c in existing_contexts if c.get("context_name", "").startswith("新对话")])
        default_name = f"新对话 {context_count + 1}" if context_count > 0 else "新对话"

        # 创建输入框
        new_context_name_field = ft.TextField(
            value=default_name,
            label="对话名称",
            hint_text="请输入对话名称",
            border_color=ft.Colors.BLUE_400,
            focused_border_color=ft.Colors.BLUE_600,
            border_radius=10,
            width=350,
            autofocus=True,
        )

        def handle_create(e):
            """处理创建对话"""
            context_name = new_context_name_field.value.strip()

            # 验证输入
            if not context_name:
                new_context_name_field.error_text = "对话名称不能为空"
                page.update()
                return

            user_id = current_user.current.get("id")

            # 创建新上下文
            new_context_id = context_service.create_user_context(user_id, context_name)
            current_context_id.current = new_context_id
            current_context_name.current = context_name

            # 清空聊天窗口
            clear_chat_history()

            # 更新对话名称显示
            update_context_name_display()

            # 重新加载上下文列表
            load_user_contexts()
            update_context_list_ui()

            # 关闭对话框
            dialog.open = False
            page.update()

        def handle_cancel(e):
            """取消创建"""
            dialog.open = False
            page.update()

        # 创建对话框
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE, color=ft.Colors.BLUE_400, size=28),
                ft.Text("新建对话", size=20, weight="bold"),
            ], spacing=10),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("请输入新对话的名称：", size=14, color=ft.Colors.GREY_400),
                    ft.Container(height=10),
                    new_context_name_field,
                ], tight=True, spacing=5),
                width=350,
                padding=ft.padding.only(top=10, bottom=10),
            ),
            actions=[
                ft.TextButton(
                    "取消",
                    on_click=handle_cancel,
                    style=ft.ButtonStyle(
                        color=ft.Colors.GREY_400,
                        overlay_color=ft.Colors.with_opacity(0.1, ft.Colors.GREY_400),
                    ),
                ),
                ft.ElevatedButton(
                    "创建",
                    on_click=handle_create,
                    bgcolor=ft.Colors.BLUE_500,
                    color=ft.Colors.WHITE,
                    height=45,
                    width=100,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=10),
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=15),
            bgcolor="#1E1E1E",
        )

        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    def switch_context(context_id: int):
        """切换到指定的上下文"""
        if not current_user.current:
            return

        user_id = current_user.current.get("id")
        current_context_id.current = context_id

        # 获取并更新当前对话名称
        for ctx in context_list_data.current:
            if ctx.get("id") == context_id:
                current_context_name.current = ctx.get("context_name", "未命名对话")
                break

        # 更新上下文的更新时间
        context_service.update_context_time(context_id)

        # 加载该上下文的历史消息
        messages = context_content_service.query_by_user_id_and_context_id(user_id, context_id)

        # 清空当前聊天窗口
        clear_chat_history()

        # 渲染历史消息
        for msg_data in messages:
            try:
                content = json.loads(msg_data.get("content", "{}"))
                role = content.get("role", "")
                message = content.get("message", "")

                if role == "user":
                    # 渲染用户消息
                    chat_history.controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Container(
                                    content=ft.Text(message, size=15, weight="w500"),
                                    bgcolor="#2B5278",
                                    padding=ft.padding.symmetric(horizontal=18, vertical=14),
                                    border_radius=18,
                                    shadow=ft.BoxShadow(
                                        spread_radius=0,
                                        blur_radius=8,
                                        color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK),
                                        offset=ft.Offset(0, 2),
                                    ),
                                ),
                            ], alignment=ft.MainAxisAlignment.END),
                            margin=ft.margin.only(left=80),
                        )
                    )
                elif role == "assistant":
                    # 渲染AI消息
                    chat_history.controls.append(
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Container(
                                        content=ft.Icon(ft.Icons.SMART_TOY, size=20, color=ft.Colors.BLUE_400),
                                        bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.BLUE_400),
                                        border_radius=20,
                                        padding=8,
                                    ),
                                    ft.Text("Gemini", weight="bold", size=15, color=ft.Colors.BLUE_300),
                                ], spacing=10),
                                ft.Markdown(
                                    message,
                                    selectable=True,
                                    extension_set=ft.MarkdownExtensionSet.GITHUB_WEB
                                ),
                            ], spacing=12),
                            bgcolor="#1E1E1E",
                            padding=20,
                            border_radius=16,
                            margin=ft.margin.only(right=80),
                            border=ft.border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.BLUE_400)),
                            shadow=ft.BoxShadow(
                                spread_radius=0,
                                blur_radius=10,
                                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                                offset=ft.Offset(0, 2),
                            ),
                        )
                    )
            except Exception as e:
                print(f"渲染消息失败: {e}")

        # 更新对话名称显示
        update_context_name_display()

        # 更新上下文列表UI（高亮当前上下文）
        update_context_list_ui()
        page.update()

    def clear_chat_history():
        """清空聊天历史（保留欢迎语）"""
        chat_history.controls.clear()
        # 添加欢迎语
        chat_history.controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Icon(ft.Icons.SMART_TOY, size=20, color=ft.Colors.BLUE_400),
                            bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.BLUE_400),
                            border_radius=20,
                            padding=8,
                        ),
                        ft.Text(current_model_name.current or "AI助手", weight="bold", size=15,
                                color=ft.Colors.BLUE_300),
                    ], spacing=10),
                    ft.Markdown(
                        f"你好！我是 {current_model_name.current or 'AI助手'}。今天有什么我可以帮你的吗？\n\n你可以尝试问我：\n- 写一段 Python 代码\n- 解释量子物理\n- 生成创意文案",
                        selectable=True,
                        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB
                    ),
                ], spacing=12),
                bgcolor="#1E1E1E",
                padding=20,
                border_radius=16,
                border=ft.border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.BLUE_400)),
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=10,
                    color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                    offset=ft.Offset(0, 2),
                ),
            )
        )

    def save_message_to_context(role: str, message: str):
        """保存消息到当前上下文"""
        if not current_user.current or not current_context_id.current:
            return

        user_id = current_user.current.get("id")
        content = json.dumps({"role": role, "message": message}, ensure_ascii=False)

        try:
            context_content_service.insert_message(user_id, current_context_id.current, content)
            # 更新上下文的更新时间
            context_service.update_context_time(current_context_id.current)
        except Exception as e:
            print(f"保存消息失败: {e}")

    # 登录状态更新函数
    def update_login_button():
        """更新侧边栏登录按钮的显示"""
        if current_user.current:
            # 已登录：显示用户头像和用户名
            sidebar.destinations[4] = ft.NavigationRailDestination(
                icon=ft.Icons.ACCOUNT_CIRCLE,
                selected_icon=ft.Icons.ACCOUNT_CIRCLE,
                label=current_user.current.get("username", "用户"),
                padding=ft.padding.symmetric(vertical=8),
            )
        else:
            # 未登录：显示登录按钮
            sidebar.destinations[4] = ft.NavigationRailDestination(
                icon=ft.Icons.LOGIN,
                selected_icon=ft.Icons.LOGIN,
                label="登录",
                padding=ft.padding.symmetric(vertical=8),
            )
        page.update()

    # 侧边栏点击事件处理
    def handle_sidebar_click(e):
        """处理侧边栏点击事件"""
        index = e.control.selected_index
        print(f"Selected destination: {index}")

        if index == 0:  # New Chat 按钮
            if current_user.current:
                create_new_context()
            else:
                # 未登录：显示登录对话框
                show_login_dialog(page, on_login_success=lambda user: handle_login_success(user))
        elif index == 1:  # Playground 按钮
            # 限制二：检查用户是否已登录
            if current_user.current:
                # 如果 Playground 面板已经展开，则缩回；否则展开
                if sidebar_expanded.current:
                    hide_context_list_panel()
                    sidebar_expanded.current = False
                else:
                    show_context_list_panel()
                    sidebar_expanded.current = True
            else:
                # 未登录：显示登录对话框
                show_login_dialog(page, on_login_success=lambda user: handle_login_success(user))
        elif index == 2:  # Library 按钮（知识库）
            if current_user.current:
                # 如果 Library 面板已经展开，则缩回；否则展开
                if library_panel_expanded.current:
                    hide_library_panel()
                else:
                    show_library_panel()
            else:
                # 未登录：显示登录对话框
                show_login_dialog(page, on_login_success=lambda user: handle_login_success(user))
        elif index == 4:  # 登录/用户按钮
            if current_user.current:
                # 已登录：显示用户菜单
                show_user_menu(page, current_user.current, on_logout=lambda: handle_logout())
            else:
                # 未登录：显示登录对话框
                show_login_dialog(page, on_login_success=lambda user: handle_login_success(user))

    def toggle_context_list():
        """切换上下文列表显示"""
        sidebar_expanded.current = not sidebar_expanded.current
        if sidebar_expanded.current:
            # 展开侧边栏，显示上下文列表
            show_context_list_panel()
        else:
            # 收起侧边栏
            hide_context_list_panel()
        page.update()

    def show_context_list_panel():
        """显示上下文列表面板"""
        # 这个函数将在创建面板组件后实现
        pass

    def hide_context_list_panel():
        """隐藏上下文列表面板"""
        # 这个函数将在创建面板组件后实现
        pass

    def handle_login_success(user):
        """登录成功回调"""
        current_user.current = user
        update_login_button()

        # 加载用户上下文
        load_user_contexts()

        # 如果有最近的上下文，加载它
        if current_context_id.current:
            switch_context(current_context_id.current)

        print(f"用户 {user.get('username')} 登录成功")

    def handle_logout():
        """登出回调"""
        current_user.current = None
        current_context_id.current = None
        context_list_data.current = []
        update_login_button()
        clear_chat_history()
        print("用户已登出")

    # 左侧侧边栏
    sidebar = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=80,
        min_extended_width=220,
        group_alignment=-0.9,
        bgcolor="#1A1A1B",
        indicator_color=ft.Colors.with_opacity(0.15, ft.Colors.BLUE_400),
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icons.ADD_CIRCLE_OUTLINE,
                selected_icon=ft.Icons.ADD_CIRCLE,
                label="New Chat",
                padding=ft.padding.symmetric(vertical=8),
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.LIBRARY_BOOKS_OUTLINED,
                selected_icon=ft.Icons.LIBRARY_BOOKS,
                label="Playground",
                padding=ft.padding.symmetric(vertical=8),
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.FOLDER_OUTLINED,
                selected_icon=ft.Icons.FOLDER,
                label="Library",
                padding=ft.padding.symmetric(vertical=8),
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.SETTINGS_OUTLINED,
                selected_icon=ft.Icons.SETTINGS,
                label="Settings",
                padding=ft.padding.symmetric(vertical=8),
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.LOGIN,
                selected_icon=ft.Icons.LOGIN,
                label="登录",
                padding=ft.padding.symmetric(vertical=8),
            ),
        ],
        on_change=handle_sidebar_click,
    )

    # 输出模式状态（True=流式输出，False=批量输出）
    is_streaming_mode = ft.Ref[ft.Switch]()

    # 中间：聊天历史显示区域
    chat_history = ft.ListView(
        expand=True,
        spacing=16,
        padding=ft.padding.symmetric(horizontal=30, vertical=20),
        auto_scroll=True,
    )

    # 欢迎语将在模型初始化后添加

    # 中间：底部输入框
    user_input = ft.TextField(
        hint_text="在这里输入提示词...",
        hint_style=ft.TextStyle(size=14, color=ft.Colors.GREY_500),
        border_color=ft.Colors.BLUE_400,
        focused_border_color=ft.Colors.BLUE_600,
        bgcolor="#1E1E1E",
        filled=True,
        expand=True,
        multiline=True,
        min_lines=1,
        max_lines=5,
        border_radius=20,
        text_size=15,
        content_padding=ft.padding.symmetric(horizontal=20, vertical=16),
        cursor_color=ft.Colors.BLUE_400,
    )

    def send_message(e):
        # 限制一：检查用户是否已登录
        if not current_user.current:
            # 未登录，显示登录对话框
            show_login_dialog(page, on_login_success=lambda user: handle_login_success(user))
            return

        if not user_input.value:
            return

        user_query = user_input.value
        user_input.value = ""
        page.update()

        # 保存用户消息到上下文
        save_message_to_context("user", user_query)

        # 添加用户消息
        chat_history.controls.append(
            ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Text(user_query, size=15, weight="w500"),
                        bgcolor="#2B5278",
                        padding=ft.padding.symmetric(horizontal=18, vertical=14),
                        border_radius=18,
                        shadow=ft.BoxShadow(
                            spread_radius=0,
                            blur_radius=8,
                            color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK),
                            offset=ft.Offset(0, 2),
                        ),
                    ),
                ], alignment=ft.MainAxisAlignment.END),
                margin=ft.margin.only(left=80),
            )
        )

        # 构建包含历史上下文的消息列表
        def build_message_history():
            """构建消息历史列表"""
            messages = []
            if current_user.current and current_context_id.current:
                # 从数据库加载历史消息
                user_id = current_user.current.get("id")
                history_messages = context_content_service.query_by_user_id_and_context_id(
                    user_id, current_context_id.current
                )

                # 转换为消息格式
                for msg_data in history_messages:
                    try:
                        content = json.loads(msg_data.get("content", "{}"))
                        role = content.get("role", "")
                        message = content.get("message", "")

                        if role in ["user", "assistant"]:
                            messages.append({
                                "role": role,
                                "content": message
                            })
                    except Exception as e:
                        print(f"解析历史消息失败: {e}")

            return messages

        # 根据输出模式选择流式或批量输出
        if is_streaming_mode.current.value:
            # 流式输出模式
            ai_container = create_streaming_ai_response(user_query, page, save_callback=save_message_to_context)
            chat_history.controls.append(ai_container)
        else:
            # 批量输出模式
            try:
                # 构建消息历史
                messages = build_message_history()

                # 调用LLM（传入完整的消息历史）
                response = askLLm.chat(messages)

                # 保存AI回复到上下文
                save_message_to_context("assistant", response)

                chat_history.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Container(
                                    content=ft.Icon(ft.Icons.SMART_TOY, size=20, color=ft.Colors.BLUE_400),
                                    bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.BLUE_400),
                                    border_radius=20,
                                    padding=8,
                                ),
                                ft.Text("Gemini", weight="bold", size=15, color=ft.Colors.BLUE_300),
                            ], spacing=10),
                            ft.Markdown(
                                response,
                                selectable=True,
                                extension_set=ft.MarkdownExtensionSet.GITHUB_WEB
                            ),
                        ], spacing=12),
                        bgcolor="#1E1E1E",
                        padding=20,
                        border_radius=16,
                        margin=ft.margin.only(right=80),
                        border=ft.border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.BLUE_400)),
                        shadow=ft.BoxShadow(
                            spread_radius=0,
                            blur_radius=10,
                            color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                            offset=ft.Offset(0, 2),
                        ),
                    )
                )
            except Exception as ex:
                chat_history.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Container(
                                    content=ft.Icon(ft.Icons.ERROR_OUTLINE, size=20, color=ft.Colors.RED_400),
                                    bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.RED_400),
                                    border_radius=20,
                                    padding=8,
                                ),
                                ft.Text("错误", weight="bold", size=15, color=ft.Colors.RED_300),
                            ], spacing=10),
                            ft.Text(f"{str(ex)}", size=15),
                        ], spacing=12),
                        bgcolor="#1E1E1E",
                        padding=20,
                        border_radius=16,
                        margin=ft.margin.only(right=80),
                        border=ft.border.all(1, ft.Colors.with_opacity(0.2, ft.Colors.RED_400)),
                        shadow=ft.BoxShadow(
                            spread_radius=0,
                            blur_radius=10,
                            color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                            offset=ft.Offset(0, 2),
                        ),
                    )
                )

        page.update()

    send_button = ft.IconButton(
        icon=ft.Icons.SEND_ROUNDED,
        icon_color=ft.Colors.WHITE,
        bgcolor=ft.Colors.BLUE_500,
        icon_size=24,
        on_click=send_message,
        style=ft.ButtonStyle(
            shape=ft.CircleBorder(),
            padding=12,
        ),
    )

    # 中间区域布局
    center_layout = ft.Container(
        expand=True,
        padding=ft.padding.only(top=15, bottom=20, left=15, right=20),
        content=ft.Column(
            controls=[
                # 顶部模型选择和输出模式切换
                ft.Container(
                    content=ft.Row([
                        # 当前对话名称显示（可点击编辑）
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.Icons.CHAT_BUBBLE_OUTLINE, size=18, color=ft.Colors.BLUE_400),
                                ft.Text(
                                    ref=context_name_text,
                                    value=current_context_name.current,
                                    size=16,
                                    weight="bold",
                                    color=ft.Colors.WHITE,
                                ),
                                ft.Icon(ft.Icons.EDIT_OUTLINED, size=16, color=ft.Colors.GREY_500),
                            ], spacing=8),
                            padding=ft.padding.only(right=20),
                            on_click=on_context_name_click,
                            tooltip="点击编辑对话名称",
                            ink=True,
                        ),
                        ft.VerticalDivider(width=1, color=ft.Colors.GREY_700),
                        ft.Container(width=10),
                        ft.Icon(ft.Icons.PSYCHOLOGY, size=20, color=ft.Colors.BLUE_400),
                        ft.Text("Model:", size=15, color=ft.Colors.GREY_400, weight="w500"),
                        ft.Text(
                            ref=center_model_display_text,
                            value=current_model_name.current,
                            size=14,
                            weight="bold",
                            color=ft.Colors.BLUE_300,
                        ),
                        ft.Container(width=20),
                        ft.Icon(ft.Icons.TUNE, size=20, color=ft.Colors.BLUE_400),
                        ft.Text("输出模式:", size=15, color=ft.Colors.GREY_400, weight="w500"),
                        ft.Switch(
                            ref=is_streaming_mode,
                            label="流式输出",
                            value=True,
                            active_color=ft.Colors.BLUE_500,
                            label_style=ft.TextStyle(size=14),
                        ),
                    ], spacing=10),
                    bgcolor="#1A1A1B",
                    padding=ft.padding.symmetric(horizontal=20, vertical=12),
                    border_radius=12,
                    margin=ft.margin.only(bottom=10),
                ),
                chat_history,
                # 底部输入框区域
                ft.Container(
                    content=ft.Row([
                        user_input,
                        send_button
                    ], spacing=12, alignment=ft.MainAxisAlignment.CENTER),
                    padding=ft.padding.only(top=10),
                ),
            ]
        )
    )

    # 右侧参数栏状态管理
    right_panel_expanded = ft.Ref[bool]()
    right_panel_expanded.current = True
    right_panel_container = ft.Ref[ft.Container]()
    right_panel_content = ft.Ref[ft.Column]()

    # 折叠按钮图标引用
    right_panel_toggle_icon = ft.Ref[ft.IconButton]()

    def on_model_display_click(e):
        """点击模型显示区域，展开模型选择面板"""
        toggle_model_panel()

    def toggle_right_panel(e):
        """切换右侧面板展开/折叠状态"""
        right_panel_expanded.current = not right_panel_expanded.current

        if right_panel_expanded.current:
            # 展开
            right_panel_container.current.width = 320
            right_panel_content.current.visible = True
            right_panel_toggle_icon.current.icon = ft.Icons.CHEVRON_RIGHT
            right_panel_toggle_icon.current.tooltip = "折叠面板"
        else:
            # 折叠
            right_panel_container.current.width = 60
            right_panel_content.current.visible = False
            right_panel_toggle_icon.current.icon = ft.Icons.CHEVRON_LEFT
            right_panel_toggle_icon.current.tooltip = "展开面板"

        page.update()

    # 右侧参数栏
    right_panel = ft.Container(
        ref=right_panel_container,
        width=320,
        bgcolor="#1A1A1B",
        padding=ft.padding.symmetric(horizontal=20, vertical=25),
        animate=ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT),
        content=ft.Column([
            # 标题区域（可点击折叠/展开）
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.SETTINGS, size=22, color=ft.Colors.BLUE_400),
                    ft.Text("Run Settings", size=19, weight="bold", color=ft.Colors.WHITE),
                    ft.IconButton(
                        ref=right_panel_toggle_icon,
                        icon=ft.Icons.CHEVRON_RIGHT,
                        icon_size=24,
                        icon_color=ft.Colors.GREY_400,
                        on_click=toggle_right_panel,
                        tooltip="折叠面板",
                    ),
                ], spacing=10, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                on_click=toggle_right_panel,
                ink=True,
            ),

            # 可折叠的设置内容
            ft.Column(
                ref=right_panel_content,
                controls=[
                    ft.Divider(color=ft.Colors.GREY_800, height=20),

                    # === 当前模型显示区域 ===
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.MEMORY, size=18, color=ft.Colors.BLUE_400),
                                ft.Text("当前模型", size=14, weight="w500", color=ft.Colors.GREY_400),
                            ], spacing=8),
                            ft.Container(
                                content=ft.Row([
                                    ft.Text(
                                        ref=current_model_display_text,
                                        value=current_model_name.current,
                                        size=15,
                                        weight="bold",
                                        color=ft.Colors.WHITE,
                                    ),
                                    ft.Icon(ft.Icons.ARROW_FORWARD_IOS, size=14, color=ft.Colors.GREY_500),
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                bgcolor="#2B2D31",
                                padding=ft.padding.symmetric(horizontal=15, vertical=12),
                                border_radius=10,
                                border=ft.border.all(1, ft.Colors.BLUE_400),
                                on_click=on_model_display_click,
                                ink=True,
                                tooltip="点击选择模型",
                            ),
                        ], spacing=8),
                        padding=ft.padding.only(bottom=15),
                    ),

                    ft.Divider(color=ft.Colors.GREY_800, height=20),

                    # Temperature 设置
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text("Temperature", size=15, weight="w500", color=ft.Colors.GREY_300),
                                ft.Text("0.7", size=13, color=ft.Colors.BLUE_400, weight="bold"),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Slider(
                                min=0,
                                max=1,
                                divisions=10,
                                value=0.7,
                                active_color=ft.Colors.BLUE_500,
                                inactive_color=ft.Colors.GREY_700,
                                thumb_color=ft.Colors.BLUE_400,
                            ),
                        ], spacing=8),
                        padding=ft.padding.only(bottom=15),
                    ),

                    # Top K 设置
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text("Top K", size=15, weight="w500", color=ft.Colors.GREY_300),
                                ft.Text("40", size=13, color=ft.Colors.BLUE_400, weight="bold"),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Slider(
                                min=1,
                                max=100,
                                divisions=100,
                                value=40,
                                active_color=ft.Colors.BLUE_500,
                                inactive_color=ft.Colors.GREY_700,
                                thumb_color=ft.Colors.BLUE_400,
                            ),
                        ], spacing=8),
                        padding=ft.padding.only(bottom=20),
                    ),

                    ft.Divider(color=ft.Colors.GREY_800, height=20),

                    # Safety Settings 区域
                    ft.Row([
                        ft.Icon(ft.Icons.SECURITY, size=20, color=ft.Colors.BLUE_400),
                        ft.Text("Safety Settings", size=16, weight="bold", color=ft.Colors.GREY_300),
                    ], spacing=10),

                    ft.Container(height=10),

                    # Safety 开关
                    ft.Container(
                        content=ft.Column([
                            ft.Container(
                                content=ft.Row([
                                    ft.Icon(ft.Icons.BLOCK, size=18, color=ft.Colors.ORANGE_400),
                                    ft.Text("Block Harassment", size=14, color=ft.Colors.GREY_300),
                                    ft.Switch(
                                        value=True,
                                        active_color=ft.Colors.BLUE_500,
                                        scale=0.9,
                                    ),
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                bgcolor="#2B2D31",
                                padding=ft.padding.symmetric(horizontal=15, vertical=10),
                                border_radius=10,
                            ),

                            ft.Container(
                                content=ft.Row([
                                    ft.Icon(ft.Icons.REPORT, size=18, color=ft.Colors.RED_400),
                                    ft.Text("Block Hate Speech", size=14, color=ft.Colors.GREY_300),
                                    ft.Switch(
                                        value=True,
                                        active_color=ft.Colors.BLUE_500,
                                        scale=0.9,
                                    ),
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                bgcolor="#2B2D31",
                                padding=ft.padding.symmetric(horizontal=15, vertical=10),
                                border_radius=10,
                            ),
                        ], spacing=10),
                    ),
                ],
                spacing=5,
                visible=True,
            ),
        ], spacing=5)
    )

    # 上下文列表面板
    context_list_container = ft.Ref[ft.Container]()
    search_field = ft.Ref[ft.TextField]()
    context_list_view = ft.Ref[ft.ListView]()

    def create_context_item(context_data):
        """创建单个上下文列表项"""
        context_id = context_data.get("id")
        context_name = context_data.get("context_name", "未命名对话")
        update_time = context_data.get("update_time", "")
        is_active = context_id == current_context_id.current

        def on_context_click(e):
            """点击上下文项"""
            switch_context(context_id)
            sidebar_expanded.current = False
            hide_context_list_panel()

        def on_rename_click(e):
            """重命名上下文"""
            show_rename_dialog(context_id, context_name)

        def on_delete_click(e):
            """删除上下文"""
            show_delete_confirm_dialog(context_id, context_name)

        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Text(context_name, size=14, weight="bold",
                                color=ft.Colors.WHITE if is_active else ft.Colors.GREY_300),
                        ft.Text(update_time[:16] if update_time else "", size=11, color=ft.Colors.GREY_500),
                    ], spacing=4),
                    expand=True,
                ),
                ft.IconButton(
                    icon=ft.Icons.EDIT_OUTLINED,
                    icon_size=18,
                    icon_color=ft.Colors.GREY_400,
                    on_click=on_rename_click,
                    tooltip="重命名",
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    icon_size=18,
                    icon_color=ft.Colors.RED_400,
                    on_click=on_delete_click,
                    tooltip="删除",
                ),
            ], spacing=5),
            bgcolor=ft.Colors.BLUE_700 if is_active else "#2B2D31",
            padding=ft.padding.symmetric(horizontal=15, vertical=12),
            border_radius=10,
            on_click=on_context_click,
            border=ft.border.only(left=ft.BorderSide(4, ft.Colors.BLUE_400)) if is_active else None,
        )

    def show_rename_dialog(context_id, old_name):
        """显示重命名对话框"""
        new_name_field = ft.TextField(
            value=old_name,
            label="新名称",
            border_color=ft.Colors.BLUE_400,
            focused_border_color=ft.Colors.BLUE_600,
            border_radius=10,
            width=300,
        )

        def handle_rename(e):
            new_name = new_name_field.value
            if new_name and new_name != old_name:
                success = context_service.update_context_name(context_id, new_name)
                if success:
                    # 如果重命名的是当前活跃的对话，更新顶部显示
                    if context_id == current_context_id.current:
                        current_context_name.current = new_name
                        update_context_name_display()

                    load_user_contexts()
                    update_context_list_ui()
            dialog.open = False
            page.update()

        def handle_cancel(e):
            dialog.open = False
            page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("重命名对话", size=18, weight="bold"),
            content=new_name_field,
            actions=[
                ft.TextButton("取消", on_click=handle_cancel),
                ft.ElevatedButton("确定", on_click=handle_rename, bgcolor=ft.Colors.BLUE_500),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor="#1E1E1E",
        )

        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    def show_delete_confirm_dialog(context_id, context_name):
        """显示删除确认对话框"""

        def handle_delete(e):
            success = context_service.delete_context(context_id)
            if success:
                # 如果删除的是当前上下文，切换到其他上下文
                if context_id == current_context_id.current:
                    load_user_contexts()
                    if context_list_data.current:
                        # 切换到第一个可用的上下文
                        switch_context(context_list_data.current[0].get("id"))
                    else:
                        # 没有其他上下文，创建新的
                        create_new_context()
                else:
                    load_user_contexts()
                    update_context_list_ui()
            dialog.open = False
            page.update()

        def handle_cancel(e):
            dialog.open = False
            page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("确认删除", size=18, weight="bold", color=ft.Colors.RED_400),
            content=ft.Text(f"确定要删除对话 \"{context_name}\" 吗？\n此操作不可恢复。", size=14),
            actions=[
                ft.TextButton("取消", on_click=handle_cancel),
                ft.ElevatedButton("删除", on_click=handle_delete, bgcolor=ft.Colors.RED_500),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor="#1E1E1E",
        )

        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    def on_search_change(e):
        """搜索框内容变化"""
        keyword = search_field.current.value
        if keyword:
            filtered_contexts = context_service.search_context_by_name(current_user.current.get("id"), keyword)
        else:
            filtered_contexts = context_list_data.current

        # 更新列表显示
        context_list_view.current.controls.clear()
        for ctx in filtered_contexts:
            context_list_view.current.controls.append(create_context_item(ctx))
        page.update()

    # 创建上下文列表面板
    context_panel = ft.Container(
        ref=context_list_container,
        width=0,
        bgcolor="#1A1A1B",
        padding=ft.padding.symmetric(horizontal=15, vertical=20),
        content=ft.Column([
            # 标题
            ft.Row([
                ft.Icon(ft.Icons.LIBRARY_BOOKS, size=22, color=ft.Colors.BLUE_400),
                ft.Text("对话历史", size=18, weight="bold", color=ft.Colors.WHITE),
            ], spacing=10),

            ft.Divider(color=ft.Colors.GREY_800, height=20),

            # 搜索框
            ft.TextField(
                ref=search_field,
                hint_text="搜索对话...",
                prefix_icon=ft.Icons.SEARCH,
                border_color=ft.Colors.BLUE_400,
                focused_border_color=ft.Colors.BLUE_600,
                border_radius=10,
                text_size=14,
                height=45,
                on_change=on_search_change,
            ),

            ft.Container(height=10),

            # 上下文列表
            ft.Container(
                content=ft.ListView(
                    ref=context_list_view,
                    spacing=10,
                    expand=True,
                ),
                expand=True,
            ),
        ], spacing=10),
        visible=False,
        animate=ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT),
    )

    def update_context_list_ui():
        """更新上下文列表UI"""
        if not context_list_view.current:
            return

        context_list_view.current.controls.clear()
        for ctx in context_list_data.current:
            context_list_view.current.controls.append(create_context_item(ctx))
        page.update()

    def show_context_list_panel():
        """显示上下文列表面板"""
        # 隐藏知识库面板（互斥）
        hide_library_panel()
        context_list_container.current.width = 300
        context_list_container.current.visible = True
        sidebar_expanded.current = True  # 同步状态
        update_context_list_ui()
        page.update()

    def hide_context_list_panel():
        """隐藏上下文列表面板"""
        context_list_container.current.width = 0
        context_list_container.current.visible = False
        sidebar_expanded.current = False  # 同步状态
        page.update()

    # ==================== 知识库面板 ====================
    library_panel_container = ft.Ref[ft.Container]()
    library_search_field = ft.Ref[ft.TextField]()
    library_list_view = ft.Ref[ft.ListView]()
    library_list_data = ft.Ref[list]()
    library_list_data.current = []
    library_panel_expanded = ft.Ref[bool]()
    library_panel_expanded.current = False

    # ==================== 模型管理面板 ====================
    model_panel_container = ft.Ref[ft.Container]()
    model_search_field = ft.Ref[ft.TextField]()
    model_list_view = ft.Ref[ft.ListView]()

    def create_library_item(library_data):
        """创建单个知识库列表项"""
        library_id = library_data.get("id")
        library_name = library_data.get("name", "未命名知识库")
        update_time = library_data.get("update_time", "")

        def on_library_click(e):
            """点击知识库项，显示详情"""
            show_library_detail_dialog(library_id)

        def on_delete_click(e):
            """删除知识库"""
            show_library_delete_confirm_dialog(library_id, library_name)

        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Text(library_name, size=14, weight="bold", color=ft.Colors.WHITE),
                        ft.Text(update_time[:16] if update_time else "", size=11, color=ft.Colors.GREY_500),
                    ], spacing=4),
                    expand=True,
                ),
                ft.IconButton(
                    icon=ft.Icons.VISIBILITY_OUTLINED,
                    icon_size=18,
                    icon_color=ft.Colors.BLUE_400,
                    on_click=on_library_click,
                    tooltip="查看详情",
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    icon_size=18,
                    icon_color=ft.Colors.RED_400,
                    on_click=on_delete_click,
                    tooltip="删除",
                ),
            ], spacing=5),
            bgcolor="#2B2D31",
            padding=ft.padding.symmetric(horizontal=15, vertical=12),
            border_radius=10,
            on_click=on_library_click,
        )

    def show_create_library_dialog():
        """显示新建知识库对话框"""
        title_field = ft.TextField(
            label="标题",
            hint_text="请输入知识库标题",
            border_color=ft.Colors.BLUE_400,
            focused_border_color=ft.Colors.BLUE_600,
            border_radius=10,
            autofocus=True,
        )

        content_field = ft.TextField(
            label="内容",
            hint_text="请输入知识库内容",
            border_color=ft.Colors.BLUE_400,
            focused_border_color=ft.Colors.BLUE_600,
            border_radius=10,
            multiline=True,
            min_lines=10,
            max_lines=20,
        )

        def handle_create(e):
            title = title_field.value
            content = content_field.value

            if not title or not title.strip():
                title_field.error_text = "标题不能为空"
                page.update()
                return

            if not content or not content.strip():
                content_field.error_text = "内容不能为空"
                page.update()
                return

            try:
                # 使用全局知识库服务实例
                library_service.create_library(title.strip(), content.strip())

                # 刷新知识库列表
                load_user_libraries()
                update_library_list_ui()

                dialog.open = False
                page.update()
            except Exception as ex:
                print(f"创建知识库失败: {ex}")
                content_field.error_text = f"创建失败: {str(ex)}"
                page.update()

        def handle_cancel(e):
            dialog.open = False
            page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("新建知识库", size=18, weight="bold"),
            content=ft.Container(
                content=ft.Column([
                    title_field,
                    content_field,
                ], spacing=15, tight=True),
                width=500,
                height=400,
            ),
            actions=[
                ft.TextButton("取消", on_click=handle_cancel),
                ft.ElevatedButton("创建", on_click=handle_create, bgcolor=ft.Colors.BLUE_500),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor="#1E1E1E",
        )

        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    def show_library_detail_dialog(library_id):
        """显示知识库详情对话框"""
        try:
            # 使用全局知识库服务实例
            library_detail = library_service.get_library_detail(library_id)

            if not library_detail:
                print(f"知识库 {library_id} 不存在")
                return

            library_name = library_detail.get("name", "未命名知识库")
            library_content = library_detail.get("content", "")
            create_time = library_detail.get("create_time", "")

            def handle_close(e):
                dialog.open = False
                page.update()

            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Row([
                    ft.Icon(ft.Icons.FOLDER, size=24, color=ft.Colors.BLUE_400),
                    ft.Text(library_name, size=18, weight="bold"),
                ], spacing=10),
                content=ft.Container(
                    content=ft.Column([
                        ft.Text(f"创建时间: {create_time[:16] if create_time else ''}", size=12,
                                color=ft.Colors.GREY_400),
                        ft.Divider(color=ft.Colors.GREY_800, height=20),
                        ft.Container(
                            content=ft.Markdown(
                                library_content,
                                selectable=True,
                                extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                                on_tap_link=lambda e: page.launch_url(e.data),
                            ),
                            expand=True,
                        ),
                    ], spacing=10, scroll=ft.ScrollMode.AUTO),
                    width=600,
                    height=500,
                ),
                actions=[
                    ft.ElevatedButton("关闭", on_click=handle_close, bgcolor=ft.Colors.BLUE_500),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
                bgcolor="#1E1E1E",
            )

            page.overlay.append(dialog)
            dialog.open = True
            page.update()
        except Exception as ex:
            print(f"显示知识库详情失败: {ex}")

    def show_library_delete_confirm_dialog(library_id, library_name):
        """显示删除知识库确认对话框"""

        def handle_delete(e):
            try:
                # 使用全局知识库服务实例
                library_service.delete_by_id(library_id)

                # 刷新知识库列表
                load_user_libraries()
                update_library_list_ui()

                dialog.open = False
                page.update()
            except Exception as ex:
                print(f"删除知识库失败: {ex}")

        def handle_cancel(e):
            dialog.open = False
            page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("确认删除", size=18, weight="bold", color=ft.Colors.RED_400),
            content=ft.Text(f"确定要删除知识库 \"{library_name}\" 吗？\n此操作不可恢复。", size=14),
            actions=[
                ft.TextButton("取消", on_click=handle_cancel),
                ft.ElevatedButton("删除", on_click=handle_delete, bgcolor=ft.Colors.RED_500),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor="#1E1E1E",
        )

        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    def on_library_search_change(e):
        """知识库搜索框内容变化"""
        keyword = library_search_field.current.value
        if keyword:
            # 按标题搜索
            filtered_libraries = [lib for lib in library_list_data.current if
                                  keyword.lower() in lib.get("name", "").lower()]
        else:
            filtered_libraries = library_list_data.current

        # 更新列表显示
        library_list_view.current.controls.clear()
        for lib in filtered_libraries:
            library_list_view.current.controls.append(create_library_item(lib))
        page.update()

    def load_user_libraries():
        """加载用户的知识库列表"""
        if not current_user.current:
            library_list_data.current = []
            return

        try:
            # 使用全局知识库服务实例
            user_id = current_user.current.get("id")
            libraries = library_service.get_user_libraries(user_id)
            library_list_data.current = libraries if libraries else []
        except Exception as ex:
            print(f"加载知识库列表失败: {ex}")
            library_list_data.current = []

    def update_library_list_ui():
        """更新知识库列表UI"""
        if not library_list_view.current:
            return

        library_list_view.current.controls.clear()
        for lib in library_list_data.current:
            library_list_view.current.controls.append(create_library_item(lib))
        page.update()

    # 创建知识库面板
    library_panel = ft.Container(
        ref=library_panel_container,
        width=0,
        bgcolor="#1A1A1B",
        padding=ft.padding.symmetric(horizontal=15, vertical=20),
        content=ft.Column([
            # 标题和新建按钮
            ft.Row([
                ft.Icon(ft.Icons.FOLDER, size=22, color=ft.Colors.BLUE_400),
                ft.Text("知识库管理", size=18, weight="bold", color=ft.Colors.WHITE),
            ], spacing=10),

            ft.Divider(color=ft.Colors.GREY_800, height=20),

            # 新建知识库按钮
            ft.ElevatedButton(
                "新建知识库",
                icon=ft.Icons.ADD,
                bgcolor=ft.Colors.BLUE_500,
                color=ft.Colors.WHITE,
                on_click=lambda e: show_create_library_dialog(),
                width=270,
            ),

            ft.Container(height=10),

            # 搜索框
            ft.TextField(
                ref=library_search_field,
                hint_text="搜索知识库...",
                prefix_icon=ft.Icons.SEARCH,
                border_color=ft.Colors.BLUE_400,
                focused_border_color=ft.Colors.BLUE_600,
                border_radius=10,
                text_size=14,
                height=45,
                on_change=on_library_search_change,
            ),

            ft.Container(height=10),

            # 知识库列表
            ft.Container(
                content=ft.ListView(
                    ref=library_list_view,
                    spacing=10,
                    expand=True,
                ),
                expand=True,
            ),
        ], spacing=10),
        visible=False,
        animate=ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT),
    )

    def toggle_library_panel():
        """切换知识库面板显示"""
        library_panel_expanded.current = not library_panel_expanded.current
        if library_panel_expanded.current:
            show_library_panel()
        else:
            hide_library_panel()

    def show_library_panel():
        """显示知识库面板"""
        # 隐藏上下文列表面板（互斥）
        hide_context_list_panel()
        library_panel_container.current.width = 300
        library_panel_container.current.visible = True
        library_panel_expanded.current = True  # 同步状态
        load_user_libraries()
        update_library_list_ui()
        page.update()

    def hide_library_panel():
        """隐藏知识库面板"""
        library_panel_container.current.width = 0
        library_panel_container.current.visible = False
        library_panel_expanded.current = False  # 同步状态
        page.update()

    # ==================== 模型管理面板功能 ====================

    def load_models():
        """加载所有模型列表"""
        try:
            models = model_service.query_all_list_by_name("")
            models.append(local_load_system_model)
            model_list_data.current = models if models else []

            # 尝试根据当前模型路径匹配模型
            if model_list_data.current and current_model_path.current:
                for model in model_list_data.current:
                    if model.get("path") == current_model_path.current:
                        current_model_id.current = model.get("id")
                        current_model_name.current = model.get("name", "默认模型")
                        update_model_display()
                        break
        except Exception as ex:
            print(f"加载模型列表失败: {ex}")
            model_list_data.current = []

    def create_model_item(model_data):
        """创建单个模型列表项"""
        model_id = model_data.get("id")
        model_name = model_data.get("name", "未命名模型")
        model_path_str = model_data.get("path", "")
        model_type = model_data.get("type", "")
        model_description = model_data.get("description", "")
        update_time = model_data.get("update_time", "")
        is_active = model_id == current_model_id.current

        def on_model_click(e):
            """点击模型项，选择该模型"""
            switch_model(model_id)

        return ft.Container(
            content=ft.Column([
                # 模型名称和选中标记
                ft.Row([
                    ft.Icon(
                        ft.Icons.CHECK_CIRCLE,
                        size=20,
                        color=ft.Colors.BLUE_400 if is_active else ft.Colors.TRANSPARENT,
                    ),
                    ft.Text(
                        model_name,
                        size=15,
                        weight="bold",
                        color=ft.Colors.WHITE if is_active else ft.Colors.GREY_300,
                    ),
                ], spacing=8),
                # 模型类型
                ft.Row([
                    ft.Icon(ft.Icons.CATEGORY, size=14, color=ft.Colors.GREY_500),
                    ft.Text(f"类型: {model_type}", size=11, color=ft.Colors.GREY_500),
                ], spacing=5),
                # 模型路径
                ft.Row([
                    ft.Icon(ft.Icons.FOLDER_OUTLINED, size=14, color=ft.Colors.GREY_500),
                    ft.Text(
                        f"路径: {model_path_str[:40]}..." if len(model_path_str) > 40 else f"路径: {model_path_str}",
                        size=11,
                        color=ft.Colors.GREY_500,
                    ),
                ], spacing=5),
                # 模型描述
                ft.Text(
                    model_description[:60] + "..." if len(model_description) > 60 else model_description,
                    size=11,
                    color=ft.Colors.GREY_400,
                ),
                # 更新时间
                ft.Text(
                    f"更新: {update_time[:16] if update_time else ''}",
                    size=10,
                    color=ft.Colors.GREY_600,
                ),
            ], spacing=6),
            bgcolor=ft.Colors.BLUE_700 if is_active else "#2B2D31",
            padding=ft.padding.symmetric(horizontal=15, vertical=12),
            border_radius=10,
            on_click=on_model_click,
            border=ft.border.only(left=ft.BorderSide(4, ft.Colors.BLUE_400)) if is_active else None,
            ink=True,
        )

    def switch_model(model_id: int):
        """切换到指定的模型"""
        global askLLm, askToolLLm, library_service
        import gc

        try:
            # 查找模型数据
            selected_model = None
            for model in model_list_data.current:
                if model.get("id") == model_id:
                    selected_model = model
                    break

            if not selected_model:
                print(f"模型 {model_id} 不存在")
                return

            # 更新当前模型信息
            current_model_id.current = model_id
            current_model_name.current = selected_model.get("name", "默认模型")
            current_model_path.current = selected_model.get("path", "")

            # === 显式释放旧模型资源 ===
            print("正在释放旧模型资源...")

            # 释放旧的 LLM 实例
            if askLLm is not None:
                try:
                    # 如果 LLM 对象有 cleanup/close 方法，调用它
                    if hasattr(askLLm, 'cleanup'):
                        askLLm.cleanup()
                    elif hasattr(askLLm, 'close'):
                        askLLm.close()
                    # 删除引用
                    del askLLm
                except Exception as e:
                    print(f"释放 askLLm 失败: {e}")

            if askToolLLm is not None:
                try:
                    if hasattr(askToolLLm, 'cleanup'):
                        askToolLLm.cleanup()
                    elif hasattr(askToolLLm, 'close'):
                        askToolLLm.close()
                    del askToolLLm
                except Exception as e:
                    print(f"释放 askToolLLm 失败: {e}")

            if library_service is not None:
                try:
                    if hasattr(library_service, 'cleanup'):
                        library_service.cleanup()
                    elif hasattr(library_service, 'close'):
                        library_service.close()
                    del library_service
                except Exception as e:
                    print(f"释放 library_service 失败: {e}")

            # 强制垃圾回收
            gc.collect()
            print("旧模型资源已释放")

            # 重新初始化 LLM（立即应用）
            print(f"正在加载新模型: {current_model_name.current}")
            new_askLLm, new_askToolLLm = register_llm(current_model_path.current)
            askLLm = new_askLLm
            askToolLLm = new_askToolLLm

            # 重新初始化知识库服务
            library_service = SystemUserLibraryService(current_model_path.current)

            # 更新UI显示
            update_model_display()
            update_model_list_ui()
            update_center_model_display()  # 更新中间模型显示

            # 重新加载当前上下文的历史消息（而不是清空）
            if current_context_id.current:
                # 如果有活跃的上下文，重新加载它的历史消息
                switch_context(current_context_id.current)
            else:
                # 如果没有活跃的上下文，只清空并显示欢迎语
                clear_chat_history()

            # 关闭模型面板
            hide_model_panel()

            print(f"已切换到模型: {current_model_name.current} (路径: {current_model_path.current})")
        except Exception as ex:
            print(f"切换模型失败: {ex}")

    def register_llm_with_path(model_path: str):
        """使用指定路径注册LLM（已废弃，使用 register_llm 代替）"""
        return register_llm(model_path)

    def on_model_search_change(e):
        """模型搜索框内容变化"""
        keyword = model_search_field.current.value
        try:
            if keyword:
                filtered_models = model_service.query_all_list_by_name(keyword)
            else:
                filtered_models = model_service.query_all_list_by_name("")

            model_list_data.current = filtered_models if filtered_models else []

            # 更新列表显示
            update_model_list_ui()
        except Exception as ex:
            print(f"搜索模型失败: {ex}")

    def update_model_list_ui():
        """更新模型列表UI"""
        if not model_list_view.current:
            return

        model_list_view.current.controls.clear()
        for model in model_list_data.current:
            model_list_view.current.controls.append(create_model_item(model))
        page.update()

    def show_create_model_dialog():
        """显示新建模型对话框"""
        name_field = ft.TextField(
            label="模型名称",
            hint_text="请输入模型名称",
            border_color=ft.Colors.BLUE_400,
            focused_border_color=ft.Colors.BLUE_600,
            border_radius=10,
            autofocus=True,
        )

        path_field = ft.TextField(
            label="模型路径",
            hint_text="请输入模型文件路径",
            border_color=ft.Colors.BLUE_400,
            focused_border_color=ft.Colors.BLUE_600,
            border_radius=10,
        )

        type_field = ft.TextField(
            label="模型类型",
            hint_text="例如: LLM, Embedding 等",
            border_color=ft.Colors.BLUE_400,
            focused_border_color=ft.Colors.BLUE_600,
            border_radius=10,
        )

        description_field = ft.TextField(
            label="模型描述",
            hint_text="请输入模型描述",
            border_color=ft.Colors.BLUE_400,
            focused_border_color=ft.Colors.BLUE_600,
            border_radius=10,
            multiline=True,
            min_lines=3,
            max_lines=5,
        )

        def handle_create(e):
            name = name_field.value
            path = path_field.value
            model_type = type_field.value
            description = description_field.value

            if not name or not name.strip():
                name_field.error_text = "模型名称不能为空"
                page.update()
                return

            if not path or not path.strip():
                path_field.error_text = "模型路径不能为空"
                page.update()
                return

            if not model_type or not model_type.strip():
                type_field.error_text = "模型类型不能为空"
                page.update()
                return

            if not description or not description.strip():
                description_field.error_text = "模型描述不能为空"
                page.update()
                return

            try:
                from dao.sqlite.system.SystemModelMapper import SystemModelType

                new_model: SystemModelType = {
                    "name": name.strip(),
                    "path": path.strip(),
                    "type": model_type.strip(),
                    "description": description.strip(),
                }

                model_service.create_model(new_model)

                # 刷新模型列表
                load_models()
                update_model_list_ui()

                dialog.open = False
                page.update()
            except Exception as ex:
                print(f"创建模型失败: {ex}")
                description_field.error_text = f"创建失败: {str(ex)}"
                page.update()

        def handle_cancel(e):
            dialog.open = False
            page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE, color=ft.Colors.BLUE_400, size=24),
                ft.Text("新建模型", size=18, weight="bold"),
            ], spacing=10),
            content=ft.Container(
                content=ft.Column([
                    name_field,
                    path_field,
                    type_field,
                    description_field,
                ], spacing=15, tight=True),
                width=500,
                height=400,
            ),
            actions=[
                ft.TextButton("取消", on_click=handle_cancel),
                ft.ElevatedButton("创建", on_click=handle_create, bgcolor=ft.Colors.BLUE_500),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor="#1E1E1E",
        )

        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    def toggle_model_panel():
        """切换模型面板显示"""
        model_panel_expanded.current = not model_panel_expanded.current
        if model_panel_expanded.current:
            show_model_panel()
        else:
            hide_model_panel()

    def show_model_panel():
        """显示模型面板"""
        # 隐藏其他面板（互斥）
        hide_context_list_panel()
        hide_library_panel()

        model_panel_container.current.width = 350
        model_panel_container.current.visible = True
        model_panel_expanded.current = True

        load_models()
        update_model_list_ui()
        page.update()

    def hide_model_panel():
        """隐藏模型面板"""
        model_panel_container.current.width = 0
        model_panel_container.current.visible = False
        model_panel_expanded.current = False
        page.update()

    # 创建模型管理面板
    model_panel = ft.Container(
        ref=model_panel_container,
        width=0,
        bgcolor="#1A1A1B",
        padding=ft.padding.symmetric(horizontal=15, vertical=20),
        content=ft.Column([
            # 标题
            ft.Row([
                ft.Icon(ft.Icons.MEMORY, size=22, color=ft.Colors.BLUE_400),
                ft.Text("模型管理", size=18, weight="bold", color=ft.Colors.WHITE),
            ], spacing=10),

            ft.Divider(color=ft.Colors.GREY_800, height=20),

            # 新建模型按钮
            ft.ElevatedButton(
                "新建模型",
                icon=ft.Icons.ADD,
                bgcolor=ft.Colors.BLUE_500,
                color=ft.Colors.WHITE,
                on_click=lambda e: show_create_model_dialog(),
                width=320,
            ),

            ft.Container(height=10),

            # 搜索框
            ft.TextField(
                ref=model_search_field,
                hint_text="搜索模型...",
                prefix_icon=ft.Icons.SEARCH,
                border_color=ft.Colors.BLUE_400,
                focused_border_color=ft.Colors.BLUE_600,
                border_radius=10,
                text_size=14,
                height=45,
                on_change=on_model_search_change,
            ),

            ft.Container(height=10),

            # 模型列表
            ft.Container(
                content=ft.ListView(
                    ref=model_list_view,
                    spacing=10,
                    expand=True,
                ),
                expand=True,
            ),
        ], spacing=10),
        visible=False,
        animate=ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT),
    )

    # 布局组装
    layout = ft.Row(
        controls=[
            sidebar,
            ft.VerticalDivider(width=1, color="#2D2D2D"),
            context_panel,
            ft.VerticalDivider(width=1, color="#2D2D2D"),
            library_panel,
            ft.VerticalDivider(width=1, color="#2D2D2D"),
            center_layout,
            ft.VerticalDivider(width=1, color="#2D2D2D"),
            right_panel,
            ft.VerticalDivider(width=1, color="#2D2D2D"),
            model_panel,
        ],
        expand=True,
        spacing=0
    )

    page.add(layout)

    # 初始化模型显示
    # 尝试从数据库加载模型并匹配当前模型路径
    try:
        models = model_service.query_all_list_by_name("")
        models.append(local_load_system_model)
        if models:
            model_list_data.current = models
            # 根据当前模型路径匹配模型
            for model in models:
                if model.get("path") == current_model_path.current:
                    current_model_id.current = model.get("id")
                    current_model_name.current = model.get("name")
                    break

        # 更新UI显示
        update_model_display()
        update_center_model_display()
    except Exception as ex:
        print(f"初始化模型显示失败: {ex}")

    # 添加欢迎语（在模型名称初始化后）
    chat_history.controls.append(
        ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(ft.Icons.SMART_TOY, size=20, color=ft.Colors.BLUE_400),
                        bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.BLUE_400),
                        border_radius=20,
                        padding=8,
                    ),
                    ft.Text(current_model_name.current or "AI助手", weight="bold", size=15, color=ft.Colors.BLUE_300),
                ], spacing=10),
                ft.Markdown(
                    f"你好！我是 {current_model_name.current or 'AI助手'}。今天有什么我可以帮你的吗？\n\n你可以尝试问我：\n- 写一段 Python 代码\n- 解释量子物理\n- 生成创意文案",
                    selectable=True,
                    extension_set=ft.MarkdownExtensionSet.GITHUB_WEB
                ),
            ], spacing=12),
            bgcolor="#1E1E1E",
            padding=20,
            border_radius=16,
            border=ft.border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.BLUE_400)),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=10,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                offset=ft.Offset(0, 2),
            ),
        )
    )
    page.update()


if __name__ == "__main__":
    ft.app(target=main)
