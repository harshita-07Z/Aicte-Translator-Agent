"""
Application entry point.
Run with:  python run.py
           uvicorn run:app --host 0.0.0.0 --port 8000 --reload
"""
from app.main import create_app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    from app.core.config import get_settings

    settings = get_settings()
    uvicorn.run(
        "run:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug,
        reload_excludes=["logs/*", "data/*", "*.log", "*.pyc", "__pycache__/*", ".pytest_cache/*"],
        log_level=settings.log_level.lower(),
    )
