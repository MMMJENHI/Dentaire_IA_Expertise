import streamlit as st
import requests
import numpy as np
import cv2
import pandas as pd
import plotly.graph_objects as go
from PIL import Image
from io import BytesIO

st.set_page_config(page_title="Expertise IA - Diagnostic Clinique", layout="wide")

st.title("🦷 Expertise IA Dentaire : Analyse de la Variable H")
st.write("Comparaison entre l'Indice H Idéal, l'Indice H Réel et Détection de Réactions Atypiques.")

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
    pos_x = st.sidebar.slider("Position Horizontale", 0, w, int(width * 0.5))
    rayon = st.sidebar.slider("Rayon d'analyse", 20, 100, 50)

    # --- CALCULS SCIENTIFIQUES ---
    y_start, y_end = max(0, pos_y-rayon), min(h, pos_y+rayon)
    profile = img_array[y_start:y_end, pos_x] / 255.0
    
    h_radio = np.mean(profile)  # H mesuré sur la radio
    h_ideal = 0.95              # Valeur théorique d'une obturation parfaite
    ecart = h_ideal - h_radio   # Calcul de l'atypie
    
    # --- AFFICHAGE RADIOS ---
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🔍 Radio Originale")
        img_rgb = cv2.cvtColor(img_array, cv2.COLOR_GRAY2RGB)
        cv2.circle(img_rgb, (pos_x, pos_y), rayon, (255, 0, 0), 2)
        st.image(img_rgb, use_container_width=True)

    with col2:
        st.subheader("🧬 Radio de Densité (Analyse H)")
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        density_map = clahe.apply(img_array)
        st.image(density_map, use_container_width=True)

    # --- GRAPHIQUE COMPARATIF ---
    st.divider()
    st.subheader("📈 Analyse Comparative : H Idéal vs H Radio")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(y=profile, name="H Radio (Réel)", line=dict(color='red', width=3)))
    fig.add_hline(y=h_ideal, line_dash="dash", line_color="green", annotation_text="H Idéal (Théorique)")
    fig.update_layout(yaxis_range=[0, 1.1], height=350)
    st.plotly_chart(fig, use_container_width=True)

    # --- TABLEAU DE RAPPORT D'EXPERTISE ---
    st.divider()
    st.header("📋 Rapport d'Expertise Densitométrique")
    
    # Logique de réaction atypique
    reaction = "Normale"
    if ecart > 0.40:
        reaction = "ATYPIQUE (Lésion probable)"
    elif ecart > 0.15:
        reaction = "Douteuse (Infiltration)"

    df_rapport = pd.DataFrame({
        "Indicateur": ["H Idéal (Seuil)", "H Radio (Mesuré)", "Écart de Densité", "Réaction Clinique"],
        "Valeur": [f"{h_ideal:.2f}", f"{h_radio:.2f}", f"{ecart:.2f}", reaction],
        "Interprétation": ["Référence Standard", "Donnée Patient", "Perte de substance", "Diagnostic final"]
    })
    
    st.table(df_rapport)

    # Conclusion Finale
    if reaction == "Normale":
        st.success(f"**Conclusion :** L'indice H ({h_radio:.2f}) est proche de l'idéal. Étanchéité confirmée.")
    else:
        st.error(f"**Alerte :** Réaction atypique détectée. L'écart de {ecart:.2f} suggère une pathologie apicale.")

else:
    st.error("Impossible de charger les données.")
