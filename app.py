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
st.set_page_config(page_title="IA Expertise Dentaire - Diagnostic Apical", layout="wide")

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

# --- INTERFACE ---
st.title("🦷 Système Expert : Analyse de la Dent 16")
st.markdown("Détection automatisée des **Pathologies Péri-apicales** par Variable H.")

# --- BARRE LATÉRALE : CHARGEMENT ---
st.sidebar.header("📁 Sources de Données")
option = st.sidebar.selectbox(
    "Mode d'importation :",
    ("Depuis mon PC (Local)", "Depuis GitHub (Raw Link)", "Lien Web Direct")
)

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

# --- ANALYSE ---
if raw_img is not None:
    img_gray = preprocess_image(raw_img)
    h_img, w_img = img_gray.shape

    st.sidebar.divider()
    st.sidebar.header("📍 Réglages du Scan")
    x_c = st.sidebar.slider("Position X (Axe Canal)", 0, w_img, int(w_img/2))
    y_haut = st.sidebar.slider("Haut du Canal (Y)", 0, h_img, int(h_img*0.2))
    y_apex = st.sidebar.slider("Fin de l'Apex (Y)", 0, h_img, int(h_img*0.9))
    y_tiers_apical = int(y_haut + (y_apex - y_haut) * 0.66)

    col1, col2 = st.columns([1, 1.2])

    with col1:
        st.subheader("🔎 Zone de Scan")
        img_visu = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)
        cv2.line(img_visu, (x_c, y_tiers_apical), (x_c, y_apex), (255, 255, 0), 10)
        cv2.circle(img_visu, (x_c, y_apex), 25, (255, 0, 0), -1) 
        st.image(img_visu, use_container_width=True)

    with col2:
        st.subheader("📈 Courbe de Densité H")
        signal = profile_line(img_gray, (y_tiers_apical, x_c), (y_apex, x_c), linewidth=5)
        w_len = 11 if len(signal) > 11 else (len(signal)-1 if len(signal)%2==0 else len(signal))
        if w_len < 3: w_len = 3
        signal_clean = savgol_filter(signal, window_length=w_len, polyorder=2)
        H_values = signal_clean / 255.0 

        # --- DÉTECTION DE LA CHUTE ---
        h_apex_final = np.mean(H_values[-15:]) # Analyse des derniers pixels (Apex)

        fig = go.Figure()
        fig.add_trace(go.Scatter(y=H_values, mode='lines', line=dict(color='#00fbff', width=4), name="Profil H"))
        
        # Coloration automatique si chute sous 0.45
        if h_apex_final < 0.45:
            fig.add_vrect(x0=len(H_values)-20, x1=len(H_values), 
                          fillcolor="red", opacity=0.3, annotation_text="CHUTE APICALE")

        fig.add_hline(y=0.90, line_dash="dash", line_color="green", annotation_text="Sain")
        fig.add_hline(y=0.45, line_dash="dash", line_color="orange", annotation_text="Seuil Patho")
        fig.update_layout(template="plotly_dark", height=350, yaxis=dict(range=[0, 1.1]))
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    
    if st.button("✨ LANCER LE DIAGNOSTIC DÉTAILLÉ"):
        with st.spinner('Analyse des tissus péri-apicaux...'):
            time.sleep(1)
            h_min = np.min(H_values)
            
            if h_apex_final < 0.45:
                status = "🚨 PATHOLOGIQUE (LÉSION DÉTECTÉE)"
                conclusion = "Chute brutale de la Variable H à l'apex (< 0.45). Indication de pathologie péri-apicale."
                st.error(f"### {status}")
            else:
                status = "✅ SAIN (CONFORME)"
                conclusion = "Densité stable à l'apex. Absence de signe radiologique de lésion."
                st.success(f"### {status}")

            # --- RAPPORT TEXTE ---
            rapport_txt = f"""
            RAPPORT D'EXPERTISE DENTAIRE
            --------------------------------
            Status : {status}
            H Apex Final : {h_apex_final:.2f}
            Conclusion : {conclusion}
            """
            st.code(rapport_txt)
            st.download_button("📥 Rapport .txt", rapport_txt, "expertise.txt")

    # --- COURS / EXPLICATION POUR LE JURY ---
    st.info("### 📘 Note Scientifique sur la Chute à l'Apex")
    st.markdown("""
    Une **chute sous 0.45** (zone radio-claire) à l'extrémité de la courbe indique que le faisceau de rayons X ne rencontre plus de matière dense. 
    En endodontie, cela traduit mathématiquement :
    1.  **Une inflammation péri-apicale** (tissus mous à la place de l'os).
    2.  **Un kyste ou granulome** (cavité remplie de liquide/tissus).
    3.  **Une résorption osseuse**.
    """)

else:
    st.info("💡 En attente d'une radio.")
