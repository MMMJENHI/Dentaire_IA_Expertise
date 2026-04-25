import streamlit as st
import requests
import numpy as np
import cv2
import pandas as pd
import plotly.graph_objects as go
from PIL import Image
from io import BytesIO

# Configuration de la page
st.set_page_config(page_title="Rapport d'Expertise IA Dentaire", layout="wide")

st.title("🦷 Système Expert : Analyse Densitométrique & Rapport")
st.write("Analyse automatisée du tiers apical pour la Dent 16.")

# --- CHARGEMENT ---
url_dent = "https://raw.githubusercontent.com/MMMJENHI/Dentaire_IA_Expertise/main/dent.jpg"

@st.cache_data
def load_img(url):
    try:
        response = requests.get(url)
        return np.array(Image.open(BytesIO(response.content)).convert('L'))
    except: return None

img_array = load_img(url_dent)

if img_array is not None:
    # --- BARRE LATÉRALE ---
    st.sidebar.header("⚙️ Paramètres d'Analyse")
    h, w = img_array.shape
    pos_y = st.sidebar.slider("Position Verticale", 0, h, int(h * 0.75))
    pos_x = st.sidebar.slider("Position Horizontale", 0, w, int(w * 0.5))
    rayon = st.sidebar.slider("Rayon de la zone", 20, 150, 60)

    # --- TRAITEMENT ---
    img_rgb = cv2.cvtColor(img_array, cv2.COLOR_GRAY2RGB)
    cv2.circle(img_rgb, (pos_x, pos_y), rayon, (255, 0, 0), 3) # Cercle rouge
    
    # Extraction des données pour le graphique
    y_start, y_end = max(0, pos_y-rayon), min(h, pos_y+rayon)
    profile = img_array[y_start:y_end, pos_x] / 255.0
    h_final = np.mean(profile)

    # --- DISPOSITION ---
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("🔍 Localisation de la zone")
        st.image(img_rgb, use_container_width=True)

    with col2:
        st.subheader("📈 Profil de Densité (H-Index)")
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=profile, mode='lines', line=dict(color='firebrick', width=4)))
        fig.update_layout(height=400, yaxis_range=[0, 1], xaxis_title="Profondeur", yaxis_title="Intensité H")
        st.plotly_chart(fig, use_container_width=True)

    # --- NOUVEAU : RAPPORT D'EXPERTISE AVEC TABLEAU ---
    st.divider()
    st.header("📋 Rapport d'Expertise Final")
    
    # Création des données du tableau
    verdict = "ÉTANCHÉITÉ VALIDÉE" if h_final > 0.85 else "SURVEILLANCE REQUISE"
    statut = "✅ Conforme" if h_final > 0.85 else "⚠️ Alerte"
    
    data = {
        "Paramètre d'Expertise": ["Indice H (Moyen)", "Zone d'Analyse (Y)", "Rayon d'Exploration", "Diagnostic Final"],
        "Valeur Mesurée": [f"{h_final:.2f}", f"{pos_y} px", f"{rayon} px", verdict],
        "Statut": [statut, "Inclus", "Optimal", statut]
    }
    
    df = pd.DataFrame(data)
    
    # Affichage du tableau stylisé
    st.table(df)

    # Conclusion dynamique
    if h_final > 0.85:
        st.success(f"**Conclusion de l'Expert :** La densité au tiers apical (H={h_final:.2f}) indique une obturation hermétique. Le risque de réinfection est jugé très faible.")
        st.balloons()
    else:
        st.warning(f"**Conclusion de l'Expert :** La densité mesurée (H={h_final:.2f}) est inférieure au seuil critique. Une infiltration ou un vide canalaire est suspecté.")

else:
    st.error("Impossible de charger les données depuis GitHub.")
