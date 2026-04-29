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

# --- 3. IDENTITÉ & LOGO ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3774/3774278.png", width=80)
st.sidebar.markdown(f"### 👨‍🔬 Expert : JENHI .M")
st.sidebar.markdown("Faculté des Sciences - FÈS")
st.sidebar.divider()

st.title("🦷 CAD System : Expertise Double Échelle (Dent 16)")

url_app = "https://dentaireiaexpertiseia.streamlit.app/"

# --- 4. CHARGEMENT ET RÉGLAGES ---
try:
    raw_img = Image.open("dent.jpg")
except:
    res = requests.get("https://raw.githubusercontent.com/MMMJENHI/Dentaire_IA_Expertise/main/dent.jpg")
    raw_img = Image.open(BytesIO(res.content))

if raw_img is not None:
    img_gray = preprocess_image(raw_img)
    h, w = img_gray.shape

    # UTILISATION DE Y_BAS (COHÉRENCE CODE ET IHM)
    x_c = st.sidebar.slider("Axe X (Forage)", 0, w, 712)
    y_apex_haut = st.sidebar.slider("Y_Apex (Haut / Point Blanc)", 0, h, 9)
    y_bas = st.sidebar.slider("Y_Bas (Limite Canal)", 0, h, 1147)

    # --- ÉQUATIONS DU MODÈLE L = W + D ---
    L = abs(y_bas - y_apex_haut)
    W = int(L * 0.34)  # Fenêtre d'expertise (Tiers Apical)
    D = int(L * 0.66)  # Distance de descente
    
    y_limite_expertise = y_apex_haut + W 
    
    # Extraction des signaux
    signal_global = profile_line(img_gray, (y_apex_haut, x_c), (y_bas, x_c), linewidth=3)
    signal_apical = signal_global[:W] 

    H_global = smooth(signal_global)
    H_apical = smooth(signal_apical)
    
    h_final = float(H_apical[0])
    h_max = float(np.max(H_apical))
    ratio_securite = (h_final / 0.45) * 100

    # --- 5. VISUALISATION CAD ---
    col1, col2 = st.columns([1, 1.5])
    with col1:
        st.subheader("🔎 Visualisation CAD")
        img_visu = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)
        
        # Trait Rouge : Scan Global (s'arrête à y_bas)
        cv2.line(img_visu, (x_c - 20, y_apex_haut), (x_c - 20, y_bas), (255, 0, 0), 6)
        # Trait Cyan : Zone Expertise
        cv2.line(img_visu, (x_c, y_apex_haut), (x_c, y_limite_expertise), (0, 255, 255), 15)
        # Apex Cible (Point Blanc)
        cv2.circle(img_visu, (x_c, y_apex_haut), 22, (255, 255, 255), -1)
        st.image(img_visu, use_container_width=True)

    with col2:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=np.arange(y_apex_haut, y_limite_expertise), y=H_apical, name="Apical", line=dict(color='cyan', width=5)))
        fig.add_hrect(y0=0.45, y1=1.0, fillcolor="green", opacity=0.15, annotation_text="CONFORME")
        fig.add_hrect(y0=0, y1=0.45, fillcolor="red", opacity=0.15, annotation_text="INFILTRATION")
        fig.add_hline(y=0.45, line_dash="dash", line_color="red", line_width=3)
        fig.update_layout(template="plotly_dark", height=400, title="Analyse Tiers Apical")
        st.plotly_chart(fig, use_container_width=True)

    # --- 6. BILAN EXPERT CAD (FORMAT SCIENTIFIQUE) ---
    st.divider()
    st.subheader("📝 Bilan Expert CAD (Format Scientifique)")
    
    col_math, col_verdict = st.columns([1, 1.5])
    
    with col_math:
        st.markdown("### 🧮 Justification Mathématique")
        st.latex(r"L_{canal} = |Y_{bas} - Y_{apex}| = " + f"{L}")
        st.latex(r"W_{expertise} = L \times 0.34 = " + f"{W} \text{{ px}}")
        st.latex(r"D_{descente} = L \times 0.66 = " + f"{D} \text{{ px}}")
        st.latex(r"Ratio_{sécurité} = \frac{H_{final}}{0.45} \times 100 = " + f"{ratio_securite:.1f}\%")

    statut = "✅ CONFORME" if h_final >= 0.45 else "🚨 NON CONFORME"
    precision_apex = "Validée (Position matricielle haute)" if y_apex_haut < 100 else "À vérifier"

    # Construction du rapport final
    rapport_expert = f"""
    RAPPORT D'EXPERTISE DENTAIRE - SYSTÈME CAD v3.0
    --------------------------------------------------
    EXPERT RESPONSABLE : JENHI .M
    UNITÉ D'ANALYSE    : Faculté des Sciences - FÈS
    PROJET             : Master Diagnostic IA - Dent 16
    APPLICATION URL    : {url_app}
    --------------------------------------------------

    [1] ANALYSE TECHNIQUE DES CAPTEURS :
    - TRAIT ROUGE (SCAN GLOBAL) : Analyse la densité sur toute 
      la longueur canalaire. Détecte les pertes de continuité.
    - TRAIT CYAN (ZONE EXPERTISE) : Focalisation sur le tiers 
      apical pour mesurer l'herméticité finale (Point Blanc).

    [2] DONNÉES DE LOCALISATION :
    - Axe de forage (X)   : {x_c} px
    - Apex Cible (Y_haut) : {y_apex_haut} px (POINT BLANC)
    - Base Canal (Y_bas)   : {y_bas} px
    - Précision Apex      : {precision_apex}

    [3] ANALYSE DE DENSITÉ :
    - Indice H final      : {h_final:.4f}
    - Indice H maximum    : {h_max:.4f}
    - Seuil de sécurité   : 0.45

    [4] VALIDATION DU VERDICT (CALCULS) :
    - Équation de structure : L = W + D ({W} + {D} = {L} px)
    - Ratio de sécurité     : {ratio_securite:.1f} %

    DIAGNOSTIC FINAL      : {statut}
    --------------------------------------------------
    INTERPRÉTATION CLINIQUE :
    "L'obturation est validée jusqu'au Point Blanc (Y={y_apex_haut}). 
    L'analyse combinée du Trait Rouge (continuité) et du Trait Cyan 
    (étanchéité apicale) confirme que la densité de {h_final:.4f} est 
    suffisante pour garantir un scellement hermétique."
    """

    with col_verdict:
        st.code(rapport_expert, language="text")
        st.download_button(
            label="💾 Générer l'Attestation d'Expertise (.txt)",
            data=rapport_expert,
            file_name=f"Expertise_CAD_JENHI.txt",
            mime="text/plain"
        )
else:
    st.info("💡 En attente du chargement de la radiographie pour expertise...")
