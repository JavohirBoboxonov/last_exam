# routers/application_resume.py

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession  # Asinxron sessiya uchun
from typing import Optional, List, Dict, Any
from status.resume import ResumeService, ApplicationService # Service klasslaringiz
from config.database import get_db
from config.models import CustomUser, ApplicationStatus
from status.schema import *
from vacancy.auth import get_current_user, require_roles

router = APIRouter(prefix="", tags=["Resumes & Applications"])

@router.post("/resumes/create", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def create_resume(
    resume_data: ResumeCreate,
    current_user: CustomUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await ResumeService.create_resume(db, resume_data, current_user)

@router.get("/resumes/my-resumes", response_model=List[ResumeResponse])
async def get_my_resumes(
    current_user: CustomUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """O'zimning resume larimni olish"""
    return await ResumeService.get_user_resumes(db, current_user)

@router.get("/resumes/{resume_id}", response_model=ResumeResponse)
async def get_resume(
    resume_id: int,
    current_user: CustomUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await ResumeService.get_resume_by_id(db, resume_id, current_user)

@router.patch("/resumes/update/{resume_id}", response_model=ResumeResponse)
async def update_resume(
    resume_id: int,
    resume_data: ResumeUpdate,
    current_user: CustomUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await ResumeService.update_resume(db, resume_id, resume_data, current_user)

@router.delete("/resumes/{resume_id}")
async def delete_resume(
    resume_id: int,
    current_user: CustomUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Resume ni o'chirish"""
    return await ResumeService.delete_resume(db, resume_id, current_user)

@router.post("/applications/vacancy/{vacancy_id}/apply", response_model=VacancyApplyResponse)
async def apply_to_vacancy(
    vacancy_id: int,
    apply_data: VacancyApplyRequest,
    current_user: CustomUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Vakansiyaga ariza berish"""
    return await ApplicationService.apply_to_vacancy(db, vacancy_id, apply_data, current_user)

@router.get("/applications/my-applications", response_model=Dict[str, Any])
async def get_my_applications(
    status: Optional[ApplicationStatusEnum] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: CustomUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await ApplicationService.get_my_applications(db, current_user, status, skip, limit)

@router.get("/applications/vacancy/{vacancy_id}/applications")
async def get_vacancy_applications(
    vacancy_id: int,
    status: Optional[ApplicationStatusEnum] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: CustomUser = Depends(require_roles(["admin", "HR"])),
    db: AsyncSession = Depends(get_db)
):
    return await ApplicationService.get_vacancy_applications(db, vacancy_id, current_user, status, skip, limit)

@router.patch("/applications/{application_id}/status")
async def update_application_status(
    application_id: int,
    update_data: VacancyApplicationUpdate,
    current_user: CustomUser = Depends(require_roles(["admin", "HR"])),
    db: AsyncSession = Depends(get_db)
):
    return await ApplicationService.update_application_status(db, application_id, update_data, current_user)

@router.delete("/applications/{application_id}/withdraw")
async def withdraw_application(
    application_id: int,
    current_user: CustomUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await ApplicationService.withdraw_application(db, application_id, current_user)

@router.get("/applications/vacancy/{vacancy_id}/check-application")
async def check_already_applied(
    vacancy_id: int,
    current_user: CustomUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Ariza berilganligini tekshirish"""
    return await ApplicationService.check_already_applied(db, vacancy_id, current_user)