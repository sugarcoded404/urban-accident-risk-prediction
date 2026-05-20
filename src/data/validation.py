"""
src/data/validation.py
Data quality functions for the tables: accidents, weather, raw_accidents.
"""

import pandas as pd
import numpy as np

WEATHER_RANGES = {
    "temperature": (-10, 50),
    "apparentTemperature": (-15, 55),
    "humidity": (0, 1),
    "precipProbability": (0, 1),
    "precipIntensity": (0, None),
    "windSpeed": (0, None),
    "cloudCover": (0, 1),
    "uvIndex": (0, 20),
    "visibility": (0, 20),
}

def null_report(df: pd.DataFrame, name: str) -> pd.DataFrame:
    """Returns a DataFrame with count and percentage of missing values per column."""
    missing = df.isnull().sum()
    pct = (missing / len(df) * 100).round(2)

    report = pd.DataFrame({
        "table": name,
        "column": missing.index,
        "missing_values": missing.values,
        "pct (%)": pct.values,
    }).query("missing_values > 0").reset_index(drop=True)

    return report

def duplicates_report(
    df: pd.DataFrame,
    name: str,
    subset: list = None
) -> dict:
    """
    Counts duplicated rows globally and by a subset of columns (keys).
    Returns a dictionary with the counts.
    """
    total_duplicates = df.duplicated().sum()
    key_duplicates = df.duplicated(subset=subset).sum() if subset else None

    print(f"[{name}] Total duplicates: {total_duplicates}")

    if subset:
        print(f"[{name}] Duplicates by key {subset}: {key_duplicates}")

    return {
        "table": name,
        "total_duplicates": total_duplicates,
        "key_duplicates": key_duplicates
    }

def validate_tw(df: pd.DataFrame, name: str) -> pd.Series:
    """
    Verifies that TW is truncated to the hour
    (minutes and seconds must be equal to 0).
    Returns problematic rows.
    """
    if "TW" not in df.columns:
        print(f"[{name}] TW column not found.")
        return pd.Series(dtype=object)

    issues = df[
        (df["TW"].dt.minute != 0) |
        (df["TW"].dt.second != 0)
    ]

    print(f"[{name}] Rows with TW not truncated to the hour: {len(issues)}")

    return issues

def compare_neighborhoods(
    acc: pd.DataFrame,
    weather: pd.DataFrame,
    raw: pd.DataFrame
) -> dict:
    """
    Compares neighborhood sets across the three tables.
    Returns neighborhoods exclusive to each table.
    """
    n_acc = set(acc["BARRIO"].dropna().str.strip().str.upper())
    n_weather = set(weather["BARRIO"].dropna().str.strip().str.upper())
    n_raw = set(raw["BARRIO"].dropna().str.strip().str.upper())

    result = {
        "only_in_accidents": n_acc - n_weather,
        "only_in_weather": n_weather - n_acc,
        "only_in_raw": n_raw - n_acc,
        "common_acc_weather": len(n_acc & n_weather),
        "total_accidents": len(n_acc),
        "total_weather": len(n_weather),
        "total_raw": len(n_raw),
    }

    print(f"Common neighborhoods accidents↔weather: {result['common_acc_weather']}")
    print(f"Neighborhoods only in accidents: {len(result['only_in_accidents'])}")
    print(f"Neighborhoods only in weather: {len(result['only_in_weather'])}")

    return result

def detect_outliers_iqr(
    df: pd.DataFrame,
    columns: list,
    factor: float = 1.5
) -> pd.DataFrame:
    """
    Detects outliers using the interquartile range (IQR).
    Returns a summary with outlier counts per column.
    """
    records = []

    for col in columns:
        if col not in df.columns:
            continue

        series = df[col].dropna()

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)

        iqr = q3 - q1

        lower_limit = q1 - factor * iqr
        upper_limit = q3 + factor * iqr

        n_outliers = (
            (series < lower_limit) |
            (series > upper_limit)
        ).sum()

        records.append({
            "column": col,
            "q1": q1,
            "q3": q3,
            "lower_limit": lower_limit,
            "upper_limit": upper_limit,
            "n_outliers": n_outliers,
            "pct (%)": round(n_outliers / len(series) * 100, 2),
        })

    return pd.DataFrame(records)

def validate_weather_ranges(weather: pd.DataFrame) -> pd.DataFrame:
    """
    Verifies that weather variables are within physically plausible ranges.
    """
    records = []

    for col, (minv, maxv) in WEATHER_RANGES.items():

        if col not in weather.columns:
            continue

        series = weather[col].dropna()

        out_of_range = 0

        if minv is not None:
            out_of_range += (series < minv).sum()

        if maxv is not None:
            out_of_range += (series > maxv).sum()

        records.append({
            "column": col,
            "expected_min": minv,
            "expected_max": maxv,
            "real_min": round(series.min(), 4),
            "real_max": round(series.max(), 4),
            "out_of_range": out_of_range,
        })

    return pd.DataFrame(records)


def temporal_coverage(df: pd.DataFrame, name: str) -> dict:
    """Temporal range and number of unique hours in the table."""

    tw = df["TW"].dropna()

    result = {
        "table": name,
        "from": tw.min(),
        "to": tw.max(),
        "unique_hours": tw.nunique(),
        "unique_days": tw.dt.date.nunique(),
    }

    print(
        f"[{name}] {result['from']} → {result['to']} "
        f"| {result['unique_days']} days "
        f"| {result['unique_hours']} unique hours"
    )

    return result


    null_report,
    duplicate_report,
    tw_validation,
    neighborhood_comparison,
    iqr_outlier_detection,
    climate_range_validation,
    temporal_coverage