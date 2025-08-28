# core/utils.py
import os
import uuid
import numpy as np
from fastapi import UploadFile

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGE_DIR = os.path.join(BASE_DIR, "static", "images")

os.makedirs(IMAGE_DIR, exist_ok=True)

async def save_image(file: UploadFile) -> str:
    """
    UploadFile을 받아서 static/images/<랜덤이름>.<확장자> 로 저장하고,
    저장된 파일의 상대 경로(또는 URL)를 반환합니다.
    """
    # 원본 확장자 추출 (예: .jpg, .png 등)
    _, ext = os.path.splitext(file.filename)
    # UUID로 랜덤 파일명 생성
    new_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(IMAGE_DIR, new_filename)

    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    return f"/static/images/{new_filename}"

def l2_normalize(v: np.ndarray) -> np.ndarray:
    return v / (np.linalg.norm(v) + 1e-12)

def l2_normalize_list(v: list[float]) -> list[float]:
    a = np.asarray(v, dtype=np.float32)
    return (a / (np.linalg.norm(a) + 1e-12)).tolist()

def cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b))