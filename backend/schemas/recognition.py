# schemas/recognition.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class CatRecognitionInput(BaseModel):
    image_path: str
    feature_vector: List[float]
    detected_at: Optional[datetime] = None
    source: Optional[str] = None  # "system" | "user"
    camera_id: Optional[str] = None
    user_id: Optional[str] = None



# 요청 예시
#{
#  "image_path": "s3://bucket/cat1.jpg",
#  "feature_vector": [0.12, 0.34, 0.56, 0.78],
#  "detected_at": "2025-08-28T10:00:00",
#  "source": "system"
#}