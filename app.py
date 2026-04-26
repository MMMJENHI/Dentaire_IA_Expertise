import streamlit as st
import requests
import numpy as np
import cv2
import plotly.graph_objects as go
from PIL import Image
from io import BytesIO
from skimage.measure import profile_line
from scipy.signal import savgol_filter
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Expertise Dentaire - Master", layout="wide")

def preprocess_image(image):
    img_array = np.array(image.convert('L'))
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    return clahe.apply(img_array)

@st.cache_data
def load_img_from_url(url):
    try:
        response = requests.get(url, timeout=5)
        return Image.open(BytesIO(response.content))
    except:
        return None

# --- TITRE ---
st.title("🦷 Système Expert : Diagnostic du Tiers Apical")

# --- BARRE LATÉRALE (IMPORT) ---
st.sidebar.header("📁 Chargement")
option = st.sidebar.selectbox("Source :", ("Depuis mon PC (Local)", "Lien GitHub (Raw)", "Lien Web"))

raw_img = None
if option == "Depuis mon PC (Local)":
    uploaded_file = st.sidebar.file_uploader("Fichier...", type=['jpg', 'jpeg', 'png'])
    if uploaded_file: raw_img = Image.open(uploaded_file)
elif option == "Lien GitHub (Raw)":
    github_url = st.sidebar.text_input("URL :", "https://raw.githubusercontent.com/MMMJENHI/Dentaire_IA_Expertise/main/dent.jpg")
    if github_url: raw_img = load_img_from_url(github_url)
else:
    web_url = st.sidebar.text_input("Lien direct :")
    if web_url: raw_img = load_img_from_url(web_url)

if raw_img is not None:
    img_gray = preprocess_image(raw_img)
    h_img, w_img = img_gray.shape

    # --- SLIDERS : CONTRÔLE DU DÉPLACEMENT ---
    st.sidebar.divider()
    st.sidebar.header("📍 Réglages Manuels")
    x_input = st.sidebar.slider("Position X (Déplacer le trait)", 0, w_img, int(w_img/2))
    y_top = st.sidebar.slider("Haut du Canal (Y)", 0, h_img, int(h_img*0.2))
    y_apex = st.sidebar.slider("Point Apex (Y)", 0, h_img, int(h_img*0.8))

    # --- CALCULS TECHNIQUES ---
    # Détermination du début du tiers apical (environ 66% du trajet Y)
    y_start_tiers = int(y_top + (y_apex - y_top) * 0.66)
    
    # Calcul de la densité H sur le trait
    signal = profile_line(img_gray, (y_start_tiers, x_input), (y_apex, x_input), linewidth=8)
    
    if len(signal) > 5:
        w_len = 11 if len(signal) > 11 else (len(signal)-1 if len(signal)%2==0 else len(signal))
        signal_smooth = savgol_filter(signal, window_length=max(3, w_len), polyorder=2)
        H_values = signal_smooth / 255.0
        h_apex_final = np.mean(H_values[-10:]) 
    else:
        H_values = np.array([0.0]); h_apex_final = 0.0

    # --- AFFICHAGE ---
    col1, col2 = st.columns([1, 1.2])

    with col1:
        st.subheader("🔎 Visualisation")
        img_rgb = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)
        
        # --- NETTOYAGE : ON NE DESSINE QUE LA ZONE UTILE ---
        # On trace uniquement le segment Cyan (Tiers Apical)
        cv2.line(img_rgb, (x_input, y_start_tiers), (x_input, y_apex), (0, 255, 255), 10)
        
        # On trace le point final (Apex) qui écrase le bout du trait
        color_status = (0, 255, 0) if h_apex_final >= 0.45 else (255, 0, 0)
        cv2.circle(img_rgb, (x_input, y_apex), 25, color_status, -1)
        
        st.image(img_rgb, use_container_width=True, caption=f"Analyse sur l'axe X = {x_input}")

    with col2:
        st.subheader("📈 Courbe de Diagnostic")
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=H_values, mode='lines', line=dict(color='#00fbff', width=5)))
        fig.add_hline(y=0.45, line_dash="dash", line_color="red")
        fig.add_hrect(y0=0, y1=0.45, fillcolor="red", opacity=0.15)
        fig.update_layout(template="plotly_dark", height=400, yaxis_title="Densité H", xaxis_title="Profondeur")
        st.plotly_chart(fig, use_container_width=True)

    # --- RAPPORT D'EXPERTISE ---
    st.divider()
    if st.button("🚀 LANCER L'EXPERTISE"):
        status = "✅ SAIN" if h_apex_final >= 0.45 else "🚨 PATHOLOGIQUE"
        st.write(f"### DIAGNOSTIC : {status}")
        
        rapport = f"""
        RAPPORT D'EXPERTISE DENTAIRE
        ----------------------------------
        POSITION X : {x_input}
        TIERS APICAL : Y={y_start_tiers} à {y_apex}
        VALEUR H MOYENNE : {h_apex_final:.2f}
        ----------------------------------
        RÉSULTAT : {status} (Conforme si H > 0.45)
        """
        st.code(rapport)

else:
    st.info("💡 Chargez une radio pour commencer l'analyse.")
