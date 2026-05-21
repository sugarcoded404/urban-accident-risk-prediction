import pandas as pd


def build_dataset(
    accidents: pd.DataFrame,
    weather: pd.DataFrame
) -> pd.DataFrame:
    """
    Realiza un LEFT JOIN de weather ← accidents
    para construir la variable objetivo binaria.

    La función conserva todas las combinaciones (BARRIO, TW) de weather y
    etiqueta como `target=1` solo cuando existe un accidente en ese barrio y
    ese instante. Como el join es sobre el mismo `TW` y barrio, no introduce
    información futura en el target.

    Parameters
    ----------
    accidents : tabla agregada (solo filas con accidentes)
    weather   : tabla meteorológica (cubre todas las combinaciones barrio-hora)

    Returns
    -------
    DataFrame que contiene todas las combinaciones (BARRIO, TW)
    y la columna `target`.
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
    """Imprime estadísticas básicas del conjunto de datos fusionado."""

    print("\n── Resumen del dataset ──────────────────────────────")

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