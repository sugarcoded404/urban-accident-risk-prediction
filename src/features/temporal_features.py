import pandas as pd

COLOMBIA_HOLIDAYS = pd.to_datetime([
    "2019-01-01","2019-01-07","2019-03-25","2019-04-18","2019-04-19",
    "2019-05-01","2019-06-03","2019-06-24","2019-07-01","2019-07-20",
    "2019-08-07","2019-08-19","2019-10-14","2019-11-04","2019-11-11",
    "2019-12-08","2019-12-25",
    "2020-01-01","2020-01-06","2020-03-23","2020-04-09","2020-04-10",
    "2020-05-01","2020-05-25","2020-06-15","2020-06-22","2020-07-20",
    "2020-08-07","2020-08-17","2020-10-12","2020-11-02","2020-11-16",
    "2020-12-08","2020-12-25",
    "2021-01-01","2021-01-11","2021-03-22","2021-04-01","2021-04-02",
    "2021-05-01","2021-05-17","2021-06-07","2021-06-14","2021-07-05",
    "2021-07-20","2021-08-07","2021-08-16","2021-10-18","2021-11-01",
    "2021-11-15","2021-12-08","2021-12-25",
])

HOLIDAYS_SET = set(COLOMBIA_HOLIDAYS.date)


def add_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generates discrete temporal features from the TW column.

    Created features
    ----------------
    hour, day, month, year : timestamp components
    weekday_num            : 0=Monday … 6=Sunday
    is_weekend             : 1 if Saturday or Sunday
    is_holiday             : 1 if the date is a public holiday in Colombia
    time_period            : early_morning / morning / afternoon /
                              early_night / night
    """

    df = df.copy()
    tw = df["TW"]

    df["hour"] = tw.dt.hour
    df["day"] = tw.dt.day
    df["month"] = tw.dt.month
    df["year"] = tw.dt.year
    
    df["weekday_num"] = tw.dt.dayofweek

    df["is_weekend"] = (
        df["weekday_num"].isin([5, 6]).astype(int)
    )

    df["is_holiday"] = (
        tw.dt.date.isin(HOLIDAYS_SET).astype(int)
    )

    df["time_period"] = pd.cut(
        df["hour"],
        bins=[-1, 5, 11, 17, 20, 23],
        labels=[
            "early_morning",
            "morning",
            "afternoon",
            "early_night",
            "night"
        ],
    ).astype(str)

    return df