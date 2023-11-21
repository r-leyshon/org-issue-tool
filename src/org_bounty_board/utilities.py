"""Utility functions."""
import pandas as pd


def check_df_for_true_column_value(tab: pd.DataFrame, colnm: str):
    """Raise ValueError if any True value is found in the target colnm."""
    if any(tab[colnm]):
        raise ValueError(f"True value found in `colnm`")
