"""
MCP (Model Context Protocol) Server

提供 PPT 分析相关的工具，供 AI 助手（如 Claude Desktop、Cursor）调用。

工具列表：
- parse_ppt: 解析 PPT/PDF 文件，返回每页文本内容（不调 LLM）
- analyze_ppt: 综合分析（总结+知识图谱+难点+练习题）
- ask_question: 基于 PPT 内容问答
- generate_notes: 生成课程笔记
- generate_quiz: 生成练习题
- export_pdf_report: 将分析结果导出为 PDF 文件
- get_token_usage: 查看 Token 消耗统计
"""

import os
import json
from pathlib import Path
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

from src.parser.pdf_parser import ParserFactory
from src.analyzer.summarizer import Summarizer
from src.analyzer.knowledge import KnowledgeAnalyzer
from src.analyzer.difficulty import DifficultyAnalyzer
from src.analyzer.quiz import QuizGenerator
from src.analyzer.qa import QAAgent
from src.analyzer.pdf_generator import generate_pdf_report
from src.analyzer.llm_client import token_tracker
from src.models.schemas import (
    SummaryResult, KnowledgeGraph, DifficultyAnalysis, QuizResult,
)

# 存储已解析的 PPT 内容（按文件名缓存）
ppt_cache: dict[str, str] = {}
# 存储原始文件名映射
original_filenames: dict[str, str] = {}

server = Server("ppt-analyse")


def _parse_ppt(filepath: str) -> str:
    """解析 PPT/PDF 文件并返回文本内容"""
    if filepath in ppt_cache:
        return ppt_cache[filepath]

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"文件不存在: {filepath}")

    parser = ParserFactory.get_parser(filepath)
    result = parser.parse(filepath)
    ppt_cache[filepath] = result.raw_text
    return result.raw_text


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """列出所有可用的 MCP 工具"""
    return [
        types.Tool(
            name="analyze_ppt",
            description="分析 PPT/PDF 课件，生成课程总结、知识图谱、难点分析和练习题",
            inputSchema={
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "PPT/PDF 文件路径（绝对路径）",
                    },
                    "analysis_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "分析类型: summary/knowledge_graph/difficulty/quiz",
                        "default": ["summary"],
                    },
                    "language": {
                        "type": "string",
                        "description": "输出语言: zh/en",
                        "default": "zh",
                    },
                },
                "required": ["filepath"],
            },
        ),
        types.Tool(
            name="ask_question",
            description="基于 PPT 内容回答学生的问题",
            inputSchema={
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "PPT/PDF 文件路径（绝对路径）",
                    },
                    "question": {
                        "type": "string",
                        "description": "学生的问题",
                    },
                    "language": {
                        "type": "string",
                        "description": "输出语言: zh/en",
                        "default": "zh",
                    },
                },
                "required": ["filepath", "question"],
            },
        ),
        types.Tool(
            name="generate_notes",
            description="根据 PPT 内容生成课程笔记",
            inputSchema={
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "PPT/PDF 文件路径（绝对路径）",
                    },
                    "detail": {
                        "type": "string",
                        "description": "详细程度: brief/normal/detailed",
                        "default": "detailed",
                    },
                    "language": {
                        "type": "string",
                        "description": "输出语言: zh/en",
                        "default": "zh",
                    },
                },
                "required": ["filepath"],
            },
        ),
        types.Tool(
            name="generate_quiz",
            description="根据 PPT 内容生成练习题",
            inputSchema={
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "PPT/PDF 文件路径（绝对路径）",
                    },
                    "num_questions": {
                        "type": "integer",
                        "description": "题目数量",
                        "default": 5,
                    },
                    "language": {
                        "type": "string",
                        "description": "输出语言: zh/en",
                        "default": "zh",
                    },
                },
                "required": ["filepath"],
            },
        ),
        types.Tool(
            name="parse_ppt",
            description="解析 PPT/PDF 文件，返回每页的文本内容（不调用 LLM，免费）",
            inputSchema={
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "PPT/PDF 文件路径（绝对路径）",
                    },
                },
                "required": ["filepath"],
            },
        ),
        types.Tool(
            name="export_pdf_report",
            description="将分析结果导出为 PDF 文件（不调用 LLM，直接拼接 JSON 数据到 PDF）",
            inputSchema={
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "PPT/PDF 文件路径（绝对路径）",
                    },
                    "summary_json": {
                        "type": "string",
                        "description": "课程总结 JSON 字符串（从 analyze_ppt 或 generate_notes 获取）",
                        "default": "",
                    },
                    "knowledge_graph_json": {
                        "type": "string",
                        "description": "知识图谱 JSON 字符串（从 analyze_ppt 获取）",
                        "default": "",
                    },
                    "difficulty_json": {
                        "type": "string",
                        "description": "难点分析 JSON 字符串（从 analyze_ppt 获取）",
                        "default": "",
                    },
                    "quiz_json": {
                        "type": "string",
                        "description": "练习题 JSON 字符串（从 analyze_ppt 或 generate_quiz 获取）",
                        "default": "",
                    },
                },
                "required": ["filepath"],
            },
        ),
        types.Tool(
            name="get_token_usage",
            description="查看 LLM Token 使用统计（总调用次数、Token 消耗）",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict
) -> list[types.TextContent]:
    """处理 MCP 工具调用"""
    try:
        if name == "analyze_ppt":
            return await _handle_analyze(arguments)
        elif name == "ask_question":
            return await _handle_ask(arguments)
        elif name == "generate_notes":
            return await _handle_notes(arguments)
        elif name == "generate_quiz":
            return await _handle_quiz(arguments)
        elif name == "parse_ppt":
            return await _handle_parse_ppt(arguments)
        elif name == "export_pdf_report":
            return await _handle_export_pdf(arguments)
        elif name == "get_token_usage":
            return await _handle_token_usage(arguments)
        else:
            raise ValueError(f"未知工具: {name}")
    except Exception as e:
        return [types.TextContent(type="text", text=f"错误: {str(e)}")]


