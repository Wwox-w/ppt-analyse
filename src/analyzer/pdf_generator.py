"""PDF 报告生成器 - 使用 ReportLab 将分析结果输出为格式化的 PDF 文件"""

import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, ListFlowable, ListItem,
    KeepTogether, HRFlowable,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as pdfcanvas

from src.models.schemas import (
    SummaryResult, KnowledgeGraph, DifficultyAnalysis, QuizResult
)

# ===== 字体注册 =====
_FONT_PATHS = [
    ("/System/Library/Fonts/STHeiti Light.ttc", 1),   # Heiti SC
    ("/System/Library/Fonts/STHeiti Medium.ttc", 1),  # Heiti SC Medium
]

_CN_FONT = None
_CN_FONT_BOLD = None

for path, subfont_idx in _FONT_PATHS:
    if os.path.exists(path):
        try:
            pdfmetrics.registerFont(TTFont("HeitiSC", path, subfontIndex=subfont_idx))
            _CN_FONT = "HeitiSC"
            _CN_FONT_BOLD = "HeitiSC"
            break
        except Exception:
            continue

# 如果找不到中文字体，回退到 Helvetica
if not _CN_FONT:
    _CN_FONT = "Helvetica"
    _CN_FONT_BOLD = "Helvetica-Bold"

# 颜色主题
PRIMARY = colors.HexColor("#2563EB")       # 蓝色主色
PRIMARY_LIGHT = colors.HexColor("#DBEAFE") # 浅蓝背景
SECONDARY = colors.HexColor("#059669")     # 绿色强调
ACCENT = colors.HexColor("#D97706")        # 橙色标注
DARK = colors.HexColor("#1E293B")          # 深色文字
GRAY = colors.HexColor("#64748B")          # 灰色文字
LIGHT_GRAY = colors.HexColor("#F1F5F9")   # 浅灰背景
WHITE = colors.white
BORDER = colors.HexColor("#E2E8F0")        # 边框色


# ===== 样式定义 =====
def _get_styles():
    """获取所有样式"""
    styles = getSampleStyleSheet()

    # 封面
    styles.add(ParagraphStyle(
        "CoverTitle", fontName=_CN_FONT_BOLD, fontSize=30,
        textColor=PRIMARY, alignment=TA_CENTER,
        spaceAfter=8, leading=40
    ))
    styles.add(ParagraphStyle(
        "CoverSubtitle", fontName=_CN_FONT, fontSize=14,
        textColor=DARK, alignment=TA_CENTER,
        spaceAfter=4, leading=20
    ))
    styles.add(ParagraphStyle(
        "CoverDate", fontName=_CN_FONT, fontSize=10,
        textColor=GRAY, alignment=TA_CENTER,
        spaceAfter=6, leading=16
    ))
    styles.add(ParagraphStyle(
        "CoverFeature", fontName=_CN_FONT, fontSize=11,
        textColor=DARK, alignment=TA_CENTER,
        spaceAfter=6, leading=18
    ))
    styles.add(ParagraphStyle(
        "CoverStat", fontName=_CN_FONT_BOLD, fontSize=22,
        textColor=PRIMARY, alignment=TA_CENTER,
        spaceAfter=2, leading=28
    ))
    styles.add(ParagraphStyle(
        "CoverStatLabel", fontName=_CN_FONT, fontSize=9,
        textColor=GRAY, alignment=TA_CENTER,
        spaceAfter=4, leading=14
    ))

    # 章节标题
    styles.add(ParagraphStyle(
        "SectionTitle", fontName=_CN_FONT_BOLD, fontSize=20,
        textColor=PRIMARY, spaceAfter=8,
        spaceBefore=16, leading=28
    ))
    styles.add(ParagraphStyle(
        "SubTitle", fontName=_CN_FONT_BOLD, fontSize=13,
        textColor=DARK, spaceAfter=4,
        spaceBefore=10, leading=18
    ))
    styles.add(ParagraphStyle(
        "SubTitle2", fontName=_CN_FONT_BOLD, fontSize=11,
        textColor=DARK, spaceAfter=3,
        spaceBefore=6, leading=16
    ))

    # 正文
    styles.add(ParagraphStyle(
        "BodyTextCN", fontName=_CN_FONT, fontSize=10,
        textColor=DARK, alignment=TA_JUSTIFY,
        spaceAfter=4, leading=16
    ))
    styles.add(ParagraphStyle(
        "BulletText", fontName=_CN_FONT, fontSize=10,
        textColor=DARK, leftIndent=20,
        spaceAfter=2, leading=16
    ))
    styles.add(ParagraphStyle(
        "SmallText", fontName=_CN_FONT, fontSize=9,
        textColor=GRAY, spaceAfter=2, leading=14
    ))

    # 表格
    styles.add(ParagraphStyle(
        "KeyText", fontName=_CN_FONT_BOLD, fontSize=10,
        textColor=DARK, leading=16
    ))
    styles.add(ParagraphStyle(
        "ValueText", fontName=_CN_FONT, fontSize=10,
        textColor=DARK, leading=16
    ))

    # 练习题
    styles.add(ParagraphStyle(
        "QuizTag", fontName=_CN_FONT_BOLD, fontSize=8,
        textColor=WHITE, leading=11
    ))
    styles.add(ParagraphStyle(
        "QuizQuestion", fontName=_CN_FONT_BOLD, fontSize=10,
        textColor=DARK, spaceAfter=3, leading=16
    ))
    styles.add(ParagraphStyle(
        "QuizOption", fontName=_CN_FONT, fontSize=9,
        textColor=DARK, leftIndent=15,
        spaceAfter=1, leading=14
    ))
    styles.add(ParagraphStyle(
        "QuizAnswer", fontName=_CN_FONT_BOLD, fontSize=9,
        textColor=SECONDARY, spaceAfter=2, leading=14
    ))
    styles.add(ParagraphStyle(
        "QuizExplanation", fontName=_CN_FONT, fontSize=9,
        textColor=GRAY, leftIndent=10,
        spaceAfter=6, leading=14
    ))

    # 页脚
    styles.add(ParagraphStyle(
        "FooterStyle", fontName=_CN_FONT, fontSize=8,
        textColor=GRAY, alignment=TA_CENTER, leading=10
    ))

    return styles


