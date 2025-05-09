#!/bin/bash

echo "🔍 查找 uvicorn 进程..."
PID=$(ps aux | grep 'uvicorn main:app' | grep -v grep | awk '{print $2}')

if [ -z "$PID" ]; then
  echo "⚠️ 没有运行中的 uvicorn main:app 服务。"
else
  echo "🛑 停止进程 PID=$PID..."
  kill -9 "$PID"
  echo "✅ 已终止 FastAPI 服务。"
fi

# 设置变量
VENV_PATH="./venv"
APP_MODULE="main:app"
HOST="0.0.0.0"
PORT="8000"
LOG_FILE="$HOME/server.log"

echo "📥 强制重置并拉取最新代码..."
git fetch --all
git reset --hard origin/main
git clean -fd

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
