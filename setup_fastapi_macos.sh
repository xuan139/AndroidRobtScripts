#!/bin/bash

# 打印脚本开始信息
echo "Starting FastAPI setup on macOS..."

# Step 1: 检查并安装 Homebrew
echo "Checking and installing Homebrew..."
if ! command -v brew &> /dev/null; then
    echo "Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo "Homebrew already installed."
fi

# Step 2: 安装 Python3（通过 Homebrew）
echo "Installing Python3..."
brew install python3

# 检查 Python3 是否安装成功
if ! command -v python3 &> /dev/null; then
    echo "Python3 installation failed! Exiting."
    exit 1
fi

# Step 3: 使用当前工作目录作为项目目录
# echo "Using current directory as project directory..."
# PROJECT_DIR=$(pwd)
# echo "Project directory set to: $PROJECT_DIR"

# Step 3 : 执行另一个 Bash 文件
echo "Executing additional script..."
bash ./create_fastapi_structure.sh

# Step 4: 创建名为 fast_api 的虚拟环境
echo "Creating virtual environment named 'fast_api'..."
python3 -m venv fast_api

# Step 5: 激活虚拟环境
echo "Activating virtual environment..."
source fast_api/bin/activate

# Step 6: 升级 pip 并安装 FastAPI 和 Uvicorn
echo "Upgrading pip and installing FastAPI and Uvicorn..."
pip install --upgrade pip
pip install fastapi uvicorn

# 检查安装是否成功
if [ $? -eq 0 ]; then
    echo "FastAPI and Uvicorn installed successfully!"
else
    echo "Failed to install FastAPI or Uvicorn."
    deactivate
    exit 1
fi

source fast_api/bin/activate  # 确保进入虚拟环境

nohup uvicorn main:app --host 0.0.0.0 --port 8000 > fastapi.log 2>&1 &

# uvicorn main:app --host 0.0.0.0 --port 8000 --reload
