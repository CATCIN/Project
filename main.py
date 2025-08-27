from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from api import cat, medicine, recognition, s3_test, mediSchedule
import os

app = FastAPI()

# ===== 1. 기본 디렉토리 설정 =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_BUILD = os.path.join(BASE_DIR, "frontend", "build")
FRONTEND_STATIC = os.path.join(FRONTEND_BUILD, "static")
FRONTEND_IMAGES = os.path.join(FRONTEND_BUILD, "images")

# ===== 2. CORS 허용 =====
cors_origins = os.getenv("CORS_ORIGINS", "")
origins = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== 3. 정적 파일 mount는 꼭 먼저 선언 =====
app.mount("/static", StaticFiles(directory=FRONTEND_STATIC), name="static")
app.mount("/images", StaticFiles(directory=FRONTEND_IMAGES), name="images")

# ===== 4. API 라우터 연결 =====
app.include_router(cat.router, prefix="/catcin")
app.include_router(medicine.router, prefix="/catcin")
app.include_router(recognition.router, prefix="/catcin")
app.include_router(s3_test.router, prefix="/catcin")
app.include_router(mediSchedule.router, prefix="/catcin")

# ===== 5. 마지막에 SPA 처리 라우터 등록 =====
@app.get("/{full_path:path}")
async def serve_react_app(request: Request):
    return FileResponse(os.path.join(FRONTEND_BUILD, "index.html"))

