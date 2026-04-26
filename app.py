import streamlit as st
import cv2
import numpy as np
from PIL import Image
import requests
from io import BytesIO
# ... (Gardez vos autres imports : qrcode, plotly, etc.)

# --- 3. INTERFACE DE CHARGEMENT ---
st.sidebar.header("📁 Source de la Radio")
source_radio = st.sidebar.radio(
    "Choisir la méthode :",
    ("Upload (Local)", "Lien URL / GitHub", "Mode Démo (dent.jpg)")
)

raw_img = None

# MODE 1 : LOCAL
if source_radio == "Upload (Local)":
    uploaded_file = st.file_uploader("Charger depuis votre PC", type=["jpg", "png", "jpeg"])
    if uploaded_file:
        raw_img = Image.open(uploaded_file)

# MODE 2 : URL / GITHUB (CORRIGÉ)
elif source_radio == "Lien URL / GitHub":
    st.info("💡 Pour GitHub, utilisez le lien 'Raw'.")
    url_input = st.text_input("Collez l'URL de l'image :", 
                              value="https://raw.githubusercontent.com/MMMJENHI/Dentaire_IA_Expertise/main/dent.jpg")
    if url_input:
        try:
            # On ajoute un 'User-Agent' pour éviter d'être bloqué par certains sites
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url_input, headers=headers, timeout=10)
            if response.status_code == 200:
                raw_img = Image.open(BytesIO(response.content))
                st.success("✅ Image chargée avec succès !")
            else:
                st.error(f"❌ Erreur {response.status_code} : Lien invalide.")
        except Exception as e:
            st.error(f"❌ Erreur de connexion : {e}")

# MODE 3 : DÉMO (FICHIER DANS VOTRE GITHUB)
else:
    try:
        # Cherche le fichier 'dent.jpg' à la racine de votre dossier GitHub
        raw_img = Image.open("dent.jpg")
        st.success("✅ Mode Démonstration actif.")
    except FileNotFoundError:
        st.error("⚠️ Fichier 'dent.jpg' introuvable dans le dossier GitHub.")
        st.info("Astuce : Vérifiez que l'image est bien nommée 'dent.jpg' (tout en minuscules).")

# --- SUITE DU CODE (Analyse et QR) ---
if raw_img is not None:
    # (Votre code de traitement reste ici...)
    st.image(raw_img, caption="Radio chargée", use_container_width=True)
