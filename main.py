from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
import os

from audio_director import process_audio_director

app = FastAPI()

# 静的ファイルの提供
app.mount("/static", StaticFiles(directory="static"), name="static")

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
    target_lufs: float = Form(-14.0)
):
    try:
        # ファイルの読み込み
        contents = await file.read()
        
        # メモリ保護: 15MB以上の大型ファイルは処理を制限してサーバー落下を防ぐ
        if len(contents) > 15 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="ファイルサイズが大きすぎます(15MB以下にしてください)")

        # 音声処理パイプラインの実行
        output_bytes = process_audio_director(
            file_bytes=contents,
            declip=declip,
            denoise=denoise,
            demask=demask,
            flute=flute,
            target_lufs=target_lufs
        )

        return Response(content=output_bytes, media_type="audio/wav")

    except Exception as e:
        print(f"Error processing audio: {e}")
        raise HTTPException(status_code=500, detail=f"処理中にエラーが発生しました: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)