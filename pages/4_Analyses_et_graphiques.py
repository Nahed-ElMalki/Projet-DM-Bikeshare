import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils import load_prepared

st.title("📊 Analyses & Visualisations")

st.markdown(
    "Cette page propose une analyse descriptive de l’utilisation du service à travers plusieurs visualisations clés."
)

df, cols = load_prepared()

# Vérifications minimales des colonnes utilisées dans tes graphes
required = ["start_hour", "day_of_week", "member_casual", "rideable_type"]
missing = [c for c in required if c not in df.columns]
if missing:
    st.error(f"Colonnes manquantes pour générer les graphes : {missing}")
    st.stop()

st.divider()

# ============================================================
# 4.1 Utilisation selon l’heure de départ (IDENTIQUE)
# ============================================================
st.subheader("4.1 Utilisation du service selon l’heure de départ")

trips_by_hour = (
    df.groupby("start_hour")
      .size()
      .reset_index(name="Nombre de trajets")
)

fig = px.bar(
    trips_by_hour,
    x="start_hour",
    y="Nombre de trajets",
    title="Nombre de trajets par heure de départ",
    labels={
        "start_hour": "Heure de départ",
        "Nombre de trajets": "Nombre de trajets"
    },
    color="Nombre de trajets",
    color_continuous_scale="Blues"
)

fig.update_layout(
    plot_bgcolor="white",
    title_x=0.5,
    xaxis=dict(tickmode="linear")
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

st.caption(
    "Cette visualisation permet d’identifier les heures de pointe de l’utilisation du service."
)

# ============================================================
# 4.2 Type de vélo × type d’utilisateur (IDENTIQUE)
# ============================================================
st.subheader("4.2 Répartition des trajets par type de vélo et type d’utilisateur")

bike_user_counts = (
    df.groupby(["rideable_type", "member_casual"])
      .size()
      .reset_index(name="n_trips")
)

fig = px.bar(
    bike_user_counts,
    x="rideable_type",
    y="n_trips",
    color="member_casual",
    barmode="group",
    title="Répartition des trajets par type de vélo et type d’utilisateur",
    labels={
        "rideable_type": "Type de vélo",
        "n_trips": "Nombre de trajets",
        "member_casual": "Type d’utilisateur"
    }
)

fig.update_layout(
    title_x=0.5,
    plot_bgcolor="white"
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

st.caption(
    "Ce graphique compare l’utilisation des différents types de vélos selon le profil d’utilisateur."
)

# ============================================================
# 4.3 Intensité jour × tranche horaire (IDENTIQUE)
# ============================================================
st.subheader("4.3 Intensité de l’utilisation du service selon le jour et la tranche horaire")

bins = [0, 6, 10, 14, 18, 22, 24]
labels = [
    "00–05 (Nuit)",
    "06–09 (Matin)",
    "10–13 (Midi)",
    "14–17 (Après-midi)",
    "18–21 (Soir)",
    "22–23 (Nuit tardive)"
]

# On travaille sur une copie pour ne pas modifier df global
df_h = df.copy()

df_h["time_slot"] = pd.cut(
    df_h["start_hour"],
    bins=bins,
    labels=labels,
    right=False
)

heatmap_data = (
    df_h.groupby(["day_of_week", "time_slot"])
        .size()
        .reset_index(name="n_trips")
)

order_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

fig = px.density_heatmap(
    heatmap_data,
    x="day_of_week",
    y="time_slot",
    z="n_trips",
    category_orders={
        "day_of_week": order_days,
        "time_slot": labels
    },
    color_continuous_scale="Blues",
    title="Intensité des trajets selon le jour et la tranche horaire",
    labels={
        "day_of_week": "Jour de la semaine",
        "time_slot": "Tranche horaire",
        "n_trips": "Nombre de trajets"
    }
)

fig.update_yaxes(autorange="reversed")
fig.update_layout(plot_bgcolor="white", title_x=0.5)

st.plotly_chart(fig, use_container_width=True)

st.divider()
st.caption(
    "La heatmap synthétise l’intensité des trajets selon le jour et la tranche horaire."
)


# ============================================================
# 4.4 Members vs Casual selon le jour ET l’heure (IDENTIQUE)
# ============================================================
st.subheader("4.4 Comparaison Members vs Casual selon le jour et l’heure")

COLOR_MAP = {
    "member": "#636EFA",
    "casual": "#00CC96"
}

hours_order = list(range(24))

day_user = (
    df.groupby(["day_of_week", "member_casual"])
      .size()
      .reset_index(name="n_trips")
)
day_user["day_of_week"] = pd.Categorical(day_user["day_of_week"], categories=order_days, ordered=True)
day_user = day_user.sort_values("day_of_week")

hour_user = (
    df.groupby(["start_hour", "member_casual"])
      .size()
      .reset_index(name="n_trips")
)
hour_user["start_hour"] = pd.Categorical(hour_user["start_hour"], categories=hours_order, ordered=True)
hour_user = hour_user.sort_values("start_hour")

fig = make_subplots(
    rows=1, cols=2,
    subplot_titles=[
        "Trajets par jour : Members vs Casual",
        "Trajets par heure : Members vs Casual"
    ]
)

for user in ["member", "casual"]:
    d = day_user[day_user["member_casual"] == user]
    fig.add_trace(
        go.Bar(
            x=d["day_of_week"],
            y=d["n_trips"],
            name=user,
            marker_color=COLOR_MAP[user]
        ),
        row=1, col=1
    )

    h = hour_user[hour_user["member_casual"] == user]
    fig.add_trace(
        go.Bar(
            x=h["start_hour"],
            y=h["n_trips"],
            name=user,
            marker_color=COLOR_MAP[user],
            showlegend=False
        ),
        row=1, col=2
    )

fig.update_layout(
    title="Comparaison Members vs Casual selon le jour et l’heure",
    barmode="group",
    plot_bgcolor="white",
    title_x=0.5,
    legend_title_text="Type d’utilisateur"
)

fig.update_xaxes(title_text="Jour de la semaine", row=1, col=1)
fig.update_yaxes(title_text="Nombre de trajets", row=1, col=1)

fig.update_xaxes(title_text="Heure de départ", dtick=1, row=1, col=2)
fig.update_yaxes(title_text="Nombre de trajets", row=1, col=2)

st.plotly_chart(fig, use_container_width=True)
st.caption(
    "Cette comparaison met en évidence les différences de comportements selon le type d’utilisateur."
)
