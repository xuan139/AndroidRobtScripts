#!/bin/bash

# 设置变量
VENV_PATH="./venv"
APP_MODULE="main:app"
HOST="0.0.0.0"
PORT="8000"
LOG_FILE="$HOME/server.log"

echo "我要强制重置本地并拉取最新代码..."
sudo git reset --hard HEAD
sudo git clean -fd
sudo git pull origin main

# 创建虚拟环境（如果不存在）
if [ ! -d "$VENV_PATH" ]; then
    echo "📁 未发现虚拟环境，正在创建..."
    python3 -m venv "$VENV_PATH"
    if [ $? -ne 0 ]; then
        echo "❌ 创建虚拟环境失败。请确保已安装 python3-venv。"
        exit 1
    fi
fi

# 激活虚拟环境
source "$VENV_PATH/bin/activate"

# 安装依赖
echo "📦 安装 requirements.txt 中的依赖..."
pip install --upgrade pip
pip install -r requirements.txt

# 启动 FastAPI 应用（后台）
echo "🚀 启动 FastAPI 应用..."
nohup uvicorn "$APP_MODULE" --host "$HOST" --port "$PORT" > "$LOG_FILE" 2>&1 &

echo "✅ FastAPI 正在运行于 http://$HOST:$PORT/"
echo "📄 日志保存在 $LOG_FILE"
