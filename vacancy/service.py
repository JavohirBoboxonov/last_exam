from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status
from config.models import Vacancy, Interest, CustomUser, InterestStatus
from vacancy.schema import VacancyCreate, VacancyUpdate

class VacancyService:
    
    @staticmethod
    def create_vacancy(
        db: Session,
        vacancy_data: VacancyCreate,
        current_user: CustomUser
    ) -> Vacancy:
        """Yangi vakansiya yaratish (faqat admin va HR)"""
        if current_user.role not in ["admin", "hr"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin and HR can create vacancies"
            )
        vacancy_data.user_id = current_user.id
        
        new_vacancy = Vacancy(**vacancy_data.dict())
        db.add(new_vacancy)
        db.commit()
        db.refresh(new_vacancy)
        return new_vacancy
    
    @staticmethod
    def get_vacancy_by_id(
        db: Session,
        vacancy_id: int,
        current_user: CustomUser
    ) -> Vacancy:
        vacancy = db.query(Vacancy).filter(Vacancy.id == vacancy_id).first()
        
        if not vacancy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vacancy not found"
            )
        return vacancy
    
    @staticmethod
    def get_all_vacancies(
        db: Session,
        current_user: CustomUser,
        skip: int = 0,
        limit: int = 100,
        filters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        query = db.query(Vacancy).filter(Vacancy.is_active == True)
        
        if filters:
            if filters.get("title"):
                query = query.filter(Vacancy.title.ilike(f"%{filters['title']}%"))
            if filters.get("location"):
                query = query.filter(Vacancy.location.ilike(f"%{filters['location']}%"))
            if filters.get("job_type"):
                query = query.filter(Vacancy.job_type == filters["job_type"])
            if filters.get("salary_min_gte"):
                query = query.filter(Vacancy.salary_min >= filters["salary_min_gte"])
            if filters.get("experience_required"):
                query = query.filter(Vacancy.experience_required == filters["experience_required"])
        
        total = query.count()
        vacancies = query.order_by(desc(Vacancy.created_at)).offset(skip).limit(limit).all()
        
        return {
            "total": total,
            "items": vacancies,
            "skip": skip,
            "limit": limit
        }
    
    @staticmethod
    def get_my_vacancies(
        db: Session,
        current_user: CustomUser,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> Dict[str, Any]:
        if current_user.role not in ["admin", "HR"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin and HR can view their vacancies"
            )
        
        query = db.query(Vacancy).filter(Vacancy.user_id == current_user.id)
        
        if is_active is not None:
            query = query.filter(Vacancy.is_active == is_active)
        
        total = query.count()
        vacancies = query.order_by(desc(Vacancy.created_at)).offset(skip).limit(limit).all()
        
        return {
            "total": total,
            "items": vacancies,
            "skip": skip,
            "limit": limit
        }
    
    @staticmethod
    def update_vacancy(
        db: Session,
        vacancy_id: int,
        vacancy_data: VacancyUpdate,
        current_user: CustomUser
    ) -> Vacancy:
        vacancy = db.query(Vacancy).filter(Vacancy.id == vacancy_id).first()
        
        if not vacancy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vacancy not found"
            )
        if current_user.role != "admin" and vacancy.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own vacancies"
            )
        
        update_data = vacancy_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(vacancy, key, value)
        
        db.commit()
        db.refresh(vacancy)
        return vacancy
    @staticmethod
    def delete_vacancy(
        db: Session,
        vacancy_id: int,
        current_user: CustomUser,
        hard_delete: bool = False
    ) -> Dict[str, str]:
        """Vakansiyani o'chirish (faqat admin va HR o'z vakansiyalarini)"""
        vacancy = db.query(Vacancy).filter(Vacancy.id == vacancy_id).first()
        
        if not vacancy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vacancy not found"
            )
        
        if current_user.role != "admin" and vacancy.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own vacancies"
            )
        
        if current_user.role == "admin":
            db.delete(vacancy)
            db.commit()
            return {"message": f"Vacancy {vacancy_id} permanently deleted"}
        else:
            vacancy.is_active = False
            db.commit()
            return {"message": f"Vacancy {vacancy_id} deactivated"}
    
    @staticmethod
    def restore_vacancy(
        db: Session,
        vacancy_id: int,
        current_user: CustomUser
    ) -> Vacancy:
        vacancy = db.query(Vacancy).filter(Vacancy.id == vacancy_id).first()
        
        if not vacancy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vacancy not found"
            )
        
        # Ruxsatni tekshirish
        if current_user.role != "admin" and vacancy.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only restore your own vacancies"
            )
        
        if vacancy.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vacancy is already active"
            )
        
        vacancy.is_active = True
        db.commit()
        db.refresh(vacancy)
        return vacancy
    
    @staticmethod
    def get_vacancy_with_interests(
        db: Session,
        vacancy_id: int,
        current_user: CustomUser,
        interest_status: Optional[InterestStatus] = None
    ) -> Dict[str, Any]:
        vacancy = db.query(Vacancy).filter(Vacancy.id == vacancy_id).first()
        
        if not vacancy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vacancy not found"
            )
        if current_user.role != "admin" and vacancy.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view interests for your own vacancies"
            )
    
        query = db.query(Interest).filter(Interest.vacancy_id == vacancy_id)
        
        if interest_status:
            query = query.filter(Interest.status == interest_status)
        
        interests = query.order_by(desc(Interest.created_at)).all()
        
        # User ma'lumotlarini qo'shish
        interests_with_users = []
        for interest in interests:
            user = db.query(CustomUser).filter(CustomUser.id == interest.user_id).first()
            interests_with_users.append({
                "id": interest.id,
                "vacancy_id": interest.vacancy_id,
                "user_id": interest.user_id,
                "cover_letter": interest.cover_letter,
                "expected_salary": interest.expected_salary,
                "message": interest.message,
                "status": interest.status,
                "created_at": interest.created_at,
                "updated_at": interest.updated_at,
                "user": {
                    "id": user.id,
                    "full_name": user.full_name,
                    "email": user.email,
                    "avatar": getattr(user, "avatar", None)
                }
            })
        
        return {
            "vacancy": vacancy,
            "total_interests": len(interests_with_users),
            "interests": interests_with_users,
            "statistics": {
                "pending": len([i for i in interests if i.status == InterestStatus.PENDING]),
                "viewed": len([i for i in interests if i.status == InterestStatus.VIEWED]),
                "accepted": len([i for i in interests if i.status == InterestStatus.ACCEPTED]),
                "rejected": len([i for i in interests if i.status == InterestStatus.REJECTED])
            }
        }
    
    @staticmethod
    def update_vacancy_status(
        db: Session,
        vacancy_id: int,
        is_active: bool,
        current_user: CustomUser
    ) -> Vacancy:
        """Vakansiya statusini o'zgartirish (active/inactive)"""
        vacancy = db.query(Vacancy).filter(Vacancy.id == vacancy_id).first()
        
        if not vacancy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vacancy not found"
            )
        if current_user.role != "admin" and vacancy.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own vacancies"
            )
        
        vacancy.is_active = is_active
        db.commit()
        db.refresh(vacancy)
        return vacancy
    
    @staticmethod
    def bulk_create_vacancies(
        db: Session,
        vacancies_data: List[VacancyCreate],
        current_user: CustomUser
    ) -> List[Vacancy]:
        if current_user.role not in ["admin", "HR"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin and HR can create vacancies"
            )
        
        created_vacancies = []
        for vacancy_data in vacancies_data:
            vacancy_data.user_id = current_user.id
            new_vacancy = Vacancy(**vacancy_data.dict())
            db.add(new_vacancy)
            created_vacancies.append(new_vacancy)
        
        db.commit()
        for vacancy in created_vacancies:
            db.refresh(vacancy)
        
        return created_vacancies
    
    @staticmethod
    def get_vacancy_statistics(
        db: Session,
        current_user: CustomUser
    ) -> Dict[str, Any]:
        if current_user.role not in ["admin", "hr"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin and HR can view statistics"
            )
        if current_user.role == "admin":
            total_vacancies = db.query(Vacancy).count()
            active_vacancies = db.query(Vacancy).filter(Vacancy.is_active == True).count()
            inactive_vacancies = db.query(Vacancy).filter(Vacancy.is_active == False).count()
            hr_stats = []
            hr_users = db.query(CustomUser).filter(CustomUser.role == "hr").all()
            for hr in hr_users:
                hr_vacancies = db.query(Vacancy).filter(Vacancy.user_id == hr.id).count()
                hr_active = db.query(Vacancy).filter(
                    Vacancy.user_id == hr.id,
                    Vacancy.is_active == True
                ).count()
                hr_stats.append({
                    "hr_id": hr.id,
                    "hr_name": hr.full_name,
                    "total_vacancies": hr_vacancies,
                    "active_vacancies": hr_active
                })
            
            return {
                "total_vacancies": total_vacancies,
                "active_vacancies": active_vacancies,
                "inactive_vacancies": inactive_vacancies,
                "hr_statistics": hr_stats
            }
        else:
            my_vacancies = db.query(Vacancy).filter(Vacancy.user_id == current_user.id)
            
            total = my_vacancies.count()
            active = my_vacancies.filter(Vacancy.is_active == True).count()
            inactive = my_vacancies.filter(Vacancy.is_active == False).count()
            total_interests = 0
            pending_interests = 0
            accepted_interests = 0
            rejected_interests = 0
            
            vacancies = my_vacancies.all()
            for vacancy in vacancies:
                interests = db.query(Interest).filter(Interest.vacancy_id == vacancy.id).all()
                total_interests += len(interests)
                pending_interests += len([i for i in interests if i.status == InterestStatus.PENDING])
                accepted_interests += len([i for i in interests if i.status == InterestStatus.ACCEPTED])
                rejected_interests += len([i for i in interests if i.status == InterestStatus.REJECTED])
            
            return {
                "total_vacancies": total,
                "active_vacancies": active,
                "inactive_vacancies": inactive,
                "interests_statistics": {
                    "total": total_interests,
                    "pending": pending_interests,
                    "accepted": accepted_interests,
                    "rejected": rejected_interests
                }
            }