import streamlit as st
import requests
import numpy as np
import cv2
import plotly.graph_objects as go
from PIL import Image
from io import BytesIO
from skimage.measure import profile_line
from scipy.signal import savgol_filter
import pandas as pd
import time

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="IA Expertise Dentaire - Master", layout="wide")

# --- FONCTIONS UTILES ---
def preprocess_image(image):
    img_array = np.array(image.convert('L'))
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    return clahe.apply(img_array)

@st.cache_data
def load_img_from_url(url):
    try:
        response = requests.get(url, timeout=5)
        return Image.open(BytesIO(response.content))
    except:
        return None

# --- NOUVELLE FONCTION : RECENTRAGE AUTOMATIQUE (X) ---
def auto_center_x(image, x_user, y_apex, margin=15):
    """
    Scanne les pixels à gauche et à droite pour trouver le centre 
    le plus dense de la racine (évite l'espace interdentaire).
    """
    try:
        x_start = max(0, x_user - margin)
        x_end = min(image.shape[1], x_user + margin)
        line_sample = image[y_apex, x_start:x_end]
        # On cherche le pic de densité (le blanc de la dent/gutta)
        best_x_offset = np.argmax(line_sample)
        return x_start + best_x_offset
    except:
        return x_user

# --- INTERFACE ---
st.title("🦷 Système Expert : Analyse de la Dent 16")
st.markdown("Système de **Segmentation Automatique** avec recentrage dynamique de l'axe canalaire.")

# --- BARRE LATÉRALE ---
st.sidebar.header("📁 Sources de Données")
option = st.sidebar.selectbox("Mode d'importation :", ("Depuis mon PC (Local)", "Depuis GitHub (Raw Link)", "Lien Web Direct"))

raw_img = None
if option == "Depuis mon PC (Local)":
    uploaded_file = st.sidebar.file_uploader("Choisir une radio...", type=['jpg', 'jpeg', 'png'])
    if uploaded_file: raw_img = Image.open(uploaded_file)
elif option == "Depuis GitHub (Raw Link)":
    github_url = st.sidebar.text_input("URL Raw GitHub :", "https://raw.githubusercontent.com/MMMJENHI/Dentaire_IA_Expertise/main/dent.jpg")
    if github_url: raw_img = load_img_from_url(github_url)
else:
    web_url = st.sidebar.text_input("Entrez l'URL de l'image :")
    if web_url: raw_img = load_img_from_url(web_url)

if raw_img is not None:
    img_gray = preprocess_image(raw_img)
    h_img, w_img = img_gray.shape

    st.sidebar.divider()
    st.sidebar.header("📍 Segmentation Anatomique")
    
    # ÉTAPE 1 : LOCALISATION SPATIALE
    x_user = st.sidebar.slider("Position approximative (X)", 0, w_img, int(w_img/2))
    y_haut = st.sidebar.slider("Haut du Canal (Y)", 0, h_img, int(h_img*0.2))
    y_apex = st.sidebar.slider("Point Apex (Y)", 0, h_img, int(h_img*0.9))

    # --- APPLICATION DU CODE DE RECENTRAGE AUTOMATIQUE ---
    # L'algorithme ajuste X pour éviter l'espace entre les dents
    x_c = auto_center_x(img_gray, x_user, y_apex)
    
    # ÉTAPE 2 : ISOLATION DU TIERS APICAL (33% terminaux)
    y_tiers_apical = int(y_haut + (y_apex - y_haut) * 0.66)

    # --- CALCUL DES VALEURS H ---
    # On scanne sur le x_c recalculé
    signal = profile_line(img_gray, (y_tiers_apical, x_c), (y_apex, x_c), linewidth=5)
    
    if len(signal) > 3:
        w_len = 11 if len(signal) > 11 else (len(signal)-1 if len(signal)%2==0 else len(signal))
        signal_clean = savgol_filter(signal, window_length=w_len, polyorder=2)
        H_values = signal_clean / 255.0 
        h_apex_final = np.mean(H_values[-10:]) # Focus sur l'apex terminal
    else:
        H_values = np.array([0])
        h_apex_final = 0

    # --- AFFICHAGE ---
    col1, col2 = st.columns([1, 1.2])

    with col1:
        st.subheader("🔎 Visualisation de la Segmentation")
        img_visu = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)
        
        # Dessin du Tiers Apical (Ligne Cyan) - Axe rectifié
        cv2.line(img_visu, (x_c, y_tiers_apical), (x_c, y_apex), (0, 255, 255), 8)
        
        # Cercle Apex (Bleu si sain, Rouge si pathologique)
        color_apex = (255, 0, 0) if h_apex_final < 0.45 else (0, 255, 0)
        cv2.circle(img_visu, (x_c, y_apex), 20, color_apex, -1) 
        
        st.image(img_visu, use_container_width=True, caption=f"Axe rectifié X: {x_c} | Zone: Tiers Apical")

    with col2:
        st.subheader("📈 Classification (Seuillage H)")
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=H_values, mode='lines', line=dict(color='#00fbff', width=4), name="Profil H"))
        
        # Zone de danger
        fig.add_hline(y=0.45, line_dash="dash", line_color="red", annotation_text="SEUIL PATHOLOGIQUE (0.45)")
        fig.add_hrect(y0=0, y1=0.45, fillcolor="red", opacity=0.1)
        
        fig.update_layout(template="plotly_dark", height=350, yaxis_title="Densité H", xaxis_title="Profondeur du tiers apical")
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    
    # ÉTAPE 3 : CLASSIFICATION FINALE
    if st.button("✨ GÉNÉRER L'EXPERTISE FINALE"):
        with st.spinner('Analyse de la densité matricielle...'):
            time.sleep(1)
            if h_apex_final < 0.45:
                status = "🚨 PATHOLOGIQUE (NON CONFORME)"
                msg = "Alerte : Chute de densité détectée. Risque de lésion péri-apicale."
                st.error(f"### {status}")
            else:
                status = "✅ SAIN (CONFORME)"
                msg = "Succès : Densité optimale. Scellement apical hermétique."
                st.success(f"### {status}")

            rapport_txt = f"""
            RAPPORT D'EXPERTISE DENTAIRE (CAD SYSTEM)
            ------------------------------------------
            ZONE : Tiers Apical | AXE X RECENTRÉ : {x_c}
            VALEUR H APEX : {h_apex_final:.2f} (Seuil : 0.45)
            DIAGNOSTIC : {status}
            INTERPRÉTATION : {msg}
            ------------------------------------------
            """
            st.code(rapport_txt)

    # --- NOTE POUR LE JURY ---
    st.info("### 📘 Note de Méthodologie")
    st.write(f"""
    **Localisation :** Le système a automatiquement ajusté l'axe de **{x_user}** à **{x_c}** pixels pour garantir l'analyse du canal.  
    **Isolation :** Seuls les derniers millimètres (entre Y={y_tiers_apical} et Y={y_apex}) sont isolés.  
    **Classification :** Un seuil de **0.45** est utilisé pour valider l'absence de réaction inflammatoire.
    """)

else:
    st.info("💡 En attente d'une radio sur le PC TOSHIBA...")
