"""基于 PPT 内容的智能问答"""

from src.analyzer.llm_client import LLMClient
from src.models.schemas import QAResponse


class QAAgent:
    """PPT 智能问答"""

    def __init__(self):
        self.llm = LLMClient()

    def ask(
        self,
        question: str,
        ppt_text: str,
        history: list[dict] = None,
        language: str = "zh",
    ) -> QAResponse:
        """
        基于 PPT 内容回答问题

        Args:
            question: 学生的问题
            ppt_text: PPT 原始文本内容
            history: 对话历史
            language: 输出语言

        Returns:
            QAResponse: 回答结果
        """
        if history is None:
            history = []

        system_prompt = f"""你是一个专业的课程辅导老师，正在帮助学生理解 PPT 课件内容。
请基于提供的 PPT 内容回答学生的问题。
要求：
1. 回答要准确、详细，基于 PPT 内容
2. 如果问题超出 PPT 范围，请说明并基于你的知识补充
3. 用通俗易懂的语言解释复杂概念
4. 可以举例说明来帮助学生理解
5. 输出语言：{'中文' if language == 'zh' else '英文'}

PPT 课件内容：
{ppt_text}"""

        # 构建带历史的消息
        messages = []
        for msg in history:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
            })
        messages.append({"role": "user", "content": question})

        response = self.llm.chat_with_history(system_prompt, messages)

        return QAResponse(
            answer=response,
            related_slides=[],  # 后续版本可以实现基于语义的页码匹配
            confidence=1.0,
        )
