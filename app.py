import streamlit as st
from PIL import Image
import os

# --- TITRE ---
st.title("🦷 Expertise IA Automatique (Mode GitHub)")

# 1. DEFINIR LE NOM DU FICHIER SUR GITHUB
nom_fichier_github = "dent.jpg"

# 2. CHARGEMENT AUTOMATIQUE (SANS PASSER PAR LE BUREAU)
if os.path.exists(nom_fichier_github):
    raw_img = Image.open(nom_fichier_github)
    st.success(f"✅ Analyse en cours : Fichier '{nom_fichier_github}' détecté sur GitHub.")
    
    # Affichage de l'image pour preuve
    st.image(raw_img, caption="Radio chargée depuis le dépôt GitHub", width=400)
else:
    st.error(f"❌ Erreur : Le fichier '{nom_fichier_github}' est absent de ton GitHub !")
    st.info("Aide : Clique sur 'Add file' sur GitHub et glisse ton image 'dent.jpg' dedans.")
    st.stop()

# --- LA SUITE DE TON ANALYSE H ---
# img_gray = preprocess_image(raw_img)
# ... le reste du code ...
