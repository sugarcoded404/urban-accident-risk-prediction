import sqlite3
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

DB_PATH = BASE_DIR / "data" / "raw" / "data_accidentes.sqlite3"

def load_tables():

    pd.set_option("display.max_columns", None)

    con = sqlite3.connect(DB_PATH)

    accidents = pd.read_sql(
        "SELECT * FROM accidentes",
        con,
        parse_dates=["TW"]
    )

    weather = pd.read_sql(
        "SELECT * FROM clima",
        con,
        parse_dates=["TW"]
    )

    raw = pd.read_sql(
        "SELECT * FROM raw_accidentes",
        con,
        parse_dates=["TW"]
    )

    con.close()

    return accidents, weather, raw
