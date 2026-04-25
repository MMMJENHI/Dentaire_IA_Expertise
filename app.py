import streamlit as st
import requests
import numpy as np
import cv2
import plotly.graph_objects as go
from PIL import Image
from io import BytesIO

st.set_page_config(page_title="Expertise Dentaire IA", layout="wide")

st.title("🦷 Système Expert : Analyse de la Dent 16")
st.write("Analyse densitométrique du tiers apical pour diagnostic endodontique.")

# 1. Chargement de l'image via GitHub
url_dent = "https://raw.githubusercontent.com/MMMJENHI/Dentaire_IA_Expertise/main/dent.jpg"

@st.cache_data
def load_data(url):
    response = requests.get(url)
    img = Image.open(BytesIO(response.content)).convert('L')
    return np.array(img)

try:
    img_array = load_data(url_dent)
    st.success("✅ Image chargée avec succès depuis GitHub !")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("🔍 Localisation Tiers Apical")
        # Simuler une zone d'analyse (le tiers apical)
        h, w = img_array.shape
        start_row, end_row = int(h*0.66), h
        roi = img_array[start_row:end_row, w//2-20:w//2+20]
        
        # Dessiner un rectangle sur l'image pour montrer la zone analysée
        display_img = cv2.cvtColor(img_array, cv2.COLOR_GRAY2RGB)
        cv2.rectangle(display_img, (w//2-20, start_row), (w//2+20, end_row), (255, 0, 0), 5)
        st.image(display_img, caption="Zone d'analyse (Tiers Apical)", use_column_width=True)

    with col2:
        st.subheader("📈 Courbe Densitométrique")
        # Extraction du profil de densité (la fameuse courbe)
        profile = np.mean(roi, axis=1)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=profile, mode='lines', name='Densité H', line=dict(color='firebrick', width=3)))
        fig.update_layout(title="Profil de densité le long du canal", xaxis_title="Profondeur (pixels)", yaxis_title="Intensité (H)")
        st.plotly_chart(fig, use_container_width=True)

    # 2. PARTIE EXPERTISE (Le Verdict)
    st.divider()
    h_final = np.max(profile) / 255.0  # Normalisation de la Variable H
    
    st.header(f"📊 Verdict IA : Indice H = {h_final:.2f}")

    if h_final > 0.85:
        st.balloons()
        st.success("🟢 ÉTANCHÉITÉ PARFAITE : Aucune infiltration détectée.")
    elif 0.50 <= h_final <= 0.85:
        st.warning("🟡 ÉTANCHÉITÉ DOUTEUSE : Risque d'infiltration apicale. Surveillance conseillée.")
    else:
        st.error("🔴 DIAGNOSTIC CRITIQUE : Lésion péri-apicale ou vide canalaire détecté.")

except Exception as e:
    st.error(f"Erreur d'accès GitHub : {e}")
    st.info("Vérifiez que MMMJENHI/Dentaire_IA_Expertise contient bien dent.jpg")