# ===== 辅助函数 =====
def _make_section_header(title: str, styles) -> list:
    """生成带装饰线的章节标题"""
    elements = []
    elements.append(Spacer(1, 8))
    elements.append(HRFlowable(
        width="100%", thickness=2, color=PRIMARY,
        spaceAfter=6, spaceBefore=0
    ))
    elements.append(Paragraph(title, styles["SectionTitle"]))
    return elements


def _make_info_table(rows: list, col_widths: list = None, styles=None) -> Table:
    """生成信息表格"""
    if col_widths is None:
        col_widths = [80, 310]

    data = []
    for label, value in rows:
        data.append([
            Paragraph(f"<b>{label}</b>", styles["KeyText"]),
            Paragraph(str(value), styles["ValueText"]),
        ])

    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, BORDER),
        ("LINEBELOW", (0, -1), (-1, -1), 0, WHITE),
    ]))
    return t


def _make_tag(text: str, bg_color, styles) -> Table:
    """生成标签"""
    tag_data = [[Paragraph(f" {text} ", styles["QuizTag"])]]
    tag_table = Table(tag_data, colWidths=[len(text) * 8 + 10])
    tag_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg_color),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    return tag_table


# ===== 页码回调 =====
def _footer(canvas_obj, doc):
    """在每页底部绘制页脚"""
    canvas_obj.saveState()
    canvas_obj.setFont(_CN_FONT, 8)
    canvas_obj.setFillColor(GRAY)
    canvas_obj.drawCentredString(
        A4[0] / 2, 15,
        f"PPT 课程分析报告 | 第 {doc.page} 页 | "
        f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    canvas_obj.restoreState()


# ===== 报告生成函数 =====
def generate_pdf_report(
    filename: str,
    summary: SummaryResult = None,
    knowledge_graph: KnowledgeGraph = None,
    difficulty: DifficultyAnalysis = None,
    quiz: QuizResult = None,
    output_dir: str = "project",
) -> str:
    """生成完整的 PDF 分析报告

    Args:
        filename: PPT 文件名
        summary: 课程总结结果
        knowledge_graph: 知识图谱结果
        difficulty: 难点分析结果
        quiz: 练习题结果
        output_dir: 输出目录

    Returns:
        str: PDF 文件路径
    """
    os.makedirs(output_dir, exist_ok=True)

    base_name = os.path.splitext(os.path.basename(filename))[0]
    pdf_filename = f"{base_name}-总结分析.pdf"
    pdf_path = os.path.join(output_dir, pdf_filename)

    styles = _get_styles()
    story = []

    # ================================================================
    # 封面
    # ================================================================
    story.append(Spacer(1, 60))
    story.append(Paragraph("PPT 课程分析报告", styles["CoverTitle"]))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(
        width="40%", thickness=2, color=PRIMARY,
        spaceAfter=12, spaceBefore=0
    ))
    story.append(Paragraph(f"📄 {filename}", styles["CoverSubtitle"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        f"生成日期: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}",
        styles["CoverDate"]
    ))
    story.append(Spacer(1, 30))

    # 统计摘要卡片
    stats = []
    if summary:
        stats.append(("📝", str(len(summary.key_points)), "关键要点"))
    if knowledge_graph:
        stats.append(("🧠", str(len(knowledge_graph.nodes)), "知识点"))
        stats.append(("🔗", str(len(knowledge_graph.relationships)), "概念关系"))
    if difficulty:
        stats.append(("🎯", str(len(difficulty.difficult_concepts)), "难点分析"))
    if quiz:
        stats.append(("✏️", str(len(quiz.questions)), "练习题"))

    if stats:
        # 每行 3 个
        stat_rows = []
        row = []
        for i, (icon, num, label) in enumerate(stats):
            cell = [
                [Paragraph(f"{icon}", styles["CoverStat"])],
                [Paragraph(num, styles["CoverStat"])],
                [Paragraph(label, styles["CoverStatLabel"])],
            ]
            cell_table = Table(cell, colWidths=[80])
            cell_table.setStyle(TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            row.append(cell_table)
            if len(row) == 3 or i == len(stats) - 1:
                # 补齐
                while len(row) < 3:
                    row.append(Table([[""]], colWidths=[80]))
                stat_rows.append(row)
                row = []

        stat_table = Table(stat_rows, colWidths=[120, 120, 120])
        stat_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
            ("LINEAFTER", (0, 0), (-2, -1), 0.5, BORDER),
        ]))
        story.append(stat_table)

    story.append(Spacer(1, 30))

    # 功能列表
    features = [
        "📝  课程总结 — 提炼核心内容与关键要点",
        "🧠  知识图谱 — 梳理知识点与概念关系",
        "🎯  难点分析 — 识别学习难点与前置知识",
        "✏️  练习题 — 巩固学习效果与自我检测",
    ]
    for f in features:
        story.append(Paragraph(f, styles["CoverFeature"]))

    story.append(PageBreak())

    # ================================================================
    # 课程总结
    # ================================================================
    if summary:
        story.extend(_make_section_header("📝 课程总结", styles))

        # 概述
        story.append(Paragraph("课程概述", styles["SubTitle"]))
        story.append(Paragraph(summary.overview, styles["BodyTextCN"]))
        story.append(Spacer(1, 6))

        # 关键要点（用表格展示）
        if summary.key_points:
            story.append(Paragraph("关键要点", styles["SubTitle"]))
            kp_data = []
            for i, kp in enumerate(summary.key_points, 1):
                kp_data.append([
                    Paragraph(f"<b>{i}.</b>", styles["KeyText"]),
                    Paragraph(kp, styles["ValueText"]),
                ])
            kp_table = Table(kp_data, colWidths=[25, 365])
            kp_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LINEBELOW", (0, 0), (-1, -2), 0.5, BORDER),
                ("LINEBELOW", (0, -1), (-1, -1), 0, WHITE),
                ("BACKGROUND", (0, 0), (0, -1), PRIMARY_LIGHT),
            ]))
            story.append(kp_table)

        # 章节总结
        if summary.chapter_summaries:
            story.append(Spacer(1, 6))
            story.append(Paragraph("章节总结", styles["SubTitle"]))
            for ch in summary.chapter_summaries:
                chapter_name = ch.get("chapter", "")
                chapter_summary = ch.get("summary", "")
                # 章节标题卡片
                ch_data = [
                    [Paragraph(f"📖 {chapter_name}", styles["SubTitle2"])],
                    [Paragraph(chapter_summary, styles["BodyTextCN"])],
                ]
                ch_table = Table(ch_data, colWidths=[390])
                ch_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (0, 0), PRIMARY_LIGHT),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
                    ("LINEBELOW", (0, 0), (0, 0), 1, PRIMARY),
                ]))
                story.append(ch_table)
                story.append(Spacer(1, 4))

        story.append(PageBreak())

    # ================================================================
    # 知识图谱
    # ================================================================
    if knowledge_graph:
        story.extend(_make_section_header("🧠 知识图谱", styles))

        # 统计概览
        high = sum(1 for n in knowledge_graph.nodes if n.importance == "high")
        medium = sum(1 for n in knowledge_graph.nodes if n.importance == "medium")
        low = sum(1 for n in knowledge_graph.nodes if n.importance == "low")

        overview_data = [
            [Paragraph("<b>统计项</b>", styles["KeyText"]),
             Paragraph("<b>数量</b>", styles["KeyText"])],
            [Paragraph("知识点总数", styles["ValueText"]),
             Paragraph(str(len(knowledge_graph.nodes)), styles["ValueText"])],
            [Paragraph("概念关系", styles["ValueText"]),
             Paragraph(str(len(knowledge_graph.relationships)), styles["ValueText"])],
            [Paragraph("核心知识点 (高)", styles["ValueText"]),
             Paragraph(str(high), styles["ValueText"])],
            [Paragraph("重要知识点 (中)", styles["ValueText"]),
             Paragraph(str(medium), styles["ValueText"])],
            [Paragraph("了解知识点 (低)", styles["ValueText"]),
             Paragraph(str(low), styles["ValueText"])],
        ]
        overview_table = Table(overview_data, colWidths=[120, 80])
        overview_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
            ("LINEBELOW", (0, 0), (-1, 0), 1, PRIMARY),
        ]))
        story.append(overview_table)
        story.append(Spacer(1, 8))

        # 按重要程度分组展示
        importance_groups = [
            ("high", "⭐ 核心知识点", PRIMARY_LIGHT),
            ("medium", "📌 重要知识点", LIGHT_GRAY),
            ("low", "📖 了解知识点", WHITE),
        ]

        for imp_level, group_title, bg_color in importance_groups:
            nodes = [n for n in knowledge_graph.nodes if n.importance == imp_level]
            if not nodes:
                continue

            story.append(Paragraph(group_title, styles["SubTitle"]))
            for n in nodes:
                related = ""
                if n.related_concepts:
                    related = f"相关概念: {', '.join(n.related_concepts)}"

                node_data = [
                    [Paragraph(f"<b>{n.name}</b>", styles["KeyText"]),
                     Paragraph(n.description, styles["ValueText"])],
                ]
                if related:
                    node_data.append([
                        Paragraph("", styles["SmallText"]),
                        Paragraph(related, styles["SmallText"]),
                    ])

                node_table = Table(node_data, colWidths=[90, 300])
                node_table.setStyle(TableStyle([
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
                    ("BACKGROUND", (0, 0), (0, 0), bg_color),
                ]))
                story.append(node_table)
                story.append(Spacer(1, 3))

        # 概念关系
        if knowledge_graph.relationships:
            story.append(Spacer(1, 4))
            story.append(Paragraph("🔗 概念关系", styles["SubTitle"]))
            rel_data = [[
                Paragraph("<b>源概念</b>", styles["KeyText"]),
                Paragraph("<b>关系</b>", styles["KeyText"]),
                Paragraph("<b>目标概念</b>", styles["KeyText"]),
            ]]
            for rel in knowledge_graph.relationships[:30]:
                rel_data.append([
                    Paragraph(rel.get("source", ""), styles["ValueText"]),
                    Paragraph(f"→ {rel.get('relation', '')} →", styles["ValueText"]),
                    Paragraph(rel.get("target", ""), styles["ValueText"]),
                ])

            rel_table = Table(rel_data, colWidths=[100, 100, 100])
            rel_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("ALIGN", (1, 0), (1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
            ]))
            story.append(rel_table)

        story.append(PageBreak())

    # ================================================================
    # 难点分析
    # ================================================================
    if difficulty:
        story.extend(_make_section_header("🎯 难点分析", styles))

        if difficulty.difficult_concepts:
            story.append(Paragraph(
                f"共识别 <b>{len(difficulty.difficult_concepts)}</b> 个难点概念，"
                f"建议重点学习。",
                styles["BodyTextCN"]
            ))
            story.append(Spacer(1, 6))

            for i, dc in enumerate(difficulty.difficult_concepts, 1):
                concept_name = dc.get("concept", "")
                reason = dc.get("reason", "")
                suggestion = dc.get("suggestion", "")

                # 难点卡片
                card_data = [
                    [Paragraph(f"<b>{i}. {concept_name}</b>", styles["SubTitle2"])],
                ]
                if reason:
                    card_data.append([
                        Paragraph(f"<b>❓ 难点原因:</b> {reason}", styles["BodyTextCN"])
                    ])
                if suggestion:
                    card_data.append([
                        Paragraph(f"<b>💡 学习建议:</b> {suggestion}", styles["BodyTextCN"])
                    ])

                card_table = Table(card_data, colWidths=[390])
                card_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#FEF3C7")),  # 淡黄标题
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
                    ("LINEBELOW", (0, 0), (0, 0), 1, ACCENT),
                ]))
                story.append(card_table)
                story.append(Spacer(1, 6))

        # 前置知识要求
        if difficulty.prerequisites:
            story.append(Spacer(1, 4))
            story.append(Paragraph("📚 前置知识要求", styles["SubTitle"]))
            story.append(Paragraph(
                "学习本课程前，建议先掌握以下知识：",
                styles["BodyTextCN"]
            ))
            prereq_data = []
            for i, pr in enumerate(difficulty.prerequisites, 1):
                prereq_data.append([
                    Paragraph(f"<b>{i}.</b>", styles["KeyText"]),
                    Paragraph(pr, styles["ValueText"]),
                ])
            prereq_table = Table(prereq_data, colWidths=[25, 365])
            prereq_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LINEBELOW", (0, 0), (-1, -2), 0.5, BORDER),
                ("LINEBELOW", (0, -1), (-1, -1), 0, WHITE),
                ("BACKGROUND", (0, 0), (0, -1), LIGHT_GRAY),
            ]))
            story.append(prereq_table)

        story.append(PageBreak())

    # ================================================================
    # 练习题
    # ================================================================
    if quiz:
        story.extend(_make_section_header("✏️ 练习题", styles))
        story.append(Paragraph(quiz.title, styles["BodyTextCN"]))
        story.append(Spacer(1, 6))

        if quiz.questions:
            type_colors = {
                "choice": colors.HexColor("#10B981"),   # 绿色
                "fill": colors.HexColor("#8B5CF6"),     # 紫色
                "essay": colors.HexColor("#3B82F6"),    # 蓝色
            }
            type_names = {
                "choice": "选择题",
                "fill": "填空题",
                "essay": "问答题",
            }

            for i, q in enumerate(quiz.questions, 1):
                tag_color = type_colors.get(q.type, GRAY)
                tag_name = type_names.get(q.type, q.type)

                # 题目卡片
                q_data = []

                # 第一行：标签 + 题号
                tag = _make_tag(tag_name, tag_color, styles)
                header = [
                    tag,
                    Paragraph(f"第 {i} 题", styles["QuizQuestion"]),
                ]
                header_table = Table([header], colWidths=[60, 330])
                header_table.setStyle(TableStyle([
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (0, 0), 0),
                ]))
                q_data.append([header_table])

                # 题目内容
                q_data.append([Paragraph(q.question, styles["QuizQuestion"])])

                # 选项
                if q.options:
                    for opt in q.options:
                        q_data.append([Paragraph(opt, styles["QuizOption"])])

                # 答案和解析
                answer_text = f"✅ 参考答案: {q.answer}"
                q_data.append([Paragraph(answer_text, styles["QuizAnswer"])])

                if q.explanation:
                    q_data.append([
                        Paragraph(f"📖 解析: {q.explanation}", styles["QuizExplanation"])
                    ])

                q_table = Table(q_data, colWidths=[390])
                q_table.setStyle(TableStyle([
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
                    ("BACKGROUND", (0, 0), (0, 0), LIGHT_GRAY),
                    ("LINEBELOW", (0, 0), (0, 0), 1, tag_color),
                ]))
                story.append(q_table)
                story.append(Spacer(1, 8))
        else:
            story.append(Paragraph("（暂无练习题）", styles["BodyTextCN"]))

        story.append(PageBreak())

    # ================================================================
    # 封底 - 学习建议
    # ================================================================
    story.append(Spacer(1, 100))
    story.append(HRFlowable(
        width="60%", thickness=2, color=PRIMARY,
        spaceAfter=20, spaceBefore=0
    ))
    story.append(Paragraph("🎓 学习建议", styles["CoverTitle"]))
    story.append(Spacer(1, 10))

    tips = [
        "1. 先通读「课程总结」，把握整体知识框架",
        "2. 对照「知识图谱」，理清概念之间的关系",
        "3. 重点关注「难点分析」中的内容，针对性学习",
        "4. 完成「练习题」检验学习效果，查漏补缺",
        "5. 结合 PPT 原文，深入理解每个知识点",
    ]
    for tip in tips:
        story.append(Paragraph(tip, styles["CoverFeature"]))

    story.append(Spacer(1, 30))
    story.append(Paragraph(
        f"本报告由 PPT Analyse Agent 自动生成",
        styles["CoverDate"]
    ))
    story.append(Paragraph(
        f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        styles["CoverDate"]
    ))

    # ===== 生成 PDF =====
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        topMargin=25*mm,
        bottomMargin=20*mm,
        leftMargin=20*mm,
        rightMargin=20*mm,
        title=f"PPT 课程分析报告 - {filename}",
        author="PPT Analyse Agent",
    )

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return pdf_path
