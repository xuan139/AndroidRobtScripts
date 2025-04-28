from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

app = FastAPI()

# 提供静态文件目录
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/static/js", StaticFiles(directory="static/js"), name="js")
app.mount("/static/css", StaticFiles(directory="static/css"), name="css")
app.mount("/static/db", StaticFiles(directory="static/db"), name="db")
app.mount("/static/image", StaticFiles(directory="static/image"), name="image")

@app.get("/", response_class=HTMLResponse)
def read_index():
    with open("static/index.html", "r") as f:
        return HTMLResponse(content=f.read(), status_code=200)
