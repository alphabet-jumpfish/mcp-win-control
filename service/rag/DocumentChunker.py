"""
RAG文档分块处理工具
提供四种文档分块方法：
1. 固定大小分块
2. 语义分块
3. 递归分块
4. 结构分块
"""
from typing import List, Optional
import re


try:
    from langchain_text_splitters import (
        CharacterTextSplitter,
        RecursiveCharacterTextSplitter,
        MarkdownHeaderTextSplitter
    )
except ImportError:
    # 兼容不同版本的langchain
    try:
        from langchain_text_splitters import (
            CharacterTextSplitter,
            RecursiveCharacterTextSplitter,
        )
        from langchain.text_splitter import MarkdownHeaderTextSplitter
    except ImportError:
        raise ImportError("请安装langchain: pip install langchain langchain-core")

from langchain_huggingface import HuggingFaceEmbeddings
import numpy as np
import torch


class DocumentChunker:

    """文档分块处理类"""
    
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
    
    def fixed_size_chunk(
        self,
        text: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separator: str = "\n\n"
    ) -> List[str]:
        """
        方法1: 文档固定大小分块函数
        
        将文档按照固定大小进行分块，适用于大多数场景
        
        Args:
            text: 要分块的文本内容
            chunk_size: 每个分块的大小（字符数）
            chunk_overlap: 分块之间的重叠字符数，用于保持上下文连续性
            separator: 分块时的分隔符，默认为双换行符
            
        Returns:
            分块后的文本列表
            
        Example:
            # >>> chunker = DocumentChunker()
            # >>> chunks = chunker.fixed_size_chunk("长文本内容...", chunk_size=500, chunk_overlap=50)
        """
        text_splitter = CharacterTextSplitter(
            separator=separator,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
        chunks = text_splitter.split_text(text)
        return chunks
    
    def semantic_chunk(
        self,
        text: str,
        chunk_size: int = 1000,
        similarity_threshold: float = 0.7,
        min_chunk_size: int = 100
    ) -> List[str]:
        """
        方法2: 内容语义分块
        
        基于语义相似度进行分块，确保每个分块内的内容语义相关
        
        Args:
            text: 要分块的文本内容
            chunk_size: 目标分块大小（字符数）
            similarity_threshold: 语义相似度阈值，低于此值的分块会被拆分
            min_chunk_size: 最小分块大小，避免分块过小
            
        Returns:
            分块后的文本列表
            
        Example:
            # >>> chunker = DocumentChunker(embedding_model_path="path/to/model")
            # >>> chunks = chunker.semantic_chunk("长文本内容...", chunk_size=500)
        """
        if self.embeddings is None:
            raise ValueError("语义分块需要初始化嵌入模型，请在构造函数中提供 embedding_model_path")
        
        # 首先使用固定大小进行初步分块
        initial_chunks = self.fixed_size_chunk(text, chunk_size=chunk_size, chunk_overlap=0)
        
        # 对每个分块进行语义分析，进一步优化
        optimized_chunks = []
        for chunk in initial_chunks:
            if len(chunk) < min_chunk_size:
                optimized_chunks.append(chunk)
                continue
            
            # 将分块进一步细分为句子
            sentences = re.split(r'[.!?。！？]\s+', chunk)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            if len(sentences) <= 1:
                optimized_chunks.append(chunk)
                continue
            
            # 计算句子之间的语义相似度
            current_chunk = sentences[0]
            for i in range(1, len(sentences)):
                # 获取当前分块和下一个句子的嵌入
                current_emb = self.embeddings.embed_query(current_chunk)
                next_emb = self.embeddings.embed_query(sentences[i])
                
                # 计算余弦相似度
                similarity = np.dot(current_emb, next_emb) / (
                    np.linalg.norm(current_emb) * np.linalg.norm(next_emb)
                )
                
                if similarity >= similarity_threshold:
                    # 相似度高，合并到当前分块
                    current_chunk += " " + sentences[i]
                else:
                    # 相似度低，保存当前分块，开始新分块
                    optimized_chunks.append(current_chunk)
                    current_chunk = sentences[i]
            
            # 添加最后一个分块
            if current_chunk:
                optimized_chunks.append(current_chunk)
        
        return optimized_chunks
    
    def recursive_chunk(
        self,
        text: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: Optional[List[str]] = None
    ) -> List[str]:
        """
        方法3: 文档递归分块
        
        递归地尝试不同的分隔符进行分块，优先使用较大的语义单元
        
        Args:
            text: 要分块的文本内容
            chunk_size: 每个分块的目标大小（字符数）
            chunk_overlap: 分块之间的重叠字符数
            separators: 分隔符优先级列表，默认按段落、句子、单词、字符顺序
            
        Returns:
            分块后的文本列表
            
        Example:
            # >>> chunker = DocumentChunker()
            # >>> chunks = chunker.recursive_chunk("长文本内容...", chunk_size=500)
        """
        if separators is None:
            # 默认分隔符优先级：段落 > 句子 > 单词 > 字符
            separators = ["\n\n", "\n", ". ", " ", ""]
        
        text_splitter = RecursiveCharacterTextSplitter(
            separators=separators,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
        chunks = text_splitter.split_text(text)
        return chunks
    
    def structure_chunk(
        self,
        text: str,
        structure_type: str = "markdown",
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> List[str]:
        """
        方法4: 文档结构分块
        
        基于文档结构（如Markdown标题、段落等）进行分块
        
        Args:
            text: 要分块的文本内容
            structure_type: 文档结构类型，支持 "markdown", "paragraph"
            chunk_size: 每个分块的目标大小（字符数）
            chunk_overlap: 分块之间的重叠字符数
            
        Returns:
            分块后的文本列表
            
        Example:
            # >>> chunker = DocumentChunker()
            # >>> chunks = chunker.structure_chunk("# 标题\n内容...", structure_type="markdown")
        """
        if structure_type == "markdown":
            # 使用Markdown结构分块
            headers_to_split_on = [
                ("#", "标题1"),
                ("##", "标题2"),
                ("###", "标题3"),
                ("####", "标题4"),
            ]
            markdown_splitter = MarkdownHeaderTextSplitter(
                headers_to_split_on=headers_to_split_on
            )
            chunks = markdown_splitter.split_text(text)
            # 将Document对象转换为字符串列表
            chunk_texts = [chunk.page_content for chunk in chunks]
            
            # 如果分块太大，进一步细分
            final_chunks = []
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
            )
            for chunk_text in chunk_texts:
                if len(chunk_text) > chunk_size:
                    sub_chunks = text_splitter.split_text(chunk_text)
                    final_chunks.extend(sub_chunks)
                else:
                    final_chunks.append(chunk_text)
            
            return final_chunks
        
        elif structure_type == "paragraph":
            # 基于段落分块
            paragraphs = re.split(r'\n\s*\n', text)
            paragraphs = [p.strip() for p in paragraphs if p.strip()]
            
            # 合并小段落，拆分大段落
            final_chunks = []
            current_chunk = ""
            
            for para in paragraphs:
                if len(current_chunk) + len(para) + 2 <= chunk_size:
                    # 可以合并
                    current_chunk += "\n\n" + para if current_chunk else para
                else:
                    # 保存当前分块
                    if current_chunk:
                        final_chunks.append(current_chunk)
                    
                    # 如果段落本身太大，需要拆分
                    if len(para) > chunk_size:
                        text_splitter = RecursiveCharacterTextSplitter(
                            chunk_size=chunk_size,
                            chunk_overlap=chunk_overlap,
                            length_function=len,
                        )
                        sub_chunks = text_splitter.split_text(para)
                        final_chunks.extend(sub_chunks)
                        current_chunk = ""
                    else:
                        current_chunk = para
            
            # 添加最后一个分块
            if current_chunk:
                final_chunks.append(current_chunk)
            
            return final_chunks
        
        else:
            raise ValueError(f"不支持的结构类型: {structure_type}，支持的类型: markdown, paragraph")

    def cleanup(self):
        """
        清理 DocumentChunker 资源，释放内存
        """
        print("正在清理 DocumentChunker 资源...")
        try:
            # 清理 embeddings 模型
            if hasattr(self, 'embeddings') and self.embeddings is not None:
                # HuggingFaceEmbeddings 内部使用的是 sentence-transformers
                # 尝试访问内部模型并清理
                if hasattr(self.embeddings, 'client'):
                    # 清理 sentence-transformers 模型
                    if hasattr(self.embeddings.client, 'to'):
                        self.embeddings.client.to('cpu')
                    del self.embeddings.client

                del self.embeddings
                self.embeddings = None
                print("- embeddings 模型已释放")

            # 清空 CUDA 缓存（如果使用了 GPU）
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                print("- CUDA 缓存已清空")

            print("DocumentChunker 资源清理完成")
        except Exception as e:
            print(f"清理 DocumentChunker 资源时出错: {e}")


if __name__ == '__main__':
    # 测试示例
    sample_text = """
    # 第一章 介绍
    这是第一章的内容。RAG（检索增强生成）是一种结合了信息检索和生成模型的技术。
    ## 1.1 背景
    在自然语言处理领域，RAG技术越来越受到关注。
    ## 1.2 目标
    我们的目标是构建一个高效的文档检索和生成系统。
    # 第二章 方法
    本章介绍我们使用的方法和技术。
    ## 2.1 文档分块
    文档分块是RAG系统的关键步骤之一。我们需要将长文档分割成较小的块，以便进行检索和生成。
    """
    chunker = DocumentChunker()
    print("=" * 50)
    print("方法1: 固定大小分块")
    print("=" * 50)
    chunks1 = chunker.fixed_size_chunk(sample_text, chunk_size=200, chunk_overlap=50)
    for i, chunk in enumerate(chunks1, 1):
        print(f"\n分块 {i} (长度: {len(chunk)}):")
        print(chunk[:100] + "..." if len(chunk) > 100 else chunk)
    print("\n" + "=" * 50)
    # print("方法3: 递归分块")
    # print("=" * 50)
    # chunks3 = chunker.recursive_chunk(sample_text, chunk_size=200, chunk_overlap=50)
    # for i, chunk in enumerate(chunks3, 1):
    #     print(f"\n分块 {i} (长度: {len(chunk)}):")
    #     print(chunk[:100] + "..." if len(chunk) > 100 else chunk)
    #
    # print("\n" + "=" * 50)
    # print("方法4: 结构分块 (Markdown)")
    # print("=" * 50)
    # chunks4 = chunker.structure_chunk(sample_text, structure_type="markdown")
    # for i, chunk in enumerate(chunks4, 1):
    #     print(f"\n分块 {i} (长度: {len(chunk)}):")
    #     print(chunk[:100] + "..." if len(chunk) > 100 else chunk)
    #
    # print("\n" + "=" * 50)
    # print("方法4: 结构分块 (段落)")
    # print("=" * 50)
    # chunks4_para = chunker.structure_chunk(sample_text, structure_type="paragraph")
    # for i, chunk in enumerate(chunks4_para, 1):
    #     print(f"\n分块 {i} (长度: {len(chunk)}):")
    #     print(chunk[:100] + "..." if len(chunk) > 100 else chunk)

