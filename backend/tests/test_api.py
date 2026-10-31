import pytest

from app.analysis import analyze_market


def test_error_on_empty_dataframe():
    empty = []
    with pytest.raises(ValueError):
        analyze_market(empty)
