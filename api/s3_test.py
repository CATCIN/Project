# api/s3_test.py
from fastapi import APIRouter, File, UploadFile, HTTPException
from datetime import datetime
from uuid import uuid4
import json
import boto3
from core.database import engine
from botocore.exceptions import NoCredentialsError

from models.model import Cat

router = APIRouter()

S3_BUCKET = "catsin-bucket"
S3_REGION = "us-east-1"

s3_client = boto3.client(
    's3',
    region_name=S3_REGION
)

@router.post("/upload-image/")
async def upload_image(file: UploadFile = File(...)):
    try:
        date_prefix = datetime.utcnow().strftime("%Y-%m-%d")
        file_extension = file.filename.split('.')[-1]
        filename = f"{uuid4()}.{file_extension}"
        s3_key = f"{date_prefix}/{filename}"  # 경로 포함 파일명

        file_content = await file.read()
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=filename,
            Body=file_content,
            ContentType=file.content_type
        )

        s3_url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{filename}"
        return {"message": "Upload successful", "url": s3_url}

    except NoCredentialsError:
        return {"error": "AWS credentials not found"}
    except Exception as e:
        return {"error": str(e)}



@router.post("/upload-system/")
async def upload_image(file: UploadFile = File(...)):
    try:
        # S3 업로드
        date_prefix = datetime.utcnow().strftime("%Y-%m-%d")
        file_extension = file.filename.split('.')[-1]
        filename = f"{uuid4()}.{file_extension}"
        s3_key = f"{date_prefix}/{filename}"

        file_content = await file.read()
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=file_content,
            ContentType=file.content_type
        )

        s3_url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{s3_key}"

    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="AWS credentials not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"S3 upload error: {e}")

    try:
        # Cat 객체 생성
        cat = Cat(
            image_path=s3_url,
            feature_vector=[0.0],  # 현재는 기본값
            source="system",
            note=""
        )
        await engine.save(cat)
        return cat

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database save error: {e}")
