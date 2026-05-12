# admin.py
from sqladmin import ModelView
from models import CustomUser, Vacancy  # Sizning asl modellaringiz

class CustomUserAdmin(ModelView, model=CustomUser):
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"
    
    column_list = [CustomUser.id, CustomUser.username, CustomUser.email, CustomUser.full_name, CustomUser.is_active, CustomUser.created_at]
    column_searchable_list = [CustomUser.username, CustomUser.email, CustomUser.full_name]
    column_filters = [CustomUser.is_active, CustomUser.created_at]
    column_default_sort = [(CustomUser.created_at, True)]
    form_columns = [CustomUser.username, CustomUser.email, CustomUser.full_name, CustomUser.is_active]
    column_readonly_list = [CustomUser.created_at]
    can_export = True
    export_types = ['csv', 'json']

class VacancyAdmin(ModelView, model=Vacancy):
    name = "Vacancy"
    name_plural = "Vacancies"
    icon = "fa-solid fa-briefcase"
    
    column_list = [Vacancy.id, Vacancy.title, Vacancy.description, Vacancy.company, Vacancy.salary, Vacancy.location, Vacancy.is_active, Vacancy.created_at]
    column_searchable_list = [Vacancy.title, Vacancy.company, Vacancy.location]
    column_filters = [Vacancy.is_active, Vacancy.salary, Vacancy.location, Vacancy.created_at]
    column_default_sort = [(Vacancy.created_at, True)]
    form_columns = [Vacancy.title, Vacancy.description, Vacancy.company, Vacancy.salary, Vacancy.location, Vacancy.is_active]
    column_readonly_list = [Vacancy.created_at]
    can_export = True
    export_types = ['csv', 'json']