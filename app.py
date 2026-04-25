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
    """Améliore le contraste de la radio pour l'analyse IA"""
    img_array = np.array(image.convert('L'))
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    return clahe.apply(img_array)

@st.cache_data
def load_img_from_url(url):
    """Charge une image depuis un lien externe"""
    try:
        response = requests.get(url, timeout=5)
        return Image.open(BytesIO(response.content))
    except:
        return None

# --- INTERFACE ---
st.title("🦷 Système Expert : Analyse de la Dent 16")
st.markdown("Diagnostic automatisé du **Tiers Apical** et de l'herméticité via la Variable H.")

# --- BARRE LATÉRALE : CHARGEMENT ---
st.sidebar.header("📁 Sources de Données")
option = st.sidebar.selectbox(
    "Mode d'importation :",
    ("Depuis mon PC (Local)", "Depuis GitHub (Raw Link)", "Lien Web Direct")
)

raw_img = None

if option == "Depuis mon PC (Local)":
    uploaded_file = st.sidebar.file_uploader("Choisir une radio...", type=['jpg', 'jpeg', 'png'])
    if uploaded_file:
        raw_img = Image.open(uploaded_file)

elif option == "Depuis GitHub (Raw Link)":
    github_url = st.sidebar.text_input("URL Raw GitHub :", 
                                      "https://raw.githubusercontent.com/MMMJENHI/Dentaire_IA_Expertise/main/dent.jpg")
    if github_url:
        raw_img = load_img_from_url(github_url)
        if raw_img: st.sidebar.success("✅ GitHub Connecté")

else:
    web_url = st.sidebar.text_input("Entrez l'URL de l'image :")
    if web_url:
        raw_img = load_img_from_url(web_url)

# --- ANALYSE ---
if raw_img is not None:
    # 1. Préparation
    img_gray = preprocess_image(raw_img)
    h_img, w_img = img_gray.shape

    # 2. Paramètres de l'Expert (Sidebar)
    st.sidebar.divider()
    st.sidebar.header("📍 Réglages du Scan")
    x_c = st.sidebar.slider("Position X (Axe Canal)", 0, w_img, int(w_img/2))
    y_haut = st.sidebar.slider("Haut du Canal (Y)", 0, h_img, int(h_img*0.2))
    y_apex = st.sidebar.slider("Fin de l'Apex (Y)", 0, h_img, int(h_img*0.9))

    # Calcul auto du tiers apical
    y_tiers_apical = int(y_haut + (y_apex - y_haut) * 0.66)

    # 3. Affichage Visuel et Graphique
    col1, col2 = st.columns([1, 1.2])

    with col1:
        st.subheader("🔎 Zone de Scan")
        img_visu = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)
        # Ligne d'analyse (Tiers apical)
        cv2.line(img_visu, (x_c, y_tiers_apical), (x_c, y_apex), (255, 255, 0), 10)
        # Point Apex
        cv2.circle(img_visu, (x_c, y_apex), 25, (255, 0, 0), -1) 
        st.image(img_visu, use_container_width=True, caption="Traitement CLAHE + Localisation Apicale")

    with col2:
        st.subheader("📈 Courbe de Densité H")
        # Extraction du profil scientifique
        signal = profile_line(img_gray, (y_tiers_apical, x_c), (y_apex, x_c), linewidth=5)
        
        # Sécurité pour le filtre de Savitzky-Golay
        w_len = 11 if len(signal) > 11 else (len(signal)-1 if len(signal)%2==0 else len(signal))
        if w_len < 3: w_len = 3
        
        signal_clean = savgol_filter(signal, window_length=w_len, polyorder=2)
        H_values = signal_clean / 255.0  # Normalisation standard 0-1

        fig = go.Figure()
        fig.add_trace(go.Scatter(y=H_values, mode='lines', line=dict(color='#00fbff', width=4), name="Profil H"))
        # Ligne seuil Idéal
        fig.add_hline(y=0.90, line_dash="dash", line_color="red", annotation_text="Seuil Idéal")
        fig.update_layout(template="plotly_dark", height=350, yaxis=dict(range=[0, 1.1]))
        st.plotly_chart(fig, use_container_width=True)

    # 4. LE BOUTON MAGIQUE (Verdict)
    st.divider()
    if st.button("✨ LANCER LE DIAGNOSTIC MAGIQUE"):
        with st.spinner('Analyse IA en cours...'):
            time.sleep(1.5)
            
            h_min = np.min(H_values)
            h_apex = H_values[-1]

            if h_apex < 0.45:
                st.snow()
                st.error(f"### 🚨 PATHOLOGIE DÉTECTÉE (H Apex = {h_apex:.2f})")
                st.write("**Diagnostic :** Destruction osseuse péri-apicale confirmée.")
            elif h_min < 0.90:
                st.warning(f"### ⚠️ ÉTANCHÉITÉ DOUTEUSE (H Min = {h_min:.2f})")
                st.write("**Diagnostic :** Risque d'infiltration. Scellage hétérogène.")
            else:
                st.balloons()
                st.success(f"### ✅ ÉTANCHÉITÉ VALIDÉE (H = {h_min:.2f})")
                st.write("**Diagnostic :** Traitement hermétique. Structure osseuse saine.")

    # 5. Rapport de données
    with st.expander("📊 Consulter les mesures brutes"):
        st.table(pd.DataFrame({
            "Indicateur": ["H Minimal (Canal)", "H Apical", "Écart / Idéal"],
            "Valeur": [f"{np.min(H_values):.2f}", f"{H_values[-1]:.2f}", f"{0.95 - np.min(H_values):.2f}"]
        }))

else:
    st.info("💡 En attente d'une radio pour lancer l'expertise.")
