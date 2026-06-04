import pytest
from src.utils.stats import calculate_mean


def test_calculate_mean():
    assert calculate_mean([1, 2, 3, 4, 5]) == 3.0
    assert calculate_mean([2.5, 2.5]) == 2.5


def test_calculate_mean_empty():
    with pytest.raises(ValueError, match="empty list"):
        calculate_mean([])
