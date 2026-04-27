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
    """Amélioration du contraste pour mieux voir l'apex"""
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

def auto_center_x(image, x_user, y_target, margin=20):
    """Ajuste X pour trouver le centre de la racine (évite l'espace interdentaire)"""
    try:
        x_start = max(0, x_user - margin)
        x_end = min(image.shape[1], x_user + margin)
        line_sample = image[y_target, x_start:x_end]
        # On cherche le pic de blancheur (la dent ou la gutta-percha)
        best_x_offset = np.argmax(line_sample)
        return x_start + best_x_offset
    except:
        return x_user

# --- INTERFACE UTILISATEUR ---
st.title("🦷 Système Expert : Analyse du Tiers Apical (Dent 16)")
st.markdown("Isolation anatomique parallèle à l'axe radiculaire et diagnostic de densité matricielle.")

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
    st.sidebar.header("📍 Segmentation & Axes")
    
    # Sliders de positionnement
    x_input = st.sidebar.slider("Axe X (Approximatif)", 0, w_img, int(w_img/2))
    y_top_canal = st.sidebar.slider("Haut du Canal (Y)", 0, h_img, int(h_img*0.2))
    y_apex_point = st.sidebar.slider("Point Apex (Y)", 0, h_img, int(h_img*0.8))

    # --- ÉTAPE 1 : RECENTRAGE DYNAMIQUE (IA) ---
    # On recentre en haut ET en bas pour créer une ligne oblique parfaite
    x_top = auto_center_x(img_gray, x_input, y_top_canal)
    x_apex = auto_center_x(img_gray, x_input, y_apex_point)
    
    # --- ÉTAPE 2 : ISOLATION DU TIERS APICAL (33% terminaux) ---
    y_start_tiers = int(y_top_canal + (y_apex_point - y_top_canal) * 0.66)
    # On calcule le X correspondant au début du tiers apical (interpolation)
    x_start_tiers = int(x_top + (x_apex - x_top) * 0.66)

    # --- ÉTAPE 3 : CALCUL DE LA VARIABLE H ---
    # Scan oblique entre le début du tiers et l'apex
    signal = profile_line(img_gray, (y_start_tiers, x_start_tiers), (y_apex_point, x_apex), linewidth=8)
    
    if len(signal) > 5:
        # Lissage de la courbe
        w_len = 11 if len(signal) > 11 else (len(signal)-1 if len(signal)%2==0 else len(signal))
        signal_smooth = savgol_filter(signal, window_length=max(3, w_len), polyorder=2)
        H_values = signal_smooth / 255.0
        h_apex_final = np.mean(H_values[-10:]) # Moyenne sur les derniers pixels de l'apex
    else:
        H_values = np.array([0.0])
        h_apex_final = 0.0

    # --- AFFICHAGE DES RÉSULTATS ---
    col1, col2 = st.columns([1, 1.2])

    with col1:
        st.subheader("🔎 Visualisation Anatomique")
        img_rgb = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)
        
        # Dessin de l'axe complet (Pointillé Gris)
        cv2.line(img_rgb, (x_top, y_top_canal), (x_start_tiers, y_start_tiers), (100, 100, 100), 2)
        
        # Dessin du TIERS APICAL (Ligne Cyan Épaisse)
        cv2.line(img_rgb, (x_start_tiers, y_start_tiers), (x_apex, y_apex_point), (0, 255, 255), 10)
        
        # Dessin de l'APEX (Cercle de statut)
        color_status = (0, 255, 0) if h_apex_final >= 0.45 else (255, 0, 0)
        cv2.circle(img_rgb, (x_apex, y_apex_point), 25, color_status, -1)
        
        st.image(img_rgb, use_container_width=True, caption=f"Segmentation oblique active | Axe X Apex : {x_apex}")

    with col2:
        st.subheader("📈 Profil de Densité H")
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=H_values, mode='lines', line=dict(color='#00fbff', width=5), name="Densité H"))
        
        # Zone de seuil
        fig.add_hline(y=0.45, line_dash="dash", line_color="red", annotation_text="SEUIL DE PATHOLOGIE")
        fig.add_hrect(y0=0, y1=0.45, fillcolor="red", opacity=0.15)
        
        fig.update_layout(template="plotly_dark", height=400, yaxis_title="Valeur H (0-1)", xaxis_title="Profondeur Tiers Apical")
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    
    # --- GÉNÉRATION DU RAPPORT ---
    if st.button("🚀 LANCER L'EXPERTISE FINALE"):
        with st.spinner('Analyse matricielle du tiers apical...'):
            time.sleep(1)
            status = "✅ SAIN (CONFORME)" if h_apex_final >= 0.45 else "🚨 PATHOLOGIQUE (NON CONFORME)"
            color_res = st.success if h_apex_final >= 0.45 else st.error
            
            color_res(f"## {status}")
            
            rapport = f"""
            RAPPORT D'EXPERTISE DENTAIRE (CAD SYSTEM)
            ------------------------------------------
            DENT ANALYSÉE : Dent 16 (Molaire Sup.)
            ZONE ISOLÉE : Tiers Apical (Segmentation Oblique)
            AXE X RECENTRÉ : {x_apex} (Correction Auto)
            FENÊTRE Y : {y_start_tiers} ➔ {y_apex_point}
            ------------------------------------------
            VALEUR H APEX : {h_apex_final:.2f}
            SEUIL CRITIQUE : 0.45
            ------------------------------------------
            CONCLUSION : {"Étanchéité optimale" if h_apex_final >= 0.45 else "Rupture d'étanchéité / Lésion détectée"}
            """
            st.code(rapport)
            st.download_button("📥 Télécharger le rapport", rapport, file_name="expertise_dent16.txt")

    # --- NOTE POUR LE JURY ---
    st.info("### 📘 Méthodologie de Master")
    st.write(f"""
    1. **Localisation :** Le système a détecté l'axe de la racine à **{x_apex}** pixels.
    2. **Isolation :** Analyse exclusive des derniers 33% de la racine (Tiers Apical).
    3. **Expertise :** Comparaison de la valeur H finale au seuil de **0.45**. 
       Une valeur de **{h_apex_final:.2f}** a été trouvée.
    """)
else:
    st.info("💡 En attente d'une radio RVG sur le PC TOSHIBA...")
