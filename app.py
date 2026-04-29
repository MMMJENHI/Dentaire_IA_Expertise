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
        w_len = 11 if len(sig) > 11 else (len(sig)-1 if len(sig)%2==0 else len(sig))
        res = savgol_filter(sig, window_length=max(3, w_len), polyorder=2) / 255.0
        return np.clip(res, 0, 1)
    return np.clip(sig / 255.0, 0, 1)

# --- 3. IDENTITÉ ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3774/3774278.png", width=80)
st.sidebar.markdown(f"### 👨‍🔬 Expert : JENHI .M")
st.sidebar.divider()

st.title("🦷 CAD System : Expertise Inversée (Apex en Haut)")

# --- 4. CHARGEMENT IMAGE ---
try:
    raw_img = Image.open("dent.jpg")
except:
    res = requests.get("https://raw.githubusercontent.com/MMMJENHI/Dentaire_IA_Expertise/main/dent.jpg")
    raw_img = Image.open(BytesIO(res.content))

if raw_img is not None:
    img_gray = preprocess_image(raw_img)
    h, w = img_gray.shape

    # --- CONFIGURATION SELON VOS DONNÉES ---
    x_c = st.sidebar.slider("Axe X (Forage)", 0, w, 718)
    y_apex_haut = st.sidebar.slider("Y_Apex (Haut de radio)", 0, h, 9)
    y_tenon_bas = st.sidebar.slider("Y_Tenon (Bas de radio)", 0, h, 1147)

    # Calcul de la longueur
    L = abs(y_tenon_bas - y_apex_haut)
    
    # Le Tiers Apical est maintenant au DEBUT du scan (les premiers 34%)
    # Car l'apex est à Y=9
    y_limite_expertise = y_apex_haut + int(L * 0.34) 
    
    # Extraction des signaux (du haut vers le bas)
    signal_global = profile_line(img_gray, (y_apex_haut, x_c), (y_tenon_bas, x_c), linewidth=3)
    # Le signal apical prend le début de la liste (le tiers proche de l'apex)
    signal_apical = signal_global[:int(len(signal_global)*0.34)]

    H_global = smooth(signal_global)
    H_apical = smooth(signal_apical)
    
    h_final = float(H_apical[0]) # L'apex est le premier point (Y=9)
    h_max = float(np.max(H_apical))
    idx_max_relatif = int(np.argmax(H_apical))
    
    col_img, col_graphs = st.columns([1, 1.5])

    with col_img:
        st.subheader("🔎 Visualisation Inversée")
        img_visu = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)
        # Trace Global en Rouge
        cv2.line(img_visu, (x_c - 20, y_apex_haut), (x_c - 20, y_tenon_bas), (255, 0, 0), 6)
        # Trace Expertise en Cyan (Le tiers du haut)
        cv2.line(img_visu, (x_c, y_apex_haut), (x_c, y_limite_expertise), (0, 255, 255), 15)
        # Point Apex (Blanc) tout en haut
        cv2.circle(img_visu, (x_c, y_apex_haut), 22, (255, 255, 255), -1)
        st.image(img_visu, use_container_width=True)

    with col_graphs:
        # FIG 1 : GLOBAL (Axe X corrigé)
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=np.arange(y_apex_haut, y_tenon_bas), y=H_global, name="Profil", line=dict(color='red')))
        fig1.update_layout(template="plotly_dark", height=230, title="Profil : Apex (9) → Tenon (1147)",
                          xaxis_title="Position Y (Pixels)", yaxis_title="Densité H")
        st.plotly_chart(fig1, use_container_width=True)

        # FIG 2 : TIERS APICAL (Expertise sur les 387 premiers pixels)
        fig2 = go.Figure()
        x_apical = np.arange(y_apex_haut, y_limite_expertise)
        fig2.add_trace(go.Scatter(x=x_apical, y=H_apical, name="Zone Critique", line=dict(color='cyan', width=5)))
        
        # Zones de diagnostic
        fig2.add_hrect(y0=0.45, y1=1.0, fillcolor="green", opacity=0.15, annotation_text="CONFORME")
        fig2.add_hrect(y0=0, y1=0.45, fillcolor="red", opacity=0.15, annotation_text="INFILTRATION")
        fig2.add_hline(y=0.45, line_dash="dash", line_color="red", line_width=3)

        # Annotation de l'Apex à Y=9
        fig2.add_annotation(x=y_apex_haut, y=h_final, text=f"APEX H: {h_final:.2f}", showarrow=True, arrowhead=2, bgcolor="white", font=dict(color="black"))

        fig2.update_layout(template="plotly_dark", height=320, title="Expertise Densitométrique (Tiers Apical)",
                          xaxis_title="Profondeur Y (Pixels)", yaxis_title="Densité H", yaxis=dict(range=[0, 1]))
        st.plotly_chart(fig2, use_container_width=True)

    # --- 6. BILAN ---
    st.divider()
    statut = "✅ ÉTANCHÉITÉ VALIDÉE" if h_final >= 0.45 else "🚨 RISQUE D'INFILTRATION"
    st.markdown(f"### Verdict Final : {statut}")
    st.info(f"Analyse effectuée sur {len(H_apical)} pixels en zone apicale haute.")
