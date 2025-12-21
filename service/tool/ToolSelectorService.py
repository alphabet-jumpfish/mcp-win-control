"""
工具选择服务
根据用户问题判断是否需要使用 MCP 工具，以及使用哪个工具

实现策略：
1. 规则匹配（快速命中，高精度场景）
2. Embedding 相似度匹配（兜底方案，更鲁棒）
"""
from typing import List, Dict, Optional, Tuple
import re
from service.rag.EmbeddingUtil import EmbeddingUtil
from service.tool import ToolList


class ToolSelector:
    """工具选择器"""

    def __init__(self, embedding_util: Optional[EmbeddingUtil] = None):
        """
        初始化工具选择器
        Args:
            embedding_util: 嵌入工具实例，用于语义相似度匹配（可选）
        """
        self.embedding_util = embedding_util

        # 工具描述列表（工具名称 -> 工具描述）
        self.tool_descriptions = ToolList.TOOL_DESCRIPTIONS
        self.tool_rules = ToolList.TOOL_RULES
        # 相似度阈值
        self.similarity_threshold = 0.6  # 默认阈值，可根据需要调整

    def select_tool(
            self,
            question: str,
            available_tools: Optional[List[str]] = None
    ) -> Tuple[Optional[str], float, str]:
        """
        根据问题选择最合适的工具
        
        Args:
            question: 用户问题
            available_tools: 可用的工具列表（如果为 None，则使用所有工具）
            
        Returns:
            (工具名称, 相似度分数, 匹配方式) 元组
            - 工具名称: 匹配到的工具名称，如果为 None 表示不需要工具
            - 相似度分数: 匹配的置信度（0-1）
            - 匹配方式: "rule"（规则匹配）或 "embedding"（语义匹配）
        """
        if available_tools is None:
            available_tools = list(self.tool_descriptions.keys())

        # 第一步：规则匹配（快速命中）
        rule_match = self._rule_match(question, available_tools)
        if rule_match:
            tool_name, confidence = rule_match
            return tool_name, confidence, "rule"

        # 第二步：Embedding 相似度匹配（兜底方案）
        if self.embedding_util:
            embedding_match = self._embedding_match(question, available_tools)
            if embedding_match:
                tool_name, similarity = embedding_match
                if similarity >= self.similarity_threshold:
                    return tool_name, similarity, "embedding"

        # 未找到匹配的工具
        return None, 0.0, "none"

    def _rule_match(
            self,
            question: str,
            available_tools: List[str]
    ) -> Optional[Tuple[str, float]]:
        """
        使用规则匹配工具
        
        Args:
            question: 用户问题
            available_tools: 可用工具列表
            
        Returns:
            (工具名称, 置信度) 元组，如果未匹配则返回 None
        """
        question_lower = question.lower()

        # 计算每个工具的匹配分数
        tool_scores = {}
        for tool_name in available_tools:
            if tool_name not in self.tool_rules:
                continue

            keywords = self.tool_rules[tool_name]
            matches = 0
            total_keywords = len(keywords)

            for keyword in keywords:
                if keyword.lower() in question_lower:
                    matches += 1

            if matches > 0:
                # 置信度 = 匹配的关键词数 / 总关键词数
                confidence = min(matches / total_keywords * 2, 1.0)  # 乘以2提高置信度
                tool_scores[tool_name] = confidence

        if not tool_scores:
            return None

        # 返回置信度最高的工具
        best_tool = max(tool_scores.items(), key=lambda x: x[1])
        return best_tool

    def _embedding_match(
            self,
            question: str,
            available_tools: List[str]
    ) -> Optional[Tuple[str, float]]:
        """
        使用 Embedding 相似度匹配工具
        
        Args:
            question: 用户问题
            available_tools: 可用工具列表
            
        Returns:
            (工具名称, 相似度) 元组，如果未匹配则返回 None
        """
        if not self.embedding_util:
            return None

        # 获取可用工具的描述
        tool_descriptions_list = []
        tool_names_list = []
        for tool_name in available_tools:
            if tool_name in self.tool_descriptions:
                tool_descriptions_list.append(self.tool_descriptions[tool_name])
                tool_names_list.append(tool_name)

        if not tool_descriptions_list:
            return None

        # 使用 EmbeddingUtil 计算相似度
        try:
            sorted_texts, sorted_scores = self.embedding_util.search_similar(
                question,
                tool_descriptions_list
            )

            if (sorted_scores is not None and len(sorted_scores) > 0 and
                    sorted_texts is not None and len(sorted_texts) > 0):
                # 获取最高相似度的工具
                best_score = sorted_scores[0]
                best_description = sorted_texts[0]
                # 找到对应的工具名称
                best_tool_name = None
                for tool_name, description in zip(tool_names_list, tool_descriptions_list):
                    if description == best_description:
                        best_tool_name = tool_name
                        break

                if best_tool_name:
                    return best_tool_name, float(best_score)
        except Exception as e:
            print(f"Embedding 匹配出错: {e}")

        return None

    def should_use_tool(self, question: str, available_tools: Optional[List[str]] = None) -> bool:
        """
        判断是否应该使用工具
        
        Args:
            question: 用户问题
            available_tools: 可用工具列表
            
        Returns:
            True 表示应该使用工具，False 表示不需要工具
        """
        tool_name, score, method = self.select_tool(question, available_tools)
        return tool_name is not None

    def get_tool_description(self, tool_name: str) -> Optional[str]:
        """
        获取工具描述
        
        Args:
            tool_name: 工具名称
            
        Returns:
            工具描述，如果不存在则返回 None
        """
        return self.tool_descriptions.get(tool_name)

    def add_tool(
            self,
            tool_name: str,
            description: str,
            keywords: Optional[List[str]] = None
    ):
        """
        添加新工具
        
        Args:
            tool_name: 工具名称
            description: 工具描述
            keywords: 关键词列表（可选）
        """
        self.tool_descriptions[tool_name] = description
        if keywords:
            self.tool_rules[tool_name] = keywords

    def update_similarity_threshold(self, threshold: float):
        """
        更新相似度阈值
        
        Args:
            threshold: 新的阈值（0-1之间）
        """
        if 0 <= threshold <= 1:
            self.similarity_threshold = threshold
        else:
            raise ValueError("阈值必须在 0 到 1 之间")


if __name__ == '__main__':
    # 测试示例
    from service.rag.EmbeddingUtil import EmbeddingUtil

    # 初始化（需要提供 embedding 模型路径）
    # embedding_util = EmbeddingUtil(embedding_model_path="path/to/model")
    tool_selector = ToolSelector(embedding_util=None)  # 仅使用规则匹配测试

    # 测试问题
    test_questions = [
        "帮我搜索一下配置文件",
        "读取这个文件的内容",
        "显示系统信息",
        "今天天气怎么样",  # 不需要工具的问题
    ]

    print("=" * 50)
    print("工具选择测试")
    print("=" * 50)

    for question in test_questions:
        tool_name, score, method = tool_selector.select_tool(question)
        if tool_name:
            print(f"\n问题: {question}")
            print(f"匹配工具: {tool_name}")
            print(f"置信度: {score:.2f}")
            print(f"匹配方式: {method}")
            print(f"工具描述: {tool_selector.get_tool_description(tool_name)}")
        else:
            print(f"\n问题: {question}")
            print("未找到匹配的工具（可能需要直接使用 LLM 回答）")
