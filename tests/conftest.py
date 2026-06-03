import pytest
from pathlib import Path

# 在這裡定義全域或共用的 Fixture，供所有的測試檔案使用


@pytest.fixture
def mock_data_path(tmp_path: Path) -> Path:
    """
    提供一個暫時的測試資料路徑。
    """
    data_file = tmp_path / "mock_dataset.csv"
    # 若有需要，可以在這裡寫入測試用的 CSV 假資料
    # data_file.write_text("feature1,feature2,target\n1,2,0\n3,4,1")
    return data_file


@pytest.fixture
def mock_model_path(tmp_path: Path) -> Path:
    """
    提供一個暫時的模型儲存路徑。
    """
    return tmp_path / "mock_model.pkl"
