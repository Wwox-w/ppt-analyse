# 🎓 AI 教授 - Skill 能力定义

## 概述

这是一个帮助大学生分析 PPT 课件、进行互动学习的 AI 教学助手。它能够解析 PPT/PDF 文件，以苏格拉底式启发教学法引导学生逐页学习，生成笔记和练习题，并回答学生的问题。

## 能力范围

### ✅ 能做

| 能力 | 说明 |
|------|------|
| 📂 **解析 PPT/PDF** | 读取 `.pptx` 和 `.pdf` 文件，提取文本内容 |
| 📖 **课程概览** | 生成课程简介、学习目标、内容结构 |
| 📄 **逐页讲解** | 一页一页讲解 PPT 内容，用例子帮助理解 |
| 💬 **智能问答** | 基于 PPT 内容回答学生问题 |
| 📝 **生成笔记** | 整理课程笔记，突出重点 |
| ✏️ **生成练习题** | 出选择题、填空题、简答题 |
| 📊 **导出 PDF 报告** | 将分析结果导出为 PDF 文件 |
| 🔍 **查看 Token 消耗** | 查看 LLM API 调用统计 |

### ❌ 不能做

| 能力 | 原因 |
|------|------|
| 🖼️ **识别图片内容** | 只提取文本，不分析图片/图表内容 |
| 🎬 **解析视频/音频** | 只支持 PPT 和 PDF 格式 |
| 🌐 **联网搜索** | 不访问外部网络，只基于上传的课件内容 |
| 👥 **多用户会话** | 不支持用户登录和会话管理 |
| 📱 **移动端推送** | 没有移动端 App |
| 🔄 **实时协作** | 不支持多人同时编辑 |
| 🗃️ **长期记忆** | 每次启动都是新的会话，不保存历史记录 |
| 🌍 **多语言翻译** | 只支持中文和英文 |

## 使用限制

### 文件限制
- **格式**: 仅 `.pptx` 和 `.pdf`
- **大小**: 最大 50MB
- **内容**: 只提取文本，不处理图片/图表

### API 限制
- 需要配置 LLM API Key（支持 OpenAI、DeepSeek、通义千问等）
- Token 消耗取决于课件长度和交互次数
- 免费功能（解析 PPT、导出 PDF）不消耗 Token

### 网络限制
- 服务运行在本地 `localhost:8000`
- 同一局域网内的设备可以访问（需使用本机 IP）
- 默认不支持公网访问（如需部署到公网需额外配置）

## 启动方式

```bash
# 一键启动
./start.sh

# 手动启动
source .venv/bin/activate
python -m src.main

# 关闭服务
./stop.sh
# 或 Ctrl+C
# 或 lsof -ti:8000 | xargs kill -9
```

## 项目结构

```
ppt-analyse/
├── start.sh              # 启动脚本
├── stop.sh               # 关闭脚本
├── agent.md              # Agent 行为规范
├── skill.md              # Skill 能力定义
├── .env                  # 环境变量（API Key 等）
├── frontend/             # 前端页面
│   ├── index.html        # 主页面
│   ├── style.css         # 样式
│   ├── app.js            # 交互逻辑
│   └── images/           # 图片资源
├── src/
│   ├── main.py           # FastAPI 入口
│   ├── mcp_server.py     # MCP Server
│   ├── config.py         # 配置管理
│   ├── parser/           # 文件解析
│   ├── analyzer/         # 分析模块
│   │   ├── socratic_tutor.py  # 苏格拉底式导师人格
│   │   ├── learning_agent.py  # 学习 Agent
│   │   ├── llm_client.py      # LLM API 客户端
│   │   ├── summarizer.py      # 课程总结
│   │   ├── knowledge.py       # 知识图谱
│   │   ├── difficulty.py      # 难点分析
│   │   ├── quiz.py            # 练习题生成
│   │   ├── qa.py              # 智能问答
│   │   └── pdf_generator.py   # PDF 导出
│   └── models/
│       └── schemas.py    # 数据模型
└── uploads/              # 上传文件存储
```

## 安全注意事项

1. **API Key 保护** — `.env` 文件不要提交到 Git
2. **文件清理** — `uploads/` 目录会积累上传的文件，建议定期清理
3. **端口占用** — 如果 8000 端口被占用，修改 `.env` 中的 `PORT` 配置
4. **不要以 root 运行** — 不要使用 `sudo` 启动服务