async def _handle_analyze(args: dict) -> list[types.TextContent]:
    """处理综合分析请求"""
    filepath = args["filepath"]
    analysis_types = args.get("analysis_types", ["summary"])
    language = args.get("language", "zh")

    ppt_text = _parse_ppt(filepath)
    results = {}

    if "summary" in analysis_types:
        summarizer = Summarizer()
        results["summary"] = summarizer.summarize(ppt_text, language).model_dump()

    if "knowledge_graph" in analysis_types:
        analyzer = KnowledgeAnalyzer()
        results["knowledge_graph"] = analyzer.extract_knowledge_graph(ppt_text, language).model_dump()

    if "difficulty" in analysis_types:
        analyzer = DifficultyAnalyzer()
        results["difficulty"] = analyzer.analyze(ppt_text, language).model_dump()

    if "quiz" in analysis_types:
        generator = QuizGenerator()
        results["quiz"] = generator.generate(ppt_text, language=language).model_dump()

    return [types.TextContent(
        type="text",
        text=json.dumps(results, ensure_ascii=False, indent=2),
    )]


async def _handle_ask(args: dict) -> list[types.TextContent]:
    """处理问答请求"""
    filepath = args["filepath"]
    question = args["question"]
    language = args.get("language", "zh")

    ppt_text = _parse_ppt(filepath)
    qa_agent = QAAgent()
    result = qa_agent.ask(question, ppt_text, language=language)

    return [types.TextContent(type="text", text=result.answer)]


async def _handle_notes(args: dict) -> list[types.TextContent]:
    """处理笔记生成请求"""
    filepath = args["filepath"]
    detail = args.get("detail", "detailed")
    language = args.get("language", "zh")

    ppt_text = _parse_ppt(filepath)
    summarizer = Summarizer()
    result = summarizer.summarize(ppt_text, language, detail)

    return [types.TextContent(
        type="text",
        text=json.dumps(result.model_dump(), ensure_ascii=False, indent=2),
    )]


