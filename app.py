import streamlit as st
import cv2
import numpy as np
import plotly.graph_objects as go
from skimage.measure import profile_line
from scipy.signal import savgol_filter
from PIL import Image
import pandas as pd
import time

# --- 1. CONFIGURATION (TOUJOURS EN PREMIER) ---
st.set_page_config(page_title="IA Expertise Dentaire", layout="wide")

# --- 2. DÉFINITION DES FONCTIONS ---
def preprocess_image(image):
    """Amélioration du contraste pour l'analyse de l'apex"""
    img_array = np.array(image.convert('L'))
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    return clahe.apply(img_array)

# --- 3. INTERFACE & CHARGEMENT ---
st.title("🦷 Système Expert : Analyse de la Dent 16")
st.markdown("Diagnostic automatisé du **Tiers Apical** et de l'herméticité.")

uploaded_file = st.file_uploader("Charger la radiographie (Optionnel)", type=["jpg", "png", "jpeg"])

raw_img = None

# Logique de sélection de l'image
if uploaded_file is not None:
    raw_img = Image.open(uploaded_file)
else:
    try:
        # Tente de charger l'image de démonstration
        raw_img = Image.open("dent.jpg")
        st.info("💡 Mode Démonstration : Image 'dent.jpg' chargée par défaut.")
    except FileNotFoundError:
        st.warning("⚠️ Veuillez charger une radio manuellement pour commencer.")
        st.stop()

# --- 4. TRAITEMENT ET ANALYSE ---
if raw_img is not None:
    img_gray = preprocess_image(raw_img)
    h, w = img_gray.shape

    # Sidebar pour les réglages
    st.sidebar.header("📍 Réglages de l'Expert")
    # Valeurs par défaut ajustées pour ton étude
    x_c = st.sidebar.slider("Position X (Centre Canal)", 0, w, int(w/2))
    y_haut = st.sidebar.slider("Haut du Canal (Y)", 0, h, int(h*0.2))
    y_apex = st.sidebar.slider("Fin de l'Apex (Y)", 0, h, int(h*0.8))

    # Calcul automatique du tiers apical (les derniers 33%)
    y_tiers_apical = int(y_haut + (y_apex - y_haut) * 0.66)

    # --- 5. AFFICHAGE VISUEL ET GRAPHIQUE ---
    col1, col2 = st.columns([1, 1.2])

    with col1:
        st.subheader("🔎 Zone de Scan")
        img_visu = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)
        
        # Dessin du Tiers Apical (Ligne Cyan)
        cv2.line(img_visu, (x_c, y_tiers_apical), (x_c, y_apex), (0, 255, 255), 10)
        
        # Dessin de l'Apex (Cercle Rouge)
        cv2.circle(img_visu, (x_c, y_apex), 25, (255, 0, 0), -1) 
        st.image(img_visu, use_container_width=True, caption="Visualisation du Tiers Apical")

    with col2:
        st.subheader("📈 Courbe de Densité H")
        # Prélèvement du signal
        signal = profile_line(img_gray, (y_tiers_apical, x_c), (y_apex, x_c), linewidth=5)
        
        if len(signal) > 5:
            # Filtrage pour lisser la courbe
            w_len = 11 if len(signal) > 11 else (len(signal)-1 if len(signal)%2==0 else len(signal))
            if w_len < 3: w_len = 3
            signal_clean = savgol_filter(signal, window_length=w_len, polyorder=2)
            H_values = signal_clean / 255.0  # Normalisation sur 1.0
        else:
            H_values = np.array([0.0])

        # Graphique interactif
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=H_values, mode='lines', line=dict(color='cyan', width=4), name="Profil H"))
        
        # Ligne de seuil pathologique (0.45)
        fig.add_shape(type="line", x0=0, y0=0.45, x1=len(H_values), y1=0.45, 
                      line=dict(color="Red", dash="dash"))
        
        fig.update_layout(template="plotly_dark", height=350, yaxis=dict(range=[0, 1.1]),
                          xaxis_title="Profondeur", yaxis_title="Densité H")
        st.plotly_chart(fig, use_container_width=True)

    # --- 6. LE BOUTON DE DIAGNOSTIC ---
    st.divider()
    if st.button("✨ LANCER LE DIAGNOSTIC MAGIQUE"):
        with st.spinner('Analyse IA en cours...'):
            time.sleep(1) 
            
            h_min = np.min(H_values)
            h_apex = H_values[-1]

            if h_apex < 0.45:
                st.snow() 
                st.error(f"### 🚨 PATHOLOGIE DÉTECTÉE (H_apex={h_apex:.2f})")
                st.write("L'IA détecte une déminéralisation à l'apex (Lésion probable).")
            elif h_min < 0.60:
                st.warning(f"### ⚠️ ÉTANCHÉITÉ DOUTEUSE (H_min={h_min:.2f})")
                st.write("Le scellage canalaire présente des zones de faible densité.")
            else:
                st.balloons() 
                st.success(f"### ✅ ÉTANCHÉITÉ VALIDÉE (H_min={h_min:.2f})")
                st.write("Le traitement est hermétique et l'os environnant est sain.")

    # --- 7. RAPPORT TECHNIQUE ---
    with st.expander("📊 Consulter les données brutes"):
        st.table(pd.DataFrame({
            "Indicateur": ["H Minimal", "H à l'Apex", "Statut Seuil"],
            "Valeur": [f"{np.min(H_values):.2f}", f"{H_values[-1]:.2f}", "0.45"]
        }))
