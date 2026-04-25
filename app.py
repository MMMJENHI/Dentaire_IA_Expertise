import streamlit as st
from PIL import Image
import os

# --- INTERFACE DENTAIRE ---
st.title("🦷 Expertise IA : Analyse de la Dent 16")

# Chargeur de fichier (Navigateur)
uploaded_file = st.file_uploader("Charger une radiographie", type=["jpg", "png", "jpeg"])

if uploaded_file is not None:
    # Si tu glisses une image dans le navigateur
    raw_img = Image.open(uploaded_file)
    st.success("✅ Image chargée depuis votre ordinateur.")
else:
    # MODE GITHUB : Cherche 'dent.jpg' dans ton dépôt GitHub
    if os.path.exists("dent.jpg"):
        raw_img = Image.open("dent.jpg")
        st.info("💡 Mode Démo : Image 'dent.jpg' chargée depuis GitHub.")
    else:
        st.warning("⚠️ En attente d'image. Veuillez glisser 'dent.jpg' ici ou l'ajouter sur GitHub.")
        st.stop()

# --- LA SUITE : APPEL DE TON ANALYSE H ---
# img_gray = preprocess_image(raw_img) ...
