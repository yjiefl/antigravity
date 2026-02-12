from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
import shutil
import re
from pathlib import Path
from pydub import AudioSegment
from openai import OpenAI
from dotenv import load_dotenv
from faster_whisper import WhisperModel
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI()

# 进度存储
progress_store = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/status")
async def get_status():
    return {
        "openai": bool(os.getenv("OPENAI_API_KEY")),
        "groq": bool(os.getenv("GROQ_API_KEY")),
        "local_available": True # Assuming dependencies are installed
    }

MAX_FILE_SIZE_MB = 25

CHUNK_LENGTH_MS = 10 * 60 * 1000 

# Global local model instance (lazy loaded)
local_model = None

def get_local_model():
    global local_model
    if local_model is None:
        print("Loading local Whisper model (small)...")
        # Use 'small' model by default for balance of speed/accuracy on CPU
        # If GPU available, it will use it automatically if device="auto"
        try:
            local_model = WhisperModel("small", device="auto", compute_type="int8")
        except Exception as e:
            print(f"Error loading local model: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to load local model: {str(e)}")
    return local_model

def adjust_srt_timestamps(srt_content: str, offset_ms: int) -> str:
    def replace_time(match):
        h, m, s, ms = int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4))
        total_ms = (h * 3600000) + (m * 60000) + (s * 1000) + ms + offset_ms
        new_h = total_ms // 3600000
        total_ms %= 3600000
        new_m = total_ms // 60000
        total_ms %= 60000
        new_s = total_ms // 1000
        new_ms = total_ms % 1000
        return f"{new_h:02}:{new_m:02}:{new_s:02},{new_ms:03}"
    pattern = re.compile(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})")
    return pattern.sub(replace_time, srt_content)

def format_timestamp(seconds: float) -> str:
    """Formats seconds into SRT timestamp format 00:00:00,000"""
    whole_seconds = int(seconds)
    milliseconds = int((seconds - whole_seconds) * 1000)
    
    hours = whole_seconds // 3600
    minutes = (whole_seconds % 3600) // 60
    seconds = whole_seconds % 60
    
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"


def local_transcribe(audio_path):
    model = get_local_model()
    segments, info = model.transcribe(audio_path, beam_size=5, language="zh")
    
    srt_output = []
    for i, segment in enumerate(segments, start=1):
        start = format_timestamp(segment.start)
        end = format_timestamp(segment.end)
        text = segment.text.strip()
        srt_output.append(f"{i}\n{start} --> {end}\n{text}\n")
    
    return "\n".join(srt_output)


@app.get("/progress/{task_id}")
async def get_progress(task_id: str):
    return progress_store.get(task_id, {"status": "waiting", "percent": 0})

@app.get("/logs")
async def get_logs():
    log_path = Path(__file__).parent.parent / "backend.log"
    if log_path.exists():
        with open(log_path, "r") as f:
            # 返回最后 100 行日志
            lines = f.readlines()
            return {"logs": "".join(lines[-100:])}
    return {"logs": "暂无日志"}

@app.post("/logs/clear")
async def clear_logs():
    log_path = Path(__file__).parent.parent / "backend.log"
    if log_path.exists():
        with open(log_path, "w") as f:
            f.write(f"--- 日志已于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 清空 ---\n")
    return {"status": "ok"}

def safe_api_transcription(client, model_name, audio_path, response_format="srt", retries=3):
    """带重试机制的 API 调用"""
    last_error = None
    for attempt in range(retries):
        try:
            with open(audio_path, "rb") as audio_file:
                return client.audio.transcriptions.create(
                    model=model_name, 
                    file=audio_file, 
                    response_format=response_format,
                    language="zh"
                )
        except Exception as e:
            last_error = e
            logger.warning(f"API 调用失败 (第 {attempt+1} 次尝试): {str(e)}")
            import time
            time.sleep(2 * (attempt + 1)) # 指数退避
    raise last_error


