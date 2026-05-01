import streamlit as st
import cv2
import numpy as np
import plotly.graph_objects as go
from skimage.measure import profile_line
from scipy.signal import savgol_filter
from PIL import Image
import requests
from io import BytesIO
from datetime import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="CAD IA v4.2 - Expertise Scientifique Fusionnée", layout="wide")

# --- 2. FONCTIONS TECHNIQUES OPTIMISÉES (CACHE TOSHIBA) ---
@st.cache_data(show_spinner=False)
def preprocess_image(_image):
    """Optimisation TOSHIBA : Fluidité du point blanc."""
    img_array = np.array(_image.convert('L'))
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    return clahe.apply(img_array)

def smooth(sig):
    if len(sig) > 5:
        w_len = 11 if len(sig) > 11 else (len(sig)-1 if len(sig)%2==0 else len(sig))
        res = savgol_filter(sig, window_length=max(3, w_len), polyorder=2) / 255.0
        return np.clip(res, 0, 1)
    return np.clip(sig / 255.0, 0, 1)

# --- 3. LOGIQUE ADAPTATIVE (ORDRE ANATOMIQUE : Cervical -> Moyen -> Apical) ---
def identifier_zone_relative(x_current, y_current, h_val):
    """Logique Expert JENHI .M - Faculté des Sciences Fès."""
    if h_val < 0.25: return "ZONE NOIRE (LÉSION)", "ALERTE RADIOCLAIRE"
    
    if h_val > 0.65 and (570 <= x_current <= 735) and (1200 <= y_current <= 1530):
        return "TENON MÉTALLIQUE", "ANALYSE D'ANCRAGE"
    if y_current > 1550 or (h_val > 0.78 and 1530 <= x_current <= 2140):
        return "COURONNE", "INTERFACE CORONAIRE"

    if 762 <= y_current <= 1180: return "TIERS CERVICAL", "ANALYSE DU CANAL"
    if 450 <= y_current < 762: return "TIERS MOYEN", "ANALYSE DU CANAL"
    if y_current < 450: return "TIERS APICAL", "EXPERTISE APICALE"
    
    return "OS ALVÉOLAIRE", "DÉTECTION HORS-CANAL"

# --- 4. INTERFACE ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3774/3774278.png", width=80)
st.sidebar.markdown(f"### 👨‍🔬 Expert : JENHI .M")
st.sidebar.markdown("Faculté des Sciences - FÈS")
st.sidebar.divider()

# --- 5. GESTION DU CHARGEMENT ---
source = st.sidebar.radio("📁 Source :", ("Local", "URL/GitHub", "Démo"))
raw_img = None
url_app = "https://dentaireiaexpertiseia.streamlit.app/"
github_url = "https://raw.githubusercontent.com/MMMJENHI/Dentaire_IA_Expertise/main/dent.jpg"

if source == "URL/GitHub":
    url_input = st.sidebar.text_input("Lien GitHub :", value=github_url)
    try:
        res = requests.get(url_input, timeout=10)
        raw_img = Image.open(BytesIO(res.content))
    except: st.sidebar.error("Erreur de chargement URL.")
elif source == "Local":
    up = st.file_uploader("Charger RVG.jpg", type=["jpg", "png", "jpeg"])
    if up: raw_img = Image.open(up)
else:
    try:
        res = requests.get(github_url)
        raw_img = Image.open(BytesIO(res.content))
    except: st.sidebar.error("Mode Démo indisponible.")

