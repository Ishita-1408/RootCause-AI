from fastapi import FastAPI

from apps.api.config import get_settings
from apps.api.routers import health


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Autonomous business investigation platform API",
    )

    app.include_router(health.router)

    return app


app = create_app()
