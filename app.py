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

# --- INTERFACE ---
st.title("🦷 Système Expert : Analyse de la Dent 16")
st.markdown("Diagnostic automatisé du **Tiers Apical** et génération de rapport d'expertise.")

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
else:
    web_url = st.sidebar.text_input("Entrez l'URL de l'image :")
    if web_url:
        raw_img = load_img_from_url(web_url)

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

        fig = go.Figure()
        fig.add_trace(go.Scatter(y=H_values, mode='lines', line=dict(color='#00fbff', width=4), name="Profil H"))
        fig.add_hline(y=0.90, line_dash="dash", line_color="red")
        fig.update_layout(template="plotly_dark", height=350, yaxis=dict(range=[0, 1.1]))
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    
    # --- LOGIQUE DE DIAGNOSTIC ET RAPPORT ---
    if st.button("✨ LANCER LE DIAGNOSTIC ET GÉNÉRER LE RAPPORT"):
        with st.spinner('Analyse IA en cours...'):
            time.sleep(1.2)
            h_min = np.min(H_values)
            h_apex = H_values[-1]
            
            # Détermination de l'état
            if h_apex < 0.45:
                status = "🚨 PATHOLOGIQUE (MALADE)"
                conclusion = "Destruction osseuse péri-apicale (Lésion). Réintervention nécessaire."
                st.snow()
                st.error(f"### {status}")
            elif h_min < 0.90:
                status = "⚠️ DOUTEUX (SURVEILLANCE)"
                conclusion = "Défaut d'herméticité ou infiltration. Risque de réinfection."
                st.warning(f"### {status}")
            else:
                status = "✅ SAIN (CONFORME)"
                conclusion = "Obturation parfaitement hermétique. Structure osseuse intègre."
                st.balloons()
                st.success(f"### {status}")

            st.write(f"**Analyse technique :** {conclusion}")

            # --- GÉNÉRATION DU FICHIER TXT ---
            rapport_txt = f"""
            RAPPORT D'EXPERTISE IA DENTAIRE
            --------------------------------
            Date de l'analyse : {time.strftime("%d/%m/%Y %H:%M")}
            Cible : Dent 16 (Tiers Apical)
            
            RESULTATS :
            - Statut : {status}
            - Indice H Apex : {h_apex:.2f}
            - Indice H Minimal : {h_min:.2f}
            
            EXPLICATION SCIENTIFIQUE :
            1. SAIN (H > 0.90) : La densité correspond à une Gutta-percha compacte.
            2. MALADE (H < 0.45) : Présence d'une zone radio-claire (noire) indiquant une infection.
            
            CONCLUSION :
            {conclusion}
            
            Expertise générée par le système MMMJENHI IA.
            """
            
            st.download_button(
                label="📥 Télécharger le Rapport (.txt)",
                data=rapport_txt,
                file_name="expertise_dentaire_16.txt",
                mime="text/plain"
            )

    # --- EXPLICATION PÉDAGOGIQUE POUR LE JURY ---
    st.divider()
    exp1, exp2 = st.columns(2)
    with exp1:
        st.info("### 🟢 Pourquoi un résultat SAIN ?")
        st.write("Un résultat est jugé **Sain** quand la courbe reste proche de **0.90-1.0**. Cela signifie que le canal est totalement rempli de matière dense qui bloque les rayons X.")
    with exp2:
        st.error("### 🔴 Pourquoi un résultat MALADE ?")
        st.write("Un résultat est jugé **Malade** (Pathologique) quand la courbe chute brutalement en dessous de **0.45** à l'apex. Cela indique un vide ou une inflammation qui laisse passer les rayons X.")

else:
    st.info("💡 En attente d'une radio pour lancer l'expertise.")
