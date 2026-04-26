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

# --- CONFIGURATION ---
st.set_page_config(page_title="IA Expertise Dentaire", layout="wide")

def generer_qr_statique(url):
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    buf = BytesIO()
    qr.make_image(fill_color="black", back_color="white").save(buf, format="PNG")
    return buf

def preprocess_image(image):
    img_array = np.array(image.convert('L'))
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    return clahe.apply(img_array)

# --- INTERFACE ---
st.title("🦷 Système Expert Interactif : Dent 16")

# Mode Démo ou Upload
uploaded_file = st.file_uploader("Charger une radio", type=["jpg", "png", "jpeg"])
raw_img = None

if uploaded_file:
    raw_img = Image.open(uploaded_file)
else:
    try:
        raw_img = Image.open("dent.jpg")
        st.info("💡 Mode démo actif")
    except:
        st.stop()

if raw_img:
    img_gray = preprocess_image(raw_img)
    h, w = img_gray.shape

    # --- SIDEBAR INTERACTIVE ---
    st.sidebar.header("📍 Contrôles de l'Expert")
    # Chaque changement ici modifie la tache rouge ET la densité
    x_c = st.sidebar.slider("Position X (Axe Canal)", 0, w, int(w/2))
    y_haut = st.sidebar.slider("Haut du Canal", 0, h, int(h*0.2))
    y_apex = st.sidebar.slider("Position de l'Apex (Tache Rouge)", 0, h, int(h*0.8))

    # QR Code
    url_app = "https://dentaireiaexpertise-eg4mdsd9cguhyhc4idk7rn.streamlit.app/"
    st.sidebar.image(generer_qr_statique(url_app), caption="Lien Mobile", width=120)

    # --- CALCULS EN TEMPS RÉEL ---
    y_tiers = int(y_haut + (y_apex - y_haut) * 0.66)
    
    # Extraction de la densité le long de la ligne
    signal = profile_line(img_gray, (y_tiers, x_c), (y_apex, x_c), linewidth=5)
    if len(signal) > 5:
        signal_clean = savgol_filter(signal, window_length=max(3, (len(signal)//3)*2+1 if len(signal)<11 else 11), polyorder=2)
        H_values = signal_clean / 255.0
    else:
        H_values = np.array([0.5])

    h_min = np.min(H_values)
    h_apex = H_values[-1]

    # --- AFFICHAGE ---
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("🔎 Visualisation")
        img_visu = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)
        # Ligne d'analyse
        cv2.line(img_visu, (x_c, y_tiers), (x_c, y_apex), (0, 255, 255), 5)
        # Tache rouge (Apex) : Change quand y_apex change
        cv2.circle(img_visu, (x_c, y_apex), 15, (255, 0, 0), -1) 
        st.image(img_visu, use_container_width=True)

    with col2:
        st.subheader("📈 Densité H (Dynamique)")
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=H_values, mode='lines', name="Profil H", line=dict(color='cyan')))
        fig.add_shape(type="line", x0=0, y0=0.45, x1=len(H_values), y1=0.45, line=dict(color="red", dash="dash"))
        fig.update_layout(template="plotly_dark", height=300, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

    # --- BOUTON DE RAPPORT .TXT ---
    st.divider()
    
    # Création du contenu du fichier texte
    rapport_txt = f"""RAPPORT D'EXPERTISE DENTAIRE
---------------------------
Date : {time.strftime("%Y-%m-%d %H:%M")}
Cible : Dent 16 (Tiers Apical)
---------------------------
MESURES ANALYTIQUES :
- Position Apex (Y) : {y_apex}
- Densité H Minimum : {h_min:.4f}
- Densité H à l'Apex : {h_apex:.4f}
---------------------------
DIAGNOSTIC :
{"VALIDE" if h_apex >= 0.45 else "PATHOLOGIE DETECTEE"}
---------------------------
Expertise générée par IA Dentaire.
"""

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("✨ ANALYSER"):
            if h_apex < 0.45: st.error("🚨 Échec d'étanchéité")
            else: st.success("✅ Étanchéité validée")
    
    with col_btn2:
        # BOUTON DE TÉLÉCHARGEMENT DU FICHIER .TXT
        st.download_button(
            label="💾 Télécharger le Rapport (.txt)",
            data=rapport_txt,
            file_name=f"expertise_dent16_{int(time.time())}.txt",
            mime="text/plain"
        )
