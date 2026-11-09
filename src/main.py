from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .api.routes import router

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(
    title="Helmet Detector YOLO11x Web Camera"
)

# ให้บริการ CSS และ JavaScript
app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR / "static"),
    name="static"
)

# API Routes
app.include_router(router)


# หน้าเว็บหลัก
@app.get("/")
async def index_page():
    return FileResponse(
        FRONTEND_DIR  / "index.html"
    )