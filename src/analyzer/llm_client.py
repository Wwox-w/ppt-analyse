"""LLM API 客户端 - 兼容 OpenAI API 格式，带 Token 统计"""

import time
from datetime import datetime
from openai import OpenAI
from src.config import settings


# ===== Token 使用统计 =====
class TokenUsage:
    """单次调用的 Token 使用情况"""

    def __init__(self, model: str, prompt_tokens: int, completion_tokens: int, total_tokens: int):
        self.model = model
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = total_tokens
        self.timestamp = datetime.now().isoformat()


class TokenTracker:
    """全局 Token 使用追踪器"""

    def __init__(self):
        self._records: list[TokenUsage] = []

    def add_record(self, usage: TokenUsage):
        self._records.append(usage)

    @property
    def total_prompt_tokens(self) -> int:
        return sum(r.prompt_tokens for r in self._records)

    @property
    def total_completion_tokens(self) -> int:
        return sum(r.completion_tokens for r in self._records)

    @property
    def total_tokens(self) -> int:
        return sum(r.total_tokens for r in self._records)

    @property
    def total_calls(self) -> int:
        return len(self._records)

    def get_records(self, limit: int = 50) -> list[dict]:
        """获取最近的调用记录"""
        records = [
            {
                "model": r.model,
                "prompt_tokens": r.prompt_tokens,
                "completion_tokens": r.completion_tokens,
                "total_tokens": r.total_tokens,
                "timestamp": r.timestamp,
            }
            for r in self._records[-limit:]
        ]
        return records

    def get_summary(self) -> dict:
        """获取汇总统计"""
        return {
            "total_calls": self.total_calls,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_tokens,
        }

    def clear(self):
        """清空统计记录"""
        self._records.clear()


# 全局 Token 追踪器实例
token_tracker = TokenTracker()


class LLMClient:
    """通用 LLM API 客户端（带 Token 统计）"""

    def __init__(self):
        self.client = OpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
        )
        self.model = settings.LLM_MODEL

    def chat(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        """
        调用 LLM 进行对话

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            **kwargs: 其他参数（temperature, max_tokens 等）

        Returns:
            str: 模型回复内容
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 4096),
        )

        # 统计 Token 使用量
        if response.usage:
            usage = TokenUsage(
                model=self.model,
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            )
            token_tracker.add_record(usage)

        return response.choices[0].message.content

    def chat_with_history(
        self,
        system_prompt: str,
        messages: list[dict],
        **kwargs,
    ) -> str:
        """
        带历史记录的对话

        Args:
            system_prompt: 系统提示词
            messages: 对话历史 [{"role": "user"/"assistant", "content": "..."}]
            **kwargs: 其他参数

        Returns:
            str: 模型回复内容
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                *messages,
            ],
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 4096),
        )

        # 统计 Token 使用量
        if response.usage:
            usage = TokenUsage(
                model=self.model,
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            )
            token_tracker.add_record(usage)

        return response.choices[0].message.content
