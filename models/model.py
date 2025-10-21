from odmantic import Model, Field, Reference
from typing import List, Optional
from typing_extensions import Literal
from datetime import datetime
from bson import ObjectId
from enum import Enum

class Category(str, Enum):
    ANTIBIOTIC = "antibiotic"
    PAINKILLER = "painkiller"
    VITAMIN = "vitamin"
    NUTRITIONAL = "nutritional"
    ANTHELMINTIC = "anthelmintic"

class Cat(Model):
    cat_code: Optional[str] = None  # 사람이 보기 쉬운 고양이 코드 (예: CAT_001)
    source: Literal["user", "system"]
    created_at: datetime = Field(default_factory=datetime.utcnow)   # 최초 등록일 (한 번 생성되면 바뀌지 않음)
    updated_at: datetime = Field(default_factory=datetime.utcnow)   # 레코드가 변경될 때마다 갱신되는 마지막 업데이트 날짜
    stats_seen: int = 1            # 업데이트 된 횟수, 본 횟수

    note: str = ""
    image_path: List[str]          # s3 경로 리스트
    feature_vector: List[float]

class Medicine(Model):
    name: str
    category: Category
    interval: int
    expires_date: datetime
    image_url: Optional[str] = None
    note: str = ""

class MediLog(Model):
    cat_id: ObjectId      
    medicine_id: ObjectId
    administered_at: datetime = Field(default_factory=datetime.utcnow)

class MediSchedule(Model):
    """
    고양이별 또는 전체 고양이에게 적용되는 투약 스케줄 모델
    - cat 필드가 None이면 전체 고양이 스케줄
    - cat 필드가 Cat 객체를 참조하면 특정 고양이 스케줄
    """
    medicine: Medicine = Reference()
    interval_days: int
    dose: int = Field(1)
    note: str = ""
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    cat_id: Optional[ObjectId] = Field(None)

    @property
    def next_due(self) -> datetime:
        base = self.created_at or datetime.utcnow()
        return base + timedelta(days=self.interval_days)

        