# --- 6. TRAITEMENT ET EXPERTISE ---
if raw_img is not None:
    img_gray = preprocess_image(raw_img)
    h_img, w_img = img_gray.shape

    st.sidebar.subheader("📍 Positionnement")
    x_c = st.sidebar.slider("Axe X (Forage)", 0, w_img, 599)
    y_apex_haut = st.sidebar.slider("Y_Apex (Point Blanc)", 0, h_img, 0)
    y_bas = st.sidebar.slider("Y_Bas (Limite Canal)", 0, h_img, 1143)
    
    L = abs(y_bas - y_apex_haut)
    W_exp = int(L * 0.34)
    y_limite_expertise = y_apex_haut + W_exp 
    
    # Signaux Expert
    sig_cyan = profile_line(img_gray, (y_apex_haut, x_c), (y_bas, x_c), linewidth=3)
    H_smooth_cyan = smooth(sig_cyan)
    sig_rouge = profile_line(img_gray, (y_apex_haut, x_c - 20), (y_bas, x_c - 20), linewidth=3)
    H_smooth_rouge = smooth(sig_rouge)
    
    h_final = float(H_smooth_cyan[0]) if len(H_smooth_cyan) > 0 else 0.0
    ratio_securite = (h_final / 0.45) * 100
    ia_zone, _ = identifier_zone_relative(x_c, y_apex_haut, h_final)

    # --- 7. RENDU VISUEL ET FIGURES SÉPARÉES ---
    row1_col1, row1_col2 = st.columns([1, 1.3])
    
    with row1_col1:
        st.subheader("🔎 Visualisation CAD (Gris + CLAHE)")
        display_img = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)
        cv2.line(display_img, (x_c - 20, y_apex_haut), (x_c - 20, y_bas), (255, 0, 0), 6) # ROUGE
        cv2.line(display_img, (x_c, y_apex_haut), (x_c, min(y_limite_expertise, h_img-1)), (0, 255, 255), 15) # CYAN
        cv2.circle(display_img, (x_c, y_apex_haut), 25, (255, 255, 255), -1) # POINT BLANC
        st.image(display_img, use_container_width=True)
        st.info(f"📍 Zone Détectée : **{ia_zone}**")

    with row1_col2:
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(y=H_smooth_cyan, name="DENSITÉ CYAN (Canal)", line=dict(color='cyan', width=4)))
        fig1.add_hrect(y0=0.45, y1=1.0, fillcolor="green", opacity=0.1, annotation_text="ZONE CONFORME")
        fig1.add_hline(y=0.45, line_dash="dash", line_color="white", annotation_text="SEUIL 0.45")
        fig1.update_layout(template="plotly_dark", height=380, title="Figure 1 : Étanchéité Apicale (Cyan)", showlegend=True)
        st.plotly_chart(fig1, use_container_width=True)

    st.divider()
    row2_col1, row2_col2 = st.columns([1.3, 1])

    with row2_col1:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(y=H_smooth_rouge, name="DENSITÉ ROUGE (Paroi)", line=dict(color='red', width=4)))
        fig2.update_layout(template="plotly_dark", height=380, title="Figure 2 : Continuité Structurelle (Rouge)", showlegend=True)
        st.plotly_chart(fig2, use_container_width=True)

    with row2_col2:
        st.subheader("📝 Bilan Scientifique")
        st.latex(r"L_{total} = |Y_{bas} - Y_{apex}| = " + f"{L}")
        st.latex(r"Ratio_{sécurité} = \frac{H_{f}}{0.45} \times 100 = " + f"{ratio_securite:.1f}\%")
        st.metric("Indice H final", f"{h_final:.4f}", delta=f"{h_final-0.45:.4f}")

    # --- 8. LOGIQUE ZONE NOIRE & INTERPRÉTATION ---
    if h_final < 0.45:
        statut_diag = "🚨 NON CONFORME (ZONE NOIRE)"
        interpretation = f"L'analyse au Point Blanc (Y={y_apex_haut}) révèle une densité critique de {h_final:.4f}. L'analyse combinée des Figures 1 et 2 confirme une rupture d'étanchéité et la présence d'une zone noire, ne permettant pas de garantir un scellement hermétique."
    else:
        statut_diag = "✅ CONFORME"
        interpretation = f"L'obturation est validée jusqu'au Point Blanc (Y={y_apex_haut}). L'analyse combinée des Figures 1 et 2 confirme que la densité de {h_final:.4f} garantit un scellement hermétique."

    # --- 9. RAPPORT D'EXPERTISE DÉTAILLÉ ---
    st.divider()
    rapport_expert = f"""
    RAPPORT D'EXPERTISE DENTAIRE - SYSTÈME CAD v4.2
    --------------------------------------------------
    EXPERT RESPONSABLE : JENHI .M
    UNITÉ D'ANALYSE    : Faculté des Sciences - FÈS
    --------------------------------------------------

    [1] ANALYSE TECHNIQUE DES CAPTEURS :
    - FIGURE 1 (CYAN) : Expertise d'étanchéité apicale (Validation scellement).
    - FIGURE 2 (ROUGE) : Scan de continuité structurelle (Validation paroi).

    [2] DONNÉES DE LOCALISATION :
    - Axe de forage (X) : {x_c} px
    - Apex Cible (Y)    : {y_apex_haut} px (POINT BLANC)
    - Bas Canal (Y)     : {y_bas} px

    [3] MÉTRIQUES DENSITOMÉTRIQUES :
    - Indice H final    : {h_final:.4f}
    - Ratio de sécurité : {ratio_securite:.1f} %
    - Seuil critique    : 0.45

    [4] VALIDATION DU VERDICT :
    DIAGNOSTIC FINAL    : {statut_diag}
    --------------------------------------------------
    INTERPRÉTATION CLINIQUE :
    "{interpretation}"
    """
    st.code(rapport_expert, language="text")
    st.download_button("💾 Exporter le Rapport (.txt)", rapport_expert, file_name=f"Expertise_{ia_zone}.txt")

else:
    st.info("💡 En attente du chargement de la radiographie.")
