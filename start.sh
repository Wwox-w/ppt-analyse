#!/bin/bash
# ============================================
# 🚀 PPT 分析 Agent - 一键启动脚本
# ============================================

echo "========================================"
echo "  🎓 AI 教授 - PPT 互动课堂"
echo "========================================"

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "📦 正在创建虚拟环境..."
    python3 -m venv .venv
fi

# 激活虚拟环境
source .venv/bin/activate

# 检查依赖
if ! python -c "import fastapi" 2>/dev/null; then
    echo "📦 正在安装依赖..."
    pip install -e ".[dev]" -q
fi

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "⚠️  未找到 .env 文件，正在从 .env.example 复制..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "📝 请编辑 .env 文件填入你的 API Key 后重新运行"
        exit 1
    else
        echo "❌ 未找到 .env.example 文件"
        exit 1
    fi
fi

echo ""
echo "🌐 启动服务..."
echo "   📖 网页界面: http://localhost:8000"
echo "   📚 API 文档: http://localhost:8000/docs"
echo ""

# 启动服务
python -m src.main
