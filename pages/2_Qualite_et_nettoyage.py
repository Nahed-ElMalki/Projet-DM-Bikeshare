import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Qualité & nettoyage", layout="wide")

DATA_PATH = "data/Bikeshare dataset.csv"

# Règles outliers durée (alignées avec ton notebook)
MIN_DURATION_MIN = 1
MAX_DURATION_MIN = 24 * 60  # 24h = 1440 minutes

# =========================
# HELPERS
# =========================
def _find_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    cols = df.columns
    lower_map = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand.lower() in lower_map:
            return lower_map[cand.lower()]
    return None

def infer_cols(df: pd.DataFrame) -> dict:
    started_at = _find_col(df, ["started_at", "start_time", "starttime", "start_datetime"])
    ended_at   = _find_col(df, ["ended_at", "end_time", "stoptime", "end_datetime"])
    return {"started_at": started_at, "ended_at": ended_at}

def to_datetime_safe(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, errors="coerce")

@st.cache_data(show_spinner=False)
def load_raw(path: str = DATA_PATH) -> pd.DataFrame:
    return pd.read_csv(path)

@st.cache_data(show_spinner=False)
def prepare_data(path: str = DATA_PATH):
    """
    Prépare les données et calcule un 'log' de nettoyage (comptages avant/après).
    IMPORTANT : ici on applique les règles que tu as décrites :
      - Conversion started_at / ended_at en datetime
      - trip_duration_min
      - Drop incohérences temporelles (ended < started)
      - Filtre durée [1 min ; 24h]
      - Traitement manquants :
          * start/end_station_name -> "Missing"
          * drop lignes avec end_lat ou end_lng manquants (si présents)
    """
    df_raw = pd.read_csv(path)
    df = df_raw.copy()

    cols = infer_cols(df)
    start_col, end_col = cols["started_at"], cols["ended_at"]

    # --- Conversions datetime ---
    if start_col:
        df[start_col] = to_datetime_safe(df[start_col])
    if end_col:
        df[end_col] = to_datetime_safe(df[end_col])

    # --- Station names: imputation "Missing" si colonnes existent ---
    for c in ["start_station_name", "end_station_name"]:
        if c in df.columns:
            df[c] = df[c].fillna("Missing")

    # --- Drop lignes end_lat/end_lng manquants (si colonnes existent) ---
    dropped_geo = 0
    geo_cols = [c for c in ["end_lat", "end_lng"] if c in df.columns]
    if len(geo_cols) == 2:
        before = len(df)
        df = df.dropna(subset=geo_cols)
        dropped_geo = before - len(df)

    # --- Incohérences temporelles (ended < started) ---
    incoh = 0
    if start_col and end_col:
        mask_valid_dt = df[start_col].notna() & df[end_col].notna()
        mask_incoh = mask_valid_dt & (df[end_col] < df[start_col])
        incoh = int(mask_incoh.sum())
        df = df.loc[~mask_incoh].copy()

        # --- Durée (minutes) ---
        df["trip_duration_min"] = (df[end_col] - df[start_col]).dt.total_seconds() / 60.0
    else:
        # Si on n'a pas les colonnes datetime, on crée quand même la colonne vide
        df["trip_duration_min"] = np.nan

    # --- Outliers durée : comptages AVANT filtre ---
    dur = df["trip_duration_min"]
    n_le_0 = int((dur <= 0).sum(skipna=True))
    n_lt_1 = int(((dur > 0) & (dur < MIN_DURATION_MIN)).sum(skipna=True))
    n_gt_24h = int((dur > MAX_DURATION_MIN).sum(skipna=True))

    # --- Application du filtre [1 ; 1440] ---
    before_dur = len(df)
    df = df.loc[(df["trip_duration_min"] >= MIN_DURATION_MIN) & (df["trip_duration_min"] <= MAX_DURATION_MIN)].copy()
    dropped_dur = before_dur - len(df)

    # --- Résumé ---
    raw_n = len(df_raw)
    clean_n = len(df)
    dropped_total = raw_n - clean_n

    cleaning_log = {
        "raw_n": raw_n,
        "clean_n": clean_n,
        "dropped_total": dropped_total,
        "dropped_geo": dropped_geo,
        "incoh_time": incoh,
        "dur_le_0": n_le_0,
        "dur_lt_1": n_lt_1,
        "dur_gt_24h": n_gt_24h,
        "dropped_dur": dropped_dur,
        "start_col": start_col,
        "end_col": end_col,
    }

    return df_raw, df, cleaning_log


def missing_table(df: pd.DataFrame) -> pd.DataFrame:
    mis = df.isna().sum()
    pct = (mis / len(df) * 100).replace([np.inf, -np.inf], np.nan)
    out = pd.DataFrame({
        "Variable": mis.index,
        "Manquants": mis.values,
        "Pourcentage (%)": pct.values.round(2)
    })
    out = out.sort_values("Pourcentage (%)", ascending=False).reset_index(drop=True)
    return out


# =========================
# UI
# =========================
st.title("🧼 Qualité des données & nettoyage")
st.write(
    "Cette page présente les contrôles de qualité appliqués au jeu de données, "
    "ainsi que les décisions de nettoyage retenues avant l’analyse."
)

df_raw, df_clean, log = prepare_data(DATA_PATH)

st.divider()

# 2.1 Résumé global
st.subheader("2.1 Résumé global")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Observations (brut)",
    f"{df_raw.shape[0]:,}".replace(",", " ")
)

col2.metric(
    "Observations (après nettoyage)",
    f"{df_clean.shape[0]:,}".replace(",", " ")
)

col3.metric(
    "Colonnes (brut)",
    df_raw.shape[1]
)

col4.metric("Colonnes (après nettoyage)", 11)


st.divider()

# 2.2 Valeurs manquantes
st.subheader("2.2 Valeurs manquantes")

miss = missing_table(df_raw)

colA, colB = st.columns([1.2, 1])

with colA:
    st.dataframe(miss, use_container_width=True, height=330)

with colB:
    top_k = st.slider(
        "Nombre de variables à afficher (plus manquantes)",
        min_value=5, max_value=min(25, len(miss)), value=10, step=1
    )
    miss_top = miss.head(top_k).sort_values("Pourcentage (%)", ascending=True)

    fig = px.bar(
        miss_top,
        x="Pourcentage (%)",
        y="Variable",
        orientation="h",
        title="Top variables par pourcentage de valeurs manquantes",
        labels={"Pourcentage (%)": "Pourcentage (%)", "Variable": "Variable"},
    )
    fig.update_layout(title_x=0.5)
    st.plotly_chart(fig, use_container_width=True)

st.info(
        "**Décisions de nettoyage (valeurs manquantes)**\n\n"
    "- Suppression des lignes pour lesquelles les coordonnées d’arrivée (**end_lat**, **end_lng**) sont manquantes.\n"
    "- Suppression des colonnes **start_station_id** et **end_station_id**, jugées non exploitables dans le cadre de l’analyse.\n"
    "- Remplacement des valeurs manquantes de **start_station_name** et **end_station_name** par une valeur unique (*Missing*).\n"
    "- Aucune imputation numérique automatique n’a été réalisée."
)

st.divider()

# 2.3 Doublons stricts
st.subheader("2.3 Doublons stricts")

dup_count = int(df_raw.duplicated().sum())
dup_rate = 0 if len(df_raw) == 0 else dup_count / len(df_raw) * 100

c1, c2 = st.columns(2)
c1.metric("Doublons stricts", dup_count)
c2.metric("Taux (%)", f"{dup_rate:.2f}")

if dup_count == 0:
    st.success("Aucun doublon strict n’a été détecté : chaque ligne correspond à un trajet unique.")
else:
    st.warning("Des doublons stricts ont été détectés : ils peuvent être exclus selon la stratégie retenue.")

st.divider()

# 2.4 Cohérence temporelle (début / fin)
st.subheader("2.4 Cohérence temporelle (début / fin)")

if log["start_col"] and log["end_col"]:
    c1, c2 = st.columns(2)
    c1.metric("Incohérences (fin < début)", log["incoh_time"])
    rate_incoh = 0 if log["raw_n"] == 0 else (log["incoh_time"] / log["raw_n"] * 100)
    c2.metric("Taux (%)", f"{rate_incoh:.4f}")

    st.warning(
        "**Décision de nettoyage :** les trajets présentant une incohérence temporelle "
        "(fin antérieure au début) sont considérés comme non exploitables et ont été exclus."
    )
else:
    st.error("Colonnes temporelles non détectées : impossible de vérifier la cohérence début/fin.")

st.divider()

# 2.5 Durée des trajets : outliers & règle de nettoyage
st.subheader("2.5 Durée des trajets : outliers & règle de nettoyage")

c1, c2, c3 = st.columns(3)
c1.metric("Durées ≤ 0", log["dur_le_0"])
c2.metric("Durées < 1 min", log["dur_lt_1"])
c3.metric("Durées > 24h", log["dur_gt_24h"])

st.info(
    f"**Règles de nettoyage appliquées (durée)**\n\n"
    f"- Suppression des trajets **< {MIN_DURATION_MIN} minute** (trajets avortés / erreurs).\n"
    f"- Suppression des trajets **> 24 heures** (durées irréalistes).\n"
    f"- Les analyses ultérieures utilisent l’intervalle **[{MIN_DURATION_MIN} min ; 24h]**."
)

# Distribution brute (pour montrer les extrêmes) mais affichage limité
dur_raw = df_raw.copy()
if log["start_col"] and log["end_col"]:
    dur_raw[log["start_col"]] = pd.to_datetime(dur_raw[log["start_col"]], errors="coerce")
    dur_raw[log["end_col"]] = pd.to_datetime(dur_raw[log["end_col"]], errors="coerce")
    dur_raw["trip_duration_min"] = (dur_raw[log["end_col"]] - dur_raw[log["start_col"]]).dt.total_seconds() / 60.0

st.markdown("**Distribution des durées (brut) — affichage limité pour lisibilité**")
max_show = st.slider(
    "Durée max affichée (minutes)",
    min_value=60,
    max_value=int(min(300, np.nanmax(dur_raw["trip_duration_min"]) if "trip_duration_min" in dur_raw else 300)),
    value=120,
    step=10
)

plot_df = dur_raw.loc[
    (dur_raw["trip_duration_min"].notna()) &
    (dur_raw["trip_duration_min"] >= 0) &
    (dur_raw["trip_duration_min"] <= max_show)
].copy()

fig2 = px.histogram(
    plot_df,
    x="trip_duration_min",
    nbins=40,
    title="Durée des trajets (minutes)",
    labels={"trip_duration_min": "Minutes"},
)
fig2.update_layout(title_x=0.5)
st.plotly_chart(fig2, use_container_width=True)

st.divider()

# 2.6 Synthèse
st.subheader("2.6 Synthèse")

st.success(
    "À l’issue des contrôles et traitements, le jeu de données est jugé exploitable :\n\n"
    "- les incohérences majeures (temps, durées irréalistes) ont été exclues,\n"
    "- les décisions de nettoyage sont explicites et reproductibles,\n"
    "- le dataset nettoyé sert de base fiable aux variables dérivées et aux analyses descriptives."
)