async def _handle_quiz(args: dict) -> list[types.TextContent]:
    """处理练习题生成请求"""
    filepath = args["filepath"]
    num_questions = args.get("num_questions", 5)
    language = args.get("language", "zh")

    ppt_text = _parse_ppt(filepath)
    generator = QuizGenerator()
    result = generator.generate(ppt_text, num_questions, language=language)

    return [types.TextContent(
        type="text",
        text=json.dumps(result.model_dump(), ensure_ascii=False, indent=2),
    )]


async def _handle_parse_ppt(args: dict) -> list[types.TextContent]:
    """处理 PPT 解析请求（不调 LLM）"""
    filepath = args["filepath"]

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"文件不存在: {filepath}")

    parser = ParserFactory.get_parser(filepath)
    result = parser.parse(filepath)
    ppt_cache[filepath] = result.raw_text

    # 保存原始文件名映射
    original_filenames[filepath] = os.path.basename(filepath)

    # 构建返回结果
    output = {
        "filename": result.filename,
        "total_slides": result.total_slides,
        "slides": [
            {
                "slide_number": s.slide_number,
                "title": s.title,
                "content": s.content[:200] + "..." if len(s.content) > 200 else s.content,
                "has_tables": s.has_tables,
                "has_images": s.has_images,
            }
            for s in result.slides
        ],
        "raw_text_length": len(result.raw_text),
    }

    return [types.TextContent(
        type="text",
        text=json.dumps(output, ensure_ascii=False, indent=2),
    )]


async def _handle_export_pdf(args: dict) -> list[types.TextContent]:
    """处理 PDF 导出请求（不调 LLM，直接拼接 JSON）"""
    filepath = args["filepath"]

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"文件不存在: {filepath}")

    # 使用原始文件名（如果存在映射），否则使用文件名
    filename = original_filenames.get(filepath, Path(filepath).name)

    # 解析前端传过来的 JSON 数据
    summary = None
    knowledge_graph = None
    difficulty = None
    quiz = None

    if args.get("summary_json"):
        try:
            data = json.loads(args["summary_json"])
            summary = SummaryResult(**data)
        except Exception as e:
            print(f"[export_pdf] summary 解析失败: {e}")

    if args.get("knowledge_graph_json"):
        try:
            data = json.loads(args["knowledge_graph_json"])
            knowledge_graph = KnowledgeGraph(**data)
        except Exception as e:
            print(f"[export_pdf] knowledge_graph 解析失败: {e}")

    if args.get("difficulty_json"):
        try:
            data = json.loads(args["difficulty_json"])
            difficulty = DifficultyAnalysis(**data)
        except Exception as e:
            print(f"[export_pdf] difficulty 解析失败: {e}")

    if args.get("quiz_json"):
        try:
            data = json.loads(args["quiz_json"])
            quiz = QuizResult(**data)
        except Exception as e:
            print(f"[export_pdf] quiz 解析失败: {e}")

    # 生成 PDF（直接拼接，不调 LLM）
    pdf_path = generate_pdf_report(
        filename=filename,
        summary=summary,
        knowledge_graph=knowledge_graph,
        difficulty=difficulty,
        quiz=quiz,
        output_dir="project",
    )

    return [types.TextContent(
        type="text",
        text=json.dumps({
            "message": "PDF 报告生成成功",
            "pdf_path": pdf_path,
            "filename": os.path.basename(pdf_path),
        }, ensure_ascii=False, indent=2),
    )]


async def _handle_token_usage(args: dict) -> list[types.TextContent]:
    """处理 Token 统计查询"""
    summary = token_tracker.get_summary()
    recent_calls = token_tracker.get_records(limit=20)

    return [types.TextContent(
        type="text",
        text=json.dumps({
            "summary": summary,
            "recent_calls": recent_calls,
        }, ensure_ascii=False, indent=2),
    )]


async def main():
    """运行 MCP Server"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="ppt-analyse",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
