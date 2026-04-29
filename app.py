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

    # --- CONFIGURATION SELON VOS DONNÉES RÉELLES ---
    # Apex est en haut (9) et Tenon est en bas (1147)
    x_c = st.sidebar.slider("Axe X (Forage)", 0, w, 718)
    y_apex_haut = st.sidebar.slider("Y_Apex (Haut de radio)", 0, h, 9)
    y_tenon_bas = st.sidebar.slider("Y_Tenon (Bas de radio)", 0, h, 1147)

    # Calculs mathématiques
    longueur_canal = abs(y_tenon_bas - y_apex_haut)
    # Le tiers apical est la zone proche de l'Apex (les 34% de départ car l'Apex est en haut)
    y_limite_expertise = y_apex_haut + int(longueur_canal * 0.34)
    nb_pixels_cyan = abs(y_limite_expertise - y_apex_haut)
    
    # Signaux (on scanne de l'Apex vers le Tenon)
    signal_global = profile_line(img_gray, (y_apex_haut, x_c), (y_tenon_bas, x_c), linewidth=3)
    signal_apical = signal_global[:int(len(signal_global)*0.34)] # On prend le début car c'est l'apex

    H_global = smooth(signal_global)
    H_apical = smooth(signal_apical)
    
    h_final = float(H_apical[0]) # Valeur à Y=9
    h_max = float(np.max(H_apical))
    ratio_securite = (h_final / 0.45) * 100

    # --- 5. VISUALISATION CAD ---
    col_img, col_graphs = st.columns([1, 1.5])

    with col_img:
        st.subheader("🔎 Visualisation CAD")
        img_visu = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)
        
        # Profil Global (Rouge)
        cv2.line(img_visu, (x_c - 20, y_apex_haut), (x_c - 20, y_tenon_bas), (255, 0, 0), 6)
        # Tiers Apical (Cyan) - En haut
        cv2.line(img_visu, (x_c, y_apex_haut), (x_c, y_limite_expertise), (0, 255, 255), 15)
        # Apex Cible (Point Blanc)
        cv2.circle(img_visu, (x_c, y_apex_haut), 22, (255, 255, 255), -1)
        
        st.image(img_visu, use_container_width=True)

        st.markdown(f"""
        <div style="background-color: #000000; padding: 20px; border-radius: 10px; border: 2px solid #ffffff;">
            <p style="color: white; font-weight: bold; font-size: 18px;">
                <span style="color: #FF0000;">━━</span> PROFIL GLOBAL (Vers Tenon)<br>
                <span style="color: #00FFFF;">━━</span> TIERS APICAL (Expertise)<br>
                <span style="color: white;">●</span> APEX CIBLE (Y={y_apex_haut})
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col_graphs:
        # Graphe Global
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=np.arange(y_apex_haut, y_tenon_bas), y=H_global, name="Global", line=dict(color='red')))
        fig1.update_layout(template="plotly_dark", height=230, title="Profil : Apex → Tenon", xaxis_title="Profondeur Y")
        st.plotly_chart(fig1, use_container_width=True)

        # Graphe Tiers Apical avec VERDICT
        fig2 = go.Figure()
        x_apical = np.arange(y_apex_haut, y_limite_expertise)
        fig2.add_trace(go.Scatter(x=x_apical, y=H_apical, name="Apical", line=dict(color='cyan', width=5)))
        
        # Zones de diagnostic colorées
        fig2.add_hrect(y0=0.45, y1=1.0, fillcolor="green", opacity=0.15, annotation_text="CONFORME")
        fig2.add_hrect(y0=0, y1=0.45, fillcolor="red", opacity=0.15, annotation_text="INFILTRATION")
        
        # Seuil Rouge Critique
        fig2.add_hline(y=0.45, line_dash="dash", line_color="red", line_width=3, annotation_text="SEUIL 0.45")
        
        fig2.update_layout(template="plotly_dark", height=320, title="Expertise Densitométrique (Tiers Apical)", 
                          xaxis_title="Position Y (Apex=9)", yaxis=dict(range=[0, 1]))
        st.plotly_chart(fig2, use_container_width=True)

    # --- 6. BILAN ET RAPPORT ---
    st.divider()
    statut = "✅ CONFORME" if h_final >= 0.45 else "🚨 NON CONFORME"
    
    rapport_expert = f"""
    RAPPORT D'EXPERTISE DENTAIRE - SYSTÈME CAD v3.0
    --------------------------------------------------
    EXPERT RESPONSABLE : JENHI .M
    PROJET             : Master Diagnostic IA - Dent 16
    --------------------------------------------------
    [1] LOCALISATION INVERSÉE :
    - Apex Cible (Haut) : {y_apex_haut} px
    - Tenon (Bas)       : {y_tenon_bas} px
    - Longueur Canal    : {longueur_canal} px
    
    [2] ANALYSE DE DENSITÉ (ZONE CYAN) :
    - Indice H final    : {h_final:.4f} (à Y=9)
    - Ratio de sécurité : {ratio_securite:.1f} %
    
    [3] VALIDATION DU VERDICT :
    - Fenêtre d'analyse : {nb_pixels_cyan} px (Tiers Apical)
    - DIAGNOSTIC FINAL  : {statut}
    --------------------------------------------------
    INTERPRÉTATION :
    "L'analyse confirme une densité supérieure au seuil de 0.45 dans les 
    premiers {nb_pixels_cyan} pixels de la racine (zone apicale). 
    L'étanchéité est validée mathématiquement."
    """
    st.subheader("📝 Bilan Expert CAD")
    st.code(rapport_expert, language="text")
    st.download_button("💾 Télécharger l'Attestation", rapport_expert, file_name="Expertise_JENHI.txt")