@app.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    provider: str = Form("openai"), # openai, groq, local
    api_key: str = Form(None),
    task_id: str = Form(None)
):
    if task_id:
        progress_store[task_id] = {"status": "正在初始化...", "percent": 0}

    temp_path = f"temp_{file.filename}"
    compressed_path = f"compressed_{file.filename}.mp3"
    
    print(f"Provider: {provider}")

    print(f"DEBUG: Processing request for provider='{provider}'")

    # Set up client based on provider
    client = None
    timeout = 60.0 # 60 seconds timeout
    
    if provider == "openai":
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            return JSONResponse(status_code=400, content={"error": "Missing OpenAI API Key"})
        client = OpenAI(api_key=key, timeout=timeout)
        model_name = "whisper-1"
    
    elif provider == "groq":
        key = api_key or os.getenv("GROQ_API_KEY")
        if not key:
            return JSONResponse(status_code=400, content={"error": "Missing Groq API Key"})
        client = OpenAI(
            api_key=key,
            base_url="https://api.groq.com/openai/v1",
            timeout=timeout
        )
        model_name = "whisper-large-v3"

    elif provider == "volcengine":
        key = api_key or os.getenv("VOLC_API_KEY")
        if not key:
            return JSONResponse(status_code=400, content={"error": "Missing Volcano Engine API Key"})
        client = OpenAI(
            api_key=key,
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            timeout=timeout
        )
        # For VolcArk, the 'model' is actually the Endpoint ID
        model_name = model or os.getenv("VOLC_ENDPOINT_ID")
        if not model_name:
            return JSONResponse(status_code=400, content={"error": "Missing Volcano Engine Endpoint ID (model)"})

    elif provider == "local":
        pass # Client setup handled in transcription logic
    
    else:
        return JSONResponse(status_code=400, content={"error": "Invalid provider"})

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Local transcription handling
        if provider == "local":
            try:
                if task_id: progress_store[task_id] = {"status": "本地模型正在转写中...", "percent": 20}
                # Local whisper handles large files automatically usually, but let's just feed it directly.
                # faster-whisper handles VAD and segmentation internally.
                print("Starting local transcription...")
                full_srt = local_transcribe(temp_path)
                if task_id: progress_store[task_id] = {"status": "完成!", "percent": 100}
                return {"filename": file.filename, "srt": full_srt}
            except Exception as e:
                # Cleanup
                if os.path.exists(temp_path): os.remove(temp_path)
                return JSONResponse(status_code=500, content={"error": f"Local transcription failed: {str(e)}"})

        # Remote API handling (OpenAI / Groq)
        # -----------------------------------
        file_size_mb = os.path.getsize(temp_path) / (1024 * 1024)
        print(f"Uploaded file size: {file_size_mb:.2f} MB")
        
        final_srt_parts = []
        target_file_path = temp_path

        # Compression logic if too big for API
        if file_size_mb > MAX_FILE_SIZE_MB:
            logger.info("File > 25MB. Compressing to MP3 32k mono...")
            if task_id: progress_store[task_id] = {"status": "文件较大，正在压缩以适配 API 限制...", "percent": 10}
            audio = AudioSegment.from_file(temp_path)
            audio.export(compressed_path, format="mp3", bitrate="32k", parameters=["-ac", "1"])
            comp_size = os.path.getsize(compressed_path) / (1024 * 1024)
            
            if comp_size <= MAX_FILE_SIZE_MB:
                target_file_path = compressed_path
            if task_id: progress_store[task_id] = {"status": "压缩完成，准备发送...", "percent": 20}
            
        current_size = os.path.getsize(target_file_path) / (1024 * 1024)
        
        if current_size <= MAX_FILE_SIZE_MB:
             logger.info(f"File size {current_size:.2f}MB is within limit. Sending to API...")
             with open(target_file_path, "rb") as audio_file:
                if provider == "groq":
                    logger.info("Using Groq API...")
                    # Groq verbose_json for headers
                    transcript = safe_api_transcription(client, model_name, target_file_path, response_format="verbose_json")
                    
                    # Convert object segments to SRT string
                    srt_combined = ""
                    for j, segment in enumerate(transcript.segments, start=1):
                        start = format_timestamp(segment.start)
                        end = format_timestamp(segment.end)
                        text = segment.text.strip()
                        srt_combined += f"{j}\n{start} --> {end}\n{text}\n\n"
                    transcript = srt_combined

                else:
                    logger.info("Using OpenAI API...")
                    transcript = safe_api_transcription(client, model_name, target_file_path, response_format="srt")

                final_srt_parts.append(transcript)
        else:
            logger.info(f"File size {current_size:.2f}MB > {MAX_FILE_SIZE_MB}MB. Splitting into chunks...")
            if task_id: progress_store[task_id] = {"status": "正在加载音频文件进行切片...", "percent": 25}
            logger.info("Loading audio with pydub (this may take a while for large files)...")
            audio = AudioSegment.from_file(temp_path)
            duration_ms = len(audio)
            logger.info(f"Audio duration: {duration_ms / 1000 / 60:.2f} minutes")
            
            chunk_count = (duration_ms + CHUNK_LENGTH_MS - 1) // CHUNK_LENGTH_MS
            for i_idx, start_ms in enumerate(range(0, duration_ms, CHUNK_LENGTH_MS)):
                current_percent = 30 + int((i_idx / chunk_count) * 60)
                status_msg = f"正在处理分段 {i_idx + 1}/{chunk_count}..."
                if task_id: progress_store[task_id] = {"status": status_msg, "percent": current_percent}
                
                logger.info(f"Processing chunk {i_idx + 1}/{chunk_count}...")
                chunk = audio[start_ms : start_ms + CHUNK_LENGTH_MS]
                chunk_filename = f"chunk_{start_ms}.mp3"
                chunk.export(chunk_filename, format="mp3", bitrate="32k")
                
                logger.info(f"Sending chunk {i_idx + 1} to API...")
                if provider == "groq":
                    response = safe_api_transcription(client, model_name, chunk_filename, response_format="verbose_json")
                    chunk_srt = ""
                    for k, segment in enumerate(response.segments, start=1):
                        start = format_timestamp(segment.start)
                        end = format_timestamp(segment.end)
                        text = segment.text.strip()
                        chunk_srt += f"{k}\n{start} --> {end}\n{text}\n\n"

                    transcript = chunk_srt
                else:
                    transcript = safe_api_transcription(client, model_name, chunk_filename, response_format="srt")

                
                adjusted_srt = adjust_srt_timestamps(transcript, start_ms)
                final_srt_parts.append(adjusted_srt)
                
                if os.path.exists(chunk_filename):
                    os.remove(chunk_filename)
                logger.info(f"Chunk {i_idx + 1} completed.")

        # Cleanup
        if os.path.exists(temp_path): os.remove(temp_path)
        if os.path.exists(compressed_path): os.remove(compressed_path)
        
        full_srt = "\n".join(final_srt_parts)
        if task_id: progress_store[task_id] = {"status": "完成!", "percent": 100}
        
        response_data = {"filename": file.filename, "srt": full_srt}
        if provider == "groq" and 'groq_headers' in locals():
            response_data["rate_limits"] = groq_headers
        
        return response_data


    except Exception as e:
        if os.path.exists(temp_path): os.remove(temp_path)
        if os.path.exists(compressed_path): os.remove(compressed_path)
        
        # Check if it's an APIError from OpenAI library which contains headers
        if hasattr(e, 'response') and hasattr(e.response, 'headers'):
             headers = e.response.headers
             remaining = headers.get('x-ratelimit-remaining-requests')
             reset = headers.get('x-ratelimit-reset-requests')
             # You could add these to the error response if useful
        
        return JSONResponse(status_code=500, content={"error": str(e)})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
