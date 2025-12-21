# 工具选择服务使用说明

## 实现策略

1. **规则匹配（快速命中）**：使用关键词匹配，适合高精度场景
2. **Embedding 相似度匹配（兜底方案）**：使用 EmbeddingUtil 计算语义相似度，更鲁棒

## 使用方法

```python
from service.tool.ToolSelectorService import ToolSelector
from service.rag.EmbeddingUtil import EmbeddingUtil

# 初始化（可选：提供 embedding_util 以启用语义匹配）
embedding_util = EmbeddingUtil(embedding_model_path="path/to/model")
tool_selector = ToolSelector(embedding_util=embedding_util)

# 方式1：选择工具
tool_name, score, method = tool_selector.select_tool("帮我搜索一下配置文件")
if tool_name:
    print(f"匹配工具: {tool_name}, 置信度: {score:.2f}, 方式: {method}")

# 方式2：判断是否需要工具
if tool_selector.should_use_tool("今天天气怎么样"):
    print("需要使用工具")
else:
    print("直接使用 LLM 回答")
```

## 内置工具

- `search_files`: 搜索文件
- `read_file`: 读取文件
- `write_file`: 写入文件
- `execute_command`: 执行命令
- `get_system_info`: 获取系统信息
- `list_directory`: 列出目录
- `create_directory`: 创建目录
- `delete_file`: 删除文件
- `copy_file`: 复制文件
- `move_file`: 移动文件

## 自定义工具

```python
# 添加新工具
tool_selector.add_tool(
    tool_name="custom_tool",
    description="自定义工具描述",
    keywords=["关键词1", "关键词2"]
)
```

## 配置参数

- `similarity_threshold`: 相似度阈值（默认 0.6），可通过 `update_similarity_threshold()` 修改