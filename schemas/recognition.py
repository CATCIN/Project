from pydantic import BaseModel
from typing import List
from datetime import datetime

class CatRecognitionInput(BaseModel):
    image_path: str
    feature_vector: List[float]
    detected_at: datetime
