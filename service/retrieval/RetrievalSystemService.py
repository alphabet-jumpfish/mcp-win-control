"""
高级检索系统实现
包含三种检索方法：
1. Query Rewrite - 查询重写
2. HyDE - 假设性文档嵌入
3. Hybrid Search - BM25 + Vector Search 混合检索
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from collections import defaultdict
import re

from service.llm.AskLLmService import AskLLM
from service.rag.EmbeddingUtil import EmbeddingUtil
from dao.chroma.ChromaDocumentDAO import ChromaDocumentDAO


class RetrievalSystem:
    """
    高级检索系统类
    实现 Query Rewrite、HyDE 和 Hybrid Search 三种检索方法
    """

    def __init__(
            self,
            llm: AskLLM,
            embedding_util: EmbeddingUtil,
            chroma_dao: ChromaDocumentDAO
    ):
        """
        初始化检索系统
        
        Args:
            llm: LLM 实例，用于查询重写和 HyDE
            embedding_util: 嵌入工具实例，用于向量化
            chroma_docuement_dao: ChromaDocumentDAO 实例，用于向量检索
        """
        self.llm = llm
        self.embedding_util = embedding_util
        self.chroma_dao = chroma_dao

        # BM25 索引（延迟初始化）
        self._bm25_index = None
        self._bm25_documents = None
        self._bm25_doc_ids = None

    # 核心方法一 查询预处理 (Query Processing)
    def query_rewrite(
            self,
            query: str,
            context: Optional[str] = None
    ) -> str:
        """
        Query Rewrite：使用 LLM 将不完整的查询改写为更完整、更具体的查询
        Args:
            query: 原始查询（可能不完整）
            context: 可选的上下文信息，帮助理解查询意图
        Returns:
            改写后的查询
        """
        # 构建提示词
        if context:
            prompt = f"""你是一个查询重写助手。用户的问题可能不完整或模糊，请将其改写为更完整、更具体的查询。
                    上下文信息：{context}
                    用户原始查询：{query}
                    请将用户的查询改写为更完整、更具体的查询，使其更容易在文档库中找到相关信息。
                    只返回改写后的查询，不要包含其他解释。"""
        else:
            prompt = f"""你是一个查询重写助手。用户的问题可能不完整或模糊，请将其改写为更完整、更具体的查询。
                    用户原始查询：{query}
                    请将用户的查询改写为更完整、更具体的查询，使其更容易在文档库中找到相关信息。
                    只返回改写后的查询，不要包含其他解释。"""

        # 使用 LLM 生成改写后的查询
        messages = [
            {"role": "user", "content": prompt}
        ]

        rewritten_query = self.llm.chat(messages)

        # 清理输出（移除可能的提示词残留）
        rewritten_query = rewritten_query.strip()
        # 如果输出包含"改写后的查询："等前缀，提取实际查询
        if "：" in rewritten_query or ":" in rewritten_query:
            parts = re.split(r'[：:]', rewritten_query, 1)
            if len(parts) > 1:
                rewritten_query = parts[-1].strip()

        return rewritten_query

    # 核心方法二 混合检索 (Hybrid Search)
    def hyde_search(
            self,
            query: str,
            n_results: int = 10,
            where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        HyDE (Hypothetical Document Embeddings)：让 LLM 先生成一个假设性答案，然后用这个答案去搜索
        Args:
            query: 用户查询
            n_results: 返回结果数量
            where: 元数据过滤条件
        Returns:
            检索结果字典，包含 ids, distances, metadatas, documents
        """
        # 第一步：让 LLM 生成假设性答案
        prompt = f"""基于以下问题，请生成一个假设性的答案。这个答案应该包含问题可能涉及的关键信息和概念。
                问题：{query}
                请生成一个假设性的答案，这个答案应该：
                1. 包含问题的关键信息
                2. 使用相关的专业术语
                3. 结构清晰，便于检索
                只返回假设性答案，不要包含其他解释。"""

        messages = [
            {"role": "user", "content": prompt}
        ]

        hypothetical_answer = self.llm.chat(messages)
        hypothetical_answer = hypothetical_answer.strip()

        # 清理输出
        if "假设性答案" in hypothetical_answer or "答案：" in hypothetical_answer:
            # 尝试提取实际答案部分
            lines = hypothetical_answer.split('\n')
            hypothetical_answer = '\n'.join([line for line in lines if not line.strip().startswith('假设')])
            hypothetical_answer = hypothetical_answer.replace('答案：', '').replace('答案:', '').strip()

        # 第二步：将假设性答案向量化
        hypothetical_embedding = self.embedding_util.embed_query(hypothetical_answer)

        # 第三步：使用假设性答案的向量进行检索
        results = self.chroma_dao.query(
            query_embedding=hypothetical_embedding.tolist(),
            n_results=n_results,
            where=where
        )

        return results

    def _build_bm25_index(self, documents: List[str], doc_ids: List[str]):
        """
        构建 BM25 索引
        Args:
            documents: 文档列表
            doc_ids: 文档 ID 列表
        """
        try:
            from rank_bm25 import BM25Okapi
        except ImportError:
            raise ImportError(
                "rank-bm25 库未安装。请运行: pip install rank-bm25"
            )

        # 分词（简单的中英文分词）
        tokenized_docs = []
        for doc in documents:
            # 简单分词：按空格、标点符号分割
            tokens = re.findall(r'\b\w+\b', doc.lower())
            tokenized_docs.append(tokens)

        # 构建 BM25 索引
        self._bm25_index = BM25Okapi(tokenized_docs)
        self._bm25_documents = documents
        self._bm25_doc_ids = doc_ids

    # 重排序 (Reranking)检索
    def _bm25_search(
            self,
            query: str,
            n_results: int = 10
    ) -> List[Tuple[str, float]]:
        """
        BM25 关键词检索
        Args:
            query: 查询文本
            n_results: 返回结果数量
        Returns:
            (doc_id, score) 元组列表，按分数降序排列
        """
        if self._bm25_index is None:
            # 需要先构建索引
            # 从 ChromaDocumentDAO 获取所有文档
            all_docs = self.chroma_dao.get_all_documents()
            if not all_docs["ids"]:
                return []
            documents = []
            doc_ids = []
            for i, doc_id in enumerate(all_docs["ids"]):
                doc_text = all_docs["documents"][i] if all_docs["documents"] else ""
                if doc_text:
                    documents.append(doc_text)
                    doc_ids.append(doc_id)
            if not documents:
                return []
            self._build_bm25_index(documents, doc_ids)
        # 查询分词
        query_tokens = re.findall(r'\b\w+\b', query.lower())
        # BM25 检索
        scores = self._bm25_index.get_scores(query_tokens)
        # 获取 Top-K 结果
        top_indices = np.argsort(scores)[::-1][:n_results]
        results = []
        for idx in top_indices:
            if scores[idx] > 0:  # 只返回有分数的结果
                results.append((self._bm25_doc_ids[idx], scores[idx]))
        return results

    def reciprocal_rank_fusion(
            self,
            vector_results: Dict[str, Any],
            bm25_results: List[Tuple[str, float]],
            k: int = 60
    ) -> List[Tuple[str, float]]:
        """
        Reciprocal Rank Fusion (RRF) 算法融合向量检索和 BM25 检索结果
        
        Args:
            vector_results: 向量检索结果（ChromaDocumentDAO.query 返回的格式）
            bm25_results: BM25 检索结果，格式为 [(doc_id, score), ...]
            k: RRF 参数，通常为 60
            
        Returns:
            融合后的结果列表，格式为 [(doc_id, rrf_score), ...]，按分数降序排列
        """
        # 构建文档 ID 到排名的映射
        doc_ranks = defaultdict(lambda: {"vector": 0, "bm25": 0})
        # 处理向量检索结果
        if vector_results.get("ids") and len(vector_results["ids"]) > 0:
            vector_ids = vector_results["ids"][0]
            for rank, doc_id in enumerate(vector_ids, start=1):
                doc_ranks[doc_id]["vector"] = rank
        # 处理 BM25 检索结果
        for rank, (doc_id, _) in enumerate(bm25_results, start=1):
            doc_ranks[doc_id]["bm25"] = rank
        # 计算 RRF 分数
        rrf_scores = []
        for doc_id, ranks in doc_ranks.items():
            rrf_score = 0.0
            # 向量检索的 RRF 贡献
            if ranks["vector"] > 0:
                rrf_score += 1.0 / (k + ranks["vector"])
            # BM25 检索的 RRF 贡献
            if ranks["bm25"] > 0:
                rrf_score += 1.0 / (k + ranks["bm25"])
            if rrf_score > 0:
                rrf_scores.append((doc_id, rrf_score))
        # 按分数降序排序
        rrf_scores.sort(key=lambda x: x[1], reverse=True)
        return rrf_scores

    def hybrid_search(
            self,
            query: str,
            n_results: int = 10,
            where: Optional[Dict[str, Any]] = None,
            vector_weight: float = 0.5,
            bm25_weight: float = 0.5
    ) -> Dict[str, Any]:
        """
        混合检索：结合 BM25 关键词检索和向量检索
        
        Args:
            query: 查询文本
            n_results: 返回结果数量
            where: 元数据过滤条件
            vector_weight: 向量检索权重（0-1）
            bm25_weight: BM25 检索权重（0-1），会自动归一化
            
        Returns:
            融合后的检索结果，格式与 ChromaDocumentDAO.query 返回的格式一致
        """
        # 归一化权重
        total_weight = vector_weight + bm25_weight
        if total_weight > 0:
            vector_weight /= total_weight
            bm25_weight /= total_weight
        # 第一步：向量检索
        query_embedding = self.embedding_util.embed_query(query)
        vector_results = self.chroma_dao.query(
            query_embedding=query_embedding.tolist(),
            n_results=n_results * 2,  # 获取更多候选，用于融合
            where=where
        )
        # 第二步：BM25 检索
        bm25_results = self._bm25_search(query, n_results=n_results * 2)
        # 第三步：使用 RRF 融合结果
        rrf_results = self.reciprocal_rank_fusion(vector_results, bm25_results)
        # 第四步：获取 Top-K 结果并构建返回格式
        top_rrf = rrf_results[:n_results]

        if not top_rrf:
            return {
                "ids": [[]],
                "distances": [[]],
                "metadatas": [[]],
                "documents": [[]]
            }

        # 从 ChromaDocumentDAO 获取这些文档的详细信息
        top_doc_ids = [doc_id for doc_id, _ in top_rrf]

        # 构建返回结果
        result_ids = []
        result_distances = []
        result_metadatas = []
        result_documents = []

        # 从向量检索结果中获取元数据和文档内容
        vector_id_to_metadata = {}
        vector_id_to_document = {}
        vector_id_to_distance = {}

        if vector_results.get("ids") and len(vector_results["ids"]) > 0:
            vector_ids = vector_results["ids"][0]
            for i, doc_id in enumerate(vector_ids):
                vector_id_to_metadata[doc_id] = vector_results["metadatas"][0][i] if vector_results.get(
                    "metadatas") else {}
                vector_id_to_document[doc_id] = vector_results["documents"][0][i] if vector_results.get(
                    "documents") else ""
                vector_id_to_distance[doc_id] = vector_results["distances"][0][i] if vector_results.get(
                    "distances") else 1.0

        # 从 ChromaDocumentDAO 获取缺失的信息
        all_docs = self.chroma_dao.get_all_documents()
        all_id_to_metadata = {}
        all_id_to_document = {}

        if all_docs.get("ids"):
            for i, doc_id in enumerate(all_docs["ids"]):
                all_id_to_metadata[doc_id] = all_docs["metadatas"][i] if all_docs.get("metadatas") else {}
                all_id_to_document[doc_id] = all_docs["documents"][i] if all_docs.get("documents") else ""

        # 构建最终结果
        for doc_id, rrf_score in top_rrf:
            result_ids.append(doc_id)
            # 使用 RRF 分数作为距离（分数越高，距离越小）
            result_distances.append(1.0 - rrf_score)
            result_metadatas.append(
                vector_id_to_metadata.get(doc_id) or all_id_to_metadata.get(doc_id, {})
            )
            result_documents.append(
                vector_id_to_document.get(doc_id) or all_id_to_document.get(doc_id, "")
            )

        return {
            "ids": [result_ids],
            "distances": [result_distances],
            "metadatas": [result_metadatas],
            "documents": [result_documents]
        }

    def search(
            self,
            query: str,
            method: str = "hybrid",
            use_query_rewrite: bool = False,
            use_hyde: bool = False,
            n_results: int = 10,
            where: Optional[Dict[str, Any]] = None,
            **kwargs
    ) -> Dict[str, Any]:
        """
        统一的检索接口
        
        Args:
            query: 查询文本
            method: 检索方法，"vector"（向量检索）、"bm25"（关键词检索）、"hybrid"（混合检索）
            use_query_rewrite: 是否使用查询重写
            use_hyde: 是否使用 HyDE 方法
            n_results: 返回结果数量
            where: 元数据过滤条件
            **kwargs: 其他参数（如 vector_weight, bm25_weight 等）
            
        Returns:
            检索结果字典
        """
        # 查询重写（可选）
        if use_query_rewrite:
            query = self.query_rewrite(query)
            print(f"[Query Rewrite] 改写后的查询: {query}")

        # HyDE 方法（如果启用，会覆盖其他检索方法）
        if use_hyde:
            return self.hyde_search(query, n_results=n_results, where=where)

        # 根据方法选择检索策略
        if method == "vector":
            # 纯向量检索
            query_embedding = self.embedding_util.embed_query(query)
            return self.chroma_dao.query(
                query_embedding=query_embedding.tolist(),
                n_results=n_results,
                where=where
            )
        elif method == "bm25":
            # 纯 BM25 检索
            bm25_results = self._bm25_search(query, n_results=n_results)

            # 转换为标准格式
            if not bm25_results:
                return {
                    "ids": [[]],
                    "distances": [[]],
                    "metadatas": [[]],
                    "documents": [[]]
                }

            # 从 ChromaDocumentDAO 获取文档详情
            doc_ids = [doc_id for doc_id, _ in bm25_results]
            all_docs = self.chroma_dao.get_all_documents()

            result_ids = []
            result_distances = []
            result_metadatas = []
            result_documents = []

            all_id_to_metadata = {}
            all_id_to_document = {}
            if all_docs.get("ids"):
                for i, doc_id in enumerate(all_docs["ids"]):
                    all_id_to_metadata[doc_id] = all_docs["metadatas"][i] if all_docs.get("metadatas") else {}
                    all_id_to_document[doc_id] = all_docs["documents"][i] if all_docs.get("documents") else ""

            for doc_id, score in bm25_results:
                result_ids.append(doc_id)
                result_distances.append(1.0 / (1.0 + score))  # 将 BM25 分数转换为距离
                result_metadatas.append(all_id_to_metadata.get(doc_id, {}))
                result_documents.append(all_id_to_document.get(doc_id, ""))

            return {
                "ids": [result_ids],
                "distances": [result_distances],
                "metadatas": [result_metadatas],
                "documents": [result_documents]
            }
        else:  # hybrid
            # 混合检索
            return self.hybrid_search(
                query,
                n_results=n_results,
                where=where,
                vector_weight=kwargs.get("vector_weight", 0.5),
                bm25_weight=kwargs.get("bm25_weight", 0.5)
            )


