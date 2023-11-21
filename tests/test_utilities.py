"""Test utilities."""
import pandas as pd
import pytest

from org_bounty_board.utilities import check_df_for_true_column_value


def test_check_df_for_true_column_value():
    """If column condition is true, unit must raise."""
    bad_data = pd.DataFrame(
        {
            "target_col": [False, False, True],
            "other_col": [False, False, False],
        }
    )
    with pytest.raises(ValueError, match="True value found in `colnm`"):
        check_df_for_true_column_value(bad_data, colnm="target_col")

    out = check_df_for_true_column_value(bad_data, colnm="other_col")
    assert out is None
