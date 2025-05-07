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
        print("❌ 不是 JSON，转换成默认结构")
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
    global last_gpt_reply  # <== 这里声明用全局的
    # global last_transcript  # 告诉 Python 用全局的变量

    global last_transcript_text 
    global last_transcript_language 
        # 如果 last_gpt_reply 为 None，使用空字符串
    last_gpt_reply = last_gpt_reply if last_gpt_reply else ""
    # last_transcript = last_transcript if last_transcript else {}
    last_transcript_text = last_transcript_text if last_transcript_text else ""    
    last_transcript_language = last_transcript_language if last_transcript_language else ""
    # ---- 安全读取 last_transcript ----

    print("上一次语言：", getattr(last_transcript_language, 'language', '未知'))
    print("上一次文本：", last_transcript_text)
    reply_text = ""

    last_reply_text = last_reply_order = last_reply_user_preference = last_reply_note = "（无）"
    gpt_reply_dict = {}

    if last_gpt_reply and last_gpt_reply.strip():
        try:
            print(f"last_gpt_reply 内容为：{repr(last_gpt_reply)}")
            gpt_reply_dict = json.loads(last_gpt_reply)
            # 提取信息...
        except json.JSONDecodeError as e:
            print("解析 last_gpt_reply 出错:", e)
    else:
        print("last_gpt_reply 是空的或仅包含空白")

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

 
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "assistant", "content": last_transcript_text},
        {"role": "assistant", "content": last_gpt_reply},
        {"role": "user", "content": transcript.text}
    ]

    # print("messages",messages)

    chat_response = client.chat.completions.create(
        model="gpt-4",  # 使用 GPT-4 模型
        messages=messages
    )
    # gpt_reply = chat_response.choices[0].message.content



    # 示例用法
    gpt_reply = chat_response.choices[0].message.content 
    print("原始 gpt_reply:", repr(gpt_reply)) # 假设你已从聊天 API 获取了这个值
    gpt_reply_dict = process_gpt_reply(gpt_reply)
    reply_text = gpt_reply_dict.get("responses", [{}])[0].get("reply", "（無）")

    print("reply_text",reply_text)

    chat_response_tts = client.audio.speech.create(
        model="tts-1",
        voice="nova",
        input=reply_text
    )

        # 获取 TTS 合成的二进制音频内容
    audio_data = chat_response_tts.content  # 获取二进制内容

# 获取音频 URL 或保存音频内容
    # audio_url = chat_response_tts['url']
    # 使用 base64 编码将音频数据转换为 data URL
    audio_base64 = base64.b64encode(audio_data).decode('utf-8')
    # 创建一个可以在 HTML 中使用的 data URL
    audio_url = f"data:audio/mp3;base64,{audio_base64}"

    # try:
    #     gpt_reply_json = json.loads(gpt_reply)  # 将字符串解析为 JSON 对象
    # except json.JSONDecodeError:
    #     gpt_reply_json = None  # 如果解析失败，则设为 None

    last_gpt_reply = gpt_reply
    # last_transcript = transcript

    last_transcript_text = transcript.text
    last_transcript_language = transcript.language
    print("gpt_reply_json",gpt_reply_dict)
    return {
        "transcript": transcript.text,
        "language": transcript.language,
        "gpt_reply": gpt_reply_dict,
        "tts_audio_url": audio_url
    }



