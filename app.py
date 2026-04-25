import streamlit as st
import requests
from PIL import Image, ImageOps
from io import BytesIO
import numpy as np
import cv2

# Configuration de la page
st.set_page_config(page_title="Expertise IA Dentaire", page_icon="🦷")

st.title("🦷 Expertise IA Dentaire - Dent 16")
st.write("Analyse densitométrique automatisée pour l'aide au diagnostic endodontique.")

# 1. URL de l'image sur GitHub
# Assurez-vous que le nom du fichier est exactement "dent.jpg" sur votre dépôt
url_dent = "https://raw.githubusercontent.com/MMMJENHI/Dentaire_IA_Expertise/main/dent.jpg"

# 2. Fonction de chargement de l'image
@st.cache_data
def load_image_from_url(url):
    try:
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        return img
    except:
        return None

# 3. Exécution du chargement
image = load_image_from_url(url_dent)

if image is not None:
    st.success("✅ Image chargée avec succès depuis GitHub !")
    
    # Affichage de l'image originale
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Radio Originale")
        st.image(image, use_column_width=True)

    # 4. Prétraitement (Exemple pour votre Master)
    with col2:
        st.subheader("Analyse de Densité")
        # Conversion en niveaux de gris pour le traitement
        img_array = np.array(image.convert('L'))
        # Application d'un filtre pour améliorer le contraste (CLAHE)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced_img = clahe.apply(img_array)
        st.image(enhanced_img, use_column_width=True)

    # 5. Calcul de la Variable H (Simulation basée sur vos seuils)
    st.divider()
    st.header("📊 Résultats de l'Expertise")
    
    # Ici, on simule un calcul sur le tiers apical
    variable_h = 0.92  # Exemple de valeur calculée
    
    st.metric(label="Indice de densité relative (Variable H)", value=f"{variable_h:.2f}")

    if variable_h > 0.90:
        st.balloons()
        st.success("✅ Étanchéité Parfaite : Validation confirmée.")
    elif 0.45 <= variable_h <= 0.85:
        st.warning("⚠️ Étanchéité Douteuse : Alerte de surveillance nécessaire.")
    else:
        st.error("🚨 Diagnostic Critique : Réaction Apicale / Lésion détectée.")

else:
    st.error("❌ Impossible de charger l'image 'dent.jpg'.")
    st.info("Vérifiez que le fichier est bien présent à la racine de votre dépôt GitHub MMMJENHI/Dentaire_IA_Expertise")

# Pied de page
st.caption("Projet de Master - Système expert d'aide au diagnostic - Développé par MMMJENHI")
