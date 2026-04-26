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
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    return clahe.apply(img_array)

def smooth(sig):
    if len(sig) > 5:
        # Fenêtre de lissage dynamique selon la taille du signal
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
        st.error("Fichier 'dent.jpg' absent. Vérifiez votre dépôt GitHub.")
        st.stop()

# --- 4. TRAITEMENT ET ANALYSE ---
if raw_img is not None:
    img_gray = preprocess_image(raw_img)
    h, w = img_gray.shape

    # SIDEBAR : CONTRÔLES CAD
    st.sidebar.header("📍 Paramètres CAD")
    
    # QR CODE VIA API (Méthode stable Hugging Face / GitHub)
    url_app = "https://dentaireiaexpertise-eg4mdsd9cguhyhc4idk7rn.streamlit.app/"
    qr_api = f"https://api.qrserver.com/v1/create-qr-code/?size=120x120&data={url_app}"
    st.sidebar.image(qr_api, caption="Lien de l'application")
    st.sidebar.divider()

    x_c = st.sidebar.slider("Position X (Axe)", 0, w, int(w/2))
    y_haut = st.sidebar.slider("Haut Canal (Y)", 0, h, int(h*0.2))
    y_apex = st.sidebar.slider("Y_apex (Point Final)", 0, h, int(h*0.8))

    # --- SÉCURITÉ ANTI-DISPARITION ---
    # Si l'Apex est au-dessus du haut, on force un segment de 20 pixels
    if y_apex <= y_haut:
        y_apex = y_haut + 20
        st.sidebar.warning("⚠️ Ajustement automatique : l'Apex a été placé sous le Haut Canal.")

    # Calcul dynamique du Tiers Apical (les derniers 33% du segment choisi)
    y_tiers_debut = int(y_haut + (y_apex - y_haut) * 0.66)
    
    # Extraction des profils de densité
    signal_global = profile_line(img_gray, (y_haut, x_c), (y_apex, x_c), linewidth=3)
    signal_apical = profile_line(img_gray, (y_tiers_debut, x_c), (y_apex, x_c), linewidth=5)

    H_global = smooth(signal_global)
    H_apical = smooth(signal_apical)
    h_final = H_apical[-1]

    # --- 5. VISUALISATION (ROUGE & CYAN) ---
    col_img, col_graphs = st.columns([1, 1.5])

    with col_img:
        st.subheader("🔎 Visualisation CAD")
        img_visu = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)
        
        # A. Trait ROUGE (Global) : Décalé pour la visibilité
        cv2.line(img_visu, (x_c - 15, y_haut), (x_c - 15, y_apex), (255, 0, 0), 3)
        
        # B. Trait CYAN épais (Expertise) : Au centre de l'axe
        cv2.line(img_visu, (x_c, y_tiers_debut), (x_c, y_apex), (255, 255, 0), 15)
        
        # C. Point APEX (Blanc) : La cible anatomique
        cv2.circle(img_visu, (x_c, y_apex), 15, (255, 255, 255), -1) 
        
        st.image(img_visu, use_container_width=True, caption="Analyse : Rouge (Total) | Cyan (Tiers Apical)")

    with col_graphs:
        # GRAPHIQUE 1 : ROUGE (Profil Global)
        st.subheader("📈 1. Profil Global (Position Y réelle)")
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x=np.arange(y_haut, y_apex), 
            y=H_global, 
            name="Profil Complet", 
            line=dict(color='red', width=3)
        ))
        fig1.update_layout(template="plotly_dark", height=250, margin=dict(t=10, b=10),
                           xaxis_title="Pixels verticaux (Axe Y)", yaxis_title="Densité H")
        st.plotly_chart(fig1, use_container_width=True)

        # GRAPHIQUE 2 : CYAN (Zoom Diagnostic)
        st.subheader("📈 2. Tiers Apical (Expertise CAD)")
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(y=H_apical, name="Zone Critique", line=dict(color='cyan', width=5)))
        # Seuil de conformité à 0.45
        fig2.add_shape(type="line", x0=0, y0=0.45, x1=len(H_apical), y1=0.45, 
                       line=dict(color="white", dash="dash"))
        fig2.update_layout(template="plotly_dark", height=250, margin=dict(t=10, b=10),
                           xaxis_title="Progression dans le Tiers (%)", yaxis_title="Densité H")
        st.plotly_chart(fig2, use_container_width=True)

    # --- 6. RAPPORT D'EXPERTISE CAD ---
    st.divider()
    statut = "✅ CONFORME" if h_final >= 0.45 else "🚨 NON CONFORME"
    
    rapport_cad = f"""RAPPORT D'EXPERTISE DENTAIRE (CAD SYSTEM)
------------------------------------------
PROPRIÉTAIRE : Projet Master - Dent 16
POSITION ANALYSÉE : X={x_c} | Y={y_apex}
VALEUR H APEX MOYENNE : {h_final:.4f}
SEUIL DE CONFORMITÉ : 0.45
------------------------------------------
DIAGNOSTIC FINAL : {statut}
------------------------------------------
LÉGENDE TECHNIQUE :
- Rouge : Trajectoire canalaire globale.
- Cyan : Segment d'herméticité apicale.
- Point Blanc : Localisation de l'Apex.
"""
    st.text_area("Bilan Expert CAD", rapport_cad, height=200)
    
    st.download_button(
        label="💾 Télécharger le Rapport CAD (.txt)",
        data=rapport_cad,
        file_name=f"Rapport_CAD_Dent16.txt",
        mime="text/plain"
    )
