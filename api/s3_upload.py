# api/s3_upload.py
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from typing import Optional, List
from datetime import datetime, timezone
import os
import boto3
from botocore.exceptions import NoCredentialsError
from core.database import engine
from models.model import Cat

router = APIRouter(prefix="/s3", tags=["s3"])

S3_BUCKET = os.getenv("S3_BUCKET", "catcin-bucket")
S3_REGION = os.getenv("AWS_REGION", "us-east-1")
s3_client = boto3.client("s3", region_name=S3_REGION)


def make_presigned_url(bucket: str, key: str, expires=600) -> str:
    return s3_client.generate_presigned_url(
        "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=expires
    )


# ============================================================
#  단일 촬영 업로드 (사진 1장에 대한 API, (source='system'))
# ============================================================
"""
@router.post("/upload-shot")
async def upload_shot(
    file: UploadFile = File(...),
    captured_at: Optional[str] = Form(None),   # ISO8601 문자열이나 epoch(ms)
    index: int = Form(0),
    source: str = Form("system"),
    note: str = Form(""),
):
    try:
        content = await file.read()

        # 촬영시각 처리
        if captured_at:
            try:
                dt = datetime.fromisoformat(captured_at.replace("Z", "+00:00"))
            except:
                dt = datetime.fromtimestamp(int(captured_at) / 1000, tz=timezone.utc)
        else:
            dt = datetime.now(timezone.utc)

        # 파일명 (YYYY-MM-DD/시각_index.ext)
        date_prefix = dt.strftime("%Y-%m-%d")
        timestamp = dt.strftime("%Y%m%d_%H%M%S")
        ext = (file.filename.rsplit(".", 1)[-1] or "bin")
        s3_key = f"{date_prefix}/{timestamp}_{index}.{ext}"

        # S3 업로드
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=content,
            ContentType=file.content_type or "application/octet-stream",
        )

        # DB 저장
        cat = Cat(
            image_path=s3_key,
            feature_vector=[0.0],
            source=source,
            save_at=dt.replace(tzinfo=None),
            last_seen=dt.replace(tzinfo=None),
            note=note,
        )
        await engine.save(cat)

        return {
            "cat_id": str(cat.id),
            "image_key": s3_key,
            "image_url": make_presigned_url(S3_BUCKET, s3_key),
            "captured_at": dt.isoformat(),
            "index": index,
        }
    except NoCredentialsError:
        raise HTTPException(500, "AWS credentials not found")
    except Exception as e:
        raise HTTPException(500, f"upload_shot error: {e}")
"""

# ===============================================================
#  사이트에서 고양이 사진 및 정보 수동 등록 API (source='user')
# ===============================================================
@router.post("/register")
async def register_from_site(
    file: UploadFile = File(...),
    note: str = Form(""),
):
    try:
        content = await file.read()
        dt = datetime.now(timezone.utc)

        # 파일명
        date_prefix = dt.strftime("%Y-%m-%d")
        timestamp = dt.strftime("%Y%m%d_%H%M%S")
        ext = (file.filename.rsplit(".", 1)[-1] or "bin")
        s3_key = f"{date_prefix}/{timestamp}.user.{ext}"

        # S3 업로드
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=content,
            ContentType=file.content_type or "application/octet-stream",
        )

        # DB 저장
        cat = Cat(
            image_path=s3_key,
            feature_vector=[0.0],
            source="user",
            save_at=dt.replace(tzinfo=None),
            last_seen=dt.replace(tzinfo=None),
            note=note,
        )
        await engine.save(cat)

        return {
            "cat_id": str(cat.id),
            "image_key": s3_key,
            "image_url": make_presigned_url(S3_BUCKET, s3_key),
        }
    except Exception as e:
        raise HTTPException(500, f"register error: {e}")
