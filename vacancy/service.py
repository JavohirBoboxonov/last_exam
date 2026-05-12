from sqlalchemy import and_, or_, desc, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status
from config.models import Vacancy, Interest, CustomUser, InterestStatus
from vacancy.schema import VacancyCreate, VacancyUpdate

class VacancyService:
    
    @staticmethod
    async def create_vacancy(
        db: AsyncSession,
        vacancy_data: VacancyCreate,
        current_user: CustomUser
    ) -> Vacancy:
        """Yangi vakansiya yaratish (faqat admin va HR)"""
        if current_user.role not in ["admin", "hr"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin and HR can create vacancies"
            )
        
        data = vacancy_data.dict()
        data["user_id"] = current_user.id
        
        new_vacancy = Vacancy(**data)
        db.add(new_vacancy)
        await db.commit()
        await db.refresh(new_vacancy)
        return new_vacancy
    
    @staticmethod
    async def get_vacancy_by_id(
        db: AsyncSession,
        vacancy_id: int,
        current_user: CustomUser
    ) -> Vacancy:
        stmt = select(Vacancy).where(Vacancy.id == vacancy_id)
        result = await db.execute(stmt)
        vacancy = result.scalars().first()
        
        if not vacancy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vacancy not found"
            )
        return vacancy
    
    @staticmethod
    async def get_all_vacancies(
        db: AsyncSession,
        current_user: CustomUser,
        skip: int = 0,
        limit: int = 100,
        filters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        stmt = select(Vacancy).where(Vacancy.is_active == True)
        
        if filters:
            if filters.get("title"):
                stmt = stmt.where(Vacancy.title.ilike(f"%{filters['title']}%"))
            if filters.get("location"):
                stmt = stmt.where(Vacancy.location.ilike(f"%{filters['location']}%"))
            if filters.get("job_type"):
                stmt = stmt.where(Vacancy.job_type == filters["job_type"])
            if filters.get("salary_min_gte"):
                stmt = stmt.where(Vacancy.salary_min >= filters["salary_min_gte"])
            if filters.get("experience_required"):
                stmt = stmt.where(Vacancy.experience_required == filters["experience_required"])
        
        # Total count uchun alohida so'rov
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0
        
        # Ma'lumotlarni olish
        stmt = stmt.order_by(desc(Vacancy.created_at)).offset(skip).limit(limit)
        result = await db.execute(stmt)
        vacancies = result.scalars().all()
        
        return {
            "total": total,
            "items": vacancies,
            "skip": skip,
            "limit": limit
        }
    
    @staticmethod
    async def get_my_vacancies(
        db: AsyncSession,
        current_user: CustomUser,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> Dict[str, Any]:
        if current_user.role not in ["admin", "hr", "HR"]: # Kichik harflarni ham tekshirish
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin and HR can view their vacancies"
            )
        
        stmt = select(Vacancy).where(Vacancy.user_id == current_user.id)
        
        if is_active is not None:
            stmt = stmt.where(Vacancy.is_active == is_active)
        
        # Count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0
        
        # Items
        stmt = stmt.order_by(desc(Vacancy.created_at)).offset(skip).limit(limit)
        result = await db.execute(stmt)
        vacancies = result.scalars().all()
        
        return {
            "total": total,
            "items": vacancies,
            "skip": skip,
            "limit": limit
        }
    
    @staticmethod
    async def update_vacancy(
        db: AsyncSession,
        vacancy_id: int,
        vacancy_data: VacancyUpdate,
        current_user: CustomUser
    ) -> Vacancy:
        vacancy = await VacancyService.get_vacancy_by_id(db, vacancy_id, current_user)
        
        if current_user.role != "admin" and vacancy.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own vacancies"
            )
        
        update_data = vacancy_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(vacancy, key, value)
        
        await db.commit()
        await db.refresh(vacancy)
        return vacancy

    @staticmethod
    async def delete_vacancy(
        db: AsyncSession,
        vacancy_id: int,
        current_user: CustomUser
    ) -> Dict[str, str]:
        vacancy = await VacancyService.get_vacancy_by_id(db, vacancy_id, current_user)
        
        if current_user.role != "admin" and vacancy.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own vacancies"
            )
        
        if current_user.role == "admin":
            await db.delete(vacancy)
            await db.commit()
            return {"message": f"Vacancy {vacancy_id} permanently deleted"}
        else:
            vacancy.is_active = False
            await db.commit()
            return {"message": f"Vacancy {vacancy_id} deactivated"}
    
    @staticmethod
    async def get_vacancy_with_interests(
        db: AsyncSession,
        vacancy_id: int,
        current_user: CustomUser,
        interest_status: Optional[InterestStatus] = None
    ) -> Dict[str, Any]:
        vacancy = await VacancyService.get_vacancy_by_id(db, vacancy_id, current_user)
        
        if current_user.role != "admin" and vacancy.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view interests for your own vacancies"
            )
    
        # Interestlarni olish (User bilan bog'langan holda select qilsa ham bo'ladi, lekin kodingiz uslubida qoldirdim)
        stmt = select(Interest).where(Interest.vacancy_id == vacancy_id)
        if interest_status:
            stmt = stmt.where(Interest.status == interest_status)
        
        result = await db.execute(stmt.order_by(desc(Interest.created_at)))
        interests = result.scalars().all()
        
        interests_with_users = []
        for interest in interests:
            user_stmt = select(CustomUser).where(CustomUser.id == interest.user_id)
            user_res = await db.execute(user_stmt)
            user = user_res.scalars().first()
            
            interests_with_users.append({
                "id": interest.id,
                "vacancy_id": interest.vacancy_id,
                "user_id": interest.user_id,
                "cover_letter": interest.cover_letter,
                "status": interest.status,
                "created_at": interest.created_at,
                "user": {
                    "id": user.id,
                    "full_name": user.full_name,
                    "email": user.email
                } if user else None
            })
        
        return {
            "vacancy": vacancy,
            "total_interests": len(interests_with_users),
            "interests": interests_with_users,
            "statistics": {
                "pending": len([i for i in interests if i.status == InterestStatus.PENDING]),
                "accepted": len([i for i in interests if i.status == InterestStatus.ACCEPTED]),
                "rejected": len([i for i in interests if i.status == InterestStatus.REJECTED])
            }
        }

    @staticmethod
    async def get_vacancy_statistics(
        db: AsyncSession,
        current_user: CustomUser
    ) -> Dict[str, Any]:
        if current_user.role not in ["admin", "hr"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin and HR can view statistics"
            )

        if current_user.role == "admin":
            # Total stats
            res_total = await db.execute(select(func.count(Vacancy.id)))
            res_active = await db.execute(select(func.count(Vacancy.id)).where(Vacancy.is_active == True))
            
            hr_users_res = await db.execute(select(CustomUser).where(CustomUser.role == "hr"))
            hr_users = hr_users_res.scalars().all()
            
            hr_stats = []
            for hr in hr_users:
                v_count_res = await db.execute(select(func.count(Vacancy.id)).where(Vacancy.user_id == hr.id))
                hr_stats.append({
                    "hr_name": hr.full_name,
                    "total_vacancies": v_count_res.scalar() or 0
                })
            
            return {
                "total_vacancies": res_total.scalar() or 0,
                "active_vacancies": res_active.scalar() or 0,
                "hr_statistics": hr_stats
            }
        else:
            # HR o'z statistikasi
            stmt = select(Vacancy).where(Vacancy.user_id == current_user.id)
            res = await db.execute(stmt)
            vacancies = res.scalars().all()
            
            total_interests = 0
            for v in vacancies:
                int_res = await db.execute(select(func.count(Interest.id)).where(Interest.vacancy_id == v.id))
                total_interests += (int_res.scalar() or 0)
                
            return {
                "my_total_vacancies": len(vacancies),
                "total_received_interests": total_interests
            }
    @staticmethod
    async def create_vacancy(
        db: AsyncSession,
        vacancy_data: VacancyCreate,
        current_user: CustomUser
    ) -> Vacancy:
        data = vacancy_data.dict()
        data["user_id"] = current_user.id 
        new_vacancy = Vacancy(**data)
        
        db.add(new_vacancy)
        await db.commit()
        await db.refresh(new_vacancy)
        
        return new_vacancy
    
    # vacancy/service.py ichida

    @staticmethod
    async def get_my_vacancies(
        db: AsyncSession,
        current_user: CustomUser,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None  # API dan kelayotgan argument
    ) -> Dict[str, Any]:
        stmt = select(Vacancy).where(Vacancy.user_id == current_user.id)
        if is_active is not None:
            stmt = stmt.where(Vacancy.is_active == is_active)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_res = await db.execute(count_stmt)
        total = total_res.scalar() or 0
        
        # 4. Ma'lumotlarni o'zini olish
        stmt = stmt.order_by(desc(Vacancy.created_at)).offset(skip).limit(limit)
        result = await db.execute(stmt)
        vacancies = result.scalars().all()
        
        return {
            "total": total,
            "items": vacancies,
            "skip": skip,
            "limit": limit
        }