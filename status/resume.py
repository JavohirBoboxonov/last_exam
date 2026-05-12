from config.models import CustomUser, Resume, Vacancy, VacancyApplication, ApplicationStatus
from status.schema import *
from config.database import get_db, AsyncSession
from fastapi import HTTPException


class ResumeService:
    @staticmethod
    def create_resume(db: AsyncSession, resume_data: ResumeCreate, current_user: CustomUser) -> Resume:
        """Resume yaratish"""
        new_resume = Resume(
            user_id=current_user.id,
            **resume_data.dict()
        )
        db.add(new_resume)
        db.commit()
        db.refresh(new_resume)
        return new_resume
    
    @staticmethod
    def get_user_resumes(db: AsyncSession, current_user: CustomUser) -> List[Resume]:
        resumes = db.query(Resume).filter(
            Resume.user_id == current_user.id,
            Resume.is_active == True
        ).order_by(Resume.created_at.desc()).all()
        return resumes
    
    @staticmethod
    def get_resume_by_id(db: AsyncSession, resume_id: int, current_user: CustomUser) -> Resume:
        """Resume ni ID bo'yicha olish"""
        resume = db.query(Resume).filter(
            Resume.id == resume_id,
            Resume.is_active == True
        ).first()
        
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        if resume.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="You can only view your own resumes")
        
        return resume
    
    @staticmethod
    def update_resume(db: AsyncSession, resume_id: int, resume_data: ResumeUpdate, current_user: CustomUser) -> Resume:
        """Resume ni yangilash"""
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        if resume.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="You can only update your own resumes")
        
        for key, value in resume_data.dict(exclude_unset=True).items():
            setattr(resume, key, value)
        
        db.commit()
        db.refresh(resume)
        return resume
    
    @staticmethod
    def delete_resume(db: AsyncSession, resume_id: int, current_user: CustomUser) -> dict:
        """Resume ni o'chirish (soft delete)"""
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        if resume.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="You can only delete your own resumes")
        
        resume.is_active = False
        db.commit()
        
        return {"message": "Resume deleted successfully"}

