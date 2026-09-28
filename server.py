import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.background import BackgroundTasks
from yt_dlp import YoutubeDL

app = FastAPI()

DOWNLOAD_DIR = "server_downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def remove_file(path: str):
    if os.path.exists(path):
        os.remove(path)

@app.get("/", response_class=HTMLResponse)
async def index():
    return """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Liquid Glass Downloader</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', sans-serif; }
            body { background: #09070f; height: 100vh; display: flex; justify-content: center; align-items: center; overflow: hidden; position: relative; }
            .bg-blur, .bg-blur-2 { position: absolute; border-radius: 50%; animation: float 12s infinite alternate ease-in-out; z-index: 1; }
            .bg-blur { width: 500px; height: 500px; background: linear-gradient(135deg, #7928ca, #ff0080); filter: blur(130px); top: -10%; right: -10%; }
            .bg-blur-2 { width: 400px; height: 400px; background: linear-gradient(135deg, #00dfd8, #007cf0); filter: blur(110px); bottom: -10%; left: -10%; animation-duration: 8s; animation-direction: alternate-reverse; }
            @keyframes float { 0% { transform: translate(0, 0) scale(1); } 100% { transform: translate(60px, 40px) scale(1.15); } }
            .glass-card { position: relative; z-index: 10; background: rgba(255, 255, 255, 0.02); backdrop-filter: blur(25px) saturate(180%); -webkit-backdrop-filter: blur(25px) saturate(180%); border: 1px solid rgba(255, 255, 255, 0.07); border-radius: 24px; padding: 40px; width: 92%; max-width: 460px; box-shadow: 0 25px 50px rgba(0,0,0,0.5); text-align: center; }
            h1 { color: #fff; font-size: 24px; margin-bottom: 6px; font-weight: 600; }
            p { color: rgba(255, 255, 255, 0.5); font-size: 14px; margin-bottom: 25px; }
            input { width: 100%; padding: 16px 20px; background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; outline: none; color: #fff; font-size: 15px; transition: all 0.3s ease; margin-bottom: 20px; }
            input:focus { border-color: rgba(0, 223, 216, 0.5); background: rgba(255, 255, 255, 0.06); box-shadow: 0 0 20px rgba(0, 223, 216, 0.15); }
            .buttons-container { display: flex; gap: 12px; }
            button { flex: 1; padding: 16px; border: none; border-radius: 12px; color: #fff; font-size: 15px; font-weight: 600; cursor: pointer; transition: all 0.3s ease; }
            .btn-video { background: linear-gradient(90deg, #007cf0, #00dfd8); box-shadow: 0 6px 15px rgba(0, 124, 240, 0.2); }
            .btn-audio { background: linear-gradient(90deg, #7928ca, #ff0080); box-shadow: 0 6px 15px rgba(255, 0, 128, 0.2); }
            button:hover:not(:disabled) { transform: translateY(-2px); filter: brightness(1.1); }
            button:disabled { background: rgba(255,255,255,0.05); color: rgba(255,255,255,0.2); cursor: not-allowed; box-shadow: none; }
            #status { margin-top: 15px; font-size: 14px; color: #00dfd8; display: none; font-weight: 500; }
        </style>
    </head>
    <body>
        <div class="bg-blur"></div><div class="bg-blur-2"></div>
        <div class="glass-card">
            <h1>Media Downloader</h1>
            <p>Вставь ссылку для мгновенного скачивания</p>
            <input type="text" id="urlInput" placeholder="Вставь ссылку на YouTube, TikTok..." autocomplete="off">
            <div class="buttons-container">
                <button id="videoBtn" class="btn-video" onclick="startDownload('video')">🎬 Видео MP4</button>
                <button id="audioBtn" class="btn-audio" onclick="startDownload('audio')">🎵 Трек MP3</button>
            </div>
            <div id="status">🔄 Инициализация...</div>
        </div>
        <script>
            function startDownload(type) {
                const urlInput = document.getElementById('urlInput');
                const videoBtn = document.getElementById('videoBtn');
                const audioBtn = document.getElementById('audioBtn');
                const status = document.getElementById('status');
                const url = urlInput.value.trim();
                if (!url) return alert('Вставь ссылку!');
                videoBtn.disabled = true; audioBtn.disabled = true; status.style.display = 'block';
                if (type === 'video') { status.innerText = '⏳ Скачиваем видео в макс. качестве...'; status.style.color = '#00dfd8'; }
                else { status.innerText = '⏳ Конвертируем в MP3...'; status.style.color = '#ff0080'; }
                window.location.href = `/download?url=${encodeURIComponent(url)}&type=${type}`;
                setTimeout(() => { videoBtn.disabled = false; audioBtn.disabled = false; status.style.display = 'none'; urlInput.value = ''; }, 5000);
            }
        </script>
    </body>
    </html>
    """

@app.get("/download")
async def download_media(url: str, type: str, background_tasks: BackgroundTasks):
    if type == "audio":
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
            'noplaylist': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        media_type = 'audio/mpeg'
        fallback_ext = 'mp3'
    else:
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
            'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
            'noplaylist': True,
        }
        media_type = 'video/mp4'
        fallback_ext = 'mp4'

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            
            if type == "audio" and not file_path.endswith('.mp3'):
                file_path = os.path.splitext(file_path)[0] + '.mp3'
            
            if not os.path.exists(file_path):
                video_id = info.get('id')
                for file in os.listdir(DOWNLOAD_DIR):
                    if video_id in file and file.endswith(fallback_ext):
                        file_path = os.path.join(DOWNLOAD_DIR, file)
                        break

            if not os.path.exists(file_path):
                raise HTTPException(status_code=500, detail="Файл не найден")
            
            background_tasks.add_task(remove_file, file_path)
            return FileResponse(path=file_path, filename=os.path.basename(file_path), media_type=media_type)
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
