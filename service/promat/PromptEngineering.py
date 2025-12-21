"""
提示词工程模块
实现 RAG 系统中的提示词构建功能：
1. 角色设定
2. 边界控制（减少幻觉）
3. 引用标注
"""

from typing import List, Dict, Any, Optional
import re


class PromptEngineering:
    """
    提示词工程类
    用于构建高质量的 RAG 提示词
    """

    def __init__(
        self,
        role: str = "专业的AI助手",
        enable_boundary_control: bool = True,
        enable_citation: bool = True,
        citation_format: str = "[Source {index}]"
    ):
        """
        初始化提示词工程类
        
        Args:
            role: 角色设定，例如 "专业的AI助手"、"技术文档专家" 等
            enable_boundary_control: 是否启用边界控制（减少幻觉）
            enable_citation: 是否启用引用标注
            citation_format: 引用格式，默认为 "[Source {index}]"，{index} 会被替换为序号
        """
        self.role = role
        self.enable_boundary_control = enable_boundary_control
        self.enable_citation = enable_citation
        self.citation_format = citation_format

    def build_rag_prompt(
        self,
        query: str,
        contexts: List[Dict[str, Any]],
        system_instruction: Optional[str] = None,
        max_context_length: int = 4000
    ) -> List[Dict[str, str]]:
        """
        构建 RAG 提示词
        
        Args:
            query: 用户查询
            contexts: 检索到的上下文列表，每个元素包含：
                - document: 文档内容
                - metadata: 元数据（可选，包含 title, url, category 等）
                - id: 文档 ID（可选）
            system_instruction: 自定义系统指令（可选）
            max_context_length: 最大上下文长度（字符数）
            
        Returns:
            格式化的消息列表，可直接用于 LLM.chat()
        """
        # 构建系统提示词
        system_prompt = self._build_system_prompt(system_instruction)
        
        # 格式化上下文
        formatted_contexts = self._format_contexts(contexts, max_context_length)
        
        # 构建用户提示词
        user_prompt = self._build_user_prompt(query, formatted_contexts)
        
        # 构建消息列表
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return messages

    def _build_system_prompt(self, custom_instruction: Optional[str] = None) -> str:
        """
        构建系统提示词
        
        Args:
            custom_instruction: 自定义指令
            
        Returns:
            系统提示词
        """
        parts = []
        
        # 角色设定
        parts.append(f"你是一个{self.role}。")
        
        # 边界控制
        if self.enable_boundary_control:
            parts.append(
                "重要提示：如果提供的上下文中没有答案，请明确说'根据提供的上下文，我无法找到相关信息'，"
                "不要编造或猜测答案。这有助于减少幻觉。"
            )
        
        # 引用标注
        if self.enable_citation:
            parts.append(
                "在回答中，请使用引用标注来标明信息来源。"
                f"格式为：{self.citation_format.format(index=1)}，其中数字对应上下文中的文档序号。"
            )
        
        # 自定义指令
        if custom_instruction:
            parts.append(custom_instruction)
        
        return "\n".join(parts)

    def _format_contexts(
        self,
        contexts: List[Dict[str, Any]],
        max_length: int = 4000
    ) -> List[Dict[str, Any]]:
        """
        格式化上下文，添加引用标记
        
        Args:
            contexts: 原始上下文列表
            max_length: 最大总长度
            
        Returns:
            格式化后的上下文列表
        """
        formatted = []
        total_length = 0
        
        for idx, context in enumerate(contexts, start=1):
            doc_content = context.get("document", "")
            metadata = context.get("metadata", {})
            
            # 构建带引用的文档内容
            citation_marker = self.citation_format.format(index=idx)
            
            # 提取文档元信息
            title = metadata.get("title", f"文档 {idx}")
            url = metadata.get("url", "")
            category = metadata.get("category", "")
            
            # 构建文档头部信息
            doc_header_parts = [f"{citation_marker}"]
            if title:
                doc_header_parts.append(f"标题: {title}")
            if category:
                doc_header_parts.append(f"分类: {category}")
            if url:
                doc_header_parts.append(f"来源: {url}")
            
            doc_header = "\n".join(doc_header_parts)
            formatted_doc = f"{doc_header}\n内容: {doc_content}"
            
            # 检查长度限制
            if total_length + len(formatted_doc) > max_length:
                # 截断当前文档
                remaining_length = max_length - total_length
                if remaining_length > 100:  # 至少保留一些内容
                    formatted_doc = formatted_doc[:remaining_length] + "..."
                    formatted.append({
                        "index": idx,
                        "content": formatted_doc,
                        "metadata": metadata,
                        "id": context.get("id")
                    })
                break
            
            formatted.append({
                "index": idx,
                "content": formatted_doc,
                "metadata": metadata,
                "id": context.get("id")
            })
            
            total_length += len(formatted_doc)
        
        return formatted

    def _build_user_prompt(
        self,
        query: str,
        formatted_contexts: List[Dict[str, Any]]
    ) -> str:
        """
        构建用户提示词
        
        Args:
            query: 用户查询
            formatted_contexts: 格式化后的上下文列表
            
        Returns:
            用户提示词
        """
        parts = []
        
        # 添加上下文部分
        if formatted_contexts:
            parts.append("以下是相关的上下文信息：\n")
            for ctx in formatted_contexts:
                parts.append(ctx["content"])
                parts.append("")  # 空行分隔
            
            parts.append("---")
            parts.append("")
        
        # 添加查询部分
        parts.append(f"问题：{query}")
        parts.append("")
        
        # 添加回答要求
        if self.enable_citation:
            parts.append(
                "请基于上述上下文回答问题。"
                "如果上下文中包含相关信息，请在回答中使用引用标注（如 [Source 1]）标明来源。"
            )
        else:
            parts.append("请基于上述上下文回答问题。")
        
        if self.enable_boundary_control:
            parts.append(
                "如果上下文中没有相关信息，请明确说明无法找到答案，不要编造。"
            )
        
        return "\n".join(parts)

    def extract_citations(self, answer: str) -> List[int]:
        """
        从回答中提取引用序号
        
        Args:
            answer: LLM 生成的回答
            
        Returns:
            引用序号列表，例如 [1, 2, 3]
        """
        citations = []
        
        # 匹配引用格式，例如 [Source 1], [Source 2] 等
        pattern = r'\[Source\s*(\d+)\]'
        matches = re.findall(pattern, answer, re.IGNORECASE)
        
        for match in matches:
            try:
                citation_num = int(match)
                if citation_num not in citations:
                    citations.append(citation_num)
            except ValueError:
                continue
        
        # 也匹配其他可能的格式，如 [1], [2] 等
        pattern2 = r'\[(\d+)\]'
        matches2 = re.findall(pattern2, answer)
        
        for match in matches2:
            try:
                citation_num = int(match)
                if citation_num not in citations:
                    citations.append(citation_num)
            except ValueError:
                continue
        
        return sorted(citations)

    def add_citations_to_answer(
        self,
        answer: str,
        contexts: List[Dict[str, Any]],
        auto_add: bool = False
    ) -> str:
        """
        为回答添加引用信息
        
        Args:
            answer: 原始回答
            contexts: 上下文列表
            auto_add: 是否自动为未标注的部分添加引用
            
        Returns:
            添加引用后的回答
        """
        if not self.enable_citation:
            return answer
        
        # 提取已有的引用
        existing_citations = self.extract_citations(answer)
        
        # 如果没有引用且启用了自动添加，尝试添加引用
        if not existing_citations and auto_add and contexts:
            # 简单策略：在回答末尾添加引用
            citation_info = []
            for idx, ctx in enumerate(contexts[:5], start=1):  # 最多引用前5个
                metadata = ctx.get("metadata", {})
                title = metadata.get("title", f"文档 {idx}")
                url = metadata.get("url", "")
                
                citation_text = f"[Source {idx}]"
                if title:
                    citation_text += f" {title}"
                if url:
                    citation_text += f" ({url})"
                
                citation_info.append(citation_text)
            
            if citation_info:
                answer += "\n\n参考来源：\n" + "\n".join(citation_info)
        
        return answer

    def build_simple_prompt(
        self,
        query: str,
        context_text: str,
        system_instruction: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        构建简单的 RAG 提示词（单段上下文）
        
        Args:
            query: 用户查询
            context_text: 上下文文本
            system_instruction: 自定义系统指令
            
        Returns:
            格式化的消息列表
        """
        # 构建系统提示词
        system_prompt = self._build_system_prompt(system_instruction)
        
        # 构建用户提示词
        user_prompt_parts = [
            "以下是相关的上下文信息：",
            "",
            context_text,
            "",
            "---",
            "",
            f"问题：{query}",
            ""
        ]
        
        if self.enable_citation:
            user_prompt_parts.append(
                "请基于上述上下文回答问题，并在回答中使用 [Source 1] 标注来源。"
            )
        else:
            user_prompt_parts.append("请基于上述上下文回答问题。")
        
        if self.enable_boundary_control:
            user_prompt_parts.append(
                "如果上下文中没有相关信息，请明确说明无法找到答案。"
            )
        
        user_prompt = "\n".join(user_prompt_parts)
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

    def update_role(self, new_role: str):
        """
        更新角色设定
        
        Args:
            new_role: 新的角色名称
        """
        self.role = new_role

    def set_boundary_control(self, enabled: bool):
        """
        设置边界控制开关
        
        Args:
            enabled: 是否启用
        """
        self.enable_boundary_control = enabled

    def set_citation(self, enabled: bool, format_str: Optional[str] = None):
        """
        设置引用标注开关
        
        Args:
            enabled: 是否启用
            format_str: 引用格式（可选）
        """
        self.enable_citation = enabled
        if format_str:
            self.citation_format = format_str


if __name__ == '__main__':
    # 示例用法
    from service.llm.AskLLmService import AskLLM
    from util.McpConfigUtil import ConfigUtil
    from util.McpConstant import Constant
    
    # 初始化提示词工程
    prompt_eng = PromptEngineering(
        role="专业的技术文档助手",
        enable_boundary_control=True,
        enable_citation=True
    )
    
    # 模拟检索到的上下文
    contexts = [
        {
            "document": "Python 是一种高级编程语言，由 Guido van Rossum 创建。",
            "metadata": {
                "title": "Python 简介",
                "url": "https://example.com/python",
                "category": "编程语言"
            },
            "id": "doc1"
        },
        {
            "document": "文件操作是编程中的常见任务，Python 提供了 open() 函数来打开文件。",
            "metadata": {
                "title": "Python 文件操作",
                "url": "https://example.com/file-ops",
                "category": "教程"
            },
            "id": "doc2"
        }
    ]
    
    # 构建 RAG 提示词
    query = "Python 如何读取文件？"
    messages = prompt_eng.build_rag_prompt(query, contexts)
    
    print("=" * 50)
    print("系统提示词：")
    print(messages[0]["content"])
    print("\n" + "=" * 50)
    print("用户提示词：")
    print(messages[1]["content"])
    
    # 测试引用提取
    test_answer = "Python 可以使用 open() 函数读取文件 [Source 2]。"
    citations = prompt_eng.extract_citations(test_answer)
    print("\n" + "=" * 50)
    print(f"测试回答: {test_answer}")
    print(f"提取的引用: {citations}")
    
    # 测试简单提示词
    print("\n" + "=" * 50)
    print("简单提示词示例：")
    simple_messages = prompt_eng.build_simple_prompt(
        query="什么是 Python？",
        context_text="Python 是一种解释型、面向对象的高级编程语言。"
    )
    print(simple_messages[1]["content"])

