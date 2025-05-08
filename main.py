from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import base64
import os
import uuid
from dotenv import load_dotenv
import json
import io
import openai

from openai import OpenAI
# 加载 .env 文件
load_dotenv()

# 推荐用环境变量读取 API Key
api_key = os.getenv("OPENAI_API_KEY")

# 初始化 OpenAI 客户端
client = OpenAI(api_key=api_key)

last_gpt_reply = None
last_transcript_text = None
last_transcript_language = None
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
app.mount("/responses", StaticFiles(directory="responses"), name="responses")

def process_gpt_reply(gpt_reply):
    try:
        gpt_reply_dict = json.loads(gpt_reply)
        print("✅ 成功解析为 JSON")
        return gpt_reply_dict
    except json.JSONDecodeError:
        print(gpt_reply)
        # 包装成标准格式返回
        return {
            "responses": [{"reply": gpt_reply}],
            "order": [],
            "user_preference": "",
            "note": "",
            "checkout": False
        }



@app.on_event("startup")
async def load_system_prompt():
    global system_prompt
    with open("system_prompt.txt", "r", encoding="utf-8") as f:
        system_prompt = f.read()


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
    global last_gpt_reply 
    global last_transcript_text 
    global last_transcript_language 
        # 如果 last_gpt_reply 为 None，使用空字符串
    last_gpt_reply = last_gpt_reply if last_gpt_reply else ""
    last_transcript_text = last_transcript_text if last_transcript_text else ""    
    last_transcript_language = last_transcript_language if last_transcript_language else ""
    # ---- 安全读取 last_transcript ----

    print("上一次语言：", last_transcript_language)
    print("上一次文本：", last_transcript_text)
    reply_text = ""

    data = await request.json()
    base64_audio = data.get("file")

    if not base64_audio:
        return JSONResponse(content={"error": "No file provided"}, status_code=400)

    # 处理不同类型的音频格式前缀
    if base64_audio.startswith("data:audio/wav;base64,"):
        base64_audio = base64_audio.replace("data:audio/wav;base64,", "")
    elif base64_audio.startswith("data:audio/mp3;base64,"):
        base64_audio = base64_audio.replace("data:audio/mp3;base64,", "")
    elif base64_audio.startswith("data:audio/ogg;base64,"):
        base64_audio = base64_audio.replace("data:audio/ogg;base64,", "")
    else:
        return JSONResponse(content={"error": "Unsupported audio format"}, status_code=400)

    # 解码 base64 数据
    try:
        audio_data = base64.b64decode(base64_audio)
    except Exception as e:
        return JSONResponse(content={"error": f"Base64 decoding error: {str(e)}"}, status_code=400)

    audio_file = io.BytesIO(audio_data)
    audio_file.name = 'audio.wav'  # 设置文件名

    try:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json"
        )

        print("新文本", transcript.text)
        print("新语言" , transcript.language)  
    except Exception as e:
        return JSONResponse(content={"error": f"Whisper API error: {str(e)}"}, status_code=500)

    print("last_gpt_reply",last_gpt_reply)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "assistant", "content": last_transcript_text},
        {"role": "assistant", "content": last_transcript_language},
        {"role": "assistant", "content": last_gpt_reply},
        {"role": "user", "content": transcript.text}
    ]

    chat_response = client.chat.completions.create(
        model="gpt-4o",  
        messages=messages
    )
 
    # 示例用法
    gpt_reply = chat_response.choices[0].message.content 

    gpt_reply_data = process_gpt_reply(gpt_reply)
       # 获取各字段值
    responses = gpt_reply_data.get("responses", [])
    reply_text = responses[0].get("reply", "") if responses else ""
    print("reply_text",reply_text)

    chat_response_tts = client.audio.speech.create(
        model="tts-1",
        voice="nova",
        input=reply_text
    )

        # 获取 TTS 合成的二进制音频内容
    audio_data = chat_response_tts.content  # 获取二进制内容
    audio_base64 = base64.b64encode(audio_data).decode('utf-8')
    audio_url = f"data:audio/mp3;base64,{audio_base64}"

    last_gpt_reply = gpt_reply
    # last_transcript = transcript
    last_transcript_text = transcript.text
    last_transcript_language = transcript.language
 
    return {
        "transcript": transcript.text,
        "language": transcript.language,
        "gpt_reply_data": gpt_reply_data,
        "tts_audio_url": audio_url
    }