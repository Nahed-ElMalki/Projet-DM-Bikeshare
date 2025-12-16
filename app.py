import streamlit as st

st.set_page_config(page_title="BikeShare — Data Management", layout="wide")

st.title("🚲 BikeShare — Application interactive de Data Management")

st.markdown(
    """
**Contexte.** Cette application permet d’explorer un jeu de données de trajets BikeShare (mobilité urbaine),
en suivant une démarche structurée de **Data Management** et de **visualisation interactive**.

**Objectifs.**
- Décrire le jeu de données (volume, variables, période, valeurs manquantes)
- Évaluer et traiter la qualité des données (incohérences, doublons, valeurs extrêmes)
- Créer des variables dérivées pertinentes pour l’analyse
- Visualiser les tendances d’usage et comparer les profils d’utilisateurs
- Explorer un texte lié au thème (Text Mining)
"""
)

st.info("Navigation : utilisez le menu à gauche pour accéder aux différentes sections.")


