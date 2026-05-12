from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession # Session emas, AsyncSession
from typing import Optional, List

from config.database import get_db
from config.models import CustomUser, InterestStatus
from vacancy.schema import *
from vacancy.auth import get_current_user, require_roles
from vacancy.service import VacancyService

router = APIRouter(prefix="/vacancies", tags=["Vacancies"])

# 1. create_vacancy
@router.post("/create", response_model=VacancyResponse, status_code=status.HTTP_201_CREATED)
async def create_vacancy(
    vacancy_data: VacancyCreate,
    current_user: CustomUser = Depends(require_roles(["admin", "HR"])),
    db: AsyncSession = Depends(get_db)
):  
    return await VacancyService.create_vacancy(db, vacancy_data, current_user)

# 2. get_vacancies
@router.get("/", response_model=VacancyListResponse)
async def get_vacancies( # async qo'shildi
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    title: Optional[str] = None,
    location: Optional[str] = None,
    job_type: Optional[str] = None,
    salary_min_gte: Optional[float] = None,
    experience_required: Optional[str] = None,
    current_user: CustomUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    filters = {
        "title": title,
        "location": location,
        "job_type": job_type,
        "salary_min_gte": salary_min_gte,
        "experience_required": experience_required
    }
    # MUHIM: await qo'shildi
    return await VacancyService.get_all_vacancies(db, current_user, skip, limit, filters)

# 3. get_my_vacancies
@router.get("/my-vacancies", response_model=VacancyListResponse)
async def get_my_vacancies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = None,
    current_user: CustomUser= Depends(require_roles(["admin", "HR"])),
    db: AsyncSession = Depends(get_db)
):
    return await VacancyService.get_my_vacancies(db, current_user, skip, limit, is_active)

# 4. get_vacancy (ID bo'yicha)
@router.get("/{vacancy_id}", response_model=VacancyResponse)
async def get_vacancy(
    vacancy_id: int,
    current_user: CustomUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await VacancyService.get_vacancy_by_id(db, vacancy_id, current_user)

# 5. update_vacancy
@router.patch("/update{vacancy_id}", response_model=VacancyResponse)
async def update_vacancy(
    vacancy_id: int,
    vacancy_data: VacancyUpdate,
    current_user: CustomUser = Depends(require_roles(["admin", "HR"])),
    db: AsyncSession = Depends(get_db)
):
    return await VacancyService.update_vacancy(db, vacancy_id, vacancy_data, current_user)

@router.delete("/delete/{vacancy_id}")
async def delete_vacancy(
    vacancy_id: int,
    current_user: CustomUser = Depends(require_roles(["admin", "HR"])),
    db: AsyncSession = Depends(get_db)
):
    return await VacancyService.delete_vacancy(db, vacancy_id, current_user)

@router.get("/{vacancy_id}/interests")
async def get_vacancy_interests(
    vacancy_id: int,
    interest_status: Optional[InterestStatus] = None,
    current_user: CustomUser = Depends(require_roles(["admin", "HR"])),
    db: AsyncSession = Depends(get_db)
):
    return await VacancyService.get_vacancy_with_interests(db, vacancy_id, current_user, interest_status) # await
@router.get("/statistics/dashboard")
async def get_vacancy_statistics(
    current_user: CustomUser = Depends(require_roles(["admin", "HR"])),
    db: AsyncSession = Depends(get_db)
):
    return await VacancyService.get_vacancy_statistics(db, current_user)

# 11. bulk_create
@router.post("/bulk-create", response_model=List[VacancyResponse])
async def bulk_create_vacancies( # async
    vacancies_data: List[VacancyCreate],
    current_user: CustomUser = Depends(require_roles(["admin", "HR"])),
    db: AsyncSession = Depends(get_db)
):
    return await VacancyService.bulk_create_vacancies(db, vacancies_data, current_user)