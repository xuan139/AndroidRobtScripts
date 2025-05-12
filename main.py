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
import time
from faster_whisper import WhisperModel
import time
import tempfile
import pyttsx3


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
        # print(gpt_reply)
        # 包装成标准格式返回
        return {
            "responses": [{"reply": gpt_reply}],
            "order": [],
            "user_preference": "",
            "note": "",
            "checkout": False
        }



def generate_tts_audio_url(reply_text):
    try:
        print("[INFO] 正在生成语音...")

        # 初始化引擎
        engine = pyttsx3.init()

        # voices = engine.getProperty('voices')
        # for voice in voices:
        #     print(f"Voice ID: {voice.id}, Name: {voice.name}")

        filename = "temp.wav"
        print(f"[INFO] 保存语音到文件: {filename}")
        
        # 尝试保存文件并捕获异常
        engine.save_to_file(reply_text, filename)
        engine.runAndWait()
        
        print("[INFO] 语音合成任务已启动")

        if not os.path.exists(filename):
            raise RuntimeError("语音文件未成功生成！")
        print("[INFO] 语音文件生成成功")

        with open(filename, "rb") as f:
            audio_data = f.read()
        print(f"[INFO] 读取音频文件，大小: {len(audio_data)} 字节")

        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        print(f"[INFO] Base64 编码完成，长度: {len(audio_base64)} 字符")

        os.remove(filename)
        print(f"[INFO] 已删除临时文件: {filename}")

        audio_url = f"data:audio/mp3;base64,{audio_base64}"
        print(f"[INFO] 生成的音频URL前50字符: {audio_url[:50]}...")

        return audio_url

    except Exception as e:
        print(f"[ERROR] 发生错误: {e}")
        return None

def split_text_by_word_limit(text, word_limit=20):
    words = text.split()
    segments = []
    
    # 按照每20个单词进行分段
    for i in range(0, len(words), word_limit):
        segments.append(' '.join(words[i:i + word_limit]))
    
    return segments

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
    audio_file.name = 'audio.mp3'  # 设置文件名

    start = time.perf_counter()
    # try:
    #     transcript = client.audio.transcriptions.create(
    #         model="whisper-1",
    #         file=audio_file,
    #         response_format="verbose_json"
    #     )

    #     end = time.perf_counter()
    #     print(f"🕒 Whisper 語音識別耗時: {end - start:.4f} 秒")

    #     print("新文本", transcript.text)
    #     print("新语言" , transcript.language)  
    # except Exception as e:
    #     return JSONResponse(content={"error": f"Whisper API error: {str(e)}"}, status_code=500)


        # 使用 tiny 模型（速度最快），可選 cpu 或 cuda
    model = WhisperModel("small", device="cuda", compute_type="float16") # 或 device="cuda" 使用 GPU

    start_time = time.time()

    # 将 BytesIO 写入临时文件
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp.write(audio_data)
        tmp.flush()
        audio_path = tmp.name  # 临时文件路径
        # 然后传给 transcribe
        segments, info = model.transcribe(audio_path)


    segments, info = model.transcribe(audio_path)
    segments = list(segments)  # 🔥 關鍵：materialize generator
    end_time = time.time()

    print(f"語言偵測結果：{info.language}")
    for segment in segments:
        print(f"[{segment.start:.2f}s - {segment.end:.2f}s]: {segment.text}")

    full_text = " ".join([segment.text for segment in segments])
    print("完整文本內容：", full_text)
    print(f"轉錄花費時間：{end_time - start_time:.2f} 秒")

    print("last_gpt_reply",last_gpt_reply)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "assistant", "content": last_transcript_text},
        {"role": "assistant", "content": last_transcript_language},
        {"role": "assistant", "content": last_gpt_reply},
        {"role": "user", "content": full_text}
    ]

    start = time.perf_counter()

    chat_response = client.chat.completions.create(
        model="gpt-4o",  
        messages=messages
    )

    end = time.perf_counter()
    print(f"🕒 ChatGPT 回應耗時: {end - start:.4f} 秒")
 
    # 示例用法
    gpt_reply = chat_response.choices[0].message.content 

    gpt_reply_data = process_gpt_reply(gpt_reply)
       # 获取各字段值
    responses = gpt_reply_data.get("responses", [])
    reply_text = responses[0].get("reply", "") if responses else ""
    # reply_text = "收到你的需求"
    print("reply_text",reply_text)

    start = time.perf_counter()
    chat_response_tts = client.audio.speech.create(
        model="tts-1",
        voice="nova",
        input=reply_text
    )

    end = time.perf_counter()
    print(f"🕒 ChatGPT tts 回应时间: {end - start:.4f} 秒")

        # 获取 TTS 合成的二进制音频内容
    audio_data = chat_response_tts.content  # 获取二进制内容
    audio_base64 = base64.b64encode(audio_data).decode('utf-8')
    audio_url = f"data:audio/mp3;base64,{audio_base64}"

    last_gpt_reply = gpt_reply
    # last_transcript = transcript
    # last_transcript_text = transcript.text
    # last_transcript_language = transcript.language
 
    return {
        "transcript": full_text,
        "language": info.language,
        "gpt_reply_data": gpt_reply_data,
        "tts_audio_url": audio_url
    }