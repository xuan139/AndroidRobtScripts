#!/bin/bash

# 项目名称
PROJECT_NAME="fastapi_project"

# 创建项目目录
echo "Creating FastAPI project structure..."
mkdir -p $PROJECT_NAME

# 创建主要目录和文件
echo "Setting up main application directories..."
mkdir -p $PROJECT_NAME/app/api
mkdir -p $PROJECT_NAME/app/models
mkdir -p $PROJECT_NAME/static/css
mkdir -p $PROJECT_NAME/static/js
mkdir -p $PROJECT_NAME/static/images
mkdir -p $PROJECT_NAME/templates
mkdir -p $PROJECT_NAME/uploaded_files

# 创建主要文件
echo "Generating initial files..."
cat <<EOL > $PROJECT_NAME/app/__init__.py
# FastAPI Application Package
EOL

cat <<EOL > $PROJECT_NAME/app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.requests import Request

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure Jinja2 templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "message": "Hello, FastAPI!"})
EOL

cat <<EOL > $PROJECT_NAME/app/api/endpoints.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/items/")
def get_items():
    return [{"item_id": 1, "name": "Sample Item"}]
EOL

cat <<EOL > $PROJECT_NAME/app/models/item.py
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    description: str
    price: float
    on_sale: bool
EOL

cat <<EOL > $PROJECT_NAME/static/css/style.css
/* Basic CSS styles for FastAPI project */
body {
    font-family: Arial, sans-serif;
    background-color: #f4f4f4;
    margin: 0;
    padding: 20px;
}
EOL

cat <<EOL > $PROJECT_NAME/static/js/app.js
// Basic JavaScript for FastAPI project
document.addEventListener("DOMContentLoaded", function () {
    console.log("FastAPI is awesome!");
});
EOL

cat <<EOL > $PROJECT_NAME/templates/index.html
<!DOCTYPE html>
<html>
<head>
    <title>FastAPI Project</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <h1>{{ message }}</h1>
    <script src="/static/js/app.js"></script>
</body>
</html>
EOL

cat <<EOL > $PROJECT_NAME/README.md
# FastAPI Project Structure

This is a recommended structure for FastAPI projects, including:
- Static files (CSS, JS, Images)
- Dynamic templates (HTML)
- Core application logic with FastAPI
EOL

echo "Project structure created successfully!"

