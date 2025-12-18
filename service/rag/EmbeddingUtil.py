from langchain_huggingface import HuggingFaceEmbeddings
import numpy as np
import torch
from typing import List, Optional

# 自定义工具
from util.McpConfigUtil import ConfigUtil
from util.McpConstant import Constant


class EmbeddingUtil:

    def infos(func):
        def wrapper(*args, **kwargs):
            print("在原函数之前执行")
            result = func(*args, **kwargs)
            print("在原函数之后执行")
            return result

        return wrapper

    def __init__(self, embedding_model_path: Optional[str] = None):
        """
        初始化文档分块器
        Args:
            embedding_model_path: 用于语义分块的嵌入模型路径（可选）
        """
        self.embedding_model_path = embedding_model_path
        self.embeddings = None
        if embedding_model_path:
            self._init_embeddings(embedding_model_path)

    def _init_embeddings(self, model_path: str):
        """初始化嵌入模型"""
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.embeddings = HuggingFaceEmbeddings(
            model_name=model_path,
            model_kwargs={"device": device},
            encode_kwargs={"normalize_embeddings": True}
        )

    def embed_query(self, query):
        query_embedding = self.embeddings.embed_query(query)
        result = np.array(query_embedding)
        return result

    def embed_querys(self, query_list):
        embedding_list = []
        for query in query_list:
            embdding = self.embed_query(query)
            embedding_list.append(embdding)
        result = np.array(embedding_list)
        return result

    @infos
    def search_similar(self, query, text_list):
        """查找与查询最相似的文本列表，按相似度降序排序"""
        # 生成查询的嵌入
        query_emb = self.embed_query(query)
        embdding_list = self.embed_querys(text_list)
        print(f"向量A：{query_emb}")
        print(f"向量B：{embdding_list}")
        # 计算余弦相似度
        similarities = np.dot(embdding_list, query_emb)
        # 按相似度排序 np.argsort 返回索引
        sorted_indices = np.argsort(similarities)[::-1]  # 降序排序
        # 返回排序结果
        sorted_texts = [text_list[i] for i in sorted_indices]
        sorted_scores = similarities[sorted_indices]
        return sorted_texts, sorted_scores


if __name__ == '__main__':
    model_path = ConfigUtil.load_model_path_from_config(Constant.CONFIG_PATH)
    embedding = EmbeddingUtil(model_path)
    print("开始流程")
    # 查询实例
    informations = ["手机的低于范围是哪里", "我在什么情况下可以免费更换手机", "手机的保质期是多久?"]
    query = "手机保修多久"
    sorted_text, sorted_scores = embedding.search_similar(query, informations)
    print("排序结果: ")
    for text, score in zip(sorted_text, sorted_scores):
        print(f"相似度{score:.4f}:{text}")
