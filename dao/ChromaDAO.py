import chromadb
from chromadb.config import Settings
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import os

from dao.DatasetType import DatasetType
from service.rag.EmbeddingUtil import EmbeddingUtil
from util.McpConfigUtil import ConfigUtil
from util.McpConstant import Constant


class ChromaDAO:
    """
    使用 Chroma 框架存储向量数据的 DAO 类
    存储字段：title, url, timestamp, category 和向量维度
    """

    def __init__(
            self,
            collection_name: str = "documents",
            persist_directory: Optional[str] = None,
            embedding_function=None
    ):
        """
        初始化 ChromaDAO
        
        Args:
            collection_name: 集合名称，默认为 "documents"
            persist_directory: 持久化目录路径，如果为 None 则使用内存模式
            embedding_function: 可选的嵌入函数，如果提供则 Chroma 会自动生成向量
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory

        # 初始化 Chroma 客户端
        if persist_directory:
            # 持久化模式：数据会保存到磁盘
            os.makedirs(persist_directory, exist_ok=True)
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )
        else:
            # 内存模式：数据仅在运行时存在
            self.client = chromadb.Client(
                settings=Settings(anonymized_telemetry=False)
            )

        # 获取或创建集合
        if embedding_function:
            # 如果提供了嵌入函数，让 Chroma 自动处理向量化
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=embedding_function,
                metadata={"hnsw:space": "cosine"}  # 使用余弦相似度
            )
        else:
            # 手动管理向量
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )

    def add_document(
            self,
            title: str,
            url: str,
            timestamp: Optional[datetime] = None,
            category: Optional[str] = None,
            embedding: Optional[List[float]] = None,
            document_text: Optional[str] = None,
            metadata: Optional[Dict[str, Any]] = None,
            dataset_type: Optional[str] = None
    ) -> str:
        """
        添加文档到向量数据库
        
        Args:
            title: 文档标题
            url: 文档 URL
            timestamp: 时间戳，如果为 None 则使用当前时间
            category: 文档分类
            embedding: 向量数据（如果 embedding_function 未设置，则必须提供）
            document_text: 文档文本内容（用于检索，可选）
            metadata: 额外的元数据（可选）
            dataset_type: "document",

        Returns:
            文档的唯一 ID
        """
        doc_id = str(uuid.uuid4())

        # 准备元数据
        doc_metadata = {
            "title": title,
            "url": url,
            "category": category or "",
            "timestamp": timestamp.isoformat() if timestamp else datetime.now().isoformat(),
            "dataset_type": dataset_type or "",
        }

        # 合并额外的元数据
        if metadata:
            doc_metadata.update(metadata)

        # 准备数据
        documents = [document_text] if document_text else None
        embeddings = [embedding] if embedding else None
        metadatas = [doc_metadata]
        ids = [doc_id]

        # 添加到集合
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

        return doc_id

    def add_documents_batch(
            self,
            documents: List[Dict[str, Any]]
    ) -> List[str]:
        """
        批量添加文档
        
        Args:
            documents: 文档列表，每个文档包含 title, url, timestamp, category, embedding, document_text 等字段
            
        Returns:
            文档 ID 列表
        """
        ids = []
        embeddings_list = []
        documents_list = []
        metadatas_list = []

        for doc in documents:
            doc_id = str(uuid.uuid4())
            ids.append(doc_id)

            # 准备元数据
            metadata = {
                "title": doc.get("title", ""),
                "url": doc.get("url", ""),
                "category": doc.get("category", ""),
                "timestamp": doc.get("timestamp", datetime.now()).isoformat() if isinstance(doc.get("timestamp"),
                                                                                            datetime) else doc.get(
                    "timestamp", datetime.now().isoformat())
            }

            # 合并额外元数据
            if "metadata" in doc:
                metadata.update(doc["metadata"])

            metadatas_list.append(metadata)

            # 添加向量和文档文本
            if "embedding" in doc:
                embeddings_list.append(doc["embedding"])
            if "document_text" in doc:
                documents_list.append(doc["document_text"])

        # 批量添加
        add_kwargs = {
            "ids": ids,
            "metadatas": metadatas_list
        }

        if embeddings_list:
            add_kwargs["embeddings"] = embeddings_list
        if documents_list:
            add_kwargs["documents"] = documents_list

        self.collection.add(**add_kwargs)

        return ids

    def query(
            self,
            query_embedding: Optional[List[float]] = None,
            query_text: Optional[str] = None,
            n_results: int = 10,
            where: Optional[Dict[str, Any]] = None,
            where_document: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        查询相似文档
        
        Args:
            query_embedding: 查询向量（如果 embedding_function 未设置，则必须提供）
            query_text: 查询文本（如果设置了 embedding_function，可以使用文本查询）
            n_results: 返回结果数量
            where: 元数据过滤条件，例如 {"category": "技术文档"}
            where_document: 文档内容过滤条件
            
        Returns:
            包含 ids, distances, metadatas, documents 的字典
        """
        query_kwargs = {
            "n_results": n_results
        }

        if query_embedding:
            query_kwargs["query_embeddings"] = [query_embedding]
        elif query_text:
            query_kwargs["query_texts"] = [query_text]
        else:
            raise ValueError("必须提供 query_embedding 或 query_text 之一")

        if where:
            query_kwargs["where"] = where
        if where_document:
            query_kwargs["where_document"] = where_document

        results = self.collection.query(**query_kwargs)

        return results

    def get_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        根据 ID 获取文档
        
        Args:
            doc_id: 文档 ID
            
        Returns:
            文档信息字典，如果不存在则返回 None
        """
        results = self.collection.get(ids=[doc_id])

        if not results["ids"]:
            return None

        return {
            "id": results["ids"][0],
            "metadata": results["metadatas"][0] if results["metadatas"] else {},
            "document": results["documents"][0] if results["documents"] else None,
            "embedding": results["embeddings"][0] if results["embeddings"] else None
        }

    def update_document(
            self,
            doc_id: str,
            title: Optional[str] = None,
            url: Optional[str] = None,
            timestamp: Optional[datetime] = None,
            category: Optional[str] = None,
            embedding: Optional[List[float]] = None,
            document_text: Optional[str] = None,
            metadata: Optional[Dict[str, Any]] = None,
            dataset_type: Optional[str] = None
    ) -> bool:
        """
        更新文档
        
        Args:
            doc_id: 文档 ID
            title: 新的标题（可选）
            url: 新的 URL（可选）
            timestamp: 新的时间戳（可选）
            category: 新的分类（可选）
            embedding: 新的向量（可选）
            document_text: 新的文档文本（可选）
            metadata: 新的元数据（可选）
            
        Returns:
            更新是否成功
        """
        # 先获取现有文档
        existing = self.get_by_id(doc_id)
        if not existing:
            return False

        # 合并元数据
        existing_metadata = existing.get("metadata", {})
        if title is not None:
            existing_metadata["title"] = title
        if url is not None:
            existing_metadata["url"] = url
        if timestamp is not None:
            existing_metadata["timestamp"] = timestamp.isoformat()
        if category is not None:
            existing_metadata["category"] = category
        if dataset_type is not None:
            existing_metadata["dataset_type"] = dataset_type
        if metadata:
            existing_metadata.update(metadata)

        # 准备更新数据
        update_kwargs = {
            "ids": [doc_id],
            "metadatas": [existing_metadata]
        }

        if embedding is not None:
            update_kwargs["embeddings"] = [embedding]
        if document_text is not None:
            update_kwargs["documents"] = [document_text]

        self.collection.update(**update_kwargs)

        return True

    def delete_document(self, doc_id: str) -> bool:
        """
        删除文档
        
        Args:
            doc_id: 文档 ID
            
        Returns:
            删除是否成功
        """
        try:
            self.collection.delete(ids=[doc_id])
            return True
        except Exception:
            return False

    def delete_documents_by_filter(
            self,
            where: Optional[Dict[str, Any]] = None,
            where_document: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        根据过滤条件批量删除文档
        
        Args:
            where: 元数据过滤条件
            where_document: 文档内容过滤条件
            
        Returns:
            删除的文档数量
        """
        # 先查询符合条件的文档
        results = self.query(
            query_embedding=[0.0] * 768,  # 临时向量，仅用于查询
            n_results=10000,  # 获取所有符合条件的文档
            where=where,
            where_document=where_document
        )

        if not results["ids"]:
            return 0

        # 删除这些文档
        self.collection.delete(ids=results["ids"])

        return len(results["ids"])

    def count(self, where: Optional[Dict[str, Any]] = None) -> int:
        """
        统计文档数量
        
        Args:
            where: 元数据过滤条件
            
        Returns:
            文档数量
        """
        if where:
            results = self.collection.get(where=where)
        else:
            results = self.collection.get()

        return len(results["ids"])

    def get_all_documents(
            self,
            limit: Optional[int] = None,
            offset: Optional[int] = None,
            where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        获取所有文档（分页支持）
        
        Args:
            limit: 返回数量限制
            offset: 偏移量
            where: 元数据过滤条件
            
        Returns:
            包含 ids, metadatas, documents, embeddings 的字典
        """
        get_kwargs = {}
        if where:
            get_kwargs["where"] = where
        if limit:
            get_kwargs["limit"] = limit
        if offset:
            get_kwargs["offset"] = offset

        return self.collection.get(**get_kwargs)

    def clear_collection(self):
        """清空整个集合"""
        self.client.delete_collection(name=self.collection_name)
        # 重新创建集合
        if hasattr(self, 'collection') and hasattr(self.collection, 'embedding_function'):
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self.collection.embedding_function,
                metadata={"hnsw:space": "cosine"}
            )
        else:
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )


if __name__ == '__main__':
    # 示例用法
    # import numpy as np
    #
    # 第一步 初始化 DAO（使用持久化模式）
    schema = "test_schema"
    chroma_save_path = ConfigUtil.load_chroma_save_path_from_config(Constant.CONFIG_PATH)
    dao = ChromaDAO(
        collection_name=schema,
        persist_directory=chroma_save_path
    )
    # # 第二步 向量化
    model_path = ConfigUtil.load_model_path_from_config(Constant.CONFIG_PATH)
    embedding_util = EmbeddingUtil(model_path)
    # #
    # # # 添加文档（需要手动提供向量）
    # # 通过 embedding 进行向量化
    title = "测试文档1"
    document_text = "这是一个测试文档的内容"
    embedding_dataset = embedding_util.embed_query(document_text)
    print(f"向量数据: {embedding_dataset}")
    print(f"向量列表数据: {embedding_dataset.tolist()}")
    #
    #
    # doc_id = dao.add_document(
    #     title=title,
    #     url="",
    #     timestamp=datetime.now(),
    #     category="技术文档",
    #     embedding=embedding_dataset.tolist(),
    #     document_text=document_text,
    #     dataset_type=DatasetType.CHROMA.value
    # )
    # #
    # print(f"添加文档成功，ID: {doc_id}")

    #
    # # 查询相似文档
    # query_embedding = np.random.rand(embedding_dim).tolist()
    results = dao.query(
        query_embedding=embedding_dataset.tolist(),
        n_results=5,
        where={"category": "技术文档"}
    )

    print(f"查询结果数量: {len(results['ids'][0])}")
    # for i, doc_id in enumerate(results['ids'][0]):
    #     print(f"文档 {i+1}: {results['metadatas'][0][i]}")
    #     print(f"  距离: {results['distances'][0][i]}")
    #
    # # 统计文档数量
    # count = dao.count(where={"category": "技术文档"})
    # print(f"技术文档总数: {count}")
