from fastapi import FastAPI, UploadFile, File
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

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_FILE_SIZE_MB = 25
# 10 minute chunks
CHUNK_LENGTH_MS = 10 * 60 * 1000 

def adjust_srt_timestamps(srt_content: str, offset_ms: int) -> str:
    """Adjusts timestamps in SRT content by adding offset_ms."""
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

    # Regex for SRT timestamp: 00:00:10,500 --> 00:00:00,000
    # Note: SRT uses comma for milliseconds
    pattern = re.compile(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})")
    
    # Process line by line or full text
    # Full text replacement is safe as long as format matches
    return pattern.sub(replace_time, srt_content)

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return JSONResponse(status_code=500, content={"error": "请在 .env 文件中配置 OPENAI_API_KEY"})
    
    client = OpenAI(api_key=api_key)

    temp_path = f"temp_{file.filename}"
    compressed_path = f"compressed_{file.filename}.mp3"

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_size_mb = os.path.getsize(temp_path) / (1024 * 1024)
        print(f"Uploaded file size: {file_size_mb:.2f} MB")
        
        final_srt_parts = []
        
        # Strategy:
        # 1. If < 25MB: Transcribe directly.
        # 2. If > 25MB: Convert to low bitrate MP3.
        # 3. If still > 25MB: Split.

        target_file_path = temp_path

        if file_size_mb > MAX_FILE_SIZE_MB:
            print("File > 25MB. Compressing to MP3 32k mono...")
            audio = AudioSegment.from_file(temp_path)
            audio.export(compressed_path, format="mp3", bitrate="32k", parameters=["-ac", "1"])
            comp_size = os.path.getsize(compressed_path) / (1024 * 1024)
            print(f"Compressed size: {comp_size:.2f} MB")
            
            if comp_size <= MAX_FILE_SIZE_MB:
                target_file_path = compressed_path
            else:
                # Still too big, need to split the COMPRESSED file logic or original
                # We will use the 'audio' object we already loaded
                pass 
        else:
            # File is small enough
            pass

        # Check if we are still working with a single file <= 25MB
        current_size = os.path.getsize(target_file_path) / (1024 * 1024)
        
        if current_size <= MAX_FILE_SIZE_MB:
             with open(target_file_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file, 
                    response_format="srt"
                )
                final_srt_parts.append(transcript)
        else:
            print("File still too large. Splitting into 10-minute chunks...")
            # Reload explicit audio if not loaded
            audio = AudioSegment.from_file(temp_path) # Use original high quality source for splitting
            duration_ms = len(audio)
            
            for i in range(0, duration_ms, CHUNK_LENGTH_MS):
                chunk = audio[i : i + CHUNK_LENGTH_MS]
               
                # Export chunk
                chunk_filename = f"chunk_{i}.mp3"
                chunk.export(chunk_filename, format="mp3", bitrate="32k")
                
                # Transcribe chunk
                with open(chunk_filename, "rb") as audio_file:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1", 
                        file=audio_file, 
                        response_format="srt"
                    )
                
                # Adjust timestamps
                adjusted_srt = adjust_srt_timestamps(transcript, i)
                final_srt_parts.append(adjusted_srt)
                
                # Clean up chunk
                if os.path.exists(chunk_filename):
                    os.remove(chunk_filename)

        # Cleanup generic files
        if os.path.exists(temp_path): os.remove(temp_path)
        if os.path.exists(compressed_path): os.remove(compressed_path)

        # Join parts
        # Note: Ideally re-index the counter (1, 2, 3...)
        full_srt = "\n\n".join(final_srt_parts)
        
        return {"filename": file.filename, "srt": full_srt}

    except Exception as e:
        # Cleanup
        if os.path.exists(temp_path): os.remove(temp_path)
        if os.path.exists(compressed_path): os.remove(compressed_path)
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
