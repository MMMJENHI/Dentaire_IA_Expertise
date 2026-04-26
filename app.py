import streamlit as st
import numpy as np
import cv2
import plotly.graph_objects as go
from PIL import Image
from skimage.measure import profile_line
from scipy.signal import savgol_filter

# --- CONFIGURATION RAPIDE ---
st.set_page_config(page_title="Expertise Dentaire - Master", layout="wide")

def preprocess_image(image):
    img_array = np.array(image.convert('L'))
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    return clahe.apply(img_array)

# --- INTERFACE ---
st.title("🦷 Diagnostic Synchrone (Optimisé)")

if 'img_gray' not in st.session_state:
    st.session_state.img_gray = None

# --- IMPORTATION ---
uploaded_file = st.sidebar.file_uploader("Radio RVG...", type=['jpg', 'jpeg', 'png'])
if uploaded_file:
    raw_img = Image.open(uploaded_file)
    # On stocke en session pour ne pas recalculer le CLAHE à chaque mouvement
    if st.session_state.img_gray is None:
        st.session_state.img_gray = preprocess_image(raw_img)

if st.session_state.img_gray is not None:
    img_gray = st.session_state.img_gray
    h_img, w_img = img_gray.shape

    # --- SLIDERS ---
    # L'option 'key' et le fait de ne pas avoir de callback lourd accélère Streamlit
    x_input = st.sidebar.slider("Axe X", 0, w_img, int(w_img/2), key="x_slider")
    y_top = st.sidebar.slider("Haut (Y)", 0, h_img, int(h_img*0.2))
    y_apex = st.sidebar.slider("Apex (Y)", 0, h_img, int(h_img*0.8))

    # --- CALCULS INSTANTANÉS ---
    y_start_tiers = int(y_top + (y_apex - y_top) * 0.66)
    
    # On réduit le linewidth à 5 pour accélérer le prélèvement des pixels
    signal = profile_line(img_gray, (y_start_tiers, x_input), (y_apex, x_input), linewidth=5)
    
    # Diagnostic rapide
    h_apex_final = np.mean(signal[-10:]) / 255.0 if len(signal) > 10 else 0.0

    # --- AFFICHAGE SYNCHRONISÉ ---
    col1, col2 = st.columns([1, 1.2])

    with col1:
        # Création de l'image de visualisation (plus rapide en RGB direct)
        img_visu = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)
        
        # Dessin du Tiers Apical (Cyan)
        cv2.line(img_visu, (x_input, y_start_tiers), (x_input, y_apex), (0, 255, 255), 8)
        
        # Dessin de la Tache Apex
        color_status = (0, 255, 0) if h_apex_final >= 0.45 else (255, 0, 0)
        cv2.circle(img_visu, (x_input, y_apex), 20, color_status, -1)
        
        st.image(img_visu, use_container_width=True)

    with col2:
        # Optimisation Plotly : on limite le nombre de points si le signal est trop long
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=signal/255.0, mode='lines', line=dict(color='#00fbff', width=4)))
        fig.add_hline(y=0.45, line_dash="dash", line_color="red")
        fig.add_hrect(y0=0, y1=0.45, fillcolor="red", opacity=0.1)
        
        fig.update_layout(
            template="plotly_dark", 
            height=380, 
            margin=dict(l=10, r=10, t=10, b=10),
            # Désactiver les animations Plotly pour gagner en vitesse
            transition_duration=0 
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # Bouton de rapport final
    if st.button("🚀 VALIDER LE DIAGNOSTIC"):
        status = "✅ CONFORME" if h_apex_final >= 0.45 else "🚨 PATHOLOGIQUE"
        st.success(f"Diagnostic : {status} (H = {h_apex_final:.2f})")
