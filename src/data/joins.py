import pandas as pd


def build_dataset(
    accidents: pd.DataFrame,
    weather: pd.DataFrame
) -> pd.DataFrame:
    """
    Performs a LEFT JOIN of weather ← accidents
    to construct the binary target variable.

    Parameters
    ----------
    accidents : aggregated table (only rows with accidents)
    weather   : weather table (covers all neighborhood-hour combinations)

    Returns
    -------
    DataFrame containing all (BARRIO, TW) combinations
    and the `target` column.
    """

    accidents = accidents.copy()
    weather = weather.copy()

    accidents["BARRIO"] = (
        accidents["BARRIO"].str.strip().str.upper()
    )

    weather["BARRIO"] = (
        weather["BARRIO"].str.strip().str.upper()
    )

    accidents["target"] = 1

    df = weather.merge(
        accidents[["TW", "BARRIO", "target"]],
        on=["TW", "BARRIO"],
        how="left",
    )

    df["target"] = df["target"].fillna(0).astype(int)

    print(f"Dataset built: {df.shape}")

    print(
        f"  Positive cases (target=1): "
        f"{df['target'].sum():,} "
        f"({df['target'].mean() * 100:.2f} %)"
    )

    print(
        f"  Negative cases (target=0): "
        f"{(df['target'] == 0).sum():,}"
    )

    return df


def join_summary(df: pd.DataFrame) -> None:
    """Prints basic statistics of the merged dataset."""

    print("\n── Dataset Summary ──────────────────────────────")

    print(f"Total rows        : {len(df):,}")
    print(f"Unique neighborhoods : {df['BARRIO'].nunique()}")

    print(
        f"Time range        : "
        f"{df['TW'].min()} → {df['TW'].max()}"
    )

    print(f"Total missing values : {df.isnull().sum().sum()}")

    print(
        f"Class imbalance   : "
        f"{df['target'].value_counts(normalize=True).round(4).to_dict()}"
    )