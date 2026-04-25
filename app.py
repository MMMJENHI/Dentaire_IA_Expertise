import streamlit as st
import requests
import numpy as np
import cv2
import plotly.graph_objects as go
from PIL import Image
from io import BytesIO

# Configuration Pro
st.set_page_config(page_title="IA Dentaire - Analyse Universelle", layout="wide")

st.title("🦷 Expertise IA Dentaire : Système d'Analyse Multimédia")
st.write("Importez une radio depuis n'importe quelle source pour lancer l'expertise densitométrique.")

# --- BARRE LATÉRALE : SYSTÈME D'IMPORTATION ---
st.sidebar.header("📁 Sources de Données")

# Choix de la méthode d'importation
option = st.sidebar.selectbox(
    "Comment voulez-vous importer l'image ?",
    ("Depuis mon PC (Local)", "Depuis GitHub (Raw Link)", "Lien Web (URL direct)")
)

img_array = None

# MÉTHODE 1 : DEPUIS LE PC (Sécurité maximale si internet coupe)
if option == "Depuis mon PC (Local)":
    uploaded_file = st.sidebar.file_uploader("Choisir une radio...", type=['jpg', 'jpeg', 'png'])
    if uploaded_file is not None:
        img_array = np.array(Image.open(uploaded_file).convert('L'))
        st.sidebar.success("✅ Image locale prête.")

# MÉTHODE 2 : DEPUIS GITHUB
elif option == "Depuis GitHub (Raw Link)":
    github_url = st.sidebar.text_input("URL Raw de l'image sur GitHub :", 
                                      "https://raw.githubusercontent.com/MMMJENHI/Dentaire_IA_Expertise/main/dent.jpg")
    if github_url:
        try:
            response = requests.get(github_url)
            img_array = np.array(Image.open(BytesIO(response.content)).convert('L'))
            st.sidebar.success("✅ Image GitHub connectée.")
        except:
            st.sidebar.error("❌ Impossible de lire ce lien GitHub.")

# MÉTHODE 3 : LIEN WEB GÉNÉRIQUE
else:
    web_url = st.sidebar.text_input("Entrez l'URL directe de l'image (http...) :")
    if web_url:
        try:
            response = requests.get(web_url)
            img_array = np.array(Image.open(BytesIO(response.content)).convert('L'))
            st.sidebar.success("✅ Image Web récupérée.")
        except:
            st.sidebar.error("❌ Lien invalide ou protégé.")

# --- ANALYSE ET EXPERTISE ---
if img_array is not None:
    # 1. Contrôles Interactifs
    st.sidebar.divider()
    st.sidebar.header("⚙️ Paramètres du Cercle")
    h, w = img_array.shape
    pos_y = st.sidebar.slider("Position Y (Verticale)", 0, h, int(h * 0.75))
    pos_x = st.sidebar.slider("Position X (Horizontale)", 0, w, int(w * 0.5))
    rayon = st.sidebar.slider("Rayon d'analyse", 10, 150, 50)

    # 2. Visualisation avec Cercle Rouge
    img_rgb = cv2.cvtColor(img_array, cv2.COLOR_GRAY2RGB)
    overlay = img_rgb.copy()
    cv2.circle(overlay, (pos_x, pos_y), rayon, (255, 0, 0), -1)
    img_final = cv2.addWeighted(overlay, 0.3, img_rgb, 0.7, 0)
    cv2.circle(img_final, (pos_x, pos_y), rayon, (255, 0, 0), 3)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🔍 Radio et Zone d'Expertise")
        st.image(img_final, use_container_width=True)

    with col2:
        st.subheader("📈 Courbe de Densité (H-Index)")
        # Calcul du profil de densité sous le cercle
        y_start, y_end = max(0, pos_y-rayon), min(h, pos_y+rayon)
        profile = img_array[y_start:y_end, pos_x] / 255.0
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=profile, mode='lines', line=dict(color='red', width=3)))
        fig.add_hrect(y0=0.9, y1=1.0, fillcolor="green", opacity=0.2, annotation_text="ÉTANCHE")
        fig.add_hrect(y0=0.0, y1=0.45, fillcolor="red", opacity=0.2, annotation_text="LÉSION")
        fig.update_layout(yaxis_range=[0, 1], margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

    # 3. Verdict Final
    h_moyen = np.mean(profile)
    st.divider()
    st.metric("Indice H de la zone", f"{h_moyen:.2f}")
    if h_moyen > 0.85:
        st.success("✅ VERDICT : Obturation de qualité, étanchéité apicale confirmée.")
    else:
        st.warning("⚠️ VERDICT : Densité insuffisante, risque d'échec endodontique.")

else:
    st.info("💡 Sélectionnez une source d'image dans le menu à gauche pour commencer l'expertise.")
