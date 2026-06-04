import pandas as pd
from src.ml_core.config import ProjectConfig
from src.exceptions import PreprocessingError, MLProjectBaseError


class Preprocessor:
    """
    負責資料清洗與特徵轉換的防腐層。
    封裝並記憶狀態（如平均值、標準差），避免 Data Leakage 與全域變數污染。
    """

    def __init__(self, config: ProjectConfig):
        """
        初始化預處理器。

        :param config: 已驗證的全域設定物件。
        """
        self.config = config
        # TODO: 宣告內部的 Scalers 或 Encoders
        self.is_fitted = False

    def fit_transform(self, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
        """
        在訓練階段執行，適應資料分佈並進行轉換。

        :param df: 原始的 DataFrame。
        :return: 一個 Tuple，包含特徵矩陣 (X) 與目標標籤 (y)。
        :raises PreprocessingError: 若發現預期外的缺失值或資料結構錯誤。
        """
        try:
            # TODO: 實作填補、縮放與類別編碼邏輯
            # X = df.drop(columns=['target'])
            # y = df['target']
            self.is_fitted = True

            # 回傳假的骨架資料
            return pd.DataFrame(), pd.Series(dtype=float)

        except MLProjectBaseError:
            raise
        except Exception as e:
            raise PreprocessingError("特徵工程階段轉換失敗") from e

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        在推論/驗證階段執行，使用已記憶的狀態進行轉換。

        :param df: 未知的新資料 DataFrame。
        :return: 轉換後的特徵矩陣 (X)。
        :raises PreprocessingError: 若尚未 fit 就呼叫，或輸入特徵不符。
        """
        if not self.is_fitted:
            raise PreprocessingError("呼叫 transform 之前必須先執行 fit_transform")

        # TODO: 實作推論時的轉換邏輯
        return pd.DataFrame()
