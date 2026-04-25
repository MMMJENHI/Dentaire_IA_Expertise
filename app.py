import streamlit as st
import requests
import numpy as np
import plotly.graph_objects as go
from PIL import Image
from io import BytesIO

st.title("🦷 Expertise Endodontique - Dent 16")

url_dent = "https://raw.githubusercontent.com/MMMJENHI/Dentaire_IA_Expertise/main/dent.jpg"

try:
    # 1. Chargement
    response = requests.get(url_dent)
    img = Image.open(BytesIO(response.content)).convert('L')
    img_array = np.array(img)
    
    st.image(img, caption="Radio chargée", width=400)
    st.success("✅ Analyse du Tiers Apical en cours...")

    # 2. Création de la Courbe (Expertise)
    # On prend une coupe verticale au milieu de la dent
    col_index = img_array.shape[1] // 2
    profile = img_array[:, col_index]
    
    fig = go.Figure(data=go.Scatter(y=profile, mode='lines', line=dict(color='red')))
    fig.update_layout(title="Profil Densitométrique (Variable H)", xaxis_title="Profondeur", yaxis_title="Intensité")
    st.plotly_chart(fig)

    # 3. Verdict Expertise
    h_moyenne = np.mean(profile[-50:]) / 255
    if h_moyenne > 0.8:
        st.balloons()
        st.success(f"Expertise : Étanchéité Validée (H={h_moyenne:.2f})")
    else:
        st.warning(f"Expertise : Surveillance Apicale (H={h_moyenne:.2f})")

except Exception as e:
    st.error(f"Erreur technique : {e}")
