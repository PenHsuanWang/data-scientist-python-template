import pytest
from pathlib import Path

# 在這裡定義全域或共用的 Fixture，供所有的測試檔案使用


@pytest.fixture
def mock_data_path(tmp_path: Path) -> Path:
    """
    提供一個暫時的測試資料路徑，並實際建立測試資料。
    """
    data_file = tmp_path / "mock_dataset.csv"
    data_file.write_text("feature1,feature2,target\n1,2,0\n3,4,1\n5,6,1")
    return data_file


@pytest.fixture
def mock_missing_data_path(tmp_path: Path) -> Path:
    """Intentionally non-existent path for error-path tests."""
    return tmp_path / "does_not_exist.csv"


@pytest.fixture
def mock_model_path(tmp_path: Path) -> Path:
    """
    提供一個暫時的模型儲存路徑。
    """
    return tmp_path / "mock_model.pkl"
