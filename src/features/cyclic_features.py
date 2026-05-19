import numpy as np
import pandas as pd


def _sin_cos(series: pd.Series, period: float):
    return (
        np.sin(2 * np.pi * series / period),
        np.cos(2 * np.pi * series / period),
    )


def add_cyclic_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds sine/cosine encoding for hour,
    day of the week, and day of the year.

    Requires the DataFrame to already contain:
    hour, weekday_num, and TW columns.
    """

    df = df.copy()

    df["hour_sin"], df["hour_cos"] = _sin_cos(df["hour"], 24)

    df["weekday_sin"], df["weekday_cos"] = _sin_cos(
        df["weekday_num"], 7
    )

    day_of_year = df["TW"].dt.dayofyear

    df["day_of_year_sin"], df["day_of_year_cos"] = _sin_cos(
        day_of_year, 365
    )

    df["month_sin"], df["month_cos"] = _sin_cos(
        df["month"], 12
    )

    return df