from sqlalchemy import (
    Column,
    ForeignKey, 
    String, 
    Integer, 
    Boolean,
    DateTime,
    Text,
    Float,
    Enum as SQLEnum
)
from datetime import datetime
from config.database import Base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

roles = ["admin", "HR", "Candidate"]

# ============ ENUMS ============
class InterestStatus(enum.Enum):
    PENDING = "pending"
    VIEWED = "viewed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

class ApplicationStatus(enum.Enum):
    PENDING = "pending"
    REVIEWED = "reviewed"
    SHORTLISTED = "shortlisted"
    REJECTED = "rejected"
    ACCEPTED = "accepted"
    WITHDRAWN = "withdrawn"
class CustomUser(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    username = Column(String(30), unique=True, index=True)
    email = Column(String(50), unique=True)
    phone_number = Column(String(15), unique=True)
    is_staff = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    role = Column(String(20), default="Candidate", nullable=False)
    password = Column(String(200))
    register_at = Column(DateTime(timezone=True), server_default=func.now())
    vacancies = relationship('Vacancy', back_populates='user')
    interests = relationship('Interest', back_populates='user')
    resumes = relationship('Resume', back_populates='user', cascade='all, delete-orphan')
    applications = relationship('VacancyApplication', foreign_keys='VacancyApplication.user_id', back_populates='user')
    reviewed_applications = relationship('VacancyApplication', foreign_keys='VacancyApplication.reviewed_by')
class Vacancy(Base):
    __tablename__ = 'vacancies'
    
    id = Column(Integer, primary_key=True, unique=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    requirements = Column(Text, nullable=True)
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    salary_currency = Column(String(3), default='UZS')
    location = Column(String(255), nullable=True)
    job_type = Column(String(50), default='full_time')
    experience_required = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = relationship('CustomUser', back_populates='vacancies')
    interests = relationship('Interest', back_populates='vacancy', cascade='all, delete-orphan')
    applications = relationship('VacancyApplication', back_populates='vacancy', cascade='all, delete-orphan')
class Interest(Base):
    __tablename__ = 'interests'
    
    id = Column(Integer, primary_key=True, unique=True, index=True)
    vacancy_id = Column(Integer, ForeignKey('vacancies.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    status = Column(SQLEnum(InterestStatus), default=InterestStatus.PENDING)
    cover_letter = Column(Text, nullable=True)
    expected_salary = Column(Float, nullable=True)
    message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    vacancy = relationship('Vacancy', back_populates='interests')
    user = relationship('CustomUser', back_populates='interests')
class Resume(Base):
    __tablename__ = 'resumes'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    
    # Professional ma'lumotlar
    position = Column(String(255), nullable=False)
    experience_years = Column(Float, default=0)
    skills = Column(Text, nullable=True)
    education = Column(Text, nullable=True)
    previous_jobs = Column(Text, nullable=True) 
    
    # Linklar
    portfolio_url = Column(String(500), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    github_url = Column(String(500), nullable=True)
    
    # Qo'shimcha
    cover_letter = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=True)
    
    is_active = Column(Boolean, server_default='true',default=True)
    is_verified = Column(Boolean, server_default='false',default=False)
    created_at = Column(DateTime, server_default=func.now(),default=datetime.utcnow)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=datetime.utcnow)
    user = relationship('CustomUser', back_populates='resumes')
    applications = relationship('VacancyApplication', back_populates='resume', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Resume(id={self.id}, position='{self.position}', user_id={self.user_id})>"
class VacancyApplication(Base):
    __tablename__ = 'vacancy_applications'
    id = Column(Integer, primary_key=True, index=True)

    vacancy_id = Column(Integer, ForeignKey('vacancies.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    resume_id = Column(Integer, ForeignKey('resumes.id', ondelete='CASCADE'), nullable=False)
    
    # Application ma'lumotlari
    status = Column(SQLEnum(ApplicationStatus), default=ApplicationStatus.PENDING)
    message = Column(Text, nullable=True)
    cover_letter = Column(Text, nullable=True)
    expected_salary = Column(Float, nullable=True)
    
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    feedback = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    vacancy = relationship('Vacancy', back_populates='applications')
    user = relationship('CustomUser', foreign_keys=[user_id], back_populates='applications')
    resume = relationship('Resume', back_populates='applications')
    reviewer = relationship('CustomUser', foreign_keys=[reviewed_by], back_populates='reviewed_applications')
    
    def __repr__(self):
        return f"<VacancyApplication(id={self.id}, vacancy_id={self.vacancy_id}, user_id={self.user_id}, status='{self.status}')>"