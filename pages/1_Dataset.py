import streamlit as st
import pandas as pd
from utils import load_raw, load_prepared

st.title("📌 Présentation du jeu de données")

st.markdown(
    """
Cette section présente le jeu de données utilisé dans le projet :
sa structure, son volume, ses types de variables, la période couverte
et la présence éventuelle de valeurs manquantes.
"""
)

# ------------------------------------------------------------------
# Chargement des données
# ------------------------------------------------------------------
df_raw = load_raw()
df, cols = load_prepared()

# ------------------------------------------------------------------
# Indicateurs clés
# ------------------------------------------------------------------
num_vars = df_raw.select_dtypes(include=["int64", "float64"]).shape[1]
cat_vars = df_raw.select_dtypes(include=["object"]).shape[1]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Nombre d’observations", f"{df_raw.shape[0]:,}".replace(",", " "))
c2.metric("Nombre total de variables", df_raw.shape[1])
c3.metric("Variables numériques", num_vars)
c4.metric("Variables catégorielles", cat_vars)



# ------------------------------------------------------------------
# Aperçu du dataset
# ------------------------------------------------------------------
st.subheader("Aperçu des données")

n = st.slider("Nombre de lignes à afficher", min_value=5, max_value=50, value=10)
st.dataframe(df_raw.head(n), use_container_width=True)

st.divider()

# ------------------------------------------------------------------
# Structure des variables
# ------------------------------------------------------------------
st.subheader("Structure des variables")

structure_df = pd.DataFrame({
    "Variable": df_raw.columns,
    "Type": df_raw.dtypes.astype(str)
})

st.dataframe(structure_df, use_container_width=True)

st.divider()

# ------------------------------------------------------------------
# Valeurs manquantes
# ------------------------------------------------------------------
st.subheader("Valeurs manquantes")

missing = df_raw.isna().sum()
missing = missing[missing > 0]

if missing.empty:
    st.success("Aucune valeur manquante détectée dans le dataset.")
else:
    missing_df = pd.DataFrame({
        "Variable": missing.index,
        "Nombre de valeurs manquantes": missing.values,
        "Pourcentage (%)": (missing.values / len(df_raw) * 100).round(2)
    })
    st.dataframe(missing_df, use_container_width=True)

st.divider()

# ------------------------------------------------------------------
# Période couverte
# ------------------------------------------------------------------
st.subheader("Période couverte")

if cols["start_dt"] is None:
    st.info(
        "La colonne de date de départ n’a pas pu être détectée automatiquement."
    )
else:
    start_min = df[cols["start_dt"]].min()
    start_max = df[cols["start_dt"]].max()

    c1, c2 = st.columns(2)
    c1.metric("Début de la période", str(start_min))
    c2.metric("Fin de la période", str(start_max))

    st.caption(
        "La période est calculée à partir de la colonne temporelle de départ."
    )
