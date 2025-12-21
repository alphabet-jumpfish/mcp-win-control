from typing import List, Dict, Optional, Tuple

# 工具描述常量
TOOL_DESCRIPTIONS: Dict[str, str] = {
    "search_files": "搜索文件：根据关键词在文件系统中搜索文件，支持文件名、路径、扩展名等搜索",
    "read_file": "读取文件：读取指定路径的文件内容",
    "write_file": "写入文件：将内容写入到指定路径的文件",
    "execute_command": "执行命令：在系统中执行命令行指令",
    "get_system_info": "获取系统信息：获取操作系统、CPU、内存等系统信息",
    "list_directory": "列出目录：列出指定目录下的文件和文件夹",
    "create_directory": "创建目录：在指定路径创建新的目录",
    "delete_file": "删除文件：删除指定路径的文件或目录",
    "copy_file": "复制文件：复制文件或目录到目标位置",
    "move_file": "移动文件：移动文件或目录到目标位置",
}

# 工具规则匹配常量
TOOL_RULES: Dict[str, List[str]] = {
    "search_files": [
        "搜索", "查找", "找文件", "搜索文件", "文件搜索",
        "find", "search", "locate", "文件在哪里", "哪个文件"
    ],
    "read_file": [
        "读取", "打开", "查看", "显示", "read", "open", "view",
        "文件内容", "看看文件", "显示文件"
    ],
    "write_file": [
        "写入", "保存", "创建文件", "写文件", "write", "save",
        "创建新文件", "保存文件"
    ],
    "execute_command": [
        "执行", "运行", "命令", "执行命令", "运行命令", "execute",
        "run", "command", "cmd", "终端"
    ],
    "get_system_info": [
        "系统信息", "系统状态", "CPU", "内存", "系统", "system info",
        "系统配置", "硬件信息"
    ],
    "list_directory": [
        "列出", "目录", "文件夹", "列表", "list", "dir", "ls",
        "查看目录", "目录内容"
    ],
    "create_directory": [
        "创建目录", "新建文件夹", "mkdir", "创建文件夹", "建立目录"
    ],
    "delete_file": [
        "删除", "删除文件", "移除", "delete", "remove", "rm",
        "删掉", "清除"
    ],
    "copy_file": [
        "复制", "拷贝", "copy", "cp", "复制文件", "拷贝文件"
    ],
    "move_file": [
        "移动", "剪切", "move", "mv", "移动文件", "剪切文件", "重命名"
    ],
}
