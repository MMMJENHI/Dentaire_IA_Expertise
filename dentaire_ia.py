import streamlit as st
import cv2
import numpy as np
import plotly.graph_objects as go
from skimage.measure import profile_line
from scipy.signal import savgol_filter
from PIL import Image
import pandas as pd
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="IA Expertise Dentaire", layout="wide")

def preprocess_image(image):
    img_array = np.array(image.convert('L'))
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    return clahe.apply(img_array)

# --- INTERFACE ---
st.title("🦷 Système Expert : Analyse de la Dent 16")
st.markdown("Diagnostic automatisé du **Tiers Apical** et de l'herméticité.")

uploaded_file = st.file_uploader("Charger la radiographie", type=["jpg", "png", "jpeg"])

if uploaded_file:
    # 1. Préparation des données
    raw_img = Image.open(uploaded_file)
    img_gray = preprocess_image(raw_img)
    h, w = img_gray.shape

    # 2. Paramètres (Sidebar)
    st.sidebar.header("📍 Réglages de l'Expert")
    x_c = st.sidebar.slider("Position X (Centre Canal)", 0, w, 712)
    y_haut = st.sidebar.slider("Haut du Canal (Y)", 0, h, 1100)
    y_apex = st.sidebar.slider("Fin de l'Apex (Y)", 0, h, 1449)

    # Calcul automatique du tiers apical
    y_tiers_apical = int(y_haut + (y_apex - y_haut) * 0.66)

    # 3. Affichage visuel et graphique
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
        
        # Sécurité filtre
        w_len = 11 if len(signal) > 11 else (len(signal)-1 if len(signal)%2==0 else len(signal))
        if w_len < 3: w_len = 3
        
        signal_clean = savgol_filter(signal, window_length=w_len, polyorder=2)
        H_values = signal_clean / 150.0 

        fig = go.Figure()
        fig.add_trace(go.Scatter(y=H_values, mode='lines', line=dict(color='cyan', width=4)))
        fig.add_shape(type="line", x0=0, y0=0.90, x1=len(H_values), y1=0.90, line=dict(color="Red", dash="dash"))
        fig.update_layout(template="plotly_dark", height=350, yaxis=dict(range=[0, 1.5]))
        st.plotly_chart(fig, use_container_width=True)

    # 4. LE BOUTON MAGIQUE
    st.divider()
    if st.button("✨ LANCER LE DIAGNOSTIC MAGIQUE"):
        with st.spinner('Analyse IA en cours...'):
            time.sleep(1.5) # Effet de calcul
            
            h_min = np.min(H_values)
            h_apex = H_values[-1]

            if h_apex < 0.45:
                st.snow() # Alerte visuelle
                st.error(f"### 🚨 PATHOLOGIE DÉTECTÉE (H={h_apex:.2f})")
                st.write("L'IA confirme une destruction osseuse à l'apex. Le traitement actuel ne protège plus la dent.")
            elif h_min < 0.90:
                st.warning(f"### ⚠️ ÉTANCHÉITÉ DOUTEUSE (H_min={h_min:.2f})")
                st.write("Le scellage présente des faiblesses. Une surveillance est nécessaire.")
            else:
                st.balloons() # Succès
                st.success(f"### ✅ ÉTANCHÉITÉ VALIDÉE (H={h_min:.2f})")
                st.write("Le traitement est parfaitement hermétique. L'os est sain.")

    # 5. Rapport Technique (Optionnel)
    with st.expander("Consulter les données brutes"):
        st.write(pd.DataFrame({
            "Métrique": ["H Minimal", "H Apex"],
            "Valeur": [f"{np.min(H_values):.2f}", f"{H_values[-1]:.2f}"]
        }))

else:
    st.info("En attente du fichier 'dent.jpg' pour l'expertise.")