if __name__ == '__main__':
    # 示例用法
    from util.McpConfigUtil import ConfigUtil
    from util.McpConstant import Constant

    # 初始化组件
    model_path = ConfigUtil.load_model_path_from_config(Constant.CONFIG_PATH)
    chroma_save_path = ConfigUtil.load_chroma_save_path_from_config(Constant.CONFIG_PATH)

    llm = AskLLM(model_path)
    embedding_util = EmbeddingUtil(model_path)
    schema = "test_schema"
    chroma_document_dao = ChromaDocumentDAO(
        collection_name=schema,
        persist_directory=chroma_save_path
    )

    # 创建检索系统
    retrieval_system = RetrievalSystem(llm, embedding_util, chroma_dao)

    # 测试查询重写
    original_query = "它怎么用？"
    # rewritten = retrieval_system.query_rewrite(original_query)
    # print(f"原始查询: {original_query}")
    # print(f"改写后: {rewritten}\n")
    #
    # # 测试 HyDE
    # print("=" * 50)
    # print("HyDE 检索:")
    # hyde_results = retrieval_system.hyde_search("Python 如何读取文件？", n_results=5)
    # print(f"找到 {len(hyde_results['ids'][0])} 个结果\n")
    #
    # # 测试混合检索
    # print("=" * 50)
    # print("混合检索:")
    # hybrid_results = retrieval_system.hybrid_search(
    #     "Python 文件操作",
    #     n_results=5
    # )
    # print(f"找到 {len(hybrid_results['ids'][0])} 个结果")

    # 测试统一接口
    print("=" * 50)
    print("统一检索接口（带查询重写）:")
    # results = retrieval_system.search(
    #     query="它怎么用？",
    #     method="hybrid",
    #     use_query_rewrite=True,
    #     n_results=5
    # )
    # print(f"找到 {len(results['ids'][0])} 个结果")
    # print(f"结果{results}")

