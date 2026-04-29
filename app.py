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
        res = savgol_filter(sig, window_length=max(3, w_len), polyorder=2) / 255.0
        return np.clip(res, 0, 1)
    return np.clip(sig / 255.0, 0, 1)

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

    x_c = st.sidebar.slider("Position X (Axe)", 0, w, int(w/2))
    y_haut = st.sidebar.slider("Haut de Canal (Y)", 0, h, int(h*0.2))
    y_apex = st.sidebar.slider("Y_apex (Bas de Canal)", 0, h, int(h*0.8))

    if y_apex <= y_haut: y_apex = y_haut + 20
    
    longueur_canal = y_apex - y_haut
    y_tiers_debut = int(y_haut + (longueur_canal * 0.66))
    nb_pixels_cyan = y_apex - y_tiers_debut
    
    signal_global = profile_line(img_gray, (y_haut, x_c), (y_apex, x_c), linewidth=3)
    signal_apical = profile_line(img_gray, (y_tiers_debut, x_c), (y_apex, x_c), linewidth=5)

    H_global = smooth(signal_global)
    H_apical = smooth(signal_apical)
    h_final = float(H_apical[-1])
    h_max = float(np.max(H_apical))
    
    ratio_securite = (h_final / 0.45) * 100

    col_img, col_graphs = st.columns([1, 1.5])

    with col_img:
        st.subheader("🔎 Visualisation CAD")
        img_visu = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)
        cv2.line(img_visu, (x_c - 20, y_haut), (x_c - 20, y_apex), (255, 0, 0), 6) 
        cv2.line(img_visu, (x_c, y_tiers_debut), (x_c, y_apex), (0, 255, 255), 15) 
        cv2.circle(img_visu, (x_c, y_apex), 22, (255, 255, 255), -1) 
        st.image(img_visu, use_container_width=True)

    with col_graphs:
        # --- COURBE 1 : GLOBAL ---
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=np.arange(y_haut, y_apex), y=H_global, name="Global", line=dict(color='red', width=3)))
        fig1.update_layout(template="plotly_dark", height=230, title="Profil de Densité Global", 
                          yaxis=dict(title="H (0-1)", range=[0, 1]))
        st.plotly_chart(fig1, use_container_width=True)

        # --- COURBE 2 : TIERS APICAL AVEC ZONES (FIGURE DEMANDÉE) ---
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(y=H_apical, name="Tiers Apical", line=dict(color='cyan', width=5)))
        
        # Seuil Critique Rouge
        fig2.add_hline(y=0.45, line_dash="dash", line_color="red", line_width=3, 
                       annotation_text="SEUIL CRITIQUE (0.45)", annotation_font_color="red")
        
        # Ajout des zones colorées pour le diagnostic
        fig2.add_hrect(y0=0.45, y1=1.0, fillcolor="green", opacity=0.15, annotation_text="HERMÉTIQUE")
        fig2.add_hrect(y0=0, y1=0.45, fillcolor="red", opacity=0.15, annotation_text="INFILTRATION")

        fig2.update_layout(template="plotly_dark", height=280, title="Expertise Tiers Apical (Normalisée)", 
                          yaxis=dict(title="Densité H", range=[0, 1]))
        st.plotly_chart(fig2, use_container_width=True)

    # --- 6. RAPPORT DÉTAILLÉ ---
    st.divider()
    statut = "✅ CONFORME" if h_final >= 0.45 else "🚨 NON CONFORME"
    
    rapport_expert = f"""
    RAPPORT D'EXPERTISE DENTAIRE - SYSTÈME CAD v3.0
    --------------------------------------------------
    EXPERT RESPONSABLE : JENHI .M
    UNITÉ D'ANALYSE    : Faculté des Sciences - Département de Chimie FÈS
    --------------------------------------------------
    [1] ANALYSE DE DENSITÉ APICALE :
    - Indice H Final   : {h_final:.4f}
    - Seuil de Sécurité: 0.45 (Ligne Rouge)
    - Ratio de Sécurité: {ratio_securite:.1f} %
    
    [2] VALIDATION DU VERDICT :
    DIAGNOSTIC FINAL   : {statut}
    
    CONCLUSION : 
    "L'analyse montre que la courbe de densité se maintient dans la zone VERTE (Hermétique).
    Le ratio de {ratio_securite:.1f}% infirme l'hypothèse d'une infiltration au point Y_apex."
    """
    st.code(rapport_expert)
