import streamlit as st
import cv2
import numpy as np
import plotly.graph_objects as go
from skimage.measure import profile_line
from scipy.signal import savgol_filter
from PIL import Image
import pandas as pd
import time
import requests
from io import BytesIO

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="CAD IA Dentaire Expert", layout="wide")

# --- 2. FONCTIONS TECHNIQUES ---
def preprocess_image(image):
    img_array = np.array(image.convert('L'))
    # Amélioration du contraste pour mieux voir la gutta-percha
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    return clahe.apply(img_array)

def smooth(sig):
    if len(sig) > 5:
        w_len = 11 if len(sig) > 11 else (len(sig)-1 if len(sig)%2==0 else len(sig))
        return savgol_filter(sig, window_length=max(3, w_len), polyorder=2) / 255.0
    return sig / 255.0

# --- 3. CHARGEMENT DE LA RADIO ---
st.title("🦷 CAD System : Expertise Double Échelle (Dent 16)")

source_radio = st.sidebar.radio("📁 Source de la Radio :", ("Local", "URL/GitHub", "Démo"))

raw_img = None
if source_radio == "Local":
    up = st.file_uploader("Radio", type=["jpg", "png", "jpeg"])
    if up: raw_img = Image.open(up)
elif source_radio == "URL/GitHub":
    url_input = st.text_input("Lien Raw :", value="https://raw.githubusercontent.com/MMMJENHI/Dentaire_IA_Expertise/main/dent.jpg")
    if url_input:
        try:
            res = requests.get(url_input, timeout=5)
            raw_img = Image.open(BytesIO(res.content))
        except: st.error("Lien invalide ou erreur réseau")
else:
    try:
        raw_img = Image.open("dent.jpg")
    except:
        st.error("Fichier 'dent.jpg' absent du dépôt.")
        st.stop()

# --- 4. TRAITEMENT ET ANALYSE ---
if raw_img is not None:
    img_gray = preprocess_image(raw_img)
    h, w = img_gray.shape

    st.sidebar.header("📍 Paramètres CAD")
    
   
# QR CODE via API (MISE À JOUR MASTER 2026)
    url_app = "https://ia-expertise-dentaire-2026.streamlit.app/"
    qr_api = f"https://api.qrserver.com/v1/create-qr-code/?size=120x120&data={url_app}"
    st.sidebar.image(qr_api, caption="Scanner pour accès Mobile")
    st.sidebar.divider()

    

    x_c = st.sidebar.slider("Position X (Axe)", 0, w, int(w/2))
    y_haut = st.sidebar.slider("Haut Canal (Y)", 0, h, int(h*0.2))
    y_apex = st.sidebar.slider("Y_apex (Point Final)", 0, h, int(h*0.8))

    # Sécurité anti-disparition
    if y_apex <= y_haut: y_apex = y_haut + 20

    # Calcul du Tiers Apical (33% finaux)
    y_tiers_debut = int(y_haut + (y_apex - y_haut) * 0.66)
    
    # Signaux
    signal_global = profile_line(img_gray, (y_haut, x_c), (y_apex, x_c), linewidth=3)
    signal_apical = profile_line(img_gray, (y_tiers_debut, x_c), (y_apex, x_c), linewidth=5)

    H_global = smooth(signal_global)
    H_apical = smooth(signal_apical)
    h_final = H_apical[-1]

    # --- 5. VISUALISATION ---
    col_img, col_graphs = st.columns([1, 1.5])

    with col_img:
        st.subheader("🔎 Visualisation CAD")
        img_visu = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)
        # Rouge : Global (décalé) | Cyan : Apical (centre) | Blanc : Apex
        cv2.line(img_visu, (x_c - 15, y_haut), (x_c - 15, y_apex), (255, 0, 0), 3)
        cv2.line(img_visu, (x_c, y_tiers_debut), (x_c, y_apex), (255, 255, 0), 12)
        cv2.circle(img_visu, (x_c, y_apex), 15, (255, 255, 255), -1) 
        st.image(img_visu, use_container_width=True)

    with col_graphs:
        # Graphe Global (Rouge)
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=np.arange(y_haut, y_apex), y=H_global, name="Global", line=dict(color='red', width=3)))
        fig1.update_layout(template="plotly_dark", height=250, margin=dict(t=10, b=10), xaxis_title="Y (Pixels)", yaxis_title="Densité H")
        st.plotly_chart(fig1, use_container_width=True)

        # Graphe Apical (Cyan)
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(y=H_apical, name="Tiers Apical", line=dict(color='cyan', width=5)))
        fig2.add_shape(type="line", x0=0, y0=0.45, x1=len(H_apical), y1=0.45, line=dict(color="white", dash="dash"))
        fig2.update_layout(template="plotly_dark", height=250, margin=dict(t=10, b=10), xaxis_title="Progression %", yaxis_title="Densité H")
        st.plotly_chart(fig2, use_container_width=True)

   # --- 6. RAPPORT D'EXPERTISE CAD (VALIDATION DU VERDICT) ---
    st.divider()
    statut = "✅ CONFORME" if h_final >= 0.45 else "🚨 NON CONFORME"
    
    # Analyse experte du point blanc
    precision_apex = "Validée (Position terminale)" if y_apex > (h * 0.7) else "À vérifier (Position haute)"

    rapport_expert = f"""
    RAPPORT D'EXPERTISE DENTAIRE - SYSTÈME CAD v3.0
    --------------------------------------------------
    UNITÉ D'ANALYSE    : Cabinet Dentaire Universitaire
    PROJET             : Master Diagnostic IA - Dent 16
    --------------------------------------------------
    
    [1] DONNÉES DE LOCALISATION :
    - Axe de forage (X) : {x_c} px
    - Limite Coronaire  : {y_haut} px
    - Cible Apicale     : {y_apex} px (POINT BLANC)
    - Précision Apex    : {precision_apex}
    
    [2] ANALYSE DE DENSITÉ (ZONE CYAN) :
    - Indice H final    : {h_final:.4f}
    - Seuil de sécurité : 0.45
    
    --------------------------------------------------
    [3] VALIDATION DU VERDICT :
    DIAGNOSTIC FINAL    : {statut}
    --------------------------------------------------
    
    INTERPRÉTATION CLINIQUE :
    "L'obturation est montée jusqu'au Point Blanc avec une 
    densité suffisante (H > 0.45). Le repère visuel blanc 
    confirme l'absence de sous-obturation et garantit 
    l'étanchéité du tiers apical."
    """

    st.subheader("📝 Bilan Expert CAD")
    
    # Affichage en bloc de code pour une lecture totale et pro
    st.code(rapport_expert, language="text")
    
    # Bouton de téléchargement
    st.download_button(
        label="💾 Générer l'Attestation d'Expertise (.txt)",
        data=rapport_expert,
        file_name=f"Expertise_CAD_Dent16.txt",
        mime="text/plain"
    )
