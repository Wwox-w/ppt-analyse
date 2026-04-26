"""难点分析器"""

from src.analyzer.llm_client import LLMClient
from src.analyzer.json_utils import parse_json_response
from src.models.schemas import DifficultyAnalysis


class DifficultyAnalyzer:
    """PPT 难点分析"""

    def __init__(self):
        self.llm = LLMClient()

    def analyze(self, ppt_text: str, language: str = "zh") -> DifficultyAnalysis:
        """
        分析课程难点

        Args:
            ppt_text: PPT 原始文本内容
            language: 输出语言

        Returns:
            DifficultyAnalysis: 难点分析结果
        """
        system_prompt = f"""你是一个专业的课程学习辅导专家，擅长分析课程中的难点和前置知识要求。
请严格按照 JSON 格式输出，不要包含其他文字。

输出格式：
{{
    "difficult_concepts": [
        {{"concept": "难点概念", "reason": "为什么难", "suggestion": "学习建议"}}
    ],
    "prerequisites": ["前置知识1", "前置知识2"]
}}"""

        user_prompt = f"""请分析以下 PPT 课件内容，找出学生可能觉得难以理解的知识点。
要求：
1. 识别可能的学习难点
2. 分析每个难点的原因（抽象、复杂、需要前置知识等）
3. 给出具体的学习建议
4. 列出学习本课程需要的前置知识
5. 输出语言：{'中文' if language == 'zh' else '英文'}

PPT 内容：
{ppt_text}"""

        response = self.llm.chat(system_prompt, user_prompt)
        return self._parse_response(response)

    def _parse_response(self, response: str) -> DifficultyAnalysis:
        """解析 LLM 返回的 JSON"""
        try:
            data = parse_json_response(response)
            return DifficultyAnalysis(**data)
        except Exception:
            return DifficultyAnalysis(difficult_concepts=[], prerequisites=[])
