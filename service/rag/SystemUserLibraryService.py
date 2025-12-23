# 数据层
from datetime import datetime
from typing import List

from dao.DatasetType import DatasetType
from dao.sqlite.rag.SystemUserLibraryMapper import SystemUserLibraryMapper
from dao.chroma.ChromaDocumentDAO import ChromaDocumentDAO
from dao.chroma.ChromaDocumentDAO import Document
from dao.memory.UserMemory import user_memory

# rag模块
from service.rag.DocumentChunker import DocumentChunker
from service.rag.EmbeddingUtil import EmbeddingUtil

# 常量
from util.McpConfigUtil import ConfigUtil
from util.McpConstant import Constant


class SystemUserLibraryService:
    """
    知识库服务
    """

    def __init__(self, model_path):
        self.system_user_library_mapper = SystemUserLibraryMapper()
        # 初始化组件
        chroma_save_path = ConfigUtil.load_chroma_save_path_from_config(Constant.CONFIG_PATH)
        schema = "schema"
        self.chroma_document_dao = ChromaDocumentDAO(
            collection_name=schema,
            persist_directory=chroma_save_path
        )
        self.model_path = model_path
        # chunk分块
        self.chunker = DocumentChunker(self.model_path)
        self.embedding_util = EmbeddingUtil(self.model_path)

    # 新增知识库
    def create_library(self, title: str, text: str):
        # chunk
        # 预处理
        # 存入向量数据库
        chunks = self.chunk_text(text)
        print(f"chunks结果:{chunks}")
        documents = self.batch_construct_document(title, chunks)
        print(f"documents结果:{chunks}")
        doc_ids = []
        if documents:
            for document in documents:
                doc_id = self.chroma_document_dao.add_document_dict(document)
                doc_ids.append(doc_id)

        user_id = None
        current_user = user_memory.get_current_user()
        if current_user:
            user_id = current_user.get("id")

        self.system_user_library_mapper.insert(
            user_id=user_id,
            name=title,
            doc_ids=str(doc_ids),
            content=text,
            path=""
        )

    # 删除知识库
    def delete_by_id(self, id):
        result = self.system_user_library_mapper.query_by_id(id)
        print(f"查询知识库结果:{result}")
        doc_ids = []
        if result:
            doc_ids = result.get("doc_ids")
        if doc_ids:
            for doc_id in doc_ids:
                self.chroma_document_dao.delete_document(doc_id)
        # sqlite中数据删除
        self.system_user_library_mapper.delete(id)

    # 批量构建文档向量结构
    def batch_construct_document(self, title, document_texts) -> List[Document]:
        results = []
        if document_texts:
            for document in document_texts:
                np_embedding = self.embedding_util.embed_query(document).tolist()
                result: Document = {
                    "title": title,
                    "url": "",
                    "timestamp": datetime.now(),
                    "category": "技术文档",
                    "embedding": np_embedding,
                    "document_text": document,
                    "dataset_type": DatasetType.CHROMA.value
                }
                results.append(result)
        return results

    # 获取用户所有知识库
    def get_user_libraries(self, user_id: int):
        """
        获取用户的所有知识库列表（按更新时间倒序）

        Args:
            user_id: 用户ID

        Returns:
            知识库列表
        """
        return self.system_user_library_mapper.query_by_user_id(user_id)

    # 获取知识库详情
    def get_library_detail(self, library_id: int):
        """
        获取知识库详情

        Args:
            library_id: 知识库ID

        Returns:
            知识库详情字典，如果不存在返回 None
        """
        return self.system_user_library_mapper.query_by_id(library_id)

    # 文档分块
    def chunk_text(self, text):
        chunks = self.chunker.semantic_chunk(text)
        return chunks

    def cleanup(self):
        """
        清理知识库服务资源，释放内存
        """
        print("正在清理 SystemUserLibraryService 资源...")
        try:
            # 清理 embedding_util
            if hasattr(self, 'embedding_util') and self.embedding_util is not None:
                if hasattr(self.embedding_util, 'cleanup'):
                    self.embedding_util.cleanup()
                del self.embedding_util
                self.embedding_util = None
                print("- embedding_util 已释放")

            # 清理 chunker
            if hasattr(self, 'chunker') and self.chunker is not None:
                if hasattr(self.chunker, 'cleanup'):
                    self.chunker.cleanup()
                del self.chunker
                self.chunker = None
                print("- chunker 已释放")

            # 清理 chroma_document_dao
            if hasattr(self, 'chroma_document_dao') and self.chroma_document_dao is not None:
                del self.chroma_document_dao
                self.chroma_document_dao = None
                print("- chroma_document_dao 已释放")

            print("SystemUserLibraryService 资源清理完成")
        except Exception as e:
            print(f"清理 SystemUserLibraryService 资源时出错: {e}")
