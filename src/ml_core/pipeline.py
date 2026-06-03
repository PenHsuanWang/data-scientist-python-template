import logging
from src.ml_core.config import ProjectConfig
from src.data_fetch.loader import DataLoader
from src.ml_core.preprocessor import Preprocessor
from src.ml_core.trainer import Trainer

logger = logging.getLogger(__name__)


class TrainingPipeline:
    """
    工作流協調者 (Main Control Loop)。
    負責定義執行順序，本身不參與資料轉換或運算邏輯。
    """

    def __init__(self, config: ProjectConfig):
        """
        初始化 Pipeline 並進行依賴注入 (Dependency Injection)。

        :param config: 專案全域設定物件。
        """
        self.config = config
        # 實例化底層的 Domain 狀態物件
        self.preprocessor = Preprocessor(config)
        self.trainer = Trainer(config)

    def run(self) -> None:
        """
        啟動機器學習訓練標準工作流。
        """
        logger.info("啟動機器學習工作流 (Training Pipeline)...")

        # 步驟 1: 獲取資料
        logger.info("Step 1: 正在從 Loader 獲取資料...")
        # 注意: 我們直接讓底層拋出的自定義例外向上傳遞
        raw_df = DataLoader.fetch(self.config.data_path)

        # 步驟 2: 特徵工程與預處理
        logger.info("Step 2: 正在執行特徵轉換 (Fit & Transform)...")
        X, y = self.preprocessor.fit_transform(raw_df)

        # 步驟 3: 模型訓練
        logger.info("Step 3: 正在進行模型訓練...")
        metrics = self.trainer.fit(X, y)
        logger.info(f"模型訓練完成。指標: {metrics}")

        # 步驟 4: 模型儲存
        logger.info("Step 4: 正在儲存模型產出物 (Artifacts)...")
        self.trainer.save(self.config.model_save_path)

        logger.info("工作流順利結束。")
