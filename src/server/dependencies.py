"""
FastAPI 依賴注入容器與 Lifespan 管理。

使用 FastAPI 的 ``Depends`` 系統提供共用元件的注入，
並透過 ``lifespan`` 管理應用程式的啟動與關閉事件。
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request

from src.ml_core.config import ProjectConfig
from src.ml_core.serving import ModelServingEngine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    FastAPI Lifespan 管理器。

    在應用程式啟動時初始化共用元件 (Config, ServingEngine)，
    並將其存放在 ``app.state`` 供 Dependency 函式取用。

    :param app: FastAPI 應用程式實例。
    """
    logger.info("FastAPI 應用程式啟動中...")

    config = ProjectConfig()
    app.state.config = config

    serving_engine = ModelServingEngine(
        tracking_uri=config.mlflow_tracking_uri,
    )
    app.state.serving_engine = serving_engine

    logger.info(
        "初始化完成 — MLflow URI: %s, Server: %s:%d",
        config.mlflow_tracking_uri,
        config.server_host,
        config.server_port,
    )

    yield

    logger.info("FastAPI 應用程式關閉中...")


def get_config(request: Request) -> ProjectConfig:
    """
    取得全域 ProjectConfig 實例。

    :param request: FastAPI Request 物件。
    :return: 已初始化的 ProjectConfig。
    """
    config: Any = request.app.state.config
    return config


def get_serving_engine(request: Request) -> ModelServingEngine:
    """
    取得 ModelServingEngine 實例。

    :param request: FastAPI Request 物件。
    :return: 已初始化的 ModelServingEngine。
    """
    engine: Any = request.app.state.serving_engine
    return engine
