# routers/application_resume.py

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime
from status.resume import *
from config.database import get_db
from config.models import CustomUser, Resume, Vacancy, VacancyApplication, ApplicationStatus
from status.schema import *
from vacancy.auth import get_current_user, require_roles

router = APIRouter(prefix="", tags=["Resumes & Applications"])

# ============ RESUME ENDPOINTS ============

@router.post("/resumes", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
def create_resume(
    resume_data: ResumeCreate,
    current_user: CustomUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Yangi resume yaratish"""
    return ResumeService.create_resume(db, resume_data, current_user)

@router.get("/resumes/my-resumes", response_model=List[ResumeResponse])
def get_my_resumes(
    current_user: CustomUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """O'zimning resume larimni olish"""
    return ResumeService.get_user_resumes(db, current_user)

@router.get("/resumes/{resume_id}", response_model=ResumeResponse)
def get_resume(
    resume_id: int,
    current_user: CustomUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Resume ni olish"""
    return ResumeService.get_resume_by_id(db, resume_id, current_user)

@router.put("/resumes/{resume_id}", response_model=ResumeResponse)
def update_resume(
    resume_id: int,
    resume_data: ResumeUpdate,
    current_user: CustomUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Resume ni yangilash"""
    return ResumeService.update_resume(db, resume_id, resume_data, current_user)

@router.delete("/resumes/{resume_id}")
def delete_resume(
    resume_id: int,
    current_user: CustomUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Resume ni o'chirish"""
    return ResumeService.delete_resume(db, resume_id, current_user)

# ============ APPLICATION ENDPOINTS ============

@router.post("/applications/vacancy/{vacancy_id}/apply", response_model=VacancyApplyResponse)
def apply_to_vacancy(
    vacancy_id: int,
    apply_data: VacancyApplyRequest,
    current_user: CustomUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Vakansiyaga ariza berish
    - Faqat autentifikatsiyalangan foydalanuvchilar
    - Bir marta ariza berish mumkin
    - Resume avtomatik yuboriladi
    """
    return ApplicationService.apply_to_vacancy(db, vacancy_id, apply_data, current_user)

@router.get("/applications/my-applications", response_model=Dict[str, Any])
def get_my_applications(
    status: Optional[ApplicationStatusEnum] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: CustomUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """O'zimning barcha arizalarimni ko'rish"""
    return ApplicationService.get_my_applications(db, current_user, status, skip, limit)

@router.get("/applications/vacancy/{vacancy_id}/applications")
def get_vacancy_applications(
    vacancy_id: int,
    status: Optional[ApplicationStatusEnum] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: CustomUser = Depends(require_roles(["admin", "hr"])),
    db: Session = Depends(get_db)
):
    """Vakansiyaga kelgan arizalarni ko'rish (faqat admin va HR)"""
    return ApplicationService.get_vacancy_applications(db, vacancy_id, current_user, status, skip, limit)

@router.patch("/applications/{application_id}/status")
def update_application_status(
    application_id: int,
    update_data: VacancyApplicationUpdate,
    current_user: CustomUser = Depends(require_roles(["admin", "hr"])),
    db: Session = Depends(get_db)
):
    """Ariza statusini yangilash (faqat admin va HR)"""
    return ApplicationService.update_application_status(db, application_id, update_data, current_user)

@router.delete("/applications/{application_id}/withdraw")
def withdraw_application(
    application_id: int,
    current_user: CustomUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Arizani qaytarib olish (faqat ariza egasi)"""
    return ApplicationService.withdraw_application(db, application_id, current_user)

@router.get("/applications/vacancy/{vacancy_id}/check-application")
def check_already_applied(
    vacancy_id: int,
    current_user: CustomUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return ApplicationService.check_already_applied(db, vacancy_id, current_user)