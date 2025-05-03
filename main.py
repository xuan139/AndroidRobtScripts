from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import base64
import os
import uuid
import openai
from dotenv import load_dotenv
import json


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
app.mount("/responses", StaticFiles(directory="responses"), name="responses")

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


    # 读取 system prompt 文件内容
    with open("system_prompt.txt", "r", encoding="utf-8") as f:
        system_prompt = f.read()

    # 构建消息列表
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": transcript}
    ]

    chat_response = client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=messages
    )
    gpt_reply = chat_response.choices[0].message.content
    print('gpt_reply',gpt_reply)
    # TTS 语音合成
    # 进行 TTS 语音合成


    # 设置音频文件保存路径
    save_directory = "./responses"  # 使用相对路径保存到当前项目的 responses 文件夹
    audio_file_path = os.path.join(save_directory, "audio.mp3")  # 设置完整的文件路径

    # 确保目标目录存在
    os.makedirs(save_directory, exist_ok=True)  # 如果目录不存在，创建该目录


    chat_response_tts = client.audio.speech.create(
        model="tts-1",  # 使用最新的 TTS 模型
        voice="nova",  # 指定语音类型
        input=gpt_reply # GPT 的文本回复作为输入
    )

        # 获取 TTS 合成的二进制音频内容
    audio_data = chat_response_tts.content  # 获取二进制内容

    # 如果文件已存在，则先删除
    if os.path.exists(audio_file_path):
        os.remove(audio_file_path)

    # 然后再保存新音频文件
    with open(audio_file_path, "wb") as f:
        f.write(audio_data)

    
    # audio_url = f"127.0.0.1:8000/responses/{os.path.basename(audio_file_path)}"  # 获取文件名并生成 URL
    # print('Generated audio URL:', audio_url)


    audio_file_path = "responses/audio.mp3"
    audio_url = f"http://127.0.0.1:8000/responses/{os.path.basename(audio_file_path)}"

    # 返回识别文本和语音路径

    # 如果 gpt_reply 是有效的 JSON 字符串
    try:
        gpt_reply_json = json.loads(gpt_reply)  # 将字符串解析为 JSON 对象
    except json.JSONDecodeError:
        gpt_reply_json = None  # 如果解析失败，则设为 None

    return {
        "transcript": transcript,
        "gpt_reply": gpt_reply_json,
        "tts_audio_url": audio_url
    }



