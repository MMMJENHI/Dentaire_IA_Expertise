import streamlit as st
import requests
import numpy as np
import cv2
import plotly.graph_objects as go
from PIL import Image
from io import BytesIO
from skimage.measure import profile_line
from scipy.signal import savgol_filter
import time

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="IA Expertise Dentaire - Master", layout="wide")

# --- FONCTIONS TECHNIQUES ---
def preprocess_image(image):
    """Amélioration du contraste pour une analyse précise"""
    img_array = np.array(image.convert('L'))
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    return clahe.apply(img_array)

@st.cache_data
def load_img_from_url(url):
    try:
        response = requests.get(url, timeout=5)
        return Image.open(BytesIO(response.content))
    except:
        return None

# --- INTERFACE UTILISATEUR ---
st.title("🦷 Système Expert : Analyse Interactive du Tiers Apical")
st.markdown("Contrôle manuel de la segmentation pour l'étude de la densité osseuse et radiculaire.")

# --- BARRE LATÉRALE ---
st.sidebar.header("📁 Importation de la Radio")
option = st.sidebar.selectbox("Source :", ("Depuis mon PC (Local)", "Lien GitHub (Raw)", "Lien Web"))

raw_img = None
if option == "Depuis mon PC (Local)":
    uploaded_file = st.sidebar.file_uploader("Fichier image...", type=['jpg', 'jpeg', 'png'])
    if uploaded_file: raw_img = Image.open(uploaded_file)
elif option == "Lien GitHub (Raw)":
    github_url = st.sidebar.text_input("URL :", "https://raw.githubusercontent.com/MMMJENHI/Dentaire_IA_Expertise/main/dent.jpg")
    if github_url: raw_img = load_img_from_url(github_url)
else:
    web_url = st.sidebar.text_input("Lien direct :")
    if web_url: raw_img = load_img_from_url(web_url)

if raw_img is not None:
    img_gray = preprocess_image(raw_img)
    h_img, w_img = img_gray.shape

    st.sidebar.divider()
    st.sidebar.header("📍 Contrôle des Axes (Manuel)")
    
    # Sliders de positionnement - CONTRÔLE TOTAL
    x_input = st.sidebar.slider("Position X (Axe de la dent)", 0, w_img, int(w_img/2))
    y_top_canal = st.sidebar.slider("Haut du Canal (Y)", 0, h_img, int(h_img*0.2))
    y_apex_point = st.sidebar.slider("Point Apex (Y)", 0, h_img, int(h_img*0.8))

    # --- ÉTAPE 1 : ISOLATION DU TIERS APICAL (Calcul de la zone Cyan) ---
    # On définit le début du tiers apical à 66% de la hauteur totale choisie
    y_start_tiers = int(y_top_canal + (y_apex_point - y_top_canal) * 0.66)
    
    # --- ÉTAPE 2 : CALCUL DE LA VARIABLE H ---
    # Le scan suit EXACTEMENT x_input choisi par l'utilisateur
    signal = profile_line(img_gray, (y_start_tiers, x_input), (y_apex_point, x_input), linewidth=8)
    
    if len(signal) > 5:
        # Lissage pour éviter les micro-bruit de l'image
        w_len = 11 if len(signal) > 11 else (len(signal)-1 if len(signal)%2==0 else len(signal))
        signal_smooth = savgol_filter(signal, window_length=max(3, w_len), polyorder=2)
        H_values = signal_smooth / 255.0
        h_apex_final = np.mean(H_values[-10:]) # Moyenne sur les derniers millimètres
    else:
        H_values = np.array([0.0])
        h_apex_final = 0.0

    # --- AFFICHAGE DES RÉSULTATS ---
    col1, col2 = st.columns([1, 1.2])

    with col1:
        st.subheader("🔎 Visualisation Anatomique")
        img_rgb = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)
        
        # 1. Dessin de l'axe supérieur (Gris discret)
        cv2.line(img_rgb, (x_input, y_top_canal), (x_input, y_start_tiers), (100, 100, 100), 2)
        
        # 2. COLORATION DU TIERS APICAL (Cyan - Suit le curseur X)
        cv2.line(img_rgb, (x_input, y_start_tiers), (x_input, y_apex_point), (0, 255, 255), 10)
        
        # 3. COLORATION DE L'APEX (Vert si Sain, Rouge si Patho)
        color_status = (0, 255, 0) if h_apex_final >= 0.45 else (255, 0, 0)
        cv2.circle(img_rgb, (x_input, y_apex_point), 25, color_status, -1)
        
        st.image(img_rgb, use_container_width=True, caption=f"Position X actuelle : {x_input}")

    with col2:
        st.subheader("📈 Courbe de Densité Clinique")
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=H_values, mode='lines', line=dict(color='#00fbff', width=5), name="Signal H"))
        
        # Seuil de pathologie
        fig.add_hline(y=0.45, line_dash="dash", line_color="red", annotation_text="Seuil (0.45)")
        fig.add_hrect(y0=0, y1=0.45, fillcolor="red", opacity=0.15)
        
        fig.update_layout(template="plotly_dark", height=400, yaxis_title="Densité H", xaxis_title="Profondeur Tiers Apical")
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    
    # --- GÉNÉRATION DU RAPPORT ---
    if st.button("🚀 GÉNÉRER L'EXPERTISE FINALE"):
        with st.spinner('Analyse en cours...'):
            time.sleep(1)
            status = "✅ SAIN (CONFORME)" if h_apex_final >= 0.45 else "🚨 PATHOLOGIQUE (NON CONFORME)"
            color_res = st.success if h_apex_final >= 0.45 else st.error
            
            color_res(f"## {status}")
            
            rapport = f"""
            RAPPORT D'EXPERTISE DENTAIRE
            ------------------------------------------
            DENT : Dent 16 | AXE X : {x_input}
            ZONE : Tiers Apical (Isolé en Cyan)
            VALEUR H APEX : {h_apex_final:.2f}
            ------------------------------------------
            CONCLUSION : {"Étanchéité confirmée" if h_apex_final >= 0.45 else "Détection de zone lacunaire / Lésion"}
            """
            st.code(rapport)
            st.download_button("📥 Télécharger Rapport", rapport, file_name="expertise.txt")

    st.info("### 📘 Note pour la Soutenance")
    st.write(f"""
    L'utilisateur déplace manuellement le trait pour sonder la matrice. 
    Dès que le trait sort de la racine (zone blanche) pour aller dans l'os (zone sombre), 
    la valeur **H** chute sous **0.45**, prouvant la précision du système de détection.
    """)
else:
    st.info("💡 En attente du chargement de la radio...")
