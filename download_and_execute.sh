#!/bin/bash

# 定义要下载的文件列表
FILES=(
    "create_fastapi_structure.sh"
    "setup_fastapi_crud.sh"
    "setup_fastapi_macos.sh"
)

# GitHub 仓库的基础 URL
BASE_URL="https://raw.githubusercontent.com/xuan139/AndroidRobtScripts/main"

# 下载标志
ALL_DOWNLOADED=true

# Step 1: 下载所有文件
for FILE in "${FILES[@]}"; do
    echo "Downloading $FILE from GitHub..."
    curl -o $FILE $BASE_URL/$FILE

    # 检查下载是否成功
    if [ $? -eq 0 ]; then
        echo "$FILE downloaded successfully!"
        chmod +x $FILE  # 赋予可执行权限
    else
        echo "Failed to download $FILE."
        ALL_DOWNLOADED=false
    fi
done

# 检查是否所有文件都下载成功
if [ "$ALL_DOWNLOADED" = false ]; then
    echo "One or more files failed to download. Exiting."
    exit 1
fi

# Step 2: 执行 setup_fastapi_macos.sh
echo "Executing setup_fastapi_macos.sh..."
./setup_fastapi_macos.sh

# 检查执行是否成功
if [ $? -eq 0 ]; then
    echo "setup_fastapi_macos.sh executed successfully!"
else
    echo "Failed to execute setup_fastapi_macos.sh."
    exit 1
fi
