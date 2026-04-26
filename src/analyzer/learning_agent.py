"""
🎓 PPT 交互式学习 Agent

核心功能：
1. 上传 PPT → 解析内容
2. 引导式学习 → 一步步带你学，每页/每章讲解
3. 互动问答 → 随时提问，Agent 基于 PPT 回答
4. 自动总结 → 学完后生成笔记
5. 出题巩固 → 生成练习题检验效果

使用流程：
    agent = LearningAgent()
    
    # 1. 开始学习
    result = agent.start_learning("path/to/ppt.pptx")
    # → 返回课程概览 + 第1页内容
    
    # 2. 继续学习下一页
    result = agent.next_page()
    # → 返回第2页讲解
    
    # 3. 提问
    result = agent.ask("什么是TCP三次握手？")
    
    # 4. 生成笔记
    result = agent.generate_notes()
    
    # 5. 生成练习题
    result = agent.generate_quiz()
"""

import json
from typing import Optional
from src.parser.pdf_parser import ParserFactory
from src.analyzer.llm_client import LLMClient
from src.analyzer.summarizer import Summarizer
from src.analyzer.quiz import QuizGenerator
from src.models.schemas import ParsedPPT, SlideContent


class LearningStep:
    """学习步骤结果"""
    
    def __init__(
        self,
        step_type: str,          # overview / slide / summary / quiz / qa / done
        title: str = "",
        content: str = "",
        slide_number: int = 0,
        total_slides: int = 0,
        progress: float = 0.0,   # 0.0 ~ 1.0
        extra: dict = None,
    ):
        self.step_type = step_type
        self.title = title
        self.content = content
        self.slide_number = slide_number
        self.total_slides = total_slides
        self.progress = progress
        self.extra = extra or {}
    
    def to_dict(self) -> dict:
        return {
            "step_type": self.step_type,
            "title": self.title,
            "content": self.content,
            "slide_number": self.slide_number,
            "total_slides": self.total_slides,
            "progress": round(self.progress * 100),  # 百分比
            "extra": self.extra,
        }


