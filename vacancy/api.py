from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional, List

from config.database import get_db
from config.models import CustomUser, InterestStatus
from vacancy.schema import *
from vacancy.auth import get_current_user, require_roles
from vacancy.service import VacancyService

router = APIRouter(prefix="/vacancies", tags=["Vacancies"])

@router.post("/", response_model=VacancyResponse, status_code=status.HTTP_201_CREATED)
def create_vacancy(
    vacancy_data: VacancyCreate,
    current_user: CustomUser = Depends(require_roles(["admin", "HR"])),
    db: Session = Depends(get_db)
):
    return VacancyService.create_vacancy(db, vacancy_data, current_user)

@router.get("/", response_model=VacancyListResponse)
def get_vacancies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    title: Optional[str] = None,
    location: Optional[str] = None,
    job_type: Optional[str] = None,
    salary_min_gte: Optional[float] = None,
    experience_required: Optional[str] = None,
    current_user: CustomUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    filters = {
        "title": title,
        "location": location,
        "job_type": job_type,
        "salary_min_gte": salary_min_gte,
        "experience_required": experience_required
    }
    return VacancyService.get_all_vacancies(db, current_user, skip, limit, filters)

@router.get("/my-vacancies", response_model=VacancyListResponse)
def get_my_vacancies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = None,
    current_user: CustomUser= Depends(require_roles(["admin", "HR"])),
    db: Session = Depends(get_db)
):
    """O'zim yaratgan vakansiyalarim"""
    return VacancyService.get_my_vacancies(db, current_user, skip, limit, is_active)

@router.get("/{vacancy_id}", response_model=VacancyResponse)
def get_vacancy(
    vacancy_id: int,
    current_user: CustomUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Vakansiyani ID bo'yicha olish"""
    return VacancyService.get_vacancy_by_id(db, vacancy_id, current_user)

@router.put("/{vacancy_id}", response_model=VacancyResponse)
def update_vacancy(
    vacancy_id: int,
    vacancy_data: VacancyUpdate,
    current_user: CustomUser = Depends(require_roles(["admin", "HR"])),
    db: Session = Depends(get_db)
):
    """Vakansiyani yangilash"""
    return VacancyService.update_vacancy(db, vacancy_id, vacancy_data, current_user)

@router.delete("/{vacancy_id}")
def delete_vacancy(
    vacancy_id: int,
    hard_delete: bool = Query(False, description="To'liq o'chirish yoki faqat deaktivatsiya"),
    current_user: CustomUser = Depends(require_roles(["admin", "HR"])),
    db: Session = Depends(get_db)
):
    """Vakansiyani o'chirish"""
    return VacancyService.delete_vacancy(db, vacancy_id, current_user, hard_delete)

@router.patch("/{vacancy_id}/restore", response_model=VacancyResponse)
def restore_vacancy(
    vacancy_id: int,
    current_user: CustomUser = Depends(require_roles(["admin", "HR"])),
    db: Session = Depends(get_db)
):
    return VacancyService.restore_vacancy(db, vacancy_id, current_user)

@router.patch("/{vacancy_id}/status")
def update_vacancy_status(
    vacancy_id: int,
    is_active: bool,
    current_user: CustomUser = Depends(require_roles(["admin", "HR"])),
    db: Session = Depends(get_db)
):
    """Vakansiya statusini o'zgartirish"""
    vacancy = VacancyService.update_vacancy_status(db, vacancy_id, is_active, current_user)
    return {
        "message": f"Vacancy status updated to {'active' if is_active else 'inactive'}",
        "vacancy_id": vacancy_id,
        "is_active": vacancy.is_active
    }

@router.get("/{vacancy_id}/interests")
def get_vacancy_interests(
    vacancy_id: int,
    interest_status: Optional[InterestStatus] = None,
    current_user: CustomUser = Depends(require_roles(["admin", "HR"])),
    db: Session = Depends(get_db)
):
    return VacancyService.get_vacancy_with_interests(db, vacancy_id, current_user, interest_status)

@router.get("/statistics/dashboard")
def get_vacancy_statistics(
    current_user: CustomUser = Depends(require_roles(["admin", "HR"])),
    db: Session = Depends(get_db)
):
    return VacancyService.get_vacancy_statistics(db, current_user)

@router.post("/bulk-create", response_model=List[VacancyResponse])
def bulk_create_vacancies(
    vacancies_data: List[VacancyCreate],
    current_user: CustomUser = Depends(require_roles(["admin", "HR"])),
    db: Session = Depends(get_db)
):
    return VacancyService.bulk_create_vacancies(db, vacancies_data, current_user)