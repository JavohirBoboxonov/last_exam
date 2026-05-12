from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, List, Dict, Any
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

class ApplicationStatusEnum(str, Enum):
    PENDING = "pending"
    REVIEWED = "reviewed"
    SHORTLISTED = "shortlisted"
    REJECTED = "rejected"
    ACCEPTED = "accepted"
    WITHDRAWN = "withdrawn"
class UserRoleEnum(str, Enum):
    ADMIN = "admin"
    HR = "hr"
    CANDIDATE = "candidate"
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRoleEnum = UserRoleEnum.CANDIDATE

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)

class UserResponse(UserBase):
    id: int
    is_active: bool
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

class VacancyBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Vakansiya sarlavhasi")
    description: str = Field(..., min_length=1, description="Vakansiya tavsifi")
    requirements: Optional[str] = Field(None, description="Talablar")
    salary_min: Optional[float] = Field(None, ge=0, description="Minimal oylik")
    salary_max: Optional[float] = Field(None, ge=0, description="Maksimal oylik")
    salary_currency: str = Field(default="UZS", max_length=3, description="Pul birligi")
    location: Optional[str] = Field(None, max_length=255, description="Ish joyi")
    job_type: JobTypeEnum = Field(default=JobTypeEnum.FULL_TIME, description="Ish turi")
    experience_required: Optional[ExperienceEnum] = Field(None, description="Kerakli tajriba")
    
    @validator('salary_max')
    def validate_salary(cls, v, values):
        if v is not None and values.get('salary_min') is not None:
            if v < values['salary_min']:
                raise ValueError('Maksimal oylik minimal oylikdan kichik bo\'lmasligi kerak')
        return v

class VacancyCreate(VacancyBase):
    user_id: Optional[int] = Field(None, gt=0, description="Foydalanuvchi ID si (avtomatik qo'yiladi)")

class VacancyUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    requirements: Optional[str] = None
    salary_min: Optional[float] = Field(None, ge=0)
    salary_max: Optional[float] = Field(None, ge=0)
    salary_currency: Optional[str] = Field(None, max_length=3)
    location: Optional[str] = Field(None, max_length=255)
    job_type: Optional[JobTypeEnum] = None
    experience_required: Optional[ExperienceEnum] = None
    is_active: Optional[bool] = None
    
    @validator('salary_max')
    def validate_salary(cls, v, values):
        if v is not None and values.get('salary_min') is not None:
            if v < values['salary_min']:
                raise ValueError('Maksimal oylik minimal oylikdan kichik bo\'lmasligi kerak')
        return v

