import pandas as pd
import streamlit as st

DATA_PATH = "data/Bikeshare dataset.csv"


def _find_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    cols_lower = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in cols_lower:
            return cols_lower[cand.lower()]
    return None


def infer_cols(df: pd.DataFrame) -> dict:
    start_dt = _find_col(df, ["started_at", "start_time", "starttime", "start_datetime"])
    end_dt   = _find_col(df, ["ended_at", "end_time", "stoptime", "end_datetime"])
    user_col = _find_col(df, ["member_casual", "usertype", "user_type", "customer_type"])
    bike_col = _find_col(df, ["rideable_type", "bike_type", "vehicle_type"])

    return {
        "start_dt": start_dt,
        "end_dt": end_dt,
        "user": user_col,
        "bike": bike_col,
    }


def _to_datetime_safe(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, errors="coerce", utc=False)


@st.cache_data(show_spinner=False)
def load_raw(path: str = DATA_PATH) -> pd.DataFrame:
    return pd.read_csv(path)


@st.cache_data(show_spinner=False)
def load_prepared(path: str = DATA_PATH) -> tuple[pd.DataFrame, dict]:
    """
    Préparation STRICTEMENT alignée avec le notebook :
    - conversion started_at, ended_at en datetime
    - création:
        * trip_duration_min = (ended_at - started_at) en minutes
        * day_of_week = started_at.dt.day_name()
        * start_hour  = started_at.dt.hour
    """
    df = pd.read_csv(path)
    cols = infer_cols(df)

    if cols["start_dt"] is None or cols["end_dt"] is None:
        # cas improbable, mais on sécurise
        return df, cols

    # Convert datetime
    df[cols["start_dt"]] = _to_datetime_safe(df[cols["start_dt"]])
    df[cols["end_dt"]] = _to_datetime_safe(df[cols["end_dt"]])

    # Drop rows where datetimes are missing (cohérent avec un calcul de durée)
    df = df.dropna(subset=[cols["start_dt"], cols["end_dt"]]).copy()

    # ✅ Variables du notebook (NOMS EXACTS)
    df["trip_duration_min"] = (df[cols["end_dt"]] - df[cols["start_dt"]]).dt.total_seconds() / 60
    df["day_of_week"] = df[cols["start_dt"]].dt.day_name()
    df["start_hour"] = df[cols["start_dt"]].dt.hour

    return df, cols
