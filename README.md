# MCP-Win-Control 项目说明文档

## 项目概述

MCP-Win-Control 是一个基于 Model Control Protocol (MCP) 的 Windows 系统控制框架，它将大语言模型（LLM）与 Windows 系统操作深度集成，通过自然语言查询实现智能任务自动化。该系统结合了 RAG（检索增强生成）、提示工程和智能工具选择技术，能够将用户请求智能路由到合适的系统工具执行。

### 核心特性

- **智能工具选择**: 基于规则匹配和语义嵌入的双模式工具选择机制
- **高级 RAG 系统**: 支持查询重写、HyDE（假设文档嵌入）和混合检索（BM25 + 向量语义搜索）
- **本地 LLM 推理**: 集成 Qwen3-0.6 模型，支持流式和非流式对话
- **多格式文档处理**: 支持 PDF、Word、Markdown、HTML 等多种文档格式
- **向量数据库**: 使用 Chroma 实现语义搜索和上下文检索
- **Web 界面**: 基于 Flet 框架的跨平台用户界面

## 项目架构

### 核心组件

#### 1. LLM 服务层
- **AskToolLLMService**: 主协调器，负责 LLM 交互、工具选择和执行编排
- **AskLLmService**: 核心 LLM 包装器，使用 Hugging Face Transformers（Qwen3-0.6 模型）
  - 支持流式和非流式对话模式
  - 集成本地模型推理

#### 2. 工具管理层
- **ToolSelectorService**: 智能工具选择器，采用双策略机制
  - 规则匹配：基于关键词的快速匹配
  - 语义匹配：基于嵌入向量的语义相似度匹配（回退策略）
- **ToolService**: 工具参数准备和结果处理
- **ToolList**: 预定义的 10 个系统工具及其匹配规则

#### 3. 数据访问层（DAO）
- **SQLiteDAOService**: 完整的 SQLite 数据库操作（CRUD、表管理）
- **ChromaDocumentDAO**: 向量数据库集成，使用 Chroma 实现语义搜索
- **SystemUserMapper**: 用户数据持久化
- **SystemUserContextMapper**: 用户上下文管理
- **EnvDAOService**: 环境配置存储

#### 4. RAG（检索增强生成）系统
- **EmbeddingUtil**: 使用 HuggingFace 生成嵌入向量
- **DocumentChunker**: 文档分割和分块策略
- **ETLService**: 数据提取、转换和加载
- **RetrievalSystemService**: 高级检索系统，支持三种检索方法
  - Query Rewrite：基于 LLM 的查询增强
  - HyDE：假设文档嵌入
  - Hybrid Search：BM25 关键词搜索 + 向量语义搜索

#### 5. 提示工程
- **PromptEngineeringService**: RAG 提示构建
  - 基于角色的系统提示
  - 边界控制（减少幻觉）
  - 引用格式化

#### 6. 其他组件
- **McpServerController**: MCP 服务器实现（使用 FastMCP）
- **WindowsCommandService**: Windows 命令执行接口
- **WebUi**: 基于 Flet 框架的 Web 界面
- **AuthService**: 身份验证和授权
- **UserMemory**: 内存中的用户会话管理

## 功能特性

### 内置系统工具（10 个）

1. **search_files**: 按关键词、路径、扩展名搜索文件
2. **read_file**: 读取文件内容
3. **write_file**: 写入文件内容
4. **execute_command**: 执行系统命令
5. **get_system_info**: 获取操作系统、CPU、内存信息
6. **list_directory**: 列出目录内容
7. **create_directory**: 创建新目录
8. **delete_file**: 删除文件/目录
9. **copy_file**: 复制文件/目录
10. **move_file**: 移动/重命名文件

### 智能工具选择

- **双模式匹配**: 规则匹配（快速）+ 语义匹配（鲁棒）
- **可配置相似度阈值**: 灵活调整匹配精度
- **支持自定义工具定义**: 可扩展工具集

### 高级 RAG 系统

- **查询重写**: 针对不完整/模糊查询进行优化
- **假设文档嵌入（HyDE）**: 生成假设答案以改进检索
- **混合检索**: 结合 BM25（关键词）和向量（语义）检索
- **重排序**: 提高上下文准确性
- **多格式文档支持**: PDF、Word、Markdown、HTML

### 数据管理

- **SQLite**: 结构化数据存储
- **Chroma 向量数据库**: 语义搜索
- **用户上下文和会话管理**: 保持对话连续性
- **环境配置持久化**: 配置管理

### LLM 集成

