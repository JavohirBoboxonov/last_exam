from fastapi import FastAPI
from sqladmin import Admin
from config.database import engine
from config import models
from auth import auth
from vacancy import api
from status import application
from config.admin import UserAdmin, VacancyAdmin, ResumeAdmin, ApplicationAdmin

app = FastAPI()
admin = Admin(app, engine)
admin.add_view(UserAdmin)
admin.add_view(VacancyAdmin)
admin.add_view(ResumeAdmin)
admin.add_view(ApplicationAdmin)

app.include_router(auth.router)
app.include_router(api.router)
app.include_router(application.router)

@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)