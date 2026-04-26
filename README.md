# 📊 PPT 分析 Agent Skill

> 帮助大学生分析 PPT 课件，智能生成学习笔记、知识图谱、练习题等

## ✨ 功能特性

### 📂 文件解析
- 支持 `.pptx` 和 `.pdf` 格式
- 提取每页幻灯片的标题、正文、备注
- 识别表格和图片
- 结构化输出，便于 AI 分析

### 🤖 AI 智能分析
| 功能 | 说明 |
|------|------|
| 📝 **课程总结** | 生成课程概述、关键要点、章节总结 |
| 🧠 **知识图谱** | 提取核心知识点，标注重要程度，分析概念关联 |
| 🎯 **难点分析** | 识别学习难点，分析原因，给出学习建议 |
| ✏️ **练习题生成** | 自动生成选择题、填空题、简答题 |
| 💬 **智能问答** | 基于 PPT 内容回答学生问题 |

### 🔌 多种接入方式
- **RESTful API** - 标准 HTTP 接口，方便集成
- **MCP Server** - 对接 Claude Desktop 等 AI 助手

## 🚀 快速开始

### 1️⃣ 安装

```bash
# 克隆项目
git clone https://github.com/Wwox-w/ppt-analyse.git
cd ppt-analyse

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -e ".[dev]"
```

### 2️⃣ 配置

复制 `.env.example` 为 `.env`，填入你的 API 信息：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# LLM API 配置（兼容 OpenAI API 格式）
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o

# 服务配置
HOST=0.0.0.0
PORT=8000
```

> 💡 支持任何兼容 OpenAI API 格式的服务，如：
> - OpenAI (GPT-4o, GPT-4)
> - DeepSeek
> - 通义千问
> - 本地部署的 vLLM / Ollama

### 3️⃣ 启动服务

**方式一：一键启动（推荐）**

```bash
./start.sh
```

**方式二：手动启动**

```bash
source .venv/bin/activate
python -m src.main
```

### 4️⃣ 打开网页

启动后，在浏览器打开：

👉 **http://localhost:8000**

你会看到 AI 教授的对话界面，上传 PPT 即可开始学习！

> 📚 也可以访问 http://localhost:8000/docs 查看 API 文档


### 4. 使用示例

#### 上传文件

```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@/path/to/your/course.pptx"
```

#### 生成课程总结

```bash
curl -X POST http://localhost:8000/summarize \
  -F "filepath=./uploads/xxx.pptx" \
  -F "language=zh" \
  -F "detail=detailed"
```

#### 智能问答

```bash
curl -X POST http://localhost:8000/ask \
  -F "filepath=./uploads/xxx.pptx" \
  -F "question=请解释一下第三章的核心概念"
```

## 🎓 交互式学习 Agent（推荐）

> 像 AI 助教一样，带着你一步步学习 PPT 课件内容。

### 学习流程

```
1. 上传 PPT → 2. 开始学习（生成概览） → 3. 逐页学习 → 4. 提问互动 → 5. 生成笔记 → 6. 做练习题
```

### API 端点

| 端点 | 功能 | 说明 |
|------|------|------|
| `POST /learn/start` | 🎓 开始学习 | 解析 PPT，生成课程概览 |
| `POST /learn/next` | 📖 下一页 | AI 讲解当前页内容 |
| `POST /learn/prev` | 🔙 上一页 | 回到上一页 |
| `POST /learn/goto` | 🔢 跳转页 | 跳到指定页码 |
| `POST /learn/ask` | 💬 提问 | 基于 PPT 内容问答 |
| `POST /learn/notes` | 📝 生成笔记 | 生成课程笔记 |
| `POST /learn/quiz` | ✏️ 练习题 | 生成练习题 |
| `POST /learn/progress` | 📊 进度 | 查看学习进度 |

### 使用示例

```bash
# 1. 上传 PPT
curl -X POST http://localhost:8000/upload \
  -F "file=@course.pptx"

# 2. 开始学习（返回课程概览）
curl -X POST http://localhost:8000/learn/start \
  -F "filepath=./uploads/xxx.pptx" \
  -F "language=zh"

# 3. 学习下一页（AI 讲解）
curl -X POST http://localhost:8000/learn/next \
  -F "filepath=./uploads/xxx.pptx"

# 4. 提问
curl -X POST http://localhost:8000/learn/ask \
  -F "filepath=./uploads/xxx.pptx" \
  -F "question=能举个生活中的例子吗？"

# 5. 生成笔记
curl -X POST http://localhost:8000/learn/notes \
  -F "filepath=./uploads/xxx.pptx"

# 6. 生成练习题
curl -X POST http://localhost:8000/learn/quiz \
  -F "filepath=./uploads/xxx.pptx" \
  -F "num_questions=5"

# 7. 查看进度
curl -X POST http://localhost:8000/learn/progress \
  -F "filepath=./uploads/xxx.pptx"
```

### 返回格式

每次学习步骤返回：

```json
{
  "step_type": "overview | slide | qa | summary | quiz | done",
  "title": "📖 第 3 页: CPU 结构",
  "content": "AI 讲解内容（Markdown 格式）...",
  "slide_number": 3,
  "total_slides": 31,
  "progress": 10,
  "extra": {}
}
```

## 🔌 MCP Server 使用

### 启动 MCP Server

```bash
source .venv/bin/activate
python -m src.mcp_server
```

### 在 Claude Desktop 中配置

编辑 Claude Desktop 的配置文件 `claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "ppt-analyse": {
      "command": "python",
      "args": ["-m", "src.mcp_server"],
      "env": {
        "LLM_API_KEY": "your_api_key_here",
        "LLM_BASE_URL": "https://api.openai.com/v1",
        "LLM_MODEL": "gpt-4o"
      }
    }
  }
}
```

### MCP 工具列表

| 工具名 | 说明 | 是否调 LLM |
|--------|------|-----------|
| `parse_ppt` | 解析 PPT/PDF，返回每页文本内容 | ❌ 免费 |
| `analyze_ppt` | 综合分析（总结+知识图谱+难点+练习题） | ✅ |
| `ask_question` | 基于 PPT 内容问答 | ✅ |
| `generate_notes` | 生成课程笔记 | ✅ |
| `generate_quiz` | 生成练习题 | ✅ |
| `export_pdf_report` | 将分析结果导出为 PDF 文件 | ❌ 免费 |
| `get_token_usage` | 查看 Token 消耗统计 | ❌ 免费 |

### 使用流程示例

```
1. parse_ppt → 查看 PPT 内容（免费）
2. analyze_ppt → LLM 分析（消耗 Token）
3. export_pdf_report → 导出 PDF 报告（免费）
4. get_token_usage → 查看 Token 消耗
```

## 🏗️ 项目结构

```
ppt-analyse/
├── pyproject.toml          # 项目配置
├── .env.example            # 环境变量模板
├── README.md               # 使用文档
├── src/
│   ├── main.py             # FastAPI 入口
│   ├── mcp_server.py       # MCP Server
│   ├── config.py           # 配置管理
│   ├── parser/
│   │   ├── pptx_parser.py  # PPTX 解析
│   │   └── pdf_parser.py   # PDF 解析
│   ├── analyzer/
│   │   ├── llm_client.py   # LLM API 客户端
│   │   ├── summarizer.py   # 课程总结
│   │   ├── knowledge.py    # 知识图谱
│   │   ├── difficulty.py   # 难点分析
│   │   ├── quiz.py         # 练习题生成
│   │   └── qa.py           # 智能问答
│   └── models/
│       └── schemas.py      # 数据模型
├── tests/
│   ├── test_parser.py      # 解析器测试
│   └── test_api.py         # API 测试
└── examples/               # 示例文件
```

## 🧪 运行测试

```bash
source .venv/bin/activate
python -m pytest tests/ -v
```

## 📋 开发计划

- [x] PPT/PDF 文件解析
- [x] 课程内容总结
- [x] 知识图谱提取
- [x] 难点分析
- [x] 练习题生成
- [x] 智能问答
- [x] RESTful API
- [x] MCP Server
- [ ] 思维导图生成
- [ ] 多轮对话上下文管理
- [ ] 对比分析多份 PPT
- [ ] Web 管理界面

## 📄 许可证

MIT
