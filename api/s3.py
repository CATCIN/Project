# api/s3_test.py
from fastapi import APIRouter, File, UploadFile, HTTPException
from datetime import datetime
from uuid import uuid4
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

@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    # 1) S3에 업로드 (날짜/uuid 키)
    date_prefix = datetime.utcnow().strftime("%Y-%m-%d")
    ext = (file.filename.rsplit(".", 1)[-1] or "bin")
    filename = f"{uuid4()}.{ext}"
    s3_key = f"{date_prefix}/{filename}"

    try:
        content = await file.read()
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,                     
            Body=content,
            ContentType=file.content_type or "application/octet-stream",
        )
    except NoCredentialsError:
        raise HTTPException(500, "AWS credentials not found")
    except Exception as e:
        raise HTTPException(500, f"S3 upload error: {e}")

    url = make_presigned_url(S3_BUCKET, s3_key, expires=600)

    return {"message": "Upload successful", "image_key": s3_key, "image_url": url}

@router.post("/upload-and-register")
async def upload_and_register(file: UploadFile = File(...)):
    # 업로드
    date_prefix = datetime.utcnow().strftime("%Y-%m-%d")
    ext = (file.filename.rsplit(".", 1)[-1] or "bin")
    filename = f"{uuid4()}.{ext}"
    s3_key = f"{date_prefix}/{filename}"

    try:
        content = await file.read()
        s3_client.put_object(
            Bucket=S3_BUCKET, Key=s3_key, Body=content, ContentType=file.content_type or "application/octet-stream"
        )
    except Exception as e:
        raise HTTPException(500, f"S3 upload error: {e}")

    # DB엔 URL 대신 키만 저장
    cat = Cat(
        image_path=s3_key,              
        feature_vector=[0.0],         
        source="system",
        note=""
    )
    await engine.save(cat)

    # 프론트 표시용 URL
    url = make_presigned_url(S3_BUCKET, s3_key, expires=600)

    return {
        "cat_id": str(cat.id),
        "image_key": s3_key,
        "image_url": url,               
    }
