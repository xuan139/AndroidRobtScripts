#!/bin/bash

# 定义 GitHub 文件 URL
SETUP_SCRIPT_URL="https://raw.githubusercontent.com/xuan139/AndroidRobtScripts/main/setup_fastapi_macos.sh"

# Step 1: 下载 setup_fastapi_macos.sh
echo "Downloading setup_fastapi_macos.sh from GitHub..."
curl -o setup_fastapi_macos.sh $SETUP_SCRIPT_URL

# 检查下载是否成功
if [ $? -eq 0 ]; then
    echo "setup_fastapi_macos.sh downloaded successfully!"
else
    echo "Failed to download setup_fastapi_macos.sh. Exiting."
    exit 1
fi

# Step 2: 赋予执行权限
echo "Granting execution permissions to setup_fastapi_macos.sh..."
chmod +x setup_fastapi_macos.sh

# Step 3: 执行脚本
echo "Executing setup_fastapi_macos.sh..."
./setup_fastapi_macos.sh

# 检查执行是否成功
if [ $? -eq 0 ]; then
    echo "Script executed successfully!"
else
    echo "Failed to execute setup_fastapi_macos.sh."
    exit 1
fi
