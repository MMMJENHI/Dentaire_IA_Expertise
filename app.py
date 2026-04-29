import streamlit as st
import cv2
import numpy as np
import plotly.graph_objects as go
from skimage.measure import profile_line
from scipy.signal import savgol_filter
from PIL import Image
import requests
from io import BytesIO

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="CAD IA Dentaire Expert - JENHI .M", layout="wide")

# --- 2. FONCTIONS TECHNIQUES ---
def preprocess_image(image):
    img_array = np.array(image.convert('L'))
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    return clahe.apply(img_array)

def smooth(sig):
    if len(sig) > 5:
        # Fenêtre adaptative pour éviter les erreurs sur les segments courts
        w_len = min(11, len(sig) // 2 * 2 - 1)
        if w_len < 3: return np.clip(sig / 255.0, 0, 1)
        res = savgol_filter(sig, window_length=w_len, polyorder=2) / 255.0
        return np.clip(res, 0, 1)
    return np.clip(sig / 255.0, 0, 1)

# --- 3. LOGO & IDENTITÉ ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3774/3774278.png", width=80)
st.sidebar.markdown(f"### 👨‍🔬 Expert : JENHI .M")
st.sidebar.markdown("Faculté des Sciences - FÈS")
st.sidebar.divider()

st.title("🦷 CAD System : Expertise Double Échelle (Dent 16)")

# --- 4. CHARGEMENT DE LA RADIO ---
try:
    raw_img = Image.open("dent.jpg")
except:
    res = requests.get("https://raw.githubusercontent.com/MMMJENHI/Dentaire_IA_Expertise/main/dent.jpg")
    raw_img = Image.open(BytesIO(res.content))

if raw_img is not None:
    img_gray = preprocess_image(raw_img)
    h, w = img_gray.shape

    # --- PARAMÈTRES DE LOCALISATION (Valeurs fusionnées) ---
    x_c = st.sidebar.slider("Axe X (Forage)", 0, w, 373)
    y_haut = st.sidebar.slider("Haut de Canal (Y)", 0, h, 1110)
    y_apex = st.sidebar.slider("Cible Apicale (Y)", 0, h, 1054)

    # --- CALCULS MATHÉMATIQUES DU MODÈLE ---
    L = abs(y_apex - y_haut)
    D = int(L * 0.66)  # Zone de descente
    W = int(L * 0.34)  # Fenêtre d'expertise
    
    # Gestion du sens du scan (si y_apex < y_haut)
    step = -1 if y_apex < y_haut else 1
    y_tiers_debut = y_haut + (step * D)
    
    # Extraction des signaux
    signal_global = profile_line(img_gray, (y_haut, x_c), (y_apex, x_c), linewidth=3)
    signal_apical = profile_line(img_gray, (y_tiers_debut, x_c), (y_apex, x_c), linewidth=5)

    H_global = smooth(signal_global)
    H_apical = smooth(signal_apical)
    
    h_final = float(H_apical[-1]) if len(H_apical) > 0 else 0.0
    h_max = float(np.max(H_apical)) if len(H_apical) > 0 else 0.0
    ratio_securite = (h_final / 0.45) * 100 if h_final > 0 else 0.0

    # --- 5. VISUALISATION CAD ---
    col1, col2 = st.columns([1, 1.5])
    with col1:
        st.subheader("🔎 Visualisation")
        img_visu = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)
        cv2.line(img_visu, (x_c - 20, y_haut), (x_c - 20, y_apex), (255, 0, 0), 6)
        cv2.line(img_visu, (x_c, y_tiers_debut), (x_c, y_apex), (0, 255, 255), 15)
        cv2.circle(img_visu, (x_c, y_apex), 22, (255, 255, 255), -1)
        st.image(img_visu, use_container_width=True)

    with col2:
        fig = go.Figure()
        if len(H_apical) > 0:
            x_range = np.linspace(y_tiers_debut, y_apex, len(H_apical))
            fig.add_trace(go.Scatter(x=x_range, y=H_apical, name="Zone Apicale", line=dict(color='cyan', width=5)))
        
        fig.add_hrect(y0=0.45, y1=1.0, fillcolor="green", opacity=0.15, annotation_text="CONFORME")
        fig.add_hrect(y0=0, y1=0.45, fillcolor="red", opacity=0.15, annotation_text="INFILTRATION")
        fig.add_hline(y=0.45, line_dash="dash", line_color="red", line_width=3)
        fig.update_layout(template="plotly_dark", height=400, title="Analyse Densitométrique Apicale", xaxis_title="Position Y (Pixels)")
        st.plotly_chart(fig, use_container_width=True)

    # --- 6. BILAN EXPERT SCIENTIFIQUE ---
    st.divider()
    st.subheader("📝 Bilan Expert CAD (Format Scientifique)")
    
    st.latex(r"L_{canal} = |Y_{apex} - Y_{haut}| = " + f"{L}")
    st.latex(r"W_{expertise} = L \times 0.34 = " + f"{W} \text{{ pixels}}")
    st.latex
