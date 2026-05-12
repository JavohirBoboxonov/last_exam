from uuid import UUID # Tepada import qiling
from datetime import datetime
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
class JobTypeEnum(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    REMOTE = "remote"
    HYBRID = "hybrid"
    CONTRACT = "contract"

class ExperienceEnum(str, Enum):
    NO_EXPERIENCE = "no_experience"
    ONE_YEAR = "1_year"
    THREE_YEARS = "3_years"
    FIVE_YEARS = "5_years"
    MORE_THAN_FIVE = "more_than_five"

class InterestStatusEnum(str, Enum):
    PENDING = "pending"
    VIEWED = "viewed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELED = "canceled"
class VacancyBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    requirements: Optional[str] = None
    salary_min: Optional[float] = Field(None, ge=0)
    salary_max: Optional[float] = Field(None, ge=0)
    salary_currency: str = Field(default="UZS", max_length=3)
    location: Optional[str] = Field(None, max_length=255)
    job_type: str = Field(default="full_time")
    experience_required: Optional[str] = None
    
    @validator('salary_max')
    def validate_salary(cls, v, values):
        if v is not None and values.get('salary_min') is not None:
            if v < values['salary_min']:
                raise ValueError('Maksimal oylik minimal oylikdan kichik bo\'lmasligi kerak')
        return v
    
    @validator('job_type')
    def validate_job_type(cls, v):
        allowed = ['full_time', 'part_time', 'remote', 'hybrid', 'contract']
        if v not in allowed:
            raise ValueError(f'job_type quyidagilardan biri bo\'lishi kerak: {allowed}')
        return v

class VacancyCreate(VacancyBase):
    pass

class VacancyUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    requirements: Optional[str] = None
    salary_min: Optional[float] = Field(None, ge=0)
    salary_max: Optional[float] = Field(None, ge=0)
    salary_currency: Optional[str] = Field(None, max_length=3)
    location: Optional[str] = Field(None, max_length=255)
    job_type: Optional[str] = None
    experience_required: Optional[str] = None
    is_active: Optional[bool] = None
    
    @validator('salary_max')
    def validate_salary(cls, v, values):
        if v is not None and values.get('salary_min') is not None:
            if v < values['salary_min']:
                raise ValueError('Maksimal oylik minimal oylikdan kichik bo\'lmasligi kerak')
        return v

class VacancyResponse(VacancyBase):
    id: int
    user_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class VacancyListResponse(BaseModel):
    total: int
    items: List[VacancyResponse]
    
    class Config:
        from_attributes = True
class InterestBase(BaseModel):
    vacancy_id: int = Field(..., gt=0)
    cover_letter: Optional[str] = None
    expected_salary: Optional[float] = Field(None, ge=0)
    message: Optional[str] = None

class InterestCreate(InterestBase):
    user_id: int = Field(..., gt=0)

class InterestUpdate(BaseModel):
    status: Optional[InterestStatusEnum] = None
    cover_letter: Optional[str] = None
    expected_salary: Optional[float] = Field(None, ge=0)
    message: Optional[str] = None

class InterestResponse(InterestBase):
    id: int
    user_id: int
    status: InterestStatusEnum
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserBriefInfo(BaseModel):
    id: int
    full_name: Optional[str] = None
    email: str
    
    class Config:
        from_attributes = True

class VacancyBriefInfo(BaseModel):
    id: int
    title: str
    location: Optional[str] = None
    
    class Config:
        from_attributes = True

class InterestWithUserResponse(InterestResponse):
    user: UserBriefInfo

class InterestWithVacancyResponse(InterestResponse):
    vacancy: VacancyBriefInfo

class VacancyInterestsResponse(BaseModel):
    vacancy_id: int
    vacancy_title: str
    total_interests: int
    interests: List[InterestWithUserResponse]

class UserInterestsResponse(BaseModel):
    user_id: int
    total_interests: int
    interests: List[InterestWithVacancyResponse]

class VacancyWithInterestsResponse(VacancyResponse):
    total_interests: int = 0
    interests: List[InterestResponse] = []

class VacancyFilterParams(BaseModel):
    user_id: Optional[int] = Field(None, gt=0)
    title: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    experience_required: Optional[str] = None
    is_active: Optional[bool] = True
    salary_min_gte: Optional[float] = Field(None, ge=0)
    salary_max_lte: Optional[float] = Field(None, ge=0)
    created_from: Optional[datetime] = None
    created_to: Optional[datetime] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)

class InterestFilterParams(BaseModel):
    vacancy_id: Optional[int] = Field(None, gt=0)
    user_id: Optional[int] = Field(None, gt=0)
    status: Optional[InterestStatusEnum] = None
    created_from: Optional[datetime] = None
    created_to: Optional[datetime] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)