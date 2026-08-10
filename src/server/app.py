"""
FastAPI Application Factory。

使用 Application Factory Pattern 建立 FastAPI 實例，
註冊所有 Router 並配置全域 Exception Handler。
"""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.exceptions import (
    MLProjectBaseError,
    ModelNotFoundError,
    ModelServingError,
)
from src.server.dependencies import lifespan
from src.server.routers import models, predict, train

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """
    建立並配置 FastAPI 應用程式。

    :return: 已配置完成的 FastAPI 實例。
    """
    app = FastAPI(
        title="ML Training & Serving API",
        description=(
            "提供模型訓練 (retrain)、推論 (serving) "
            "與模型版本管理的統一 HTTP 介面。"
            "整合 MLflow 進行實驗追蹤與 Model Registry 管理。"
        ),
        version="0.1.0",
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ───────────────────────────────────────────────
    app.include_router(train.router)
    app.include_router(predict.router)
    app.include_router(models.router)

    # ── Exception Handlers ────────────────────────────────────
    _register_exception_handlers(app)

    # ── Health Check ──────────────────────────────────────────
    @app.get(
        "/health",
        tags=["System"],
        summary="健康檢查",
    )
    def health_check() -> dict[str, str]:
        """回傳服務運行狀態。"""
        return {"status": "healthy"}

    return app


def _register_exception_handlers(app: FastAPI) -> None:
    """
    註冊全域例外處理器，將領域例外轉為結構化的 HTTP 回應。

    :param app: FastAPI 應用程式實例。
    """

    @app.exception_handler(ModelNotFoundError)
    async def model_not_found_handler(
        request: Request,
        exc: ModelNotFoundError,
    ) -> JSONResponse:
        logger.warning("Model not found: %s", exc)
        return JSONResponse(
            status_code=404,
            content={"error": "ModelNotFoundError", "detail": str(exc)},
        )

    @app.exception_handler(ModelServingError)
    async def model_serving_handler(
        request: Request,
        exc: ModelServingError,
    ) -> JSONResponse:
        logger.error("Model serving error: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"error": "ModelServingError", "detail": str(exc)},
        )

    @app.exception_handler(MLProjectBaseError)
    async def domain_error_handler(
        request: Request,
        exc: MLProjectBaseError,
    ) -> JSONResponse:
        logger.error("Domain error: %s", exc)
        return JSONResponse(
            status_code=500,
            content={
                "error": type(exc).__name__,
                "detail": str(exc),
            },
        )
