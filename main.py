from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from api import cat, medicine, mediSchedule, s3_upload, s3_view, recognition
import os

app = FastAPI()

# ===== 기본 디렉토리 설정 =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_BUILD = os.path.join(BASE_DIR, "frontend", "build")
FRONTEND_STATIC = os.path.join(FRONTEND_BUILD, "static")
FRONTEND_IMAGES = os.path.join(FRONTEND_BUILD, "images")

# ===== CORS 허용 =====
cors_origins = os.getenv("CORS_ORIGINS", "")
origins = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== 정적 파일 설정 =====
app.mount("/static", StaticFiles(directory=FRONTEND_STATIC), name="static")
app.mount("/images", StaticFiles(directory=FRONTEND_IMAGES), name="images")

# ===== API 라우터 연결 =====
app.include_router(cat.router, prefix="/catcin")
app.include_router(medicine.router, prefix="/catcin")
app.include_router(recognition.router, prefix="/catcin")
app.include_router(mediSchedule.router, prefix="/catcin")
app.include_router(s3_upload.router, prefix="/catcin")
app.include_router(s3_view.router, prefix="/catcin")

# ===== SPA 처리 라우터 등록 =====
app.mount("/", StaticFiles(directory=FRONTEND_BUILD, html=True), name="spa")
