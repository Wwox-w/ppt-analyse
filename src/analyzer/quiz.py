"""练习题生成器"""

from src.analyzer.llm_client import LLMClient
from src.analyzer.json_utils import parse_json_response
from src.models.schemas import QuizResult, QuizQuestion


class QuizGenerator:
    """基于 PPT 内容生成练习题"""

    def __init__(self):
        self.llm = LLMClient()

    def generate(
        self,
        ppt_text: str,
        num_questions: int = 5,
        question_types: list[str] = None,
        language: str = "zh",
    ) -> QuizResult:
        """
        生成练习题

        Args:
            ppt_text: PPT 原始文本内容
            num_questions: 题目数量
            question_types: 题目类型列表，可选: choice/fill/essay
            language: 输出语言

        Returns:
            QuizResult: 练习题集
        """
        if question_types is None:
            question_types = ["choice", "fill", "essay"]

        type_desc = {
            "choice": "选择题（4个选项）",
            "fill": "填空题",
            "essay": "简答题",
        }
        types_str = "、".join([type_desc.get(t, t) for t in question_types])

        system_prompt = f"""你是一个专业的课程出题专家，擅长根据课件内容生成高质量的练习题。
请严格按照 JSON 格式输出，不要包含其他文字。

输出格式：
{{
    "title": "练习题标题",
    "questions": [
        {{
            "type": "choice/fill/essay",
            "question": "题目内容",
            "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
            "answer": "参考答案",
            "explanation": "解析"
        }}
    ]
}}"""

        user_prompt = f"""请根据以下 PPT 课件内容，生成 {num_questions} 道练习题。
题目类型包括：{types_str}
要求：
1. 题目要覆盖课件中的核心知识点
2. 难度适中，适合大学生自测
3. 选择题要提供4个选项
4. 所有题目都要给出参考答案和详细解析
5. 输出语言：{'中文' if language == 'zh' else '英文'}

PPT 内容：
{ppt_text}"""

        response = self.llm.chat(system_prompt, user_prompt)
        return self._parse_response(response)

    def _parse_response(self, response: str) -> QuizResult:
        """解析 LLM 返回的 JSON"""
        try:
            data = parse_json_response(response)
            return QuizResult(**data)
        except Exception as e:
            print(f"[QuizGenerator] JSON 解析失败: {e}")
            return QuizResult(title="练习题", questions=[])
