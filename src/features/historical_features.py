import pandas as pd
import numpy as np


def add_historical_features(
    df: pd.DataFrame,
    raw: pd.DataFrame
) -> pd.DataFrame:
    """
    Calcula features históricas por barrio usando raw_accidentes.
    Completamente vectorizado — sin loops Python.

    Features generadas
    ------------------
    hist_acc_neighborhood_total : acumulado de accidentes en el barrio hasta TW
    hist_acc_neighborhood_30d   : accidentes en los últimos 30 días en el barrio
    hist_acc_hour_neighborhood  : histórico barrio × hora
    hist_rate_neighborhood      : tasa promedio histórica de accidentes por hora
    """
    df  = df.copy().sort_values("TW").reset_index(drop=True)
    raw = raw.copy()

    raw["BARRIO"] = raw["BARRIO"].str.strip().str.upper()
    df["BARRIO"]  = df["BARRIO"].str.strip().str.upper()

    raw_sorted = (
        raw.sort_values("TW")[["TW", "BARRIO"]]
        .assign(n=1)
    )
    acc_tw = (
        raw_sorted
        .groupby(["BARRIO", "TW"])["n"]
        .sum()
        .reset_index()
    )

    acc_cum = (
        acc_tw
        .sort_values(["BARRIO", "TW"])
    )

    acc_cum["hist_acc_neighborhood_total"] = (
        acc_cum
        .groupby("BARRIO")["n"]
        .cumsum()
    )

    acc_cum = acc_cum.rename(columns={"TW": "TW_raw"})

    df = pd.merge_asof(
        df.sort_values("TW"),
        acc_cum.sort_values("TW_raw"),
        left_on="TW", right_on="TW_raw",
        by="BARRIO",
        direction="backward",
    )
    df["hist_acc_neighborhood_total"] = df["hist_acc_neighborhood_total"].fillna(0)

    df_30d = df[["TW", "BARRIO"]].copy()
    df_30d["TW_30d"] = df_30d["TW"] - pd.Timedelta(days=30)

    acc_cum_30d = acc_cum.rename(
        columns={"TW_raw": "TW_30d_raw",
                 "hist_acc_neighborhood_total": "acc_cum_30d_ago"}
    )

    df_30d = pd.merge_asof(
        df_30d.sort_values("TW_30d"),
        acc_cum_30d.sort_values("TW_30d_raw"),
        left_on="TW_30d", right_on="TW_30d_raw",
        by="BARRIO",
        direction="backward",
    ).sort_values("TW").reset_index(drop=True)

    df_30d["acc_cum_30d_ago"] = df_30d["acc_cum_30d_ago"].fillna(0)

    df = df.sort_values("TW").reset_index(drop=True)
    df["hist_acc_neighborhood_30d"] = (
        df["hist_acc_neighborhood_total"].values
        - df_30d["acc_cum_30d_ago"].values
    ).clip(min=0)

    raw["hour"] = raw["TW"].dt.hour
    hist_hour = (
        raw.groupby(["BARRIO", "hour"])
        .size()
        .reset_index(name="hist_acc_hour_neighborhood")
    )
    df["hour"] = df["TW"].dt.hour
    df = df.merge(hist_hour, on=["BARRIO", "hour"], how="left")
    df["hist_acc_hour_neighborhood"] = df["hist_acc_hour_neighborhood"].fillna(0)

    n_hours = (
        raw.groupby("BARRIO")["TW"].nunique()
        .reset_index(name="n_observed_hours")
    )
    total_acc = (
        raw.groupby("BARRIO").size()
        .reset_index(name="total_accidents")
    )
    rate = n_hours.merge(total_acc, on="BARRIO")
    rate["hist_rate_neighborhood"] = rate["total_accidents"] / rate["n_observed_hours"]

    df = df.merge(rate[["BARRIO", "hist_rate_neighborhood"]], on="BARRIO", how="left")
    df["hist_rate_neighborhood"] = df["hist_rate_neighborhood"].fillna(0)

    df = df.drop(columns=["TW_raw"], errors="ignore")

    print(
        "Historical features added: "
        "hist_acc_neighborhood_total, "
        "hist_acc_neighborhood_30d, "
        "hist_acc_hour_neighborhood, "
        "hist_rate_neighborhood"
    )
    return df