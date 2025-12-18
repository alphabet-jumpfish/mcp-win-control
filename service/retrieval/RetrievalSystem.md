这是 RAG 的“大脑”，决定了是否能找到相关信息。不要只做简单的向量相似度搜索（Naive RAG）。
查询预处理 (Query Processing)：
Query Rewrite：用户的问题往往是不完整的。使用 LLM 将“它怎么用？”改写为“Transformer 库中的 Trainer 模块怎么使用？”。
HyDE (Hypothetical Document Embeddings)：让 LLM 先生成一个假设性答案，然后用这个答案去库里搜。
混合检索 (Hybrid Search)：
痛点：向量检索擅长语义匹配，但不擅长精确匹配（如专有名词、产品型号）。
方案：Keyword Search (BM25) + Vector Search (Dense)。将两者的结果加权融合（Reciprocal Rank Fusion, RRF）。
重排序 (Reranking) —— 提分神器：
向量检索为了速度（ANN）会牺牲精度，且 Embedding 往往丢失细微语义。
流程：先粗排检索 Top-50，再用 Cross-Encoder 模型（如 BGE-Reranker, Cohere Rerank）精排选出 Top-5。
这一步能显著提高 Context 的准确率。