class ApplicationService:
    @staticmethod
    def apply_to_vacancy(db: AsyncSession, vacancy_id: int, apply_data: VacancyApplyRequest, current_user: CustomUser) -> Dict[str, Any]:
        # Vakansiya mavjudligini tekshirish
        vacancy = db.query(Vacancy).filter(
            Vacancy.id == vacancy_id,
            Vacancy.is_active == True
        ).first()
        
        if not vacancy:
            raise HTTPException(status_code=404, detail="Vacancy not found or not active")
        
        # Resume mavjudligini tekshirish
        resume = db.query(Resume).filter(
            Resume.id == apply_data.resume_id,
            Resume.user_id == current_user.id,
            Resume.is_active == True
        ).first()
        
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found or not active")
        
        # Oldin ariza berganmi tekshirish
        existing_application = db.query(VacancyApplication).filter(
            VacancyApplication.vacancy_id == vacancy_id,
            VacancyApplication.user_id == current_user.id,
            VacancyApplication.status != ApplicationStatusEnum.WITHDRAWN
        ).first()
        
        if existing_application:
            raise HTTPException(status_code=400, detail="You have already applied to this vacancy")
        
        # Ariza yaratish
        new_application = VacancyApplication(
            vacancy_id=vacancy_id,
            user_id=current_user.id,
            resume_id=apply_data.resume_id,
            message=apply_data.message,
            cover_letter=apply_data.cover_letter or resume.cover_letter,
            expected_salary=apply_data.expected_salary,
            status=ApplicationStatusEnum.PENDING
        )
        
        db.add(new_application)
        db.commit()
        db.refresh(new_application)
        
        return {
            "message": "Successfully applied to vacancy",
            "application_id": new_application.id,
            "status": new_application.status.value,
            "applied_at": new_application.created_at
        }
    
    @staticmethod
    def get_my_applications(db: AsyncSession, current_user: CustomUser, status: Optional[ApplicationStatusEnum], skip: int, limit: int) -> Dict[str, Any]:
        """Foydalanuvchining barcha arizalarini olish"""
        query = db.query(VacancyApplication).filter(VacancyApplication.user_id == current_user.id)
        
        if status:
            query = query.filter(VacancyApplication.status == status)
        
        total = query.count()
        applications = query.order_by(VacancyApplication.created_at.desc()).offset(skip).limit(limit).all()
        
        result = []
        for app in applications:
            vacancy = db.query(Vacancy).filter(Vacancy.id == app.vacancy_id).first()
            resume = db.query(Resume).filter(Resume.id == app.resume_id).first()
            
            result.append({
                "id": app.id,
                "vacancy_id": app.vacancy_id,
                "vacancy_title": vacancy.title if vacancy else None,
                "vacancy_location": vacancy.location if vacancy else None,
                "resume_id": app.resume_id,
                "resume_position": resume.position if resume else None,
                "status": app.status,
                "message": app.message,
                "expected_salary": app.expected_salary,
                "feedback": app.feedback,
                "created_at": app.created_at,
                "updated_at": app.updated_at
            })
        
        return {"total": total, "items": result, "skip": skip, "limit": limit}
    
    @staticmethod
    def get_vacancy_applications(db: AsyncSession, vacancy_id: int, current_user: CustomUser, status: Optional[ApplicationStatusEnum], skip: int, limit: int) -> Dict[str, Any]:
        """Vakansiyaga kelgan arizalarni olish (faqat admin va HR)"""
        vacancy = db.query(Vacancy).filter(Vacancy.id == vacancy_id).first()
        
        if not vacancy:
            raise HTTPException(status_code=404, detail="Vacancy not found")
        
        if current_user.role not in ["admin"] and vacancy.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="You can only view applications for your own vacancies")
        
        query = db.query(VacancyApplication).filter(VacancyApplication.vacancy_id == vacancy_id)
        
        if status:
            query = query.filter(VacancyApplication.status == status)
        
        total = query.count()
        applications = query.order_by(VacancyApplication.created_at.desc()).offset(skip).limit(limit).all()
        
        result = []
        for app in applications:
            user = db.query(CustomUser).filter(CustomUser.id == app.user_id).first()
            resume = db.query(Resume).filter(Resume.id == app.resume_id).first()
            
            result.append({
                "id": app.id,
                "user": {
                    "id": user.id if user else None,
                    "full_name": user.full_name if user else None,
                    "email": user.email if user else None
                },
                "resume": {
                    "id": resume.id if resume else None,
                    "position": resume.position if resume else None,
                    "experience_years": resume.experience_years if resume else None,
                    "skills": resume.skills if resume else None
                },
                "status": app.status,
                "message": app.message,
                "expected_salary": app.expected_salary,
                "feedback": app.feedback,
                "created_at": app.created_at
            })
        
        stats = {
            "total": total,
            "pending": db.query(VacancyApplication).filter(
                VacancyApplication.vacancy_id == vacancy_id,
                VacancyApplication.status == ApplicationStatusEnum.PENDING
            ).count(),
            "reviewed": db.query(VacancyApplication).filter(
                VacancyApplication.vacancy_id == vacancy_id,
                VacancyApplication.status == ApplicationStatusEnum.REVIEWED
            ).count(),
            "shortlisted": db.query(VacancyApplication).filter(
                VacancyApplication.vacancy_id == vacancy_id,
                VacancyApplication.status == ApplicationStatusEnum.SHORTLISTED
            ).count(),
            "accepted": db.query(VacancyApplication).filter(
                VacancyApplication.vacancy_id == vacancy_id,
                VacancyApplication.status == ApplicationStatusEnum.ACCEPTED
            ).count(),
            "rejected": db.query(VacancyApplication).filter(
                VacancyApplication.vacancy_id == vacancy_id,
                VacancyApplication.status == ApplicationStatusEnum.REJECTED
            ).count()
        }
        
        return {
            "vacancy_id": vacancy_id,
            "vacancy_title": vacancy.title,
            "statistics": stats,
            "applications": result,
            "skip": skip,
            "limit": limit
        }
    
    @staticmethod
    def update_application_status(db: AsyncSession, application_id: int, update_data: VacancyApplicationUpdate, current_user: CustomUser) -> Dict[str, Any]:
        """Ariza statusini yangilash"""
        application = db.query(VacancyApplication).filter(VacancyApplication.id == application_id).first()
        
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        vacancy = db.query(Vacancy).filter(Vacancy.id == application.vacancy_id).first()
        
        if current_user.role not in ["admin"] and vacancy.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="You can only update applications for your own vacancies")
        
        if update_data.status:
            application.status = update_data.status
            application.reviewed_by = current_user.id
            application.reviewed_at = datetime.utcnow()
        
        if update_data.feedback:
            application.feedback = update_data.feedback
        
        if update_data.expected_salary:
            application.expected_salary = update_data.expected_salary
        
        db.commit()
        db.refresh(application)
        
        return {
            "message": f"Application status updated to {application.status.value}",
            "application_id": application.id,
            "status": application.status.value,
            "feedback": application.feedback
        }
    
    @staticmethod
    def withdraw_application(db: AsyncSession, application_id: int, current_user: CustomUser) -> Dict[str, str]:
        """Arizani qaytarib olish"""
        application = db.query(VacancyApplication).filter(
            VacancyApplication.id == application_id,
            VacancyApplication.user_id == current_user.id
        ).first()
        
        if not application:
            raise HTTPException(status_code=404, detail="Application not found or not yours")
        
        if application.status == ApplicationStatusEnum.WITHDRAWN:
            raise HTTPException(status_code=400, detail="Application already withdrawn")
        
        application.status = ApplicationStatusEnum.WITHDRAWN
        db.commit()
        
        return {"message": "Application withdrawn successfully"}
    
    @staticmethod
    def check_already_applied(db: AsyncSession, vacancy_id: int, current_user: CustomUser) -> Dict[str, Any]:
        """Foydalanuvchi bu vakansiyaga ariza berganmi tekshirish"""
        application = db.query(VacancyApplication).filter(
            VacancyApplication.vacancy_id == vacancy_id,
            VacancyApplication.user_id == current_user.id,
            VacancyApplication.status != ApplicationStatusEnum.WITHDRAWN
        ).first()
        
        if application:
            return {
                "applied": True,
                "application_id": application.id,
                "status": application.status.value,
                "applied_at": application.created_at
            }
        
        return {"applied": False, "message": "You haven't applied to this vacancy yet"}
        