class VacancyResponse(VacancyBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class VacancyListResponse(BaseModel):
    total: int
    items: List[VacancyResponse]
    skip: Optional[int] = 0
    limit: Optional[int] = 100
    
    class Config:
        from_attributes = True

# ============ RESUME SCHEMAS ============
class ResumeBase(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=255, description="To'liq ism")
    email: EmailStr = Field(..., description="Email manzil")
    phone: Optional[str] = Field(None, max_length=50, description="Telefon raqam")
    position: str = Field(..., max_length=255, description="Lavozim")
    experience_years: float = Field(0, ge=0, description="Tajriba yillari")
    skills: Optional[str] = Field(None, description="Ko'nikmalar (vergul bilan)")
    education: Optional[str] = Field(None, description="Ma'lumoti")
    previous_jobs: Optional[str] = Field(None, description="Oldingi ish joylari")
    portfolio_url: Optional[str] = Field(None, max_length=500, description="Portfolio URL")
    linkedin_url: Optional[str] = Field(None, max_length=500, description="LinkedIn URL")
    github_url: Optional[str] = Field(None, max_length=500, description="GitHub URL")
    cover_letter: Optional[str] = Field(None, description="Qo'shimcha xat")

class ResumeCreate(ResumeBase):
    pass

class ResumeUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    position: Optional[str] = Field(None, max_length=255)
    experience_years: Optional[float] = Field(None, ge=0)
    skills: Optional[str] = None
    education: Optional[str] = None
    previous_jobs: Optional[str] = None
    portfolio_url: Optional[str] = Field(None, max_length=500)
    linkedin_url: Optional[str] = Field(None, max_length=500)
    github_url: Optional[str] = Field(None, max_length=500)
    cover_letter: Optional[str] = None
    is_active: Optional[bool] = None

class ResumeResponse(ResumeBase):
    id: int
    user_id: int
    is_active: bool
    file_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class InterestBase(BaseModel):
    vacancy_id: int = Field(..., gt=0, description="Vakansiya ID")
    cover_letter: Optional[str] = Field(None, description="Qo'shimcha xat")
    expected_salary: Optional[float] = Field(None, ge=0, description="Kutilayotgan oylik")
    message: Optional[str] = Field(None, max_length=1000, description="Qo'shimcha xabar")

class InterestCreate(InterestBase):
    user_id: Optional[int] = Field(None, gt=0, description="Foydalanuvchi ID (avtomatik)")

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

class InterestWithUserResponse(InterestResponse):
    user: UserBriefInfo

class InterestWithVacancyResponse(InterestResponse):
    vacancy: 'VacancyBriefInfo'

class VacancyApplicationBase(BaseModel):
    vacancy_id: int = Field(..., gt=0, description="Vakansiya ID")
    resume_id: int = Field(..., gt=0, description="Resume ID")
    message: Optional[str] = Field(None, max_length=1000, description="Qo'shimcha xabar")
    cover_letter: Optional[str] = Field(None, description="Qo'shimcha xat")
    expected_salary: Optional[float] = Field(None, ge=0, description="Kutilayotgan oylik")

class VacancyApplicationCreate(VacancyApplicationBase):
    user_id: Optional[int] = Field(None, gt=0, description="Foydalanuvchi ID (avtomatik)")

class VacancyApplicationUpdate(BaseModel):
    status: Optional[ApplicationStatusEnum] = Field(None, description="Ariza statusi")
    feedback: Optional[str] = Field(None, description="HR dan javob")
    expected_salary: Optional[float] = Field(None, ge=0, description="Kutilayotgan oylik")

class VacancyApplicationResponse(VacancyApplicationBase):
    id: int
    user_id: int
    status: ApplicationStatusEnum
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    feedback: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class VacancyApplicationWithDetailsResponse(VacancyApplicationResponse):
    vacancy: Optional[VacancyResponse] = None
    resume: Optional[ResumeResponse] = None
    user: Optional[UserBriefInfo] = None

class VacancyApplyRequest(BaseModel):
    resume_id: int = Field(..., gt=0, description="Qaysi resume bilan ariza berish")
    message: Optional[str] = Field(None, max_length=1000, description="Qo'shimcha xabar")
    cover_letter: Optional[str] = Field(None, description="Qo'shimcha xat")
    expected_salary: Optional[float] = Field(None, ge=0, description="Kutilayotgan oylik")

class VacancyApplyResponse(BaseModel):
    message: str
    application_id: int
    status: str
    applied_at: datetime

class VacancyBriefInfo(BaseModel):
    id: int
    title: str
    location: Optional[str] = None
    job_type: Optional[JobTypeEnum] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    
    class Config:
        from_attributes = True

class VacancyWithInterestsResponse(VacancyResponse):
    total_interests: int = 0
    interests: List[InterestResponse] = []

class VacancyWithApplicationsResponse(VacancyResponse):
    total_applications: int = 0
    applications_statistics: Dict[str, int] = {}
    applications: List[VacancyApplicationResponse] = []

class UserInterestsResponse(BaseModel):
    user_id: int
    total_interests: int
    interests: List[InterestWithVacancyResponse]

class UserApplicationsResponse(BaseModel):
    user_id: int
    total_applications: int
    applications: List[VacancyApplicationWithDetailsResponse]

class ResumeWithApplicationsResponse(ResumeResponse):
    applications: List[VacancyApplicationResponse] = []

# ============ FILTER PARAMETERS ============
class VacancyFilterParams(BaseModel):
    user_id: Optional[int] = Field(None, gt=0)
    title: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[JobTypeEnum] = None
    experience_required: Optional[ExperienceEnum] = None
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

class ApplicationFilterParams(BaseModel):
    vacancy_id: Optional[int] = Field(None, gt=0)
    user_id: Optional[int] = Field(None, gt=0)
    status: Optional[ApplicationStatusEnum] = None
    created_from: Optional[datetime] = None
    created_to: Optional[datetime] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)

class VacancyStatisticsResponse(BaseModel):
    total_vacancies: int
    active_vacancies: int
    inactive_vacancies: int
    by_job_type: Dict[str, int] = {}
    by_experience: Dict[str, int] = {}
    hr_statistics: Optional[List[Dict[str, Any]]] = None

class ApplicationStatisticsResponse(BaseModel):
    total_applications: int
    by_status: Dict[str, int] = {}
    by_vacancy: Dict[str, int] = {}
    average_expected_salary: Optional[float] = None
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    status_code: int