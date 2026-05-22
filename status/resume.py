from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status
from datetime import datetime

from config.models import Vacancy, VacancyApplication, Resume, CustomUser, ApplicationStatus
from status.schema import VacancyApplyRequest, VacancyApplicationUpdate, ResumeCreate, ResumeUpdate

class ResumeService:
    @staticmethod
    async def create_resume(db: AsyncSession, resume_data: ResumeCreate, current_user: CustomUser):
        """Asinxron Resume yaratish"""
        new_resume = Resume(
            user_id=current_user.id,
            **resume_data.model_dump()
        )
        db.add(new_resume)
        try:
            await db.commit() #
            # ID va default qiymatlarni olish uchun select ishlatamiz
            stmt = select(Resume).where(Resume.id == new_resume.id)
            result = await db.execute(stmt)
            return result.scalar_one()
        except Exception as e:
            await db.rollback()
            raise e

    @staticmethod
    async def get_user_resumes(db: AsyncSession, current_user: CustomUser):
        stmt = select(Resume).where(
            Resume.user_id == current_user.id,
            Resume.is_active == True
        ).order_by(desc(Resume.created_at))
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_resume_by_id(db: AsyncSession, resume_id: int, current_user: CustomUser):
        stmt = select(Resume).where(Resume.id == resume_id, Resume.is_active == True)
        result = await db.execute(stmt)
        resume = result.scalar_one_or_none()
        if not resume or resume.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Resume topilmadi")
        return resume
    @staticmethod
    async def update_resume(db: AsyncSession, resume_id: int, resume_data: ResumeUpdate, current_user: CustomUser):
        stmt = select(Resume).where(Resume.id == resume_id)
        result = await db.execute(stmt)
        resume = result.scalar_one_or_none()
        
        if not resume:
            raise HTTPException(status_code=404, detail="Resume topilmadi")
        
        if resume.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Siz faqat o'z resumeingizni tahrirlashingiz mumkin")
        update_data = resume_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(resume, key, value)
        resume.updated_at = datetime.utcnow()

        try:
            await db.commit()
            await db.refresh(resume)
            return resume
        except Exception as e:
            await db.rollback()
            raise e

class ApplicationService:
    @staticmethod
    async def apply_to_vacancy(db: AsyncSession, vacancy_id: int, apply_data: VacancyApplyRequest, current_user: CustomUser):
        v_stmt = select(Vacancy).where(Vacancy.id == vacancy_id, Vacancy.is_active == True)
        v_res = await db.execute(v_stmt)
        vacancy = v_res.scalar_one_or_none()
        if not vacancy:
            raise HTTPException(status_code=404, detail="Vakansiya faol emas")

        stmt = select(VacancyApplication).where(
            VacancyApplication.vacancy_id == vacancy_id,
            VacancyApplication.user_id == current_user.id,
            VacancyApplication.status != ApplicationStatus.WITHDRAWN
        )
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Siz ariza topshirib bo'lgansiz")

        new_app = VacancyApplication(
            vacancy_id=vacancy_id,
            user_id=current_user.id,
            resume_id=apply_data.resume_id,
            status=ApplicationStatus.PENDING,
            message=apply_data.message
        )
        db.add(new_app)
        await db.commit() #
        await db.refresh(new_app)
        return {"application_id": new_app.id, "status": new_app.status.value, "message": new_app.message, "applied_at": new_app.created_at}

    @staticmethod
    async def check_already_applied(db: AsyncSession, vacancy_id: int, current_user: CustomUser):
        stmt = select(VacancyApplication).where(
            VacancyApplication.vacancy_id == vacancy_id,
            VacancyApplication.user_id == current_user.id,
            VacancyApplication.status != ApplicationStatus.WITHDRAWN
        )
        result = await db.execute(stmt)
        app = result.scalar_one_or_none()
        return {"applied": app is not None, "status": app.status.value if app else None}
    @staticmethod
    async def update_application_status(
        db: AsyncSession,
        application_id: int,
        update_data: VacancyApplicationUpdate,
        current_user: CustomUser
    ) -> Dict[str, Any]:
        stmt = select(VacancyApplication).where(VacancyApplication.id == application_id)
        result = await db.execute(stmt)
        application = result.scalar_one_or_none()
        
        if not application:
            raise HTTPException(status_code=404, detail="Ariza topilmadi")
        v_stmt = select(Vacancy).where(Vacancy.id == application.vacancy_id)
        v_result = await db.execute(v_stmt)
        vacancy = v_result.scalar_one_or_none()
        
        if current_user.role not in ["admin", "HR"] and (not vacancy or vacancy.user_id != current_user.id):
            raise HTTPException(
                status_code=403, 
                detail="Sizda ushbu ariza statusini o'zgartirish huquqi yo'q"
            )
        if update_data.status:
            application.status = update_data.status
        if update_data.feedback:
            application.feedback = update_data.feedback
        if update_data.expected_salary:
            application.expected_salary = update_data.expected_salary
        
        try:
            await db.commit()
            await db.refresh(application)
            return {
                "message": f"Ariza statusi '{application.status.value}' ga o'zgartirildi",
                "application_id": application.id,
                "status": application.status.value,
                "feedback": application.feedback
            }
        except Exception as e:
            await db.rollback()
            raise e