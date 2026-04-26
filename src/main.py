"""
PPT 分析 Agent - FastAPI 入口

提供 RESTful API 接口，支持：
- 上传 PPT/PDF 文件
- 课程内容总结
- 知识图谱提取
- 难点分析
- 练习题生成
- 智能问答
"""

import os
import uuid
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from src.config import settings
from src.parser.pdf_parser import ParserFactory
from src.analyzer.summarizer import Summarizer
from src.analyzer.knowledge import KnowledgeAnalyzer
from src.analyzer.difficulty import DifficultyAnalyzer
from src.analyzer.quiz import QuizGenerator
from src.analyzer.qa import QAAgent
from src.analyzer.pdf_generator import generate_pdf_report
from src.analyzer.llm_client import token_tracker
from src.analyzer.learning_agent import LearningAgent
from src.models.schemas import (
    AnalysisRequest,
    AnalysisResult,
    QARequest,
    QAResponse,
    SummaryResult,
    KnowledgeGraph,
    DifficultyAnalysis,
    QuizResult,
)

# 确保上传目录存在
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# 存储已解析的 PPT 内容
ppt_cache: dict[str, str] = {}
# 存储原始文件名映射: uuid_path -> original_filename
original_filenames: dict[str, str] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    yield
    # 关闭时
    ppt_cache.clear()


app = FastAPI(
    title="PPT 分析 Agent API",
    description="帮助大学生分析 PPT 课件，生成学习笔记、知识图谱、练习题等",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 中间件（允许前端跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 静态文件服务（前端页面）
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

# 挂载前端静态文件目录（使用 /static 前缀避免冲突）
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="frontend")


@app.get("/", summary="🎓 AI 教授 - PPT 互动课堂")
async def serve_frontend():
    """提供前端页面"""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Frontend not found"}


def _parse_ppt(filepath: str) -> str:
    """解析 PPT/PDF 文件并缓存"""
    if filepath in ppt_cache:
        return ppt_cache[filepath]

    parser = ParserFactory.get_parser(filepath)
    result = parser.parse(filepath)
    ppt_cache[filepath] = result.raw_text
    return result.raw_text


@app.post("/upload", summary="上传 PPT/PDF 文件")
async def upload_file(file: UploadFile = File(...)):
    """
    上传 PPT 或 PDF 文件

    - 支持 .pptx 和 .pdf 格式
    - 文件大小限制: 50MB
    - 返回文件 ID，用于后续分析
    """
    # 验证文件类型
    if not (file.filename.endswith(".pptx") or file.filename.endswith(".pdf")):
        raise HTTPException(
            status_code=400,
            detail="仅支持 .pptx 和 .pdf 格式的文件",
        )

    # 生成唯一文件名
    file_id = str(uuid.uuid4())
    ext = Path(file.filename).suffix
    save_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}{ext}")

    # 保存文件
    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="文件大小超过限制（50MB）",
        )

    with open(save_path, "wb") as f:
        f.write(content)

    # 保存原始文件名映射
    original_filenames[save_path] = file.filename

    # 预解析并缓存
    try:
        _parse_ppt(save_path)
    except Exception as e:
        os.remove(save_path)
        raise HTTPException(status_code=400, detail=f"文件解析失败: {str(e)}")

    return {
        "file_id": file_id,
        "filename": file.filename,
        "filepath": save_path,
        "message": "文件上传成功",
    }


@app.post("/analyze", response_model=AnalysisResult, summary="分析 PPT 内容")
async def analyze_ppt(
    filepath: str = Form(...),
    analysis_types: str = Form(default="summary"),
    language: str = Form(default="zh"),
    detail_level: str = Form(default="detailed"),
):
    """
    综合分析 PPT 课件

    - filepath: 上传后返回的文件路径
    - analysis_types: 分析类型，逗号分隔，如 "summary,knowledge_graph,difficulty,quiz"
    - language: 输出语言 zh/en
    - detail_level: 详细程度 brief/normal/detailed
    """
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="文件不存在，请先上传")

    ppt_text = _parse_ppt(filepath)
    types_list = [t.strip() for t in analysis_types.split(",")]

    result = AnalysisResult(filename=Path(filepath).name)

    if "summary" in types_list:
        summarizer = Summarizer()
        result.summary = summarizer.summarize(ppt_text, language, detail_level)

    if "knowledge_graph" in types_list:
        analyzer = KnowledgeAnalyzer()
        result.knowledge_graph = analyzer.extract_knowledge_graph(ppt_text, language)

    if "difficulty" in types_list:
        analyzer = DifficultyAnalyzer()
        result.difficulty = analyzer.analyze(ppt_text, language)

    if "quiz" in types_list:
        generator = QuizGenerator()
        result.quiz = generator.generate(ppt_text, language=language)

    return result


@app.post("/summarize", response_model=SummaryResult, summary="生成课程总结")
async def summarize(
    filepath: str = Form(...),
    language: str = Form(default="zh"),
    detail: str = Form(default="detailed"),
):
    """生成 PPT 课程内容总结"""
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="文件不存在，请先上传")

    ppt_text = _parse_ppt(filepath)
    summarizer = Summarizer()
    return summarizer.summarize(ppt_text, language, detail)


@app.post("/knowledge-graph", response_model=KnowledgeGraph, summary="提取知识图谱")
async def knowledge_graph(
    filepath: str = Form(...),
    language: str = Form(default="zh"),
):
    """提取 PPT 中的知识图谱"""
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="文件不存在，请先上传")

    ppt_text = _parse_ppt(filepath)
    analyzer = KnowledgeAnalyzer()
    return analyzer.extract_knowledge_graph(ppt_text, language)


@app.post("/difficulty", response_model=DifficultyAnalysis, summary="分析课程难点")
async def difficulty_analysis(
    filepath: str = Form(...),
    language: str = Form(default="zh"),
):
    """分析 PPT 课程中的难点"""
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="文件不存在，请先上传")

    ppt_text = _parse_ppt(filepath)
    analyzer = DifficultyAnalyzer()
    return analyzer.analyze(ppt_text, language)


@app.post("/quiz", response_model=QuizResult, summary="生成练习题")
async def generate_quiz(
    filepath: str = Form(...),
    num_questions: int = Form(default=5),
    language: str = Form(default="zh"),
):
    """根据 PPT 内容生成练习题"""
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="文件不存在，请先上传")

    ppt_text = _parse_ppt(filepath)
    generator = QuizGenerator()
    return generator.generate(ppt_text, num_questions, language=language)


@app.post("/ask", response_model=QAResponse, summary="智能问答")
async def ask_question(
    filepath: str = Form(...),
    question: str = Form(...),
    language: str = Form(default="zh"),
):
    """基于 PPT 内容回答学生问题"""
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="文件不存在，请先上传")

    ppt_text = _parse_ppt(filepath)
    qa_agent = QAAgent()
    return qa_agent.ask(question, ppt_text, language=language)


@app.post("/export-pdf", summary="导出 PDF 分析报告")
async def export_pdf(
    filepath: str = Form(...),
    summary_json: str = Form(default=""),
    knowledge_graph_json: str = Form(default=""),
    difficulty_json: str = Form(default=""),
    quiz_json: str = Form(default=""),
):
    """
    生成完整的 PDF 分析报告并保存到 project 文件夹

    不再调用 LLM API，直接接收前端传过来的分析结果 JSON 拼接到 PDF 中。

    - filepath: 上传后返回的文件路径
    - summary_json: 课程总结 JSON 字符串
    - knowledge_graph_json: 知识图谱 JSON 字符串
    - difficulty_json: 难点分析 JSON 字符串
    - quiz_json: 练习题 JSON 字符串
    """
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="文件不存在，请先上传")

    # 使用原始文件名（如果存在映射），否则使用 UUID 文件名
    filename = original_filenames.get(filepath, Path(filepath).name)

    # 解析前端传过来的 JSON 数据
    import json

    summary = None
    knowledge_graph = None
    difficulty = None
    quiz = None

    if summary_json:
        try:
            data = json.loads(summary_json)
            summary = SummaryResult(**data)
        except Exception as e:
            print(f"[export-pdf] summary 解析失败: {e}")

    if knowledge_graph_json:
        try:
            data = json.loads(knowledge_graph_json)
            knowledge_graph = KnowledgeGraph(**data)
        except Exception as e:
            print(f"[export-pdf] knowledge_graph 解析失败: {e}")

    if difficulty_json:
        try:
            data = json.loads(difficulty_json)
            difficulty = DifficultyAnalysis(**data)
        except Exception as e:
            print(f"[export-pdf] difficulty 解析失败: {e}")

    if quiz_json:
        try:
            data = json.loads(quiz_json)
            quiz = QuizResult(**data)
        except Exception as e:
            print(f"[export-pdf] quiz 解析失败: {e}")

    # 生成 PDF（直接拼接，不调 LLM）
    pdf_path = generate_pdf_report(
        filename=filename,
        summary=summary,
        knowledge_graph=knowledge_graph,
        difficulty=difficulty,
        quiz=quiz,
        output_dir="project",
    )

    return {
        "message": "PDF 报告生成成功",
        "pdf_path": pdf_path,
        "filename": os.path.basename(pdf_path),
    }


@app.get("/token-usage", summary="Token 使用统计")
async def get_token_usage():
    """
    获取 LLM Token 使用统计

    返回所有 LLM 调用的 Token 消耗汇总和最近记录。
    """
    return {
        "summary": token_tracker.get_summary(),
        "recent_calls": token_tracker.get_records(limit=20),
    }


@app.post("/token-usage/clear", summary="清空 Token 统计")
async def clear_token_usage():
    """清空 Token 使用统计记录"""
    token_tracker.clear()
    return {"message": "Token 统计已清空"}


# ================================================================
# 🎓 交互式学习 Agent API
# ================================================================

# 存储学习会话（按 filepath 索引）
learning_sessions: dict[str, LearningAgent] = {}


@app.post("/learn/start", summary="🎓 开始学习 PPT")
async def learn_start(filepath: str = Form(...), language: str = Form(default="zh")):
    """
    开始学习 PPT 课件

    1. 解析 PPT 内容
    2. 生成课程概览
    3. 返回第1页的讲解

    返回:
    - step_type: overview / slide / done
    - title: 标题
    - content: 讲解内容（Markdown 格式）
    - slide_number: 当前页码
    - total_slides: 总页数
    - progress: 学习进度百分比
    """
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="文件不存在，请先上传")

    agent = LearningAgent(language=language)
    result = agent.start_learning(filepath)

    # 保存会话
    learning_sessions[filepath] = agent

    return result.to_dict()


@app.post("/learn/next", summary="📖 学习下一页")
async def learn_next(filepath: str = Form(...)):
    """继续学习下一页"""
    agent = learning_sessions.get(filepath)
    if not agent:
        raise HTTPException(status_code=400, detail="请先调用 /learn/start 开始学习")

    result = agent.next_page()
    return result.to_dict()


@app.post("/learn/prev", summary="🔙 回到上一页")
async def learn_prev(filepath: str = Form(...)):
    """回到上一页"""
    agent = learning_sessions.get(filepath)
    if not agent:
        raise HTTPException(status_code=400, detail="请先调用 /learn/start 开始学习")

    result = agent.prev_page()
    return result.to_dict()


@app.post("/learn/goto", summary="🔢 跳到指定页")
async def learn_goto(filepath: str = Form(...), page: int = Form(...)):
    """跳到指定页码"""
    agent = learning_sessions.get(filepath)
    if not agent:
        raise HTTPException(status_code=400, detail="请先调用 /learn/start 开始学习")

    result = agent.go_to_page(page)
    return result.to_dict()


@app.post("/learn/ask", summary="💬 提问")
async def learn_ask(filepath: str = Form(...), question: str = Form(...)):
    """基于 PPT 内容提问"""
    agent = learning_sessions.get(filepath)
    if not agent:
        raise HTTPException(status_code=400, detail="请先调用 /learn/start 开始学习")

    result = agent.ask(question)
    return result.to_dict()


@app.post("/learn/notes", summary="📝 生成课程笔记")
async def learn_notes(
    filepath: str = Form(...),
    detail: str = Form(default="detailed"),
):
    """生成课程笔记（调用 LLM 总结）"""
    agent = learning_sessions.get(filepath)
    if not agent:
        raise HTTPException(status_code=400, detail="请先调用 /learn/start 开始学习")

    result = agent.generate_notes(detail=detail)
    return result.to_dict()


@app.post("/learn/quiz", summary="✏️ 生成练习题")
async def learn_quiz(
    filepath: str = Form(...),
    num_questions: int = Form(default=5),
):
    """生成练习题（调用 LLM）"""
    agent = learning_sessions.get(filepath)
    if not agent:
        raise HTTPException(status_code=400, detail="请先调用 /learn/start 开始学习")

    result = agent.generate_quiz(num_questions=num_questions)
    return result.to_dict()


@app.post("/learn/progress", summary="📊 查看学习进度")
async def learn_progress(filepath: str = Form(...)):
    """查看当前学习进度"""
    agent = learning_sessions.get(filepath)
    if not agent:
        raise HTTPException(status_code=400, detail="请先调用 /learn/start 开始学习")

    return agent.get_progress()


@app.get("/health", summary="健康检查")
async def health_check():
    """服务健康检查"""
    return {"status": "ok", "service": "ppt-analyse"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
    )