- **本地模型推理**: Qwen3-0.6 模型
- **流式和非流式对话模式**: 灵活的交互方式
- **提示工程**: 基于角色的指令和边界控制
- **引用和幻觉控制**: 提高回答准确性

### Web 界面

- **Flet 框架**: 跨平台访问
- **用户认证**: 安全的用户管理
- **会话管理**: 多用户支持

## 技术栈

### 核心依赖

**AI/ML 框架**
- `transformers` (4.57.3): Hugging Face 模型加载和推理
- `mcp` (1.24.0): Model Control Protocol 实现
- `langchain_huggingface` (1.2.0): LangChain 集成
- `langgraph` (1.0.5): 基于图的工作流编排
- `modelscope` (1.32.0): 模型仓库和框架
- `accelerate` (1.12.0): 分布式训练/推理
- `trl` (0.26.0): Transformer 强化学习
- `evalscope`: 模型评估框架
- `onnx` (1.19.1): 模型导出和优化

**数据库和检索**
- `chromadb` (0.4.0+): 向量数据库，用于语义搜索
- `rank-bm25` (0.2.2): BM25 关键词搜索算法
- `sqlite3`: 关系型数据库（内置）

**文档处理**
- `pdfplumber` (0.10.0+): PDF 解析
- `python-docx` (1.1.0+): Word 文档处理
- `beautifulsoup4` (4.12.0+): HTML 解析
- `markdown` (3.5.0+): Markdown 处理

**其他工具**
- `PyYAML` (6.0+): 配置管理
- `flet` (0.28.3): 跨平台 UI 框架

## 使用说明

### 环境要求

- **Python**: 3.8 或更高版本
- **操作系统**: Windows 10/11
- **内存**: 建议 8GB 以上（用于本地 LLM 推理）
- **磁盘空间**: 至少 5GB（用于模型和数据存储）

### 安装步骤

```bash
# 克隆项目
git clone <repository-url>
cd MCP-Win-Control

# 安装依赖
pip install -r requirements.txt

# 配置环境
# 1. 编辑 config.yaml 文件，设置模型路径和数据库路径
# 2. 确保 Qwen3-0.6 模型已下载到 model/qwen3-0.6/ 目录
# 3. 创建必要的数据目录
mkdir -p dataset/chroma dataset/sqlite
```

### 配置说明

编辑 `config.yaml` 文件进行配置：

```yaml
# LLM 模型配置
model:
  path: "model/qwen3-0.6"
  device: "cuda"  # 或 "cpu"

# 数据库配置
database:
  sqlite_path: "dataset/sqlite/mcp.db"
  chroma_path: "dataset/chroma"

# 工具选择器配置
tool_selector:
  similarity_threshold: 0.7
  use_semantic_matching: true

# RAG 配置
rag:
  chunk_size: 500
  chunk_overlap: 50
  retrieval_method: "hybrid"  # query_rewrite, hyde, hybrid
```

### 快速开始

#### 1. 启动 MCP 服务器

```python
from controller.McpServerController import McpServerController

# 启动服务器
controller = McpServerController()
controller.start()
```

#### 2. 使用 LLM 工具服务

```python
from service.llm.AskToolLLMService import AskToolLLM

# 创建 LLM 实例
ask_tool = AskToolLLM()

# 执行查询
result = await ask_tool.run("查询系统信息")
print(result)

# 执行文件操作
result = await ask_tool.run("搜索 C 盘下所有的 .txt 文件")
print(result)
```

#### 3. 使用 RAG 系统

```python
from service.retrieval.RetrievalSystemService import RetrievalSystem

# 初始化检索系统
retrieval = RetrievalSystem()

# 添加文档
retrieval.add_documents("path/to/documents")

# 执行检索
results = retrieval.retrieve("如何使用工具选择器？", method="hybrid")
print(results)
```

#### 4. 启动 Web 界面

```python
from web.WebUi import WebUi

# 启动 Web UI
ui = WebUi()
ui.start()
```

### 使用示例

**示例 1: 文件搜索**
```python
query = "找到所有包含 'config' 的 Python 文件"
result = await ask_tool.run(query)
```

**示例 2: 系统信息查询**
```python
query = "显示当前系统的 CPU 和内存使用情况"
result = await ask_tool.run(query)
```

**示例 3: 文件操作**
```python
query = "将 test.txt 文件复制到 backup 目录"
result = await ask_tool.run(query)
```


## 开发指南

### 项目结构

