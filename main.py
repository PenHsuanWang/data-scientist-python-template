import sys
import logging
import argparse
from pathlib import Path
from pydantic import ValidationError

from src.ml_core.config import ProjectConfig
from src.ml_core.pipeline import TrainingPipeline
from src.adapters.loader import DataLoader
from src.ml_core.preprocessor import Preprocessor
from src.ml_core.trainer import Trainer
from src.exceptions import MLProjectBaseError

# 設定基礎日誌輸出
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("SystemEntry")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ML Training Pipeline")
    parser.add_argument(
        "--data-path", type=Path, help="覆蓋原始資料來源路徑 (Optional)"
    )
    parser.add_argument(
        "--model-save-path", type=Path, help="覆蓋模型儲存路徑 (Optional)"
    )
    parser.add_argument("--learning-rate", type=float, help="覆蓋模型學習率 (Optional)")
    return parser.parse_args()


def main() -> None:
    """
    系統的統一進入點 (CLI Entry Point)。
    負責：
    1. 解析並準備全域設定檔 (Config)。
    2. 實例化並啟動控制流 (Pipeline)。
    3. 佈下最外層的防護網，攔截所有例外並產生對應的 Exit Code。
    """
    try:
        logger.info("系統初始化中...")

        # 1. 準備 Config (CLI 參數會覆蓋 .env 或環境變數)
        args = _parse_args()
        cli_overrides = {k: v for k, v in vars(args).items() if v is not None}
        config = ProjectConfig(**cli_overrides)

        # 2. 實例化並啟動 Pipeline (依賴注入)
        pipeline = TrainingPipeline(
            config=config,
            loader=DataLoader(),
            preprocessor=Preprocessor(config),
            trainer=Trainer(config),
        )
        pipeline.run()

    # 捕捉設定檔驗證失敗 (來自 Pydantic)
    except ValidationError as e:
        logger.error("系統啟動失敗，設定檔參數驗證錯誤:")
        for err in e.errors():
            logger.error(f"  - 參數 '{err['loc'][0]}': {err['msg']}")
        sys.exit(1)

    # 捕捉專案內部定義的所有業務邏輯錯誤 (Domain Exceptions)
    except MLProjectBaseError as e:
        logger.error(f"工作流執行失敗，發生業務邏輯錯誤: {e}")
        # 如果需要更詳細的 Traceback，可以在此處開啟
        sys.exit(2)

    # 捕捉未預期崩潰 (OOM, OS Error, SystemExit 等底層錯誤)
    except Exception as e:
        logger.critical(f"系統發生未預期的崩潰 (System Crash): {e}", exc_info=True)
        sys.exit(3)

    # 正常退出
    sys.exit(0)


if __name__ == "__main__":
    main()
