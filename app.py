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

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="IA Expertise Dentaire - JENHI .M", layout="wide")

# --- FONCTIONS TECHNIQUES ---
def preprocess_image(image):
    """Amélioration du contraste CLAHE pour l'expertise"""
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

def auto_center_x(image, x_user, y_target, margin=20):
    """IA de recentrage : Trouve le pic de densité (Gutta-Percha)"""
    try:
        x_start = max(0, x_user - margin)
        x_end = min(image.shape[1], x_user + margin)
        line_sample = image[y_target, x_start:x_end]
        best_x_offset = np.argmax(line_sample)
        return x_start + best_x_offset
    except:
        return x_user

# --- BARRE LATÉRALE (IDENTITÉ & CONFIGURATION) ---
st.sidebar.markdown("""
    <div style="text-align: center;">
        <h2 style="color: #00fbff; margin-bottom: 0;">JENHI .M</h2>
        <p style="font-size: 0.8em; color: gray;">Expertise IA Dentaire | Master 2026</p>
    </div>
    """, unsafe_allow_html=True)

# URL OFFICIELLE & QR CODE DYNAMIQUE
url_officielle = "https://dentaireiaexpertiseia.streamlit.app/"
qr_api = f"https://api.qrserver.com/v1/create-qr-code/?size=120x120&data={url_officielle}"

st.sidebar.image(qr_api, caption="Accès Mobile Officiel")
st.sidebar.divider()

st.sidebar.header("📁 Importation Radio")
option = st.sidebar.selectbox("Source :", ("Depuis mon PC (Local)", "Lien GitHub (Raw)", "Lien Web"))

raw_img = None
if option == "Depuis mon PC (Local)":
    uploaded_file = st.sidebar.file_uploader("Fichier image...", type=['jpg', 'jpeg', 'png'])
    if uploaded_file: raw_img = Image.open(uploaded_file)
elif option == "Lien GitHub (Raw)":
    github_url = "https://raw.githubusercontent.com/MMMJENHI/Dentaire_IA_Expertise/main/dent.jpg"
    raw_img = load_img_from_url(github_url)
else:
    web_url = st.sidebar.text_input("Lien direct :")
    if web_url: raw_img = load_img_from_url(web_url)

# --- CORPS DE L'APPLICATION ---
st.title("🦷 Système Expert : Analyse du Tiers Apical (Dent 16)")

if raw_img is not None:
    img_gray = preprocess_image(raw_img)
    h_img, w_img = img_gray.shape  # Définition des variables h_img et w_img

    st.sidebar.divider()
    st.sidebar.header("📍 Segmentation & Axes")
    
    # Utilisation correcte de w_img et h_img pour éviter la NameError
    x_input = st.sidebar.slider("Position X (Axe)", 0, w_img, int(w_img/2))
    y_top_canal = st.sidebar.slider("Haut du Canal (Y)", 0, h_img, int(h_img*0.2))
    y_apex_point = st.sidebar.slider("Point Apex (Y)", 0, h_img, int(h_img*0.8))

    # RECENTRAGE IA
    x_top = auto_center_x(img_gray, x_input, y_top_canal)
    x_apex = auto_center_x(img_gray, x_input, y_apex_point)
    
    # ISOLATION TIERS APICAL (Derniers 33%)
    y_start_tiers = int(y_top_canal + (y_apex_point - y_top_canal) * 0.66)
    x_start_tiers = int(x_top + (x_apex - x_top) * 0.66)

    # CALCUL DE LA DENSITÉ H
    signal = profile_line(img_gray, (y_start_tiers, x_start_tiers), (y_apex_point, x_apex), linewidth=8)
    
    if len(signal) > 5:
        w_len = 11 if len(signal) > 11 else (len(signal)-1 if len(signal)%2==0 else len(signal))
        signal_smooth = savgol_filter(signal, window_length=max(3, w_len), polyorder=2)
        H_values = signal_smooth / 255.0
        h_apex_final = np.mean(H_values[-10:])
    else:
        H_values = np.array([0.0])
        h_apex_final = 0.0

    # AFFICHAGE
    col1, col2 = st.columns([1, 1.2])

    with col1:
        st.subheader("🔎 Visualisation")
        img_rgb = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)
        cv2.line(img_rgb, (x_top, y_top_canal), (x_start_tiers, y_start_tiers), (100, 100, 100), 2)
        cv2.line(img_rgb, (x_start_tiers, y_start_tiers), (x_apex, y_apex_point), (0, 255, 255), 10)
        color_status = (0, 255, 0) if h_apex_final >= 0.45 else (255, 0, 0)
        cv2.circle(img_rgb, (x_apex, y_apex_point), 25, color_status, -1)
        st.image(img_rgb, use_container_width=True, caption=f"Axe X détecté : {x_apex}")

    with col2:
        st.subheader("📈 Profil de Densité H (Tiers Apical)")
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=H_values, mode='lines', line=dict(color='#00fbff', width=5), name="Densité Gutta"))
        fig.add_hline(y=0.45, line_dash="dash", line_color="red", annotation_text="SEUIL HERMÉTIQUE")
        fig.update_layout(template="plotly_dark", height=400, yaxis_title="Valeur H (Normalisée)", xaxis_title="Profondeur du tiers")
        st.plotly_chart(fig, use_container_width=True)

    if st.button("🚀 LANCER L'EXPERTISE"):
        status = "✅ OBTURATION HERMÉTIQUE" if h_apex_final >= 0.45 else "🚨 DEFAUT D'ÉTANCHÉITÉ"
        st.info(f"### {status}")
        rapport = f"Expertise JENHI .M\nDensité H Finale : {h_apex_final:.2f}\nURL: {url_officielle}"
        st.code(rapport)

else:
    st.info("💡 En attente d'une radio dentaire (Dent 16)...")
