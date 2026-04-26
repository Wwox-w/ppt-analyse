"""PDF 文件解析器"""

import fitz  # PyMuPDF
from src.models.schemas import SlideContent, ParsedPPT


class PDFParser:
    """解析 PDF 文件（通常是从 PPT 导出的 PDF）"""

    def parse(self, filepath: str) -> ParsedPPT:
        """
        解析 PDF 文件

        Args:
            filepath: PDF 文件路径

        Returns:
            ParsedPPT: 解析后的结构化内容
        """
        doc = fitz.open(filepath)
        slides_content = []
        all_text_parts = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            page_data = self._parse_page(page, page_num + 1)
            slides_content.append(page_data)

            if page_data.title:
                all_text_parts.append(f"## 第{page_num + 1}页: {page_data.title}")
            else:
                all_text_parts.append(f"## 第{page_num + 1}页")
            if page_data.content:
                all_text_parts.append(page_data.content)

        doc.close()

        return ParsedPPT(
            filename=filepath.split("/")[-1],
            total_slides=len(slides_content),
            slides=slides_content,
            raw_text="\n\n".join(all_text_parts),
        )

    def _parse_page(self, page, page_num: int) -> SlideContent:
        """解析单页 PDF"""
        # 提取文本块（按位置分组）
        blocks = page.get_text("dict")["blocks"]
        text_parts = []
        title = ""

        for block in blocks:
            if block["type"] == 0:  # 文本块
                for line in block["lines"]:
                    line_text = ""
                    for span in line["spans"]:
                        line_text += span["text"]

                    if line_text.strip():
                        # 字体较大的可能是标题
                        font_size = line["spans"][0]["size"] if line["spans"] else 0
                        if font_size > 20 and not title:
                            title = line_text.strip()
                        else:
                            text_parts.append(line_text.strip())

            elif block["type"] == 1:  # 图片块
                pass  # PDF 中的图片暂时跳过

        return SlideContent(
            slide_number=page_num,
            title=title,
            content="\n".join(text_parts),
            notes="",
            has_tables=False,
            has_images=False,
        )


class ParserFactory:
    """解析器工厂"""

    @staticmethod
    def get_parser(filepath: str):
        """
        根据文件扩展名获取对应的解析器

        Args:
            filepath: 文件路径

        Returns:
            PPTXParser 或 PDFParser

        Raises:
            ValueError: 不支持的文件格式
        """
        if filepath.lower().endswith(".pptx"):
            from src.parser.pptx_parser import PPTXParser
            return PPTXParser()
        elif filepath.lower().endswith(".pdf"):
            return PDFParser()
        else:
            raise ValueError(f"不支持的文件格式: {filepath}，仅支持 .pptx 和 .pdf")
