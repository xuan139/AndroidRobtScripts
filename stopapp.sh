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
