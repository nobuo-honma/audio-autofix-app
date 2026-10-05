from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
import audio_director

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return Response(content=b"", media_type="image/x-icon")

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

@app.post("/api/process")
async def process_audio(
    file: UploadFile = File(...),
    declip: bool = Form(True),
    denoise: bool = Form(True),
    demask: bool = Form(True),
    flute: bool = Form(True),
    lufs: float = Form(-14.0)
):
    try:
        file_bytes = await file.read()
        processed_bytes = audio_director.process_audio_director(
            file_bytes=file_bytes,
            declip=declip,
            denoise=denoise,
            demask=demask,
            flute=flute,
            target_lufs=lufs
        )

        return Response(
            content=processed_bytes,
            media_type="audio/wav",
            headers={"Content-Disposition": "attachment; filename=mastered_audio.wav"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)