class LearningAgent:
    """PPT 交互式学习 Agent"""
    
    def __init__(self, language: str = "zh"):
        self.llm = LLMClient()
        self.language = language
        
        # PPT 数据
        self.ppt: Optional[ParsedPPT] = None
        self.filepath: str = ""
        
        # 学习状态
        self.current_slide_index: int = -1  # -1 表示还没开始
        self.learning_history: list[dict] = []  # 学习历史
        self.qa_history: list[dict] = []  # 问答历史
        
        # 分析结果（学完后生成）
        self.summary_result = None
        self.quiz_result = None
    
    # ================================================================
    # 1. 开始学习
    # ================================================================
    
    def start_learning(self, filepath: str) -> LearningStep:
        """开始学习 PPT
        
        1. 解析 PPT
        2. 生成课程概览
        3. 定位到第1页
        """
        # 解析 PPT
        parser = ParserFactory.get_parser(filepath)
        self.ppt = parser.parse(filepath)
        self.filepath = filepath
        
        # 重置学习状态
        self.current_slide_index = -1
        self.learning_history = []
        self.qa_history = []
        
        # 生成课程概览
        overview = self._generate_overview()
        
        # 记录学习历史
        self.learning_history.append({
            "type": "overview",
            "content": overview,
        })
        
        return LearningStep(
            step_type="overview",
            title=f"📚 {self.ppt.filename} - 课程概览",
            content=overview,
            slide_number=0,
            total_slides=self.ppt.total_slides,
            progress=0.0,
            extra={
                "total_slides": self.ppt.total_slides,
                "has_tables": any(s.has_tables for s in self.ppt.slides),
                "has_images": any(s.has_images for s in self.ppt.slides),
            },
        )
    
    def _generate_overview(self) -> str:
        """生成课程概览（调用 LLM）"""
        # 提取每页标题
        slide_titles = []
        for s in self.ppt.slides:
            title = s.title or f"第 {s.slide_number} 页"
            slide_titles.append(f"  第 {s.slide_number} 页: {title}")
        
        titles_text = "\n".join(slide_titles)
        
        # 取前几页和后几页的内容作为概览参考
        sample_text = ""
        for s in self.ppt.slides[:3]:
            sample_text += f"\n第{s.slide_number}页: {s.title}\n{s.content[:300]}"
        
        prompt = f"""你是一个耐心的大学课程辅导老师。学生刚刚上传了一份 PPT 课件，请帮他生成一个课程概览。

PPT 文件名: {self.ppt.filename}
总页数: {self.ppt.total_slides} 页

各页标题:
{titles_text}

前几页内容预览:
{sample_text}

请生成课程概览，包含：
1. 📖 **课程简介** — 这门课大概讲什么（2-3句话）
2. 🎯 **学习目标** — 学完这门课能掌握什么（3-5点）
3. 📋 **内容结构** — 按章节/页数划分的内容结构
4. 💡 **学习建议** — 怎么学效果最好

要求：
- 用{'中文' if self.language == 'zh' else '英文'}回答
- 语气亲切、鼓励，像学长/学姐在分享经验
- 不要一次性讲太多细节，先给个整体印象
- 最后告诉学生：可以一页一页跟着学，也可以直接提问"""
        
        return self.llm.chat(
            "你是一个亲切耐心的大学课程辅导老师，帮助学生一步步学习 PPT 课件内容。",
            prompt,
        )
    
    # ================================================================
    # 2. 逐页学习
    # ================================================================
    
    def next_page(self) -> LearningStep:
        """学习下一页"""
        if not self.ppt:
            return LearningStep(
                step_type="error",
                title="还没开始学习",
                content="请先调用 start_learning() 开始学习",
            )
        
        self.current_slide_index += 1
        
        if self.current_slide_index >= len(self.ppt.slides):
            # 所有页都学完了，进入总结阶段
            return self._finish_learning()
        
        slide = self.ppt.slides[self.current_slide_index]
        progress = (self.current_slide_index + 1) / len(self.ppt.slides)
        
        # 生成这一页的讲解
        explanation = self._explain_slide(slide)
        
        # 记录学习历史
        self.learning_history.append({
            "type": "slide",
            "slide_number": slide.slide_number,
            "content": explanation,
        })
        
        return LearningStep(
            step_type="slide",
            title=f"📖 第 {slide.slide_number} 页: {slide.title or '无标题'}",
            content=explanation,
            slide_number=slide.slide_number,
            total_slides=self.ppt.total_slides,
            progress=progress,
            extra={
                "has_tables": slide.has_tables,
                "has_images": slide.has_images,
                "remaining": self.ppt.total_slides - self.current_slide_index - 1,
            },
        )
    
    def prev_page(self) -> LearningStep:
        """回到上一页"""
        if not self.ppt:
            return LearningStep(step_type="error", title="还没开始学习", content="请先调用 start_learning()")
        
        if self.current_slide_index <= 0:
            return LearningStep(
                step_type="error", title="已经是第一页了",
                content="这是第一页，没有上一页了",
                slide_number=1, total_slides=self.ppt.total_slides, progress=1/self.ppt.total_slides,
            )
        
        self.current_slide_index -= 1
        slide = self.ppt.slides[self.current_slide_index]
        progress = (self.current_slide_index + 1) / len(self.ppt.slides)
        
        explanation = self._explain_slide(slide)
        
        return LearningStep(
            step_type="slide",
            title=f"📖 第 {slide.slide_number} 页: {slide.title or '无标题'}",
            content=explanation,
            slide_number=slide.slide_number,
            total_slides=self.ppt.total_slides,
            progress=progress,
        )
    
    def go_to_page(self, page_number: int) -> LearningStep:
        """跳到指定页"""
        if not self.ppt:
            return LearningStep(step_type="error", title="还没开始学习", content="请先调用 start_learning()")
        
        if page_number < 1 or page_number > len(self.ppt.slides):
            return LearningStep(
                step_type="error", title="页码无效",
                content=f"页码范围是 1 ~ {len(self.ppt.slides)}",
                total_slides=self.ppt.total_slides,
            )
        
        self.current_slide_index = page_number - 1
        slide = self.ppt.slides[self.current_slide_index]
        progress = (self.current_slide_index + 1) / len(self.ppt.slides)
        
        explanation = self._explain_slide(slide)
        
        return LearningStep(
            step_type="slide",
            title=f"📖 第 {slide.slide_number} 页: {slide.title or '无标题'}",
            content=explanation,
            slide_number=slide.slide_number,
            total_slides=self.ppt.total_slides,
            progress=progress,
        )
    
    def _explain_slide(self, slide: SlideContent) -> str:
        """用 LLM 讲解一页幻灯片"""
        # 构建上下文：前几页的内容
        context_pages = []
        start = max(0, self.current_slide_index - 2)
        for i in range(start, self.current_slide_index):
            s = self.ppt.slides[i]
            context_pages.append(f"第{s.slide_number}页: {s.title}\n{s.content[:200]}")
        
        context = "\n\n".join(context_pages) if context_pages else "（这是第一页）"
        
        # 当前页内容
        current_content = f"标题: {slide.title or '（无标题）'}\n正文: {slide.content}"
        if slide.notes:
            current_content += f"\n备注: {slide.notes}"
        if slide.has_tables:
            current_content += "\n[此页包含表格]"
        if slide.has_images:
            current_content += "\n[此页包含图片]"
        
        prompt = f"""你是一个耐心的大学课程辅导老师，正在带着学生一页一页地学习 PPT 课件。

当前进度：第 {slide.slide_number} 页 / 共 {self.ppt.total_slides} 页

前面几页的内容：
{context}

当前页内容：
{current_content}

请用{'中文' if self.language == 'zh' else '英文'}讲解这一页，要求：
1. **通俗易懂** — 用生活中的例子解释复杂概念
2. **重点突出** — 告诉学生这一页最重要的是什么
3. **承上启下** — 联系前面讲过的内容，预告后面要学什么
4. **互动引导** — 讲完后问学生一个思考题，或者鼓励学生提问
5. **语气亲切** — 像学长/学姐在耐心讲解

格式：
📌 **重点**
  （这一页的核心内容，2-3句话）

💡 **讲解**
  （详细的讲解，用例子帮助理解）

🤔 **想一想**
  （一个思考题，帮助学生巩固）"""
        
        return self.llm.chat(
            "你是一个亲切耐心的大学课程辅导老师，用通俗易懂的方式讲解 PPT 内容。",
            prompt,
        )
    
    def _finish_learning(self) -> LearningStep:
        """所有页学完，进入总结阶段"""
        prompt = f"""学生刚刚学完了整个 PPT 课件（共 {self.ppt.total_slides} 页）。

PPT 文件名: {self.ppt.filename}

请生成一个学习完成祝贺，包含：
1. 🎉 **完成祝贺** — 鼓励学生完成了全部学习
2. 📊 **学习回顾** — 简要回顾学过的核心内容
3. 🎯 **接下来可以做什么**：
   - 生成课程笔记（保存重点）
   - 做练习题（检验学习效果）
   - 继续提问（深入理解）
   - 导出 PDF 报告（保存学习成果）

语气要亲切、鼓励！"""
        
        content = self.llm.chat(
            "你是一个亲切耐心的大学课程辅导老师。",
            prompt,
        )
        
        return LearningStep(
            step_type="done",
            title="🎉 恭喜！全部学完了！",
            content=content,
            slide_number=self.ppt.total_slides,
            total_slides=self.ppt.total_slides,
            progress=1.0,
            extra={
                "can_generate_notes": True,
                "can_generate_quiz": True,
                "can_export_pdf": True,
            },
        )
    
    # ================================================================
    # 3. 互动问答
    # ================================================================
    
    def ask(self, question: str) -> LearningStep:
        """基于 PPT 内容回答问题"""
        if not self.ppt:
            return LearningStep(step_type="error", title="还没开始学习", content="请先上传 PPT")
        
        # 构建上下文：当前页 + 附近几页
        context = self._build_qa_context()
        
        # 构建对话历史
        history_text = ""
        for msg in self.qa_history[-6:]:  # 最近3轮对话
            role = "学生" if msg["role"] == "user" else "老师"
            history_text += f"\n{role}: {msg['content']}"
        
        prompt = f"""你是一个耐心的大学课程辅导老师，正在帮助学生理解 PPT 课件内容。

PPT 文件名: {self.ppt.filename}
总页数: {self.ppt.total_slides} 页
当前学习到第 {self.current_slide_index + 1} 页

PPT 全文内容（用于参考）:
{context}

最近的对话历史:
{history_text}

学生的问题: {question}

请用{'中文' if self.language == 'zh' else '英文'}回答，要求：
1. **基于 PPT 内容**回答，如果 PPT 中没有相关信息，请说明并补充你的知识
2. **通俗易懂**，用例子帮助理解
3. **如果合适**，可以反问学生一个问题来引导思考
4. 回答最后可以问学生："还想了解什么吗？" """
        
        answer = self.llm.chat(
            "你是一个亲切耐心的大学课程辅导老师，帮助学生理解 PPT 内容。",
            prompt,
        )
        
        # 记录问答历史
        self.qa_history.append({"role": "user", "content": question})
        self.qa_history.append({"role": "assistant", "content": answer})
        
        return LearningStep(
            step_type="qa",
            title=f"💬 {question[:50]}{'...' if len(question) > 50 else ''}",
            content=answer,
            slide_number=self.current_slide_index + 1 if self.current_slide_index >= 0 else 0,
            total_slides=self.ppt.total_slides,
            progress=(self.current_slide_index + 1) / len(self.ppt.slides) if self.ppt else 0,
            extra={
                "question": question,
                "history_length": len(self.qa_history) // 2,
            },
        )
    
    def _build_qa_context(self) -> str:
        """构建问答上下文"""
        # 当前页附近的内容（详细）
        nearby = []
        start = max(0, self.current_slide_index - 3)
        end = min(len(self.ppt.slides), self.current_slide_index + 4)
        
        for i in range(start, end):
            s = self.ppt.slides[i]
            nearby.append(f"第{s.slide_number}页: {s.title}\n{s.content}")
        
        nearby_text = "\n\n".join(nearby)
        
        # 所有页的标题索引
        all_titles = []
        for s in self.ppt.slides:
            all_titles.append(f"第{s.slide_number}页: {s.title or '（无标题）'}")
        
        titles_text = "\n".join(all_titles)
        
        return f"""【各页标题索引】
{titles_text}

【当前页附近内容】
{nearby_text}"""
    
    # ================================================================
    # 4. 生成笔记
    # ================================================================
    
    def generate_notes(self, detail: str = "detailed") -> LearningStep:
        """生成课程笔记"""
        if not self.ppt:
            return LearningStep(step_type="error", title="还没开始学习", content="请先上传 PPT")
        
        summarizer = Summarizer()
        self.summary_result = summarizer.summarize(
            self.ppt.raw_text,
            language=self.language,
            detail=detail,
        )
        
        # 格式化为易读的笔记
        notes = f"""# 📝 {self.ppt.filename} - 课程笔记

## 📖 课程概述
{self.summary_result.overview}

## 🎯 关键要点
"""
        for i, kp in enumerate(self.summary_result.key_points, 1):
            notes += f"\n{i}. {kp}"
        
        if self.summary_result.chapter_summaries:
            notes += "\n\n## 📋 章节总结\n"
            for ch in self.summary_result.chapter_summaries:
                notes += f"\n### {ch.get('chapter', '')}\n{ch.get('summary', '')}\n"
        
        return LearningStep(
            step_type="summary",
            title=f"📝 {self.ppt.filename} - 课程笔记",
            content=notes,
            slide_number=self.current_slide_index + 1 if self.current_slide_index >= 0 else 0,
            total_slides=self.ppt.total_slides,
            progress=1.0,
            extra={
                "summary_json": self.summary_result.model_dump() if self.summary_result else None,
            },
        )
    
    # ================================================================
    # 5. 生成练习题
    # ================================================================
    
    def generate_quiz(self, num_questions: int = 5) -> LearningStep:
        """生成练习题"""
        if not self.ppt:
            return LearningStep(step_type="error", title="还没开始学习", content="请先上传 PPT")
        
        generator = QuizGenerator()
        self.quiz_result = generator.generate(
            self.ppt.raw_text,
            num_questions=num_questions,
            language=self.language,
        )
        
        # 格式化为易读的练习题
        quiz_text = f"# ✏️ {self.quiz_result.title}\n\n"
        
        type_names = {"choice": "【选择题】", "fill": "【填空题】", "essay": "【问答题】"}
        
        for i, q in enumerate(self.quiz_result.questions, 1):
            q_type = type_names.get(q.type, f"【{q.type}】")
            quiz_text += f"\n### {q_type} 第{i}题\n{q.question}\n"
            
            if q.options:
                for opt in q.options:
                    quiz_text += f"  {opt}\n"
            
            quiz_text += f"\n✅ 答案: {q.answer}\n"
            if q.explanation:
                quiz_text += f"📖 解析: {q.explanation}\n"
            quiz_text += "\n---\n"
        
        return LearningStep(
            step_type="quiz",
            title=f"✏️ {self.quiz_result.title}",
            content=quiz_text,
            slide_number=self.current_slide_index + 1 if self.current_slide_index >= 0 else 0,
            total_slides=self.ppt.total_slides,
            progress=1.0,
            extra={
                "quiz_json": self.quiz_result.model_dump() if self.quiz_result else None,
                "num_questions": len(self.quiz_result.questions),
            },
        )
    
    # ================================================================
    # 6. 获取学习进度
    # ================================================================
    
    def get_progress(self) -> dict:
        """获取当前学习进度"""
        if not self.ppt:
            return {"status": "not_started", "message": "还没开始学习"}
        
        return {
            "status": "learning" if self.current_slide_index < len(self.ppt.slides) else "completed",
            "filename": self.ppt.filename,
            "total_slides": self.ppt.total_slides,
            "current_slide": self.current_slide_index + 1 if self.current_slide_index >= 0 else 0,
            "progress": round((self.current_slide_index + 1) / len(self.ppt.slides) * 100),
            "qa_count": len(self.qa_history) // 2,
            "has_summary": self.summary_result is not None,
            "has_quiz": self.quiz_result is not None,
        }
    
    def get_current_slide_raw(self) -> Optional[SlideContent]:
        """获取当前页的原始内容"""
        if not self.ppt or self.current_slide_index < 0:
            return None
        if self.current_slide_index >= len(self.ppt.slides):
            return None
        return self.ppt.slides[self.current_slide_index]
