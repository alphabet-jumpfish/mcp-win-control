数据准备 -> 索引构建 -> 检索系统 -> 生成系统 -> 评估与迭代
1、第一阶段：数据准备 (Data Preparation)
    这是 RAG 的“地基”，数据质量直接决定系统上限。
    数据清洗 (ETL)：
    格式统一：处理 PDF、Word、Markdown、HTML 等不同格式。对于 PDF，要解决表格、多栏布局解析错乱的问题（推荐工具：Unstructured, LlamaParse）。
    去噪：去除页眉、页脚、HTML 标签、无意义的特殊字符。
2、分块策略 (Chunking Strategy) —— 这是最关键的超参数：
    Fixed-size (固定大小)：简单，但可能切断语义（如 chunk_size=512, overlap=50）。
    Recursive (递归式)：按段落 -> 句子 -> 单词层级切分，保留结构完整性（最常用）。
    Semantic (语义分块)：利用 Embedding 判断句子间的语义突变点进行切分，效果最好但计算成本高。
    Agentic/Parent-Child：检索时用小切片（提升匹配度），给 LLM 时送入该切片所属的大父文档（提供完整上下文）。