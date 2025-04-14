#!/bin/bash

echo "🚀 Starting FastAPI static site setup on macOS..."

# 1. 安装 Homebrew
echo "🔍 Checking Homebrew..."
if ! command -v brew &> /dev/null; then
    echo "📦 Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo "✅ Homebrew already installed."
fi

# 2. 安装 Python3
echo "🐍 Installing Python3..."
brew install python3

if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 installation failed!"
    exit 1
fi

# 3. 创建项目结构
echo "📁 Setting up project structure..."
mkdir -p app/static
cd app

# 4. 创建 index.html
cat <<EOF > static/index.html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>FastAPI Static Page</title>
</head>
<body>
    <h1>Hello from FastAPI + index.html 🎉</h1>
</body>
</html>
EOF

# 5. 创建 main.py
cat <<EOF > main.py
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

app = FastAPI()
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_index():
    html_path = Path(__file__).parent / "static" / "index.html"
    return html_path.read_text(encoding='utf-8')
EOF

cd ..

# 6. 创建虚拟环境
echo "🐍 Creating virtual environment 'fast_api'..."
python3 -m venv fast_api

# 7. 激活虚拟环境
echo "🧪 Activating virtual environment..."
source fast_api/bin/activate

# 8. 安装依赖
echo "⬆️ Upgrading pip and installing FastAPI + Uvicorn..."
pip install --upgrade pip
pip install fastapi uvicorn

if [ $? -ne 0 ]; then
    echo "❌ Failed to install FastAPI/Uvicorn"
    deactivate
    exit 1
fi

# 9. 启动服务
echo "🚀 Starting FastAPI server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
