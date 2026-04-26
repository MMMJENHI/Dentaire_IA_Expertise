import streamlit as st
import cv2
import numpy as np
import plotly.graph_objects as go
from skimage.measure import profile_line
from scipy.signal import savgol_filter
from PIL import Image
import pandas as pd
import time
import requests
from io import BytesIO

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="CAD IA Dentaire", layout="wide")

# --- 2. FONCTIONS ---
def preprocess_image(image):
    img_array = np.array(image.convert('L'))
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    return clahe.apply(img_array)

# --- 3. CHARGEMENT ---
st.title("🦷 CAD System : Expertise Apicale Dent 16")

source_radio = st.sidebar.radio("📁 Source :", ("Local", "URL/GitHub", "Démo"))

raw_img = None
if source_radio == "Local":
    up = st.file_uploader("Radio", type=["jpg", "png", "jpeg"])
    if up: raw_img = Image.open(up)
elif source_radio == "URL/GitHub":
    url = st.text_input("Lien Raw :", value="https://raw.githubusercontent.com/MMMJENHI/Dentaire_IA_Expertise/main/dent.jpg")
    if url:
        try:
            res = requests.get(url, timeout=5)
            raw_img = Image.open(BytesIO(res.content))
        except: st.error("Lien invalide")
else:
    try: raw_img = Image.open("dent.jpg")
    except: st.stop()

# --- 4. ANALYSE EXPERTE ---
if raw_img is not None:
    img_gray = preprocess_image(raw_img)
    h, w = img_gray.shape

    # Réglages Sidebar (QR SUPPRIMÉ ICI)
    st.sidebar.header("📍 Contrôles CAD")
    x_c = st.sidebar.slider("Position X", 0, w, int(w/2))
    y_haut = st.sidebar.slider("Haut Canal", 0, h, int(h*0.2))
    y_apex = st.sidebar.slider("Y_apex (Tache Rouge)", 0, h, int(h*0.8))

    y_tiers = int(y_haut + (y_apex - y_haut) * 0.66)

    # Courbe de densité
    signal = profile_line(img_gray, (y_tiers, x_c), (y_apex, x_c), linewidth=5)
    if len(signal) > 5:
        signal_clean = savgol_filter(signal, window_length=max(3, (len(signal)//3)*2+1 if len(signal)<11 else 11), polyorder=2)
        H_values = signal_clean / 255.0
    else:
        H_values = np.array([0.5])

    h_apex = H_values[-1]

    # Visualisation
    col1, col2 = st.columns(2)
    with col1:
        img_visu = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)
        cv2.line(img_visu, (x_c, y_tiers), (x_c, y_apex), (0, 255, 255), 8)
        cv2.circle(img_visu, (x_c, y_apex), 20, (255, 0, 0), -1) 
        st.image(img_visu, use_container_width=True, caption="Analyse CAD en cours")

    with col2:
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=H_values, mode='lines', line=dict(color='cyan', width=4)))
        fig.add_shape(type="line", x0=0, y0=0.45, x1=len(H_values), y1=0.45, line=dict(color="Red", dash="dash"))
        fig.update_layout(template="plotly_dark", height=350, yaxis_title="Densité H")
        st.plotly_chart(fig, use_container_width=True)

    # --- 5. GÉNÉRATION DU RAPPORT CAD ---
    st.divider()
    
    statut = "✅ CONFORME" if h_apex >= 0.45 else "🚨 NON CONFORME"
    
    # Formatage exact du rapport demandé
    rapport_cad = f"""RAPPORT D'EXPERTISE DENTAIRE (CAD SYSTEM)
------------------------------------------
PROPRIÉTAIRE : Projet Master - Dent 16
POSITION ANALYSÉE : X={x_c} | Y_apex={y_apex}
VALEUR H APEX MOYENNE : {h_apex:.4f}
SEUIL DE CONFORMITÉ : 0.45
------------------------------------------
DIAGNOSTIC FINAL : {statut}
------------------------------------------
COMMENTAIRES EXPERTS :
- L'indice H mesure l'herméticité de l'obturation.
- Une valeur < 0.45 indique une réaction apicale ou un vide.
- Limites : Seuil dépendant du capteur et du matériau.
"""

    st.text_area("Prévisualisation du Rapport CAD", rapport_cad, height=250)

    st.download_button(
        label="💾 Télécharger le Rapport (.txt)",
        data=rapport_cad,
        file_name=f"Rapport_CAD_Dent16.txt",
        mime="text/plain"
    )
