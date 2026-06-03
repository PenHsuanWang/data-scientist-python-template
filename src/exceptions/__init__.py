"""
專案專屬例外類別樹 (Custom Exception Hierarchy)
定義所有與業務邏輯相關的例外，以便在上層進行攔截與處理。
"""


class MLProjectBaseError(Exception):
    """
    所有機器學習專案自定義例外的基底類別。

    :param message: 錯誤訊息
    """

    pass


class ConfigurationError(MLProjectBaseError):
    """設定檔或參數錯誤 (如缺少必要參數、路徑不存在)。"""

    pass


class DataFetchError(MLProjectBaseError):
    """資料獲取層 (I/O) 錯誤 (如 DB 斷線、檔案找不到)。"""

    pass


class PreprocessingError(MLProjectBaseError):
    """特徵工程階段錯誤 (如發現預期外的 NaN、特徵維度不匹配)。"""

    pass


class ModelTrainingError(MLProjectBaseError):
    """模型訓練階段錯誤 (如演算法不收斂、OOM)。"""

    pass
