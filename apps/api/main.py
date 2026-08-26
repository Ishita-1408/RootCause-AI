"""RootCause AI FastAPI Application."""

import logging
import time
from pathlib import Path

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from apps.api.config import get_settings
from apps.api.routers import (
    agent,
    ai,
    analytics,
    anomalies,
    auth,
    database,
    datasets,
    diagnostics,
    health,
    investigations,
    rootcause,
)

logger = logging.getLogger("apps.api")

# Resolve path to frontend production build
PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEB_DIST_DIR = PROJECT_ROOT / "apps" / "web" / "dist"


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    # Configure root logger level
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Autonomous business investigation platform API",
    )

    # 1. Configurable, Restricted CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # 2. Structured Request Logging Middleware
    @app.middleware("http")
    async def structured_logging_middleware(
        request: Request, call_next: object
    ) -> Response:
        start_time = time.perf_counter()
        path = request.url.path
        method = request.method

        try:
            response = await call_next(request)  # type: ignore[operator]
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.info(f"{method} {path} -> {response.status_code} ({duration_ms}ms)")
            return response  # type: ignore[no-any-return]
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                f"Unhandled Exception on {method} {path} "
                f"after {duration_ms}ms: {type(exc).__name__}"
            )
            raise

    # 3. Global Unhandled Exception Handler
    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.error(
            f"Global exception caught on {request.method} {request.url.path}: {exc}"
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected server error occurred."},
        )

    # 4. Include API Routers First (highest priority)
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(database.router)
    app.include_router(datasets.router)
    app.include_router(analytics.router)
    app.include_router(anomalies.router)
    app.include_router(investigations.router)
    app.include_router(diagnostics.router)
    app.include_router(rootcause.router)
    app.include_router(ai.router)
    app.include_router(agent.router)

    # 5. Serve React Production SPA Static Files (if built)
    if (WEB_DIST_DIR / "assets").is_dir():
        app.mount(
            "/assets",
            StaticFiles(directory=str(WEB_DIST_DIR / "assets")),
            name="static_assets",
        )

    index_html = WEB_DIST_DIR / "index.html"

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa(full_path: str) -> Response:
        """Serve built static files or fallback to index.html for React SPA routing."""
        # Never intercept API or Swagger docs
        if (
            full_path.startswith("api/")
            or full_path.startswith("docs")
            or full_path.startswith("redoc")
            or full_path.startswith("openapi.json")
        ):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": "Not found"},
            )

        if index_html.is_file():
            target_file = WEB_DIST_DIR / full_path
            if full_path and target_file.is_file():
                return FileResponse(target_file)
            return FileResponse(index_html)

        # Fallback if frontend dist not yet built
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "ok",
                "app": settings.app_name,
                "docs": "/docs",
                "message": (
                    "Frontend static assets not built. Run 'npm run build' in apps/web."
                ),
            },
        )

    return app


app = create_app()
