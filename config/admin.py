from sqladmin import ModelView
from config.models import CustomUser, Vacancy, Resume, Interest, VacancyApplication

class UserAdmin(ModelView, model=CustomUser):
    column_list = [CustomUser.id, CustomUser.username, CustomUser.role, CustomUser.is_active]
    icon = "fa-solid fa-user"

class VacancyAdmin(ModelView, model=Vacancy):
    column_list = [Vacancy.id, Vacancy.title, Vacancy.job_type, Vacancy.is_active]
    icon = "fa-solid fa-briefcase"

class ResumeAdmin(ModelView, model=Resume):
    column_list = [Resume.id, Resume.full_name, Resume.position]
    icon = "fa-solid fa-file"

class ApplicationAdmin(ModelView, model=VacancyApplication):
    column_list = [VacancyApplication.id, VacancyApplication.status, VacancyApplication.created_at]
    icon = "fa-solid fa-paper-plane"