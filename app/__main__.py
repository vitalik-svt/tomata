from uvicorn import run
from app.settings import settings

if __name__ == '__main__':

    run("app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        workers=settings.app_workers,
        reload=settings.app_reload,
        log_level=settings.app_log_level.lower()
    )
