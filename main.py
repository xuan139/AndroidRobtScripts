from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import base64
import os
import uuid
import openai
from dotenv import load_dotenv


# 加载 .env 文件
load_dotenv()

# 获取 API key
api_key = os.getenv("OPENAI_API_KEY")

print (api_key)
# 创建 openai 客户端
client = openai.OpenAI(api_key=api_key)


app = FastAPI()

# 加 CORS 中间件，解决 405 错误
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有前端访问，开发方便
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 提供静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/static/js", StaticFiles(directory="static/js"), name="js")
app.mount("/static/css", StaticFiles(directory="static/css"), name="css")
app.mount("/static/db", StaticFiles(directory="static/db"), name="db")
app.mount("/static/images", StaticFiles(directory="static/images"), name="images")
app.mount("/static/uploads", StaticFiles(directory="static/uploads"), name="uploads")

@app.get("/", response_class=HTMLResponse)
def read_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), status_code=200)


@app.get("/backend", response_class=HTMLResponse)
def read_backend():
    with open("static/backend.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), status_code=200)

# 上传录音 base64
@app.post("/upload-audio-base64")
async def upload_audio_base64(request: Request):
    data = await request.json()
    base64_audio = data.get("file")

    if not base64_audio:
        return JSONResponse(content={"error": "No file provided"}, status_code=400)

    # 处理 base64 字符串（去掉前缀）
    if base64_audio.startswith("data:audio/wav;base64,"):
        base64_audio = base64_audio.replace("data:audio/wav;base64,", "")

    # 解码 base64
    try:
        audio_data = base64.b64decode(base64_audio)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)

    # 保存到文件
    save_path = "static/uploads"
    os.makedirs(save_path, exist_ok=True)

    # 使用 uuid 生成唯一的文件名
    file_name = f"{uuid.uuid4()}.wav"  # 生成一个唯一的文件名
    file_path = os.path.join(save_path, file_name)
    # file_path = os.path.join(save_path, "uploaded_audio.wav")
    
    with open(file_path, "wb") as f:
        f.write(audio_data)


 # Whisper 转录
   # Step 1: Whisper 识别语音
    try:
        with open(file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )

        print('transcript',transcript)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Whisper error: {str(e)}"})

    # ChatGPT 回复
    chat_response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{
            "role": "user",
            "content": transcript
        }]
    )
    gpt_reply = chat_response.choices[0].message.content
    print('gpt_reply',gpt_reply)
    # TTS 语音合成
    # tts = gTTS(text=gpt_reply, lang="zh")
    # tts_path = os.path.join(RESPONSE_DIR, f"{file_id}.mp3")
    # tts.save(tts_path)

    # 返回识别文本和语音路径
    return {
        "transcript": transcript,
        "gpt_reply": gpt_reply
        # "tts_audio_url": f"/responses/{file_id}.mp3"
    }

