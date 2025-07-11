from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, dashboard

# Создание приложения
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    debug=settings.debug
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(auth.router)
app.include_router(dashboard.router)

@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "message": "PK Online Web Interface API",
        "version": settings.version,
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host=settings.host, 
        port=settings.port,
        reload=settings.debug
    ) 