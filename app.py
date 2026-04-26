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
st.set_page_config(page_title="CAD IA Dentaire Expert", layout="wide")

# --- 2. FONCTIONS ---
def preprocess_image(image):
    img_array = np.array(image.convert('L'))
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    return clahe.apply(img_array)

# --- 3. CHARGEMENT ---
st.title("🦷 CAD System : Visualisation Expert (Dent 16)")

source_radio = st.sidebar.radio("📁 Source :", ("Local", "URL/GitHub", "Démo"))

raw_img = None
if source_radio == "Local":
    up = st.file_uploader("Radio", type=["jpg", "png", "jpeg"])
    if up: raw_img = Image.open(up)
elif source_radio == "URL/GitHub":
    url_input = st.text_input("Lien Raw :", value="https://raw.githubusercontent.com/MMMJENHI/Dentaire_IA_Expertise/main/dent.jpg")
    if url_input:
        try:
            res = requests.get(url_input, timeout=5)
            raw_img = Image.open(BytesIO(res.content))
        except: st.error("Lien invalide")
else:
    try:
        raw_img = Image.open("dent.jpg")
    except:
        st.error("Fichier dent.jpg manquant")
        st.stop()

# --- 4. ANALYSE EXPERTE ---
if raw_img is not None:
    img_gray = preprocess_image(raw_img)
    h, w = img_gray.shape

    # --- BARRE LATÉRALE ---
    st.sidebar.header("📍 Contrôles CAD")
    
    # QR CODE API (Méthode stable Hugging Face/GitHub)
    url_projet = "https://dentaireiaexpertise-eg4mdsd9cguhyhc4idk7rn.streamlit.app/"
    qr_api = f"https://api.qrserver.com/v1/create-qr-code/?size=120x120&data={url_projet}"
    st.sidebar.image(qr_api, caption="Lien Mobile")
    st.sidebar.divider()

    x_c = st.sidebar.slider("Position X (Axe)", 0, w, int(w/2))
    y_haut = st.sidebar.slider("Haut Canal (Y)", 0, h, int(h*0.2))
    y_apex = st.sidebar.slider("Y_apex (Point Final)", 0, h, int(h*0.8))

    # Calcul des zones
    y_tiers_debut = int(y_haut + (y_apex - y_haut) * 0.66)
    
    # 1. Extraction Signal Global (Rouge)
    signal_global = profile_line(img_gray, (y_haut, x_c), (y_apex, x_c), linewidth=3)
    # 2. Extraction Signal Tiers Apical (Cyan)
    signal_apical = profile_line(img_gray, (y_tiers_debut, x_c), (y_apex, x_c), linewidth=5)

    def smooth(sig):
        if len(sig) > 5:
            w_len = 11 if len(sig) > 11 else (len(sig)-1 if len(sig)%2==0 else len(sig))
            return savgol_filter(sig, window_length=max(3, w_len), polyorder=2) / 255.0
        return sig / 255.0

    H_global = smooth(signal_global)
    H_apical = smooth(signal_apical)
    h_final = H_apical[-1]

    # --- 5. VISUALISATION (ROUGE & CYAN) ---
    col_img, col_graphs = st.columns([1, 1.5])

    with col_img:
        st.subheader("🔎 Visualisation CAD")
        img_visu = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)
        
        # Trait ROUGE (Global) : Décalé de 10 pixels à gauche
        cv2.line(img_visu, (x_c - 15, y_haut), (x_c - 15, y_apex), (255, 0, 0), 3)
        
        # Trait CYAN (Tiers Apical) : Au centre, très épais
        cv2.line(img_visu, (x_c, y_tiers_debut), (x_c, y_apex), (255, 255, 0), 15)
        
        # Point APEX (Blanc)
        cv2.circle(img_visu, (x_c, y_apex), 15, (255, 255, 255), -1) 
        
        st.image(img_visu, use_container_width=True)

    with col_graphs:
        # GRAPHIQUE 1 : ROUGE (GLOBAL)
        st.subheader("📈 1. Profil Global (Axe Y)")
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=np.arange(y_haut, y_apex), y=H_global, name="Totalité", line=dict(color='red', width=3)))
        fig1.update_layout(template="plotly_dark", height=250, margin=dict(t=10, b=10),
                           xaxis_title="Position Y (Pixels)", yaxis_title="Densité H")
        st.plotly_chart(fig1, use_container_width=True)

        # GRAPHIQUE 2 : CYAN (APICAL)
        st.subheader("📈 2. Zoom Tiers Apical")
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(y=H_apical, name="Expertise", line=dict(color='cyan', width=5)))
        # Seuil
        fig2.add_shape(type="line", x0=0, y0=0.45, x1=len(H_apical), y1=0.45, line=dict(color="white", dash="dash"))
        fig2.update_layout(template="plotly_dark", height=250, margin=dict(t=10, b=10),
                           xaxis_title="Progression Apicale (%)", yaxis_title="Densité H")
        st.plotly_chart(fig2, use_container_width=True)

    # --- 6. RAPPORT CAD ---
    st.divider()
    statut = "✅ CONFORME" if h_final >= 0.45 else "🚨 NON CONFORME"
    rapport_cad = f"RAPPORT CAD - DENT 16\nPROPRIÉTAIRE : Projet Master\nPOSITION : X={x_c} | Y={y_apex}\nVALEUR H : {h_final:.4f}\nDIAGNOSTIC : {statut}"
    
    st.text_area("Bilan Expert", rapport_cad, height=150)
    st.download_button("💾 Télécharger Rapport", rapport_cad, "Rapport_CAD.txt")
