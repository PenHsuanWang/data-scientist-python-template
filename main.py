import sys
import logging
import argparse
from pathlib import Path
from pydantic import ValidationError

from src.ml_core.config import ProjectConfig
from src.ml_core.pipeline import TrainingPipeline
from src.adapters.loader import DataLoader
from src.adapters.mlflow_tracker import (
    MLflowExperimentTracker,
    NoOpExperimentTracker,
)
from src.ml_core.preprocessor import Preprocessor
from src.ml_core.trainer import Trainer
from src.exceptions import MLProjectBaseError

# 設定基礎日誌輸出
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("SystemEntry")


def _build_parser() -> argparse.ArgumentParser:
    """
    建立包含 train / serve 子命令的 CLI 解析器。

    :return: 已配置的 ArgumentParser。
    """
    parser = argparse.ArgumentParser(
        description="ML Training & Serving Platform",
    )
    subparsers = parser.add_subparsers(
        dest="command",
        help="可用的子命令",
    )

    # ── train 子命令 ──────────────────────────────────────────
    train_parser = subparsers.add_parser(
        "train",
        help="執行模型訓練流程",
    )
    train_parser.add_argument(
        "--data-path",
        type=Path,
        help="覆蓋原始資料來源路徑 (Optional)",
    )
    train_parser.add_argument(
        "--learning-rate",
        type=float,
        help="覆蓋模型學習率 (Optional)",
    )
    train_parser.add_argument(
        "--experiment-name",
        type=str,
        help="覆蓋 MLflow experiment 名稱 (Optional)",
    )
    train_parser.add_argument(
        "--register-model",
        type=str,
        help="自動將模型註冊至 Model Registry 的名稱",
    )
    train_parser.add_argument(
        "--no-tracking",
        action="store_true",
        help="停用 MLflow 追蹤 (使用 NoOp Tracker)",
    )

    # ── serve 子命令 ──────────────────────────────────────────
    serve_parser = subparsers.add_parser(
        "serve",
        help="啟動 FastAPI 服務",
    )
    serve_parser.add_argument(
        "--host",
        type=str,
        help="覆蓋服務監聽位址 (預設 0.0.0.0)",
    )
    serve_parser.add_argument(
        "--port",
        type=int,
        help="覆蓋服務監聽埠號 (預設 8000)",
    )

    return parser


def _run_train(args: argparse.Namespace) -> None:
    """
    執行訓練子命令。

    :param args: CLI 解析後的參數。
    """
    # 準備 Config (CLI 參數覆蓋 .env 或環境變數)
    cli_overrides: dict[str, object] = {}
    if args.data_path is not None:
        cli_overrides["data_path"] = args.data_path
    if args.learning_rate is not None:
        cli_overrides["learning_rate"] = args.learning_rate
    if args.experiment_name is not None:
        cli_overrides["mlflow_experiment_name"] = args.experiment_name
    if args.register_model is not None:
        cli_overrides["mlflow_registered_model_name"] = args.register_model

    config = ProjectConfig(**cli_overrides)

    # 建立 Tracker
    if args.no_tracking:
        tracker = NoOpExperimentTracker()
        logger.info("MLflow 追蹤已停用 (使用 NoOp Tracker)")
    else:
        tracker = MLflowExperimentTracker(
            tracking_uri=config.mlflow_tracking_uri,
        )

    # 實例化並啟動 Pipeline (依賴注入)
    pipeline = TrainingPipeline(
        config=config,
        loader=DataLoader(),
        preprocessor=Preprocessor(config),
        trainer=Trainer(config),
        tracker=tracker,
    )

    result = pipeline.run()
    logger.info(
        "訓練完成 — Run ID: %s, Metrics: %s",
        result.run_id,
        result.metrics,
    )


def _run_serve(args: argparse.Namespace) -> None:
    """
    啟動 FastAPI 服務子命令。

    :param args: CLI 解析後的參數。
    """
    import uvicorn

    from src.server.app import create_app

    config = ProjectConfig()
    host = args.host or config.server_host
    port = args.port or config.server_port

    app = create_app()

    logger.info("啟動 FastAPI 服務 — %s:%d", host, port)
    uvicorn.run(app, host=host, port=port)


def main() -> None:
    """
    系統的統一進入點 (CLI Entry Point)。

    支援兩個子命令：
    - ``train``：執行模型訓練流程（整合 MLflow 追蹤）。
    - ``serve``：啟動 FastAPI 服務（提供 retrain 與 serving API）。
    """
    parser = _build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    try:
        if args.command == "train":
            _run_train(args)
        elif args.command == "serve":
            _run_serve(args)

    # 捕捉設定檔驗證失敗 (來自 Pydantic)
    except ValidationError as e:
        logger.error("系統啟動失敗，設定檔參數驗證錯誤:")
        for err in e.errors():
            logger.error(f"  - 參數 '{err['loc'][0]}': {err['msg']}")
        sys.exit(1)

    # 捕捉專案內部定義的所有業務邏輯錯誤 (Domain Exceptions)
    except MLProjectBaseError as e:
        logger.error(f"工作流執行失敗，發生業務邏輯錯誤: {e}")
        sys.exit(2)

    # 捕捉未預期崩潰 (OOM, OS Error, SystemExit 等底層錯誤)
    except Exception as e:
        logger.critical(
            f"系統發生未預期的崩潰 (System Crash): {e}",
            exc_info=True,
        )
        sys.exit(3)

    sys.exit(0)


if __name__ == "__main__":
    main()
