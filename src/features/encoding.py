import pandas as pd
import numpy as np


class FrequencyEncoder:
    """
    Replaces each category with its relative frequency
    in the training set.
    """

    def __init__(self, columns: list):
        self.columns = columns
        self.maps: dict = {}

    def fit(self, df: pd.DataFrame) -> "FrequencyEncoder":

        for col in self.columns:
            self.maps[col] = (
                df[col]
                .value_counts(normalize=True)
                .to_dict()
            )

        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:

        df = df.copy()

        for col in self.columns:

            df[f"{col}_freq"] = (
                df[col]
                .map(self.maps[col])
                .fillna(0)
            )

        return df

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        return self.fit(df).transform(df)


class TargetEncoder:
    """
    Replaces each category with the target mean
    calculated on the training set.

    Applies smoothing to avoid overfitting
    on categories with few observations.
    """

    def __init__(
        self,
        columns: list,
        smoothing: float = 10.0
    ):

        self.columns = columns
        self.smoothing = smoothing

        self.maps: dict = {}
        self.global_mean: float = 0.0

    def fit(
        self,
        df: pd.DataFrame,
        y: pd.Series
    ) -> "TargetEncoder":

        self.global_mean = y.mean()

        tmp = df.copy()

        tmp["__target__"] = y.values

        for col in self.columns:

            stats = (
                tmp.groupby(col)["__target__"]
                .agg(["mean", "count"])
            )

            smooth = (
                (
                    stats["count"] * stats["mean"]
                    + self.smoothing * self.global_mean
                )
                /
                (stats["count"] + self.smoothing)
            )

            self.maps[col] = smooth.to_dict()

        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:

        df = df.copy()

        for col in self.columns:

            df[f"{col}_te"] = (
                df[col]
                .map(self.maps[col])
                .fillna(self.global_mean)
            )

        return df

    def fit_transform(
        self,
        df: pd.DataFrame,
        y: pd.Series
    ) -> pd.DataFrame:

        return self.fit(df, y).transform(df)