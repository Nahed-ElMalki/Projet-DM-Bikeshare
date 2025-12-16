import streamlit as st
import pandas as pd

from utils import load_prepared  # doit retourner (df, cols_map)

# =========================
# Page 3 — Variables créées
# =========================

st.title("🧩 Création de nouvelles variables")

st.markdown(
    "Cette page présente les variables dérivées construites à partir des informations temporelles des trajets. "
    "Elle permet de documenter ces variables et d’en proposer une exploration rapide, avant les analyses graphiques."
)

# --- Load prepared data (après nettoyage / préparation)
df, cols = load_prepared()

st.divider()

# -------------------------
# 3.1 Variables dérivées créées (documentation)
# -------------------------
st.subheader("3.1 Variables dérivées créées")

vars_doc = pd.DataFrame(
    [
        {
            "Variable": "trip_duration_min",
            "Type": "Numérique",
            "Description": "Durée du trajet en minutes, calculée comme (ended_at − started_at).",
        },
        {
            "Variable": "day_of_week",
            "Type": "Catégorielle",
            "Description": "Jour de la semaine du départ, extrait de started_at (Monday–Sunday).",
        },
        {
            "Variable": "start_hour",
            "Type": "Numérique",
            "Description": "Heure de départ du trajet (0–23), extraite de started_at.",
        },
    ]
)

st.dataframe(vars_doc, use_container_width=True, hide_index=True)

st.divider()

# -------------------------
# 3.2 Justification (court, académique)
# -------------------------
st.subheader("3.2 Justification")

st.markdown(
    "Les variables dérivées permettent d’analyser l’utilisation du service selon le temps :\n\n"
    "- `trip_duration_min` : étudier la distribution des durées et repérer des valeurs atypiques.\n"
    "- `day_of_week` et `start_hour` : analyser les comportements selon le jour et l’heure (périodes de pointe, week-end, etc.)."
)

st.divider()

# -------------------------
# 3.3 Exploration interactive (Data Analyst)
# -------------------------
st.subheader("🔎 Exploration interactive des variables dérivées")

# Liste des variables réellement présentes
available_vars = [v for v in ["trip_duration_min", "day_of_week", "start_hour"] if v in df.columns]

if len(available_vars) == 0:
    st.error("Aucune variable dérivée attendue n’est disponible dans les données préparées.")
    st.stop()

var_choice = st.selectbox("Sélectionner une variable", available_vars)

# Série de base
s = df[var_choice].dropna()

# Filtrage cohérent après nettoyage (uniquement pour la durée)
# -> on exclut les trajets < 1 minute (non représentatifs / erreurs)
# -> on exclut les trajets > 24h (irréalistes)
if var_choice == "trip_duration_min":
    s = s[(s >= 1) & (s <= 24 * 60)]

if len(s) == 0:
    st.warning("Aucune valeur disponible après filtrage.")
    st.stop()

# --- Affichage métriques + tableaux
c1, c2, c3, c4 = st.columns(4)

if var_choice == "trip_duration_min":
    c1.metric("Min (min)", f"{s.min():.2f}")
    c2.metric("Médiane (min)", f"{s.median():.2f}")
    c3.metric("Moyenne (min)", f"{s.mean():.2f}")
    c4.metric("Max (min)", f"{s.max():.2f}")

    st.markdown("**Exemples de durées (les plus longues, après nettoyage)**")

    top_long = (
        s.sort_values(ascending=False)
        .head(10)
        .reset_index(drop=True)
        .to_frame(name="Durée du trajet (minutes)")
    )

    st.dataframe(
        top_long.style.format({"Durée du trajet (minutes)": "{:.2f}"}),
        use_container_width=True,
    )

elif var_choice == "start_hour":
    c1.metric("Heure min", int(s.min()))
    c2.metric("Heure max", int(s.max()))
    c3.metric("Valeurs uniques", int(s.nunique()))
    mode_val = s.mode().iloc[0] if not s.mode().empty else None
    c4.metric("Heure la plus fréquente", int(mode_val) if mode_val is not None else "-")

    st.markdown("**Heures les plus fréquentes**")
    top = s.value_counts().head(10).reset_index()
    top.columns = ["Heure", "Occurrences"]
    st.dataframe(top, use_container_width=True, hide_index=True)

else:  # day_of_week
    vc = s.value_counts()
    top_day = vc.idxmax()
    c1.metric("Jours distincts", int(s.nunique()))
    c2.metric("Jour dominant", str(top_day))
    c3.metric("Occurrences", int(vc.max()))
    c4.metric("Part (%)", f"{(vc.max() / len(s) * 100):.2f}%")

    st.markdown("**Répartition (jours les plus fréquents)**")
    top = vc.head(10).reset_index()
    top.columns = ["Jour", "Occurrences"]
    st.dataframe(top, use_container_width=True, hide_index=True)

st.divider()

# -------------------------
# 3.4 Échantillon (preuve de préparation)
# -------------------------
st.subheader("3.4 Échantillon des données préparées")

cols_to_show = [c for c in [
    "ride_id", "member_casual", "rideable_type",
    "started_at", "ended_at",
    "trip_duration_min", "day_of_week", "start_hour"
] if c in df.columns]

st.dataframe(df[cols_to_show].head(15), use_container_width=True)
