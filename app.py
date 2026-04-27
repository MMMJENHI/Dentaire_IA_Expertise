import streamlit as st
import cv2
import numpy as np
import plotly.graph_objects as go
from skimage.measure import profile_line
from scipy.signal import savgol_filter
from PIL import Image
import requests
from io import BytesIO

# --- CONFIGURATION PAGE ---
st.set_page_config(page_title="CAD IA Dentaire", layout="wide")

# --- FONCTIONS DE CALCUL ---
def preprocess(image):
    img_array = np.array(image.convert('L'))
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    return clahe.apply(img_array)

def smooth(sig):
    if len(sig) > 5:
        w = 11 if len(sig) > 11 else (len(sig)-1 if len(sig)%2==0 else len(sig))
        return savgol_filter(sig, window_length=max(3, w), polyorder=2) / 255.0
    return sig / 255.0

# --- CHARGEMENT ---
st.title("🦷 CAD System : Expertise Tiers Apical (Dent 16)")

source = st.sidebar.radio("Source :", ("Démo", "URL/GitHub", "Local"))
raw_img = None

if source == "URL/GitHub":
    url = st.text_input("Lien Image :", "https://raw.githubusercontent.com/MMMJENHI/Dentaire_IA_Expertise/main/dent.jpg")
    if url:
        try:
            res = requests.get(url, timeout=5)
            raw_img = Image.open(BytesIO(res.content))
        except: st.error("Lien invalide")
elif source == "Local":
    up = st.file_uploader("Radio", type=["jpg", "png", "jpeg"])
    if up: raw_img = Image.open(up)
else:
    try: raw_img = Image.open("dent.jpg")
    except: st.warning("Fichier démo 'dent.jpg' non trouvé.")

# --- ANALYSE CAD ---
if raw_img is not None:
    img_gray = preprocess(raw_img)
    h, w = img_gray.shape

    st.sidebar.header("📍 Paramètres")
    x_c = st.sidebar.slider("Position X", 0, w, int(w/2))
    y_haut = st.sidebar.slider("Haut Canal", 0, h, int(h*0.2))
    y_apex = st.sidebar.slider("Y_apex", 0, h, int(h*0.8))

    # Sécurité mathématique
    if y_apex <= y_haut: y_apex = y_haut + 10

    # Calcul des zones (Tiers Apical = derniers 33%)
    y_tiers = int(y_haut + (y_apex - y_haut) * 0.66)
    
    # Extraire et lisser
    H_global = smooth(profile_line(img_gray, (y_haut, x_c), (y_apex, x_c), linewidth=3))
    H_apical = smooth(profile_line(img_gray, (y_tiers, x_c), (y_apex, x_c), linewidth=5))
    h_final = H_apical[-1]

    # AFFICHAGE
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.subheader("🔎 Visualisation")
        img_v = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)
        # Rouge = Global / Cyan = Expertise
        cv2.line(img_v, (x_c-15, y_haut), (x_c-15, y_apex), (255, 0, 0), 3)
        cv2.line(img_v, (x_c, y_tiers), (x_c, y_apex), (255, 255, 0), 12)
        cv2.circle(img_v, (x_c, y_apex), 15, (255, 255, 255), -1) # Apex Blanc
        st.image(img_v, use_container_width=True)

    with col2:
        # Graphe 1 : Rouge
        f1 = go.Figure()
        f1.add_trace(go.Scatter(x=np.arange(y_haut, y_apex), y=H_global, line=dict(color='red')))
        f1.update_layout(template="plotly_dark", height=230, title="Profil Global (Rouge)", margin=dict(t=30, b=10))
        st.plotly_chart(f1, use_container_width=True)
        
        # Graphe 2 : Cyan
        f2 = go.Figure()
        f2.add_trace(go.Scatter(y=H_apical, line=dict(color='cyan', width=4)))
        f2.add_shape(type="line", x0=0, y0=0.45, x1=len(H_apical), y1=0.45, line=dict(color="white", dash="dash"))
        f2.update_layout(template="plotly_dark", height=230, title="Analyse Tiers Apical (Cyan)", margin=dict(t=30, b=10))
        st.plotly_chart(f2, use_container_width=True)

    # RAPPORT
    st.divider()
    statut = "✅ CONFORME" if h_final >= 0.45 else "🚨 NON CONFORME"
    rapport = f"RAPPORT CAD - DENT 16\nPOSITION : X={x_c} | Y={y_apex}\nVALEUR H : {h_final:.4f}\nDIAGNOSTIC : {statut}"
    st.text_area("Bilan Expert", rapport, height=150)
    st.download_button("💾 Télécharger Rapport (.txt)", rapport, "Rapport_CAD.txt")
