import streamlit as st
from PIL import Image
import os

st.title("🦷 Test IA Dentaire")

# Test de présence du fichier
if os.path.exists("dent.jpg"):
    st.success("✅ Image 'dent.jpg' trouvée sur le serveur GitHub.")
    img = Image.open("dent.jpg")
    st.image(img)
else:
    st.error("❌ Fichier 'dent.jpg' absent du dépôt GitHub.")

st.write("Si vous voyez ce message, le serveur fonctionne !")
