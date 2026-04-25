import streamlit as st
import requests
import numpy as np
import cv2
import plotly.graph_objects as go
from PIL import Image
from io import BytesIO

# Configuration de la page
st.set_page_config(page_title="IA Dentaire - Expertise", layout="wide")

st.title("🦷 Expertise IA Dentaire : Analyse de la Dent 16")
st.write("Analyse densitométrique automatisée pour l'aide au diagnostic endodontique.")

# 1. Accès aux données sur GitHub (Image Raw)
url_dent = "https://raw.githubusercontent.com/MMMJENHI/Dentaire_IA_Expertise/main/dent.jpg"

@st.cache_data
def load_img(url):
    response = requests.get(url)
    img = Image.open(BytesIO(response.content)).convert('L')
    return np.array(img)

try:
    img_array = load_img(url_dent)
    st.success("✅ Image chargée avec succès depuis GitHub !")

    # --- BARRE LATÉRALE : Contrôles du Cercle Rouge ---
    st.sidebar.header("Contrôles d'Analyse")
    st.sidebar.write("Faites varier le cercle pour analyser la zone souhaitée :")
    
    height, width = img_array.shape
    pos_y = st.sidebar.slider("Position Verticale (Y)", 0, height, int(height * 0.75))
    pos_x = st.sidebar.slider("Position Horizontale (X)", 0, width, int(width * 0.5))
    rayon = st.sidebar.slider("Rayon du Cercle", 10, 100, 40)

    # --- TRAITEMENT D'IMAGE ---
    # Créer une version couleur pour dessiner le cercle
    img_rgb = cv2.cvtColor(img_array, cv2.COLOR_GRAY2RGB)
    # Dessiner le cercle rouge transparent
    overlay = img_rgb.copy()
    cv2.circle(overlay, (pos_x, pos_y), rayon, (255, 0, 0), -1) # Cercle plein
    alpha = 0.4  # Transparence
    img_final = cv2.addWeighted(overlay, alpha, img_rgb, 1 - alpha, 0)
    # Ajouter un contour rouge vif
    cv2.circle(img_final, (pos_x, pos_y), rayon, (255, 0, 0), 2)

    # --- AFFICHAGE ---
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("🔍 Radio de la Dent 16 (Analyse)")
        st.image(img_final, caption=f"Zone analysée à X={pos_x}, Y={pos_y}", use_column_width=True)

    with col2:
        st.subheader("📈 Courbe Densitométrique (H-Index)")
        
        # Extraire les données de pixels sous le cercle (profil vertical)
        y_start, y_end = max(0, pos_y-rayon), min(height, pos_y+rayon)
        profile = img_array[y_start:y_end, pos_x] / 255.0 # Normalisation 0-1
        
        # Création du graphique Plotly
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=profile, mode='lines+markers', name='Indice H', line=dict(color='red')))
        
        # Ajouter les zones de couleurs (Seuils d'expertise)
        fig.add_hrect(y0=0.9, y1=1.0, fillcolor="green", opacity=0.2, annotation_text="Validation")
        fig.add_hrect(y0=0.45, y1=0.89, fillcolor="yellow", opacity=0.2, annotation_text="Alerte")
        fig.add_hrect(y0=0.0, y1=0.44, fillcolor="red", opacity=0.2, annotation_text="Critique")
        
        fig.update_layout(yaxis_range=[0, 1], xaxis_title="Profondeur dans la zone", yaxis_title="Intensité H")
        st.plotly_chart(fig, use_container_width=True)

    # --- TABLEAU DE BORD EXPERT ---
    st.divider()
    h_moyen = np.mean(profile)
    
    c1, c2 = st.columns(2)
    c1.metric("Indice H Moyen", f"{h_moyen:.2f}")
    
    if h_moyen > 0.90:
        c2.success("Verdict : Étanchéité Parfaite ✅")
        st.balloons()
    elif h_moyen > 0.45:
        c2.warning("Verdict : Étanchéité Douteuse ⚠️")
    else:
        c2.error("Verdict : Diagnostic Critique 🚨")

except Exception as e:
    st.error(f"Erreur d'accès aux données : {e}")
    st.info("Assurez-vous que le fichier 'dent.jpg' est bien présent sur votre GitHub MMMJENHI.")
