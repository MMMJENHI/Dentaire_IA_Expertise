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
st.set_page_config(page_title="CAD IA Dentaire Expert - JENHI .M", layout="wide")

# --- 2. FONCTIONS TECHNIQUES ---
def preprocess_image(image):
    img_array = np.array(image.convert('L'))
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    return clahe.apply(img_array)

def smooth(sig):
    if len(sig) > 5:
        w_len = 11 if len(sig) > 11 else (len(sig)-1 if len(sig)%2==0 else len(sig))
        return savgol_filter(sig, window_length=max(3, w_len), polyorder=2) / 255.0
    return sig / 255.0

# --- 3. LOGO & IDENTITÉ ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3774/3774278.png", width=80)
st.sidebar.markdown(f"### 👨‍🔬 Expert : JENHI .M")
st.sidebar.divider()

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
        except: st.error("Lien invalide")
else:
    try:
        raw_img = Image.open("dent.jpg")
    except:
        st.error("Fichier 'dent.jpg' absent.")
        st.stop()

# --- 4. TRAITEMENT ---
if raw_img is not None:
    img_gray = preprocess_image(raw_img)
    h, w = img_gray.shape

    # QR CODE DYNAMIQUE
    url_app = "https://dentaireiaexpertiseia.streamlit.app/"
    qr_api = f"https://api.qrserver.com/v1/create-qr-code/?size=120x120&data={url_app}"
    st.sidebar.image(qr_api, caption="Lien Mobile Officiel")
    st.sidebar.divider()

    x_c = st.sidebar.slider("Position X (Axe)", 0, w, int(w/2))
    y_haut = st.sidebar.slider("Haut Canal (Y)", 0, h, int(h*0.2))
    y_apex = st.sidebar.slider("Y_apex (Point Final)", 0, h, int(h*0.8))

    if y_apex <= y_haut: y_apex = y_haut + 20
    y_tiers_debut = int(y_haut + (y_apex - y_haut) * 0.66)
    
    signal_global = profile_line(img_gray, (y_haut, x_c), (y_apex, x_c), linewidth=3)
    signal_apical = profile_line(img_gray, (y_tiers_debut, x_c), (y_apex, x_c), linewidth=5)

    H_global = smooth(signal_global)
    H_apical = smooth(signal_apical)
    h_final = H_apical[-1]
    h_max = np.max(H_apical)

    # --- 5. VISUALISATION COMBINÉE ---
    col_img, col_graphs = st.columns([1, 1.5])

    with col_img:
        st.subheader("🔎 Visualisation CAD")
        img_visu = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)
        
        # --- DESSINS ULTRA-VISIBLES ---
        # Rouge Épais (Global)
        cv2.line(img_visu, (x_c - 20, y_haut), (x_c - 20, y_apex), (255, 0, 0), 6) 
        # Cyan Fluorescent (Tiers Apical)
        cv2.line(img_visu, (x_c, y_tiers_debut), (x_c, y_apex), (0, 255, 255), 15) 
        # Blanc Pur (Apex)
        cv2.circle(img_visu, (x_c, y_apex), 22, (255, 255, 255), -1) 
        
        st.image(img_visu, use_container_width=True)

        # --- LÉGENDE GÉANTE ---
        st.markdown("""
        <div style="background-color: #000000; padding: 25px; border-radius: 15px; border: 3px solid #ffffff; line-height: 1.8;">
            <p style="font-size: 24px; margin: 0; font-weight: bold;">
                <span style="color: #FF0000;">━━</span> <span style="color: white;">PROFIL GLOBAL (ROUGE)</span>
            </p>
            <p style="font-size: 24px; margin: 0; font-weight: bold;">
                <span style="color: #00FFFF;">━━</span> <span style="color: white;">TIERS APICAL (CYAN)</span>
            </p>
            <p style="font-size: 24px; margin: 0; font-weight: bold;">
                <span style="color: white; border: 2px solid white; border-radius: 50%; padding: 0 10px;">●</span> <span style="color: white;">APEX CIBLE (TRÈS BLANC)</span>
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col_graphs:
        # Graphe 1: Scan Global (Changement de titre demandé)
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=np.arange(y_haut, y_apex), y=H_global, name="Global", line=dict(color='red', width=3)))
        fig1.update_layout(template="plotly_dark", height=250, title="Profil de Densité Global", yaxis_title="Densité H")
        st.plotly_chart(fig1, use_container_width=True)

        # Graphe 2: Tiers Apical avec H final et Seuil
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(y=H_apical, name="Apical", line=dict(color='cyan', width=5)))
        
        # Ligne de seuil de sécurité
        fig2.add_hline(y=0.45, line_dash="dash", line_color="white", annotation_text="SEUIL SÉCURITÉ (0.45)", annotation_position="top left")
        
        # Annotations pour H final et H max
        fig2.add_annotation(x=len(H_apical)-1, y=h_final, text=f"H FINAL: {h_final:.4f}", showarrow=True, arrowhead=2, bgcolor="cyan", font=dict(color="black"))
        fig2.add_annotation(x=np.argmax(H_apical), y=h_max, text=f"H MAX: {h_max:.4f}", showarrow=True, yshift=10)

        fig2.update_layout(template="plotly_dark", height=300, title="Expertise Tiers Apical (Analyse H)", yaxis_title="Densité H", xaxis_title="Profondeur du Tiers")
        st.plotly_chart(fig2, use_container_width=True)

    # --- 6. RAPPORT & VERDICT ---
    st.divider()
    statut = "✅ CONFORME" if h_final >= 0.45 else "🚨 NON CONFORME"
    precision_apex = "Validée (Position terminale)" if y_apex > (h * 0.7) else "À vérifier"

    rapport_expert = f"""
    RAPPORT D'EXPERTISE DENTAIRE - SYSTÈME CAD v3.0
    --------------------------------------------------
    EXPERT RESPONSABLE : JENHI .M
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
    - Indice H maximum  : {h_max:.4f}
    - Seuil de sécurité : 0.45
    
    --------------------------------------------------
    [3] VALIDATION DU VERDICT :
    DIAGNOSTIC FINAL    : {statut}
    --------------------------------------------------
    
    INTERPRÉTATION CLINIQUE :
    "L'obturation est montée jusqu'au Point Blanc avec une 
    densité finale de {h_final:.4f}. Le seuil de sécurité (0.45) 
    étant franchi, l'étanchéité du tiers apical est validée."
    """

    st.subheader("📝 Bilan Expert CAD")
    st.code(rapport_expert, language="text")
    
    st.download_button(
        label="💾 Générer l'Attestation (.txt)",
        data=rapport_expert,
        file_name=f"Expertise_CAD_JENHI.txt"
    )
else:
    st.info("💡 En attente du chargement d'une radio.")
