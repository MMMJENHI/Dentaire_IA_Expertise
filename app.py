import streamlit as st
import cv2
import numpy as np
import plotly.graph_objects as go
from skimage.measure import profile_line
from PIL import Image
import os
import time

# --- CONFIGURATION PAGE ---
st.set_page_config(page_title="Expertise Dentaire IA", layout="wide")

# --- FONCTION DE TRAITEMENT ---
def preprocess_image(image):
    img_array = np.array(image.convert('L'))
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    return clahe.apply(img_array)

# --- CHARGEMENT AUTOMATIQUE GITHUB ---
st.title("🦷 Expertise IA Automatique : Dent 16")
nom_fichier = "dent.jpg"

if os.path.exists(nom_fichier):
    raw_img = Image.open(nom_fichier)
    img_gray = preprocess_image(raw_img)
    h, w = img_gray.shape
    
    # --- BARRE LATERALE POUR L'INTERACTION ---
    st.sidebar.header("🕹️ Commandes de l'Expert")
    # Ces sliders redonnent l'interaction avec le code
    x_c = st.sidebar.slider("Position X (Axe Canal)", 0, w, int(w/2))
    y_haut = st.sidebar.slider("Haut de la racine (Y1)", 0, h, int(h/3))
    y_apex = st.sidebar.slider("Pointe de l'Apex (Y2)", 0, h, int(h/1.2))

    # Calcul automatique du tiers apical (les derniers 33%)
    y_tiers = int(y_haut + (y_apex - y_haut) * 0.66)

    # --- AFFICHAGE ---
    col1, col2 = st.columns([1, 1.2])

    with col1:
        st.subheader("📸 Localisation")
        # Dessiner la ligne de scan sur l'image
        img_visu = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)
        cv2.line(img_visu, (x_c, y_tiers), (x_c, y_apex), (255, 255, 0), 15)
        st.image(img_visu, caption="Scan du Tiers Apical", use_container_width=True)

    with col2:
        st.subheader("📊 Courbe de Densité (H)")
        # Extraction du profil de densité
        profil = profile_line(img_gray, (y_tiers, x_c), (y_apex, x_c), linewidth=10)
        h_values = profil / 255.0 # Normalisation

        fig = go.Figure()
        fig.add_trace(go.Scatter(y=h_values, mode='lines', name='Indice H', line=dict(color='gold', width=3)))
        fig.update_layout(template="plotly_dark", height=400)
        st.plotly_chart(fig, use_container_width=True)

    # --- LE BOUTON MAGIQUE (RÉTABLIT L'ACTION) ---
    st.divider()
    if st.button("✨ LANCER LE DIAGNOSTIC FINAL"):
        with st.spinner('Analyse des harmoniques de densité...'):
            time.sleep(1)
            h_min = np.min(h_values)
            if h_min < 0.40:
                st.snow()
                st.error(f"🚨 RÉACTION APICALE DÉTECTÉE (H min = {h_min:.2f})")
            else:
                st.balloons()
                st.success(f"✅ ÉTANCHÉITÉ VALIDÉE (H min = {h_min:.2f})")

else:
    st.error("Fichier dent.jpg introuvable sur GitHub.")
