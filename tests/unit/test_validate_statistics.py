import importlib
import pandas as pd
import numpy as np
from pathlib import Path
import pytest

vs = importlib.import_module("scripts.validate_statistics")


@pytest.mark.unit
def test_analyze_distribution_and_interpret(tmp_path):
    # Create a small CSV with right-skewed data
    path = tmp_path / "data.csv"
    df = pd.DataFrame({"total_power_mw": [800, 820, 780, 3000, 850, 810, 2900]})
    df.to_csv(path, index=False)

    stats = vs.analyze_distribution(str(path))
    assert stats["count"] == 7
    expected = vs.interpret_distribution(stats, "Burst Web Browsing")
    assert expected in ("Right-skewed (burst workload)", "Normal (constant workload)", "Left-skewed (idle periods)")
