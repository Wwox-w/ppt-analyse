"""知识图谱分析器"""

from src.analyzer.llm_client import LLMClient
from src.analyzer.json_utils import parse_json_response
from src.models.schemas import KnowledgeGraph, KnowledgePoint


class KnowledgeAnalyzer:
    """PPT 知识图谱分析"""

    def __init__(self):
        self.llm = LLMClient()

    def extract_knowledge_graph(self, ppt_text: str, language: str = "zh") -> KnowledgeGraph:
        """
        提取知识图谱

        Args:
            ppt_text: PPT 原始文本内容
            language: 输出语言

        Returns:
            KnowledgeGraph: 知识图谱
        """
        system_prompt = f"""你是一个专业的课程知识分析专家，擅长从课件中提取知识点并构建知识图谱。
请严格按照 JSON 格式输出，不要包含其他文字。

输出格式：
{{
    "nodes": [
        {{"name": "知识点名称", "description": "知识点描述", "importance": "high/medium/low", "related_concepts": ["相关概念1", "相关概念2"]}}
    ],
    "relationships": [
        {{"source": "概念A", "target": "概念B", "relation": "依赖/关联/包含/前置/扩展"}}
    ]
}}"""

        user_prompt = f"""请分析以下 PPT 课件内容，提取其中的核心知识点并构建知识图谱。
要求：
1. 识别所有重要的概念、定义、公式、定理
2. 标注每个知识点的重要程度
3. 找出知识点之间的关联关系（依赖、关联、包含、前置、扩展等）
4. 输出语言：{'中文' if language == 'zh' else '英文'}

PPT 内容：
{ppt_text}"""

        response = self.llm.chat(system_prompt, user_prompt)
        return self._parse_response(response)

    def _parse_response(self, response: str) -> KnowledgeGraph:
        """解析 LLM 返回的 JSON"""
        try:
            data = parse_json_response(response)
            return KnowledgeGraph(**data)
        except Exception:
            return KnowledgeGraph(nodes=[], relationships=[])
