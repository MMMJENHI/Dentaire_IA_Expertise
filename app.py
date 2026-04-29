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

st.title("🦷 CAD System : Expertise Double Échelle (Dent 16)")

# --- 4. CHARGEMENT IMAGE ---
try:
    raw_img = Image.open("dent.jpg")
except:
    res = requests.get("https://raw.githubusercontent.com/MMMJENHI/Dentaire_IA_Expertise/main/dent.jpg")
    raw_img = Image.open(BytesIO(res.content))

if raw_img is not None:
    img_gray = preprocess_image(raw_img)
    h, w = img_gray.shape

    # --- CONFIGURATION DES COORDONNÉES ---
    x_c = st.sidebar.slider("Axe X (Forage)", 0, w, 718)
    y_apex_haut = st.sidebar.slider("Y_Apex (Haut)", 0, h, 9)
    y_tenon_bas = st.sidebar.slider("Y_Tenon (Bas)", 0, h, 1147)

    # --- CALCULS MATHÉMATIQUES ---
    L = abs(y_tenon_bas - y_apex_haut)
    W = int(L * 0.34)  # Fenêtre d'expertise (Tiers Apical)
    D = int(L * 0.66)  # Zone de descente
    
    y_limite_expertise = y_apex_haut + W 
    
    # Signaux
    signal_global = profile_line(img_gray, (y_apex_haut, x_c), (y_tenon_bas, x_c), linewidth=3)
    signal_apical = signal_global[:W] 

    H_global = smooth(signal_global)
    H_apical = smooth(signal_apical)
    
    h_final = float(H_apical[0])
    ratio_securite = (h_final / 0.45) * 100

    # --- 5. VISUALISATION ---
    col1, col2 = st.columns([1, 1.5])
    with col1:
        st.subheader("🔎 Visualisation CAD")
        img_visu = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)
        cv2.line(img_visu, (x_c - 20, y_apex_haut), (x_c - 20, y_tenon_bas), (255, 0, 0), 6)
        cv2.line(img_visu, (x_c, y_apex_haut), (x_c, y_limite_expertise), (0, 255, 255), 15)
        cv2.circle(img_visu, (x_c, y_apex_haut), 22, (255, 255, 255), -1)
        st.image(img_visu, use_container_width=True)

    with col2:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=np.arange(y_apex_haut, y_limite_expertise), y=H_apical, name="Apical", line=dict(color='cyan', width=5)))
        fig2.add_hrect(y0=0.45, y1=1.0, fillcolor="green", opacity=0.15, annotation_text="CONFORME")
        fig2.add_hrect(y0=0, y1=0.45, fillcolor="red", opacity=0.15, annotation_text="INFILTRATION")
        fig2.add_hline(y=0.45, line_dash="dash", line_color="red", line_width=3)
        fig2.update_layout(template="plotly_dark", height=400, title=f"Expertise : Fenêtre W = {W} px", xaxis_title="Position Y (Pixels)")
        st.plotly_chart(fig2, use_container_width=True)

    # --- 6. BILAN EXPERT CAD (FORMAT SCIENTIFIQUE) ---
    st.divider()
    st.subheader("📝 Bilan Expert CAD (Format Scientifique)")
    
    # Affichage des équations avec syntaxe LaTeX sécurisée
    st.latex(r"L_{canal} = |Y_{tenon} - Y_{apex}| = " + f"{L}")
    st.latex(r"D_{descente} = L \times 0.66 = " + f"{D} \text{ pixels}")
    st.latex(r"W_{expertise} = L \times 0.34 = " + f"{W} \text{ pixels}")
    st.latex(r"Ratio_{sécurité} = \left( \frac{H_{final}}{0.45} \right) \times 100 = " + f"{ratio_securite:.2f} \%")

    statut = "✅ CONFORME (Étanchéité Validée)" if h_final >= 0.45 else "🚨 NON CONFORME (Risque d'Infiltration)"

    rapport_expert = f"""
    RAPPORT D'EXPERTISE DENTAIRE - SYSTÈME CAD v3.0
    --------------------------------------------------
    EXPERT RESPONSABLE : JENHI .M
    DATE D'ANALYSE     : 29/04/2026
    --------------------------------------------------
    [1] ANALYSE STRUCTURELLE :
    - Longueur totale (L)     : {L} px
    - Descente neutre (D)     : {D} px
    - Fenêtre apicale (W)     : {W} px
    
    [2] MÉTRIQUES DE DENSITÉ :
    - Indice H Final (Apex)   : {h_final:.4f}
    - Seuil Critique          : 0.45
    - Ratio de Sécurité       : {ratio_securite:.2f} %
    
    [3] VERDICT FINAL :
    {statut}
    --------------------------------------------------
    INTERPRÉTATION :
    "La mesure à Y={y_apex_haut} confirme une densité de {h_final:.4f}. 
    Le ratio de sécurité de {ratio_securite:.2f}% atteste de la qualité 
    hermétique du scellement dans le tiers apical."
    """
    
    st.code(rapport_expert, language="text")
    st.download_button("💾 Exporter le Bilan Scientifique", rapport_expert, file_name="Bilan_Expert_JENHI.txt")