```
MCP-Win-Control/
├── controller/                          # 控制器层
│   └── McpServerController.py          # MCP 服务器入口
├── dao/                                 # 数据访问层
│   ├── chroma/
│   │   └── ChromaDocumentDAO.py                # 向量数据库 DAO
│   ├── sqlite/
│   │   ├── SQLiteDAOService.py         # SQLite 操作
│   │   ├── system/
│   │   │   └── SystemUserMapper.py     # 用户数据映射
│   │   ├── context/
│   │   │   ├── SystemUserContextMapper.py
│   │   │   └── SystemUserContextContentMapper.py
│   │   └── EnvDAOService.py            # 环境配置
│   ├── memory/
│   │   └── UserMemory.py               # 内存存储
│   └── DatasetType.py                  # 数据集类型定义
├── service/                             # 业务逻辑层
│   ├── llm/
│   │   ├── AskLLmService.py            # LLM 核心服务
│   │   └── AskToolLLMService.py        # LLM + 工具编排
│   ├── tool/
│   │   ├── ToolList.py                 # 工具定义
│   │   ├── ToolService.py              # 工具执行
│   │   └── ToolSelectorService.py      # 工具选择逻辑
│   ├── rag/
│   │   ├── EmbeddingUtil.py            # 嵌入向量生成
│   │   ├── DocumentChunker.py          # 文档分块
│   │   ├── ETLService.py               # 数据处理
│   │   └── RAG.md                      # RAG 文档
│   ├── retrieval/
│   │   ├── RetrievalSystemService.py   # 高级检索
│   │   └── RetrievalSystem.md          # 检索文档
│   ├── promat/
│   │   ├── PromptEngineering.py        # 提示构建
│   │   ├── PromptEngineeringService.py # 提示服务
│   │   └── promat.md                   # 提示文档
│   ├── auth/
│   │   └── AuthService.py              # 身份验证
│   └── windos/
│       └── WindowsCommandService.py    # Windows 命令
├── util/                                # 工具类
│   ├── McpConstant.py                  # 常量定义
│   └── McpConfigUtil.py                # 配置工具
├── web/
│   └── WebUi.py                        # Web 界面
├── model/
│   └── qwen3-0.6/                      # Qwen3 模型文件
├── dataset/
│   ├── chroma/                         # 向量数据库存储
│   └── sqlite/                         # SQLite 数据库
├── config.yaml                         # 配置文件
├── requirements.txt                    # Python 依赖
└── README.md                           # 项目文档
```

### 扩展工具

#### 添加新工具的步骤

1. **在 ToolList.py 中定义工具**

```python
# service/tool/ToolList.py
new_tool = {
    "name": "your_tool_name",
    "description": "工具的详细描述",
    "parameters": {
        "param1": {
            "type": "string",
            "description": "参数描述",
            "required": True
        }
    },
    "rules": ["关键词1", "关键词2"]  # 用于规则匹配
}
```

2. **实现工具处理逻辑**

在 `WindowsCommandService.py` 或创建新的服务类中实现工具逻辑：

```python
def your_tool_name(self, param1: str) -> dict:
    """
    工具实现逻辑
    """
    try:
        # 实现具体功能
        result = perform_operation(param1)
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
```

3. **更新工具选择器配置**

如果需要调整工具选择的相似度阈值，在 `config.yaml` 中修改：

```yaml
tool_selector:
  similarity_threshold: 0.7  # 调整阈值
  use_semantic_matching: true
```

### 自定义 RAG 检索策略

#### 添加新的检索方法

1. **在 RetrievalSystemService.py 中添加方法**

```python
def custom_retrieval(self, query: str, top_k: int = 5) -> List[Document]:
    """
    自定义检索策略
    """
    # 实现检索逻辑
    results = self.vector_store.similarity_search(query, k=top_k)
    return results
```

2. **在配置中启用**

```yaml
rag:
  retrieval_method: "custom"  # 使用自定义方法
```

### 扩展文档处理器

支持新的文档格式：

```python
# service/rag/ETLService.py
def process_custom_format(self, file_path: str) -> List[Document]:
    """
    处理自定义格式文档
    """
    # 实现文档解析逻辑
    content = parse_custom_file(file_path)
    return self.chunker.split_text(content)
```

### 调试和日志

