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

load_dotenv()

app = FastAPI()

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


@app.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    provider: str = Form("openai"), # openai, groq, local
    api_key: str = Form(None)
):
    temp_path = f"temp_{file.filename}"
    compressed_path = f"compressed_{file.filename}.mp3"
    
    print(f"Provider: {provider}")

    print(f"DEBUG: Processing request for provider='{provider}'")

    # Set up client based on provider
    client = None
    if provider == "openai":

        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            return JSONResponse(status_code=400, content={"error": "Missing OpenAI API Key"})
        client = OpenAI(api_key=key)
        model_name = "whisper-1"
    
    elif provider == "groq":
        key = api_key or os.getenv("GROQ_API_KEY")
        if not key:
            return JSONResponse(status_code=400, content={"error": "Missing Groq API Key"})
        client = OpenAI(
            api_key=key,
            base_url="https://api.groq.com/openai/v1"
        )
        model_name = "whisper-large-v3" # Groq often uses this ID

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
                # Local whisper handles large files automatically usually, but let's just feed it directly.
                # faster-whisper handles VAD and segmentation internally.
                print("Starting local transcription...")
                full_srt = local_transcribe(temp_path)
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
            print("File > 25MB. Compressing to MP3 32k mono...")
            audio = AudioSegment.from_file(temp_path)
            audio.export(compressed_path, format="mp3", bitrate="32k", parameters=["-ac", "1"])
            comp_size = os.path.getsize(compressed_path) / (1024 * 1024)
            
            if comp_size <= MAX_FILE_SIZE_MB:
                target_file_path = compressed_path
            
        current_size = os.path.getsize(target_file_path) / (1024 * 1024)
        
        if current_size <= MAX_FILE_SIZE_MB:
             with open(target_file_path, "rb") as audio_file:
                if provider == "groq":
                    print("Groq path: Requesting verbose_json segments...")
                    # Use with_raw_response to access headers
                    raw_response = client.audio.transcriptions.with_raw_response.create(
                        model=model_name, 
                        file=audio_file, 
                        response_format="verbose_json",
                        language="zh"
                    )
                    response = raw_response.parse()
                    
                    # Capture rate limit headers
                    groq_headers = {
                        "x-ratelimit-limit-requests": raw_response.headers.get("x-ratelimit-limit-requests"),
                        "x-ratelimit-limit-tokens": raw_response.headers.get("x-ratelimit-limit-tokens"),
                        "x-ratelimit-remaining-requests": raw_response.headers.get("x-ratelimit-remaining-requests"),
                        "x-ratelimit-remaining-tokens": raw_response.headers.get("x-ratelimit-remaining-tokens"),
                        "x-ratelimit-reset-requests": raw_response.headers.get("x-ratelimit-reset-requests"),
                        "x-ratelimit-reset-tokens": raw_response.headers.get("x-ratelimit-reset-tokens"),
                         # Groq often provides audio specific limits too
                        "x-ratelimit-remaining-audio-seconds": raw_response.headers.get("x-ratelimit-remaining-audio-seconds", "N/A")
                    }

                    # Convert object segments to SRT string
                    transcript = ""
                    for j, segment in enumerate(response.segments, start=1):
                        start = format_timestamp(segment.start)
                        end = format_timestamp(segment.end)
                        text = segment.text.strip()
                        transcript += f"{j}\n{start} --> {end}\n{text}\n\n"


                else:
                    transcript = client.audio.transcriptions.create(
                        model=model_name, 
                        file=audio_file, 
                        response_format="srt",
                        language="zh"
                    )

                final_srt_parts.append(transcript)
        else:
            print("File still too large. Splitting into 10-minute chunks...")
            audio = AudioSegment.from_file(temp_path)
            duration_ms = len(audio)
            
            for i in range(0, duration_ms, CHUNK_LENGTH_MS):
                chunk = audio[i : i + CHUNK_LENGTH_MS]
                chunk_filename = f"chunk_{i}.mp3"
                chunk.export(chunk_filename, format="mp3", bitrate="32k")
                
                with open(chunk_filename, "rb") as audio_file:
                    if provider == "groq":
                        response = client.audio.transcriptions.create(
                            model=model_name, 
                            file=audio_file, 
                            response_format="verbose_json",
                            language="zh"
                        )
                        chunk_srt = ""
                        for k, segment in enumerate(response.segments, start=1):
                            start = format_timestamp(segment.start)
                            end = format_timestamp(segment.end)
                            text = segment.text.strip()
                            chunk_srt += f"{k}\n{start} --> {end}\n{text}\n\n"

                        transcript = chunk_srt
                    else:
                        transcript = client.audio.transcriptions.create(
                            model=model_name, 
                            file=audio_file, 
                            response_format="srt",
                            language="zh"
                        )

                
                adjusted_srt = adjust_srt_timestamps(transcript, i)
                final_srt_parts.append(adjusted_srt)
                
                if os.path.exists(chunk_filename):
                    os.remove(chunk_filename)

        # Cleanup
        if os.path.exists(temp_path): os.remove(temp_path)
        if os.path.exists(compressed_path): os.remove(compressed_path)

        if os.path.exists(compressed_path): os.remove(compressed_path)
        
        response_data = {"filename": file.filename, "srt": str(full_srt)} # Ensure srt is string
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
