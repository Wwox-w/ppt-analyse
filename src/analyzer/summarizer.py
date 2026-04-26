"""课程内容总结分析器"""

from src.analyzer.llm_client import LLMClient
from src.analyzer.json_utils import parse_json_response
from src.models.schemas import SummaryResult


class Summarizer:
    """PPT 课程内容总结"""

    def __init__(self):
        self.llm = LLMClient()

    def summarize(self, ppt_text: str, language: str = "zh", detail: str = "detailed") -> SummaryResult:
        """
        生成课程总结

        Args:
            ppt_text: PPT 原始文本内容
            language: 输出语言
            detail: 详细程度 (brief/normal/detailed)

        Returns:
            SummaryResult: 结构化总结结果
        """
        detail_instruction = {
            "brief": "请给出简洁的总结，每个章节用1-2句话概括",
            "normal": "请给出适中的总结，每个章节用3-5句话概括",
            "detailed": "请给出详细的总结，每个章节用一段话概括，并列出关键要点",
        }.get(detail, "请给出详细的总结")

        system_prompt = f"""你是一个专业的课程学习助手，擅长分析 PPT 课件内容并生成高质量的学习总结。
请严格按照 JSON 格式输出，不要包含其他文字。

输出格式：
{{
    "overview": "课程整体概述（2-3句话）",
    "key_points": ["关键要点1", "关键要点2", ...],
    "chapter_summaries": [
        {{"chapter": "章节/页码", "summary": "该部分内容总结"}}
    ]
}}"""

        user_prompt = f"""请分析以下 PPT 课件内容，{detail_instruction}。
输出语言：{'中文' if language == 'zh' else '英文'}

PPT 内容：
{ppt_text}"""

        response = self.llm.chat(system_prompt, user_prompt)
        return self._parse_response(response)

    def _parse_response(self, response: str) -> SummaryResult:
        """解析 LLM 返回的 JSON"""
        try:
            data = parse_json_response(response)
            return SummaryResult(**data)
        except Exception:
            # 如果解析失败，返回原始文本
            return SummaryResult(
                overview=response[:500] if response else "解析失败",
                key_points=[],
                chapter_summaries=[],
            )