项目使用 Python 的 logging 模块。配置日志级别：

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,  # DEBUG, INFO, WARNING, ERROR
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        用户界面层                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Web UI     │  │  MCP Client  │  │  CLI/API     │      │
│  │   (Flet)     │  │              │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      控制器层                                 │
│              ┌──────────────────────┐                        │
│              │ McpServerController  │                        │
│              └──────────────────────┘                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      LLM 服务层                               │
│  ┌──────────────────┐      ┌──────────────────┐            │
│  │ AskToolLLMService│◄────►│  AskLLmService   │            │
│  │  (工具编排)       │      │  (Qwen3-0.6)     │            │
│  └──────────────────┘      └──────────────────┘            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    工具管理层                                 │
│  ┌──────────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ ToolSelector     │  │  ToolService │  │  ToolList    │ │
│  │ (规则+语义匹配)   │  │  (执行)      │  │  (定义)      │ │
│  └──────────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    RAG & 检索层                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Retrieval    │  │  Embedding   │  │  Prompt      │     │
│  │ System       │  │  Util        │  │  Engineering │     │
│  │ (混合检索)    │  │  (向量化)     │  │  (提示构建)   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    数据访问层                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  ChromaDocumentDAO   │  │  SQLiteDAO   │  │  UserMemory  │     │
│  │  (向量存储)   │  │  (关系存储)   │  │  (会话)      │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Windows 系统层                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  文件系统     │  │  命令执行     │  │  系统信息     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## 工作流程

### 典型查询处理流程

1. **用户输入**: 用户通过 Web UI 或 API 提交自然语言查询
2. **LLM 理解**: AskToolLLMService 使用 Qwen3 模型理解用户意图
3. **工具选择**: ToolSelector 通过规则匹配或语义匹配选择合适的工具
4. **参数提取**: ToolService 从查询中提取工具所需参数
5. **工具执行**: 调用相应的 Windows 命令或文件操作
6. **结果返回**: 将执行结果格式化后返回给用户

### RAG 增强查询流程

1. **查询接收**: 接收用户的复杂查询
2. **查询重写**: 使用 LLM 优化和扩展查询（可选）
3. **混合检索**:
   - BM25 关键词搜索
   - 向量语义搜索
   - 结果融合和重排序
4. **上下文构建**: 使用检索到的文档构建提示上下文
5. **LLM 生成**: 基于上下文生成准确答案
6. **引用标注**: 标注答案来源，减少幻觉

## 性能优化建议

### 1. 模型推理优化
- 使用 GPU 加速（CUDA）
- 启用模型量化（INT8/INT4）
- 批处理多个查询

### 2. 检索优化
- 调整 chunk_size 和 chunk_overlap
- 使用更高效的嵌入模型
- 启用向量索引缓存

### 3. 数据库优化
- 定期清理过期数据
- 为常用查询创建索引
- 使用连接池

## 常见问题（FAQ）

### Q1: 如何更换 LLM 模型？

修改 `config.yaml` 中的模型路径，并确保模型格式兼容 Hugging Face Transformers：

```yaml
model:
  path: "path/to/your/model"
```

### Q2: 如何提高工具选择的准确性？

1. 调整相似度阈值
2. 在 ToolList.py 中添加更多匹配规则
3. 使用更好的嵌入模型

### Q3: 支持哪些文档格式？

目前支持：PDF、Word (.docx)、Markdown (.md)、HTML、纯文本 (.txt)

### Q4: 如何处理大文件？

系统会自动将大文件分块处理。可以在 config.yaml 中调整分块参数：

```yaml
rag:
  chunk_size: 500      # 每块字符数
  chunk_overlap: 50    # 块之间重叠字符数
```

### Q5: 如何启用 GPU 加速？

确保安装了 CUDA 和对应的 PyTorch 版本，然后在配置中设置：

```yaml
model:
  device: "cuda"
```

## 待办事项

- [ ] 添加单元测试和集成测试
- [ ] 支持更多系统工具（网络操作、进程管理等）
- [ ] 优化工具匹配算法（引入学习机制）
- [ ] 增强错误处理和日志记录
- [ ] 添加性能监控和指标收集
- [ ] 支持多语言界面
- [ ] 实现工具执行的安全沙箱
- [ ] 添加 API 文档（Swagger/OpenAPI）

## 贡献指南

欢迎贡献代码、报告问题或提出改进建议。

### 贡献流程

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 代码规范

- 遵循 PEP 8 Python 代码风格
- 添加必要的注释和文档字符串
- 编写单元测试
- 确保所有测试通过

## 许可证

本项目采用 MIT 许可证。详见 LICENSE 文件。

## 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 发送 Pull Request
- 邮件联系项目维护者

## 致谢

感谢以下开源项目：

- [Hugging Face Transformers](https://github.com/huggingface/transformers)
- [LangChain](https://github.com/langchain-ai/langchain)
- [Chroma](https://github.com/chroma-core/chroma)
- [Flet](https://github.com/flet-dev/flet)
- [Qwen](https://github.com/QwenLM/Qwen)

---

**MCP-Win-Control** - 让 AI 智能控制 Windows 系统