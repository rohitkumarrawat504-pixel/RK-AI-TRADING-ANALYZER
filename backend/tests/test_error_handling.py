import pytest
import pandas as pd

from app.analysis import analyze_market


def test_missing_or_short_market_data_raises():
    short_df = pd.DataFrame([{"open": 100, "high": 101, "low": 99, "close": 100, "volume": 1000}])
    with pytest.raises(ValueError):
        analyze_market(short_df)
