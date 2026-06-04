import pytest
from src.adapters.loader import DataLoader
from src.exceptions import DataFetchError


def test_dataloader_success(mock_data_path):
    loader = DataLoader()
    df = loader.fetch(mock_data_path)
    assert df is not None
    assert "feature1" in df.columns


def test_dataloader_missing_file(mock_missing_data_path):
    loader = DataLoader()
    with pytest.raises(DataFetchError, match="資料來源不存在"):
        loader.fetch(mock_missing_data_path)
