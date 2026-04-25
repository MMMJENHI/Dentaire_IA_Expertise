import streamlit as st
import requests
import numpy as np
import cv2
import plotly.graph_objects as go
from PIL import Image
from io import BytesIO


# Remplace la section de chargement par celle-ci
st.sidebar.header("📁 Importer une Radio")

uploaded_file = st.sidebar.file_get_directory_or_file("Choisir une image (JPG, PNG)...")

if uploaded_file is not None:
    # Charger l'image directement depuis ton ordinateur
    img_array = np.array(Image.open(uploaded_file).convert('L'))
    st.sidebar.success("✅ Image locale chargée !")
else:
    # Sinon, charger par défaut depuis GitHub
    img_array = load_img(url_final)

st.set_page_config(page_title="IA Dentaire - Multi-Chargement", layout="wide")

st.title("🦷 Expertise IA Dentaire : Analyse Dynamique")

# --- BARRE LATÉRALE : CHARGEMENT ---
st.sidebar.header("📁 Chargement des données")

# Option pour changer la source de l'image
source_option = st.sidebar.radio("Source de l'image :", 
                                  ("Image par défaut (Dent 16)", "Lien GitHub Personnalisé"))

if source_option == "Image par défaut (Dent 16)":
    url_final = "https://raw.githubusercontent.com/MMMJENHI/Dentaire_IA_Expertise/main/dent.jpg"
else:
    # Permet de coller une nouvelle URL Raw de GitHub
    url_final = st.sidebar.text_input("Collez l'URL RAW de l'image GitHub :", 
                                     "https://raw.githubusercontent.com/MMMJENHI/Dentaire_IA_Expertise/main/dent.jpg")

@st.cache_data
def load_img(url):
    try:
        response = requests.get(url)
        img = Image.open(BytesIO(response.content)).convert('L')
        return np.array(img)
    except:
        return None

# --- EXÉCUTION ---
img_array = load_img(url_final)

if img_array is not None:
    st.sidebar.success("✅ Image chargée avec succès !")
    
    # Contrôles du Cercle Rouge
    st.sidebar.divider()
    st.sidebar.header("⚙️ Réglages Expertise")
    height, width = img_array.shape
    pos_y = st.sidebar.slider("Position Verticale (Y)", 0, height, int(height * 0.75))
    pos_x = st.sidebar.slider("Position Horizontale (X)", 0, width, int(width * 0.5))
    rayon = st.sidebar.slider("Rayon du Cercle", 10, 100, 40)

    # Dessin du cercle
    img_rgb = cv2.cvtColor(img_array, cv2.COLOR_GRAY2RGB)
    overlay = img_rgb.copy()
    cv2.circle(overlay, (pos_x, pos_y), rayon, (255, 0, 0), -1)
    img_final = cv2.addWeighted(overlay, 0.4, img_rgb, 0.6, 0)
    cv2.circle(img_final, (pos_x, pos_y), rayon, (255, 0, 0), 2)

    # Affichage
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🔍 Visualisation")
        st.image(img_final, use_container_width=True)
    
    with col2:
        st.subheader("📈 Profil Densitométrique")
        y_start, y_end = max(0, pos_y-rayon), min(height, pos_y+rayon)
        profile = img_array[y_start:y_end, pos_x] / 255.0
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=profile, mode='lines', name='Indice H', line=dict(color='red')))
        fig.add_hrect(y0=0.9, y1=1.0, fillcolor="green", opacity=0.2)
        fig.add_hrect(y0=0.0, y1=0.45, fillcolor="red", opacity=0.2)
        fig.update_layout(yaxis_range=[0, 1], margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)

    # Verdict
    h_moyen = np.mean(profile)
    st.metric("Indice H Moyen", f"{h_moyen:.2f}")
    if h_moyen > 0.85:
        st.success("Verdict : Étanchéité Validée ✅")
    else:
        st.warning("Verdict : Analyse Requise ⚠️")

else:
    st.error("❌ Impossible d'accéder à l'image. Vérifiez l'URL GitHub.")
