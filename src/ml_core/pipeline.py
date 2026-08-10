import logging
from dataclasses import dataclass, field

from src.adapters.loader import DataLoaderProtocol
from src.adapters.mlflow_tracker import ExperimentTrackerProtocol
from src.ml_core.config import ProjectConfig
from src.ml_core.preprocessor import Preprocessor
from src.ml_core.trainer import Trainer

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TrainingResult:
    """
    訓練流程的結果物件，封裝 Run 追蹤資訊與指標。

    :param run_id: 實驗追蹤系統的 Run ID。
    :param metrics: 訓練指標字典。
    :param model_uri: 模型 Artifact 的 URI (若有記錄)。
    """

    run_id: str
    metrics: dict[str, float] = field(default_factory=dict)
    model_uri: str | None = None


class TrainingPipeline:
    """
    工作流協調者 (Main Control Loop)。
    負責定義執行順序，本身不參與資料轉換或運算邏輯。
    整合 ExperimentTracker 進行實驗追蹤與模型記錄。
    """

    def __init__(
        self,
        config: ProjectConfig,
        loader: DataLoaderProtocol,
        preprocessor: Preprocessor,
        trainer: Trainer,
        tracker: ExperimentTrackerProtocol,
    ):
        """
        初始化 Pipeline 並進行依賴注入 (Dependency Injection)。

        :param config: 專案全域設定物件。
        :param loader: 資料讀取器實例。
        :param preprocessor: 資料預處理器實例。
        :param trainer: 模型訓練器實例。
        :param tracker: 實驗追蹤器實例。
        """
        self.config = config
        self.loader = loader
        self.preprocessor = preprocessor
        self.trainer = trainer
        self.tracker = tracker

    def run(self) -> TrainingResult:
        """
        啟動機器學習訓練標準工作流。

        :return: 包含 run_id、訓練指標與模型 URI 的結果物件。
        """
        logger.info("啟動機器學習工作流 (Training Pipeline)...")

        # 步驟 0: 開啟實驗追蹤
        run_id = self.tracker.start_run(
            experiment_name=self.config.mlflow_experiment_name,
        )
        model_uri: str | None = None

        try:
            # 記錄超參數
            self.tracker.log_params(
                {
                    "learning_rate": self.config.learning_rate,
                    "random_state": self.config.random_state,
                    "data_path": str(self.config.data_path),
                }
            )

            # 步驟 1: 獲取資料
            logger.info("Step 1: 正在從 Loader 獲取資料...")
            raw_df = self.loader.fetch(self.config.data_path)

            # 步驟 2: 特徵工程與預處理
            logger.info("Step 2: 正在執行特徵轉換 (Fit & Transform)...")
            X, y = self.preprocessor.fit_transform(raw_df)

            # 步驟 3: 模型訓練
            logger.info("Step 3: 正在進行模型訓練...")
            metrics = self.trainer.fit(X, y)
            logger.info(f"模型訓練完成。指標: {metrics}")

            # 步驟 4: 記錄指標
            self.tracker.log_metrics(metrics)

            # 步驟 5: 記錄模型 Artifact
            logger.info("Step 4: 正在記錄模型至 Experiment Tracker...")
            try:
                model = self.trainer.get_model()
                model_uri = self.tracker.log_model(
                    model=model,
                    artifact_path="model",
                    registered_model_name=(self.config.mlflow_registered_model_name),
                )
            except Exception:
                logger.warning(
                    "模型尚未實作 get_model()，跳過模型記錄",
                    exc_info=True,
                )

            # 步驟 6: 可選的本地備份儲存
            if self.config.model_save_path is not None:
                logger.info("Step 5: 正在儲存模型至本地 (備份)...")
                self.trainer.save(self.config.model_save_path)

        finally:
            # 確保 Run 一定會被正確關閉
            self.tracker.end_run()

        logger.info("工作流順利結束。Run ID: %s", run_id)
        return TrainingResult(
            run_id=run_id,
            metrics=metrics,
            model_uri=model_uri,
        )
