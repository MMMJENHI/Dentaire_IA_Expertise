import streamlit as st
import cv2
import numpy as np
import plotly.graph_objects as go
from skimage.measure import profile_line
from scipy.signal import savgol_filter
from PIL import Image
import pandas as pd
import time
import qrcode
from io import BytesIO
import os

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="IA Expertise Dentaire", layout="wide")

# --- 2. FONCTIONS ---

def generer_qr_statique(url):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Conversion pour Streamlit
    buf = BytesIO()
    img.save(buf, format="PNG")
    
    # Astuce : On retourne aussi l'objet image pour le sauvegarde
    return buf, img

def preprocess_image(image):
    img_array = np.array(image.convert('L'))
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    return clahe.apply(img_array)

# --- 3. INTERFACE & LOGIQUE ---
st.title("🦷 Système Expert : Analyse de la Dent 16")

uploaded_file = st.file_uploader("Charger la radiographie", type=["jpg", "png", "jpeg"])

raw_img = None
if uploaded_file is not None:
    raw_img = Image.open(uploaded_file)
else:
    try:
        raw_img = Image.open("dent.jpg")
    except FileNotFoundError:
        st.warning("⚠️ Image 'dent.jpg' manquante.")
        st.stop()

if raw_img is not None:
    img_gray = preprocess_image(raw_img)
    h, w = img_gray.shape

    # --- SIDEBAR & QR CODE ---
    st.sidebar.header("📍 Réglages de l'Expert")
    x_c = st.sidebar.slider("Position X", 0, w, int(w/2))
    y_haut = st.sidebar.slider("Haut du Canal", 0, h, int(h*0.2))
    y_apex = st.sidebar.slider("Fin de l'Apex", 0, h, int(h*0.8))

    st.sidebar.markdown("---")
    st.sidebar.write("### 📲 Application Mobile")
    
    # VOTRE LIEN COURT COMBINÉ
    url_app = "https://tinyurl.com/ia-dent-16"
    
    # Génération du QR
    qr_buf, qr_img_obj = generer_qr_statique(url_app)
    st.sidebar.image(qr_buf, caption="Scanner pour l'expertise mobile", width=150)

    # --- 4. ANALYSE VISUELLE ---
    y_tiers_apical = int(y_haut + (y_apex - y_haut) * 0.66)
    col1, col2 = st.columns([1, 1.2])

    with col1:
        st.subheader("🔎 Zone de Scan")
        img_visu = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)
        cv2.line(img_visu, (x_c, y_tiers_apical), (x_c, y_apex), (0, 255, 255), 10)
        cv2.circle(img_visu, (x_c, y_apex), 25, (255, 0, 0), -1) 
        st.image(img_visu, use_container_width=True)

    with col2:
        st.subheader("📈 Courbe de Densité H")
        signal = profile_line(img_gray, (y_tiers_apical, x_c), (y_apex, x_c), linewidth=5)
        if len(signal) > 5:
            w_len = 11 if len(signal) > 11 else (len(signal)-1 if len(signal)%2==0 else len(signal))
            signal_clean = savgol_filter(signal, window_length=max(3, w_len), polyorder=2)
            H_values = signal_clean / 255.0
        else:
            H_values = np.array([0.0])

        fig = go.Figure()
        fig.add_trace(go.Scatter(y=H_values, mode='lines', line=dict(color='cyan', width=4)))
        fig.update_layout(template="plotly_dark", height=300, yaxis=dict(range=[0, 1.1]))
        st.plotly_chart(fig, use_container_width=True)

    if st.button("✨ LANCER LE DIAGNOSTIC"):
        h_apex = H_values[-1]
        if h_apex < 0.45:
            st.error(f"🚨 PATHOLOGIE DÉTECTÉE ({h_apex:.2f})")
        else:
            st.success(f"✅ ÉTANCHÉITÉ VALIDÉE ({h_apex:.2f})")
