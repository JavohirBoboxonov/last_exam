from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from fastapi import HTTPException, status
from typing import Optional, Dict, Any
from datetime import datetime

from config.models import Vacancy, VacancyApplication, Resume, CustomUser, ApplicationStatus
from status.schema import VacancyApplyRequest, VacancyApplicationUpdate, ResumeCreate

class ApplicationSecondService:
    
    @staticmethod
    async def apply_to_vacancy(
        db: AsyncSession, 
        vacancy_id: int, 
        apply_data: VacancyApplyRequest, 
        current_user: CustomUser
    ) -> Dict[str, Any]:
        v_stmt = select(Vacancy).where(Vacancy.id == vacancy_id, Vacancy.is_active == True)
        v_res = await db.execute(v_stmt)
        vacancy = v_res.scalar_one_or_none()
        if not vacancy:
            raise HTTPException(status_code=404, detail="Vakansiya topilmadi yoki faol emas")
        r_stmt = select(Resume).where(Resume.id == apply_data.resume_id, Resume.user_id == current_user.id)
        r_res = await db.execute(r_stmt)
        resume = r_res.scalar_one_or_none()
        if not resume:
            raise HTTPException(status_code=404, detail="Rezyume topilmadi")
        existing_stmt = select(VacancyApplication).where(
            VacancyApplication.vacancy_id == vacancy_id,
            VacancyApplication.user_id == current_user.id,
            VacancyApplication.status != ApplicationStatus.WITHDRAWN
        )
        existing_res = await db.execute(existing_stmt)
        if existing_res.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Siz ushbu vakansiyaga ariza topshirib bo'lgansiz")

        # 4. Yangi ariza yaratish
        new_application = VacancyApplication(
            vacancy_id=vacancy_id,
            user_id=current_user.id,
            resume_id=apply_data.resume_id,
            message=apply_data.message,
            status=ApplicationStatus.PENDING
        )
        
        db.add(new_application)
        try:
            await db.commit()
            await db.refresh(new_application)
            return {
                "message": "Vakansiyaga muvaffaqiyatli ariza topshirildi",
                "application_id": new_application.id,
                "status": new_application.status.value,
                "applied_at": new_application.created_at
            }
        except Exception as e:
            await db.rollback()
            raise e

    @staticmethod
    async def get_my_applications(
        db: AsyncSession,
        current_user: CustomUser,
        status: Optional[ApplicationStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        stmt = select(VacancyApplication).where(VacancyApplication.user_id == current_user.id)
        if status:
            stmt = stmt.where(VacancyApplication.status == status)
        
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_res = await db.execute(count_stmt)
        total = total_res.scalar()
        stmt = stmt.order_by(desc(VacancyApplication.created_at)).offset(skip).limit(limit)
        apps_res = await db.execute(stmt)
        applications = apps_res.scalars().all()

        return {"total": total, "items": applications}

    @staticmethod
    async def check_already_applied(
        db: AsyncSession,
        vacancy_id: int,
        current_user: CustomUser
    ) -> Dict[str, Any]:
        """Ariza berilganligini tekshirish"""
        stmt = select(VacancyApplication).where(
            VacancyApplication.vacancy_id == vacancy_id,
            VacancyApplication.user_id == current_user.id,
            VacancyApplication.status != ApplicationStatus.WITHDRAWN
        )
        result = await db.execute(stmt)
        application = result.scalar_one_or_none()
        
        if application:
            return {
                "applied": True, 
                "application_id": application.id, 
                "status": application.status.value
            }
        return {"applied": False, "message": "Siz hali ariza topshirmagansiz"}