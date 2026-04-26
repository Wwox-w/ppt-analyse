"""数据模型定义"""

from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional


class SlideContent(BaseModel):
    """单页幻灯片内容"""
    slide_number: int = Field(..., description="页码")
    title: str = Field(default="", description="幻灯片标题")
    content: str = Field(default="", description="幻灯片正文内容")
    notes: str = Field(default="", description="演讲者备注")
    has_tables: bool = Field(default=False, description="是否包含表格")
    has_images: bool = Field(default=False, description="是否包含图片")


class ParsedPPT(BaseModel):
    """解析后的完整 PPT 内容"""
    filename: str = Field(..., description="文件名")
    total_slides: int = Field(..., description="总页数")
    slides: list[SlideContent] = Field(default_factory=list, description="所有幻灯片")
    raw_text: str = Field(default="", description="全部文本内容（用于 LLM 分析）")


# ---- 分析结果模型 ----

class SummaryResult(BaseModel):
    """课程总结结果"""
    overview: str = Field(..., description="课程概述")
    key_points: list[str] = Field(default_factory=list, description="关键要点")
    chapter_summaries: list[dict] = Field(
        default_factory=list,
        description="每章总结 [{'chapter': '标题', 'summary': '内容'}]"
    )


class KnowledgePoint(BaseModel):
    """知识点"""
    name: str = Field(..., description="知识点名称")
    description: str = Field(..., description="知识点描述")
    importance: str = Field(default="medium", description="重要程度: high/medium/low")
    related_concepts: list[str] = Field(default_factory=list, description="相关概念")


class KnowledgeGraph(BaseModel):
    """知识图谱"""
    nodes: list[KnowledgePoint] = Field(default_factory=list, description="知识节点")
    relationships: list[dict] = Field(
        default_factory=list,
        description="关系 [{'source': '概念A', 'target': '概念B', 'relation': '依赖/关联/...'}]"
    )


class DifficultyAnalysis(BaseModel):
    """难点分析"""
    difficult_concepts: list[dict] = Field(
        default_factory=list,
        description="难点列表 [{'concept': '概念', 'reason': '难点原因', 'suggestion': '学习建议'}]"
    )
    prerequisites: list[str] = Field(default_factory=list, description="前置知识要求")


class QuizQuestion(BaseModel):
    """练习题"""
    type: str = Field(..., description="题目类型: choice/fill/essay")
    question: str = Field(..., description="题目内容")
    options: list[str] = Field(default_factory=list, description="选择题选项")
    answer: str = Field(..., description="参考答案")
    explanation: str = Field(default="", description="解析")


class QuizResult(BaseModel):
    """练习题集"""
    title: str = Field(..., description="练习题标题")
    questions: list[QuizQuestion] = Field(default_factory=list, description="题目列表")


class QARequest(BaseModel):
    """问答请求"""
    question: str = Field(..., description="学生的问题")
    history: list[dict] = Field(default_factory=list, description="对话历史")


class QAResponse(BaseModel):
    """问答响应"""
    answer: str = Field(..., description="回答内容")
    related_slides: list[int] = Field(default_factory=list, description="相关幻灯片页码")
    confidence: float = Field(default=1.0, description="置信度")


class AnalysisRequest(BaseModel):
    """分析请求"""
    analysis_types: list[str] = Field(
        default=["summary"],
        description="分析类型: summary/knowledge_graph/difficulty/quiz"
    )
    language: str = Field(default="zh", description="输出语言")
    detail_level: str = Field(default="detailed", description="详细程度: brief/normal/detailed")


class AnalysisResult(BaseModel):
    """综合分析结果"""
    filename: str = Field(..., description="文件名")
    summary: Optional[SummaryResult] = Field(default=None, description="课程总结")
    knowledge_graph: Optional[KnowledgeGraph] = Field(default=None, description="知识图谱")
    difficulty: Optional[DifficultyAnalysis] = Field(default=None, description="难点分析")
    quiz: Optional[QuizResult] = Field(default=None, description="练习题")
