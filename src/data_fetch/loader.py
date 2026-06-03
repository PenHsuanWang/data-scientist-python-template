import pandas as pd
from pathlib import Path
from src.exceptions import DataFetchError


class DataLoader:
    """
    負責與外部世界進行 I/O 互動的資料獲取層。
    本層完全不涉及特徵工程或業務邏輯。
    """

    @staticmethod
    def fetch(data_path: Path) -> pd.DataFrame:
        """
        讀取外部資料來源並回傳為 Pandas DataFrame。

        :param data_path: 欲讀取的檔案或資料庫路徑。
        :return: 包含原始資料的 DataFrame。
        :raises DataFetchError: 若檔案不存在、格式錯誤或發生 I/O 例外。
        """
        if not data_path.exists():
            raise DataFetchError(f"資料來源不存在: {data_path}")

        try:
            # TODO: 實作實際的 CSV 讀取或 DB 連線邏輯
            # return pd.read_csv(data_path)
            return pd.DataFrame()
        except Exception as e:
            raise DataFetchError("獲取資料時發生未預期的錯誤") from e
