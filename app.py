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
        return savgol_filter(sig, window_length=max(3, w_len), polyorder=2) / 255.0
    return sig / 255.0

# --- 3. IDENTITÉ ET LOGO (SIDEBAR) ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3774/3774278.png", width=70)
st.sidebar.markdown(f"## JENHI .M")
st.sidebar.info("Expert Master IA Dentaire")
st.sidebar.divider()

# --- 4. CHARGEMENT ---
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
        except: st.error("Erreur de lien")
else:
    try:
        raw_img = Image.open("dent.jpg")
    except:
        st.warning("Mode démo : Image 'dent.jpg' manquante.")

# --- 5. ANALYSE ET PARAMÈTRES ---
if raw_img is not None:
    img_gray = preprocess_image(raw_img)
    h, w = img_gray.shape

    # QR CODE DYNAMIQUE
    url_app = "https://dentaireiaexpertiseia.streamlit.app/"
    qr_api = f"https://api.qrserver.com/v1/create-qr-code/?size=100x100&data={url_app}"
    st.sidebar.image(qr_api, caption="Lien de l'Application")

    st.sidebar.header("📍 Paramètres CAD")
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

    col_img, col_graphs = st.columns([1, 1.5])

    with col_img:
        st.subheader("🔎 Visualisation CAD")
        img_visu = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)
        
        # Superposition des axes
        cv2.line(img_visu, (x_c - 15, y_haut), (x_c - 15, y_apex), (255, 0, 0), 3) # Rouge
        cv2.line(img_visu, (x_c, y_tiers_debut), (x_c, y_apex), (0, 255, 255), 10) # Cyan
        cv2.circle(img_visu, (x_c, y_apex), 15, (255, 255, 255), -1) # Blanc
        
        st.image(img_visu, use_container_width=True)
        
        # --- LÉGENDE NETTE (HTML/MARKDOWN) ---
        st.info("""
        **LÉGENDE D'ANALYSE :**
        - 🟥 **Tracé Rouge :** Profil global de l'obturation.
        - 🟦 **Zone Cyan :** Tiers apical (Analyse de densité).
        - ⚪ **Point Blanc :** Apex (Cible terminale).
        """)

    with col_graphs:
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=np.arange(y_haut, y_apex), y=H_global, name="Scan Global", line=dict(color='red', width=3)))
        fig1.update_layout(template="plotly_dark", height=230, title="Distribution : Canal Complet", yaxis_title="Densité H")
        st.plotly_chart(fig1, use_container_width=True)

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(y=H_apical, name="Tiers Apical", line=dict(color='cyan', width=5)))
        fig2.add_shape(type="line", x0=0, y0=0.45, x1=len(H_apical), y1=0.45, line=dict(color="white", dash="dash"))
        fig2.update_layout(template="plotly_dark", height=230, title="Expertise : Zone Cyan (Seuil 0.45)", yaxis_title="Densité H")
        st.plotly_chart(fig2, use_container_width=True)

    # --- 6. VERDICT ET RAPPORT ---
    st.divider()
    statut = "✅ CONFORME (HERMÉTIQUE)" if h_final >= 0.45 else "🚨 NON CONFORME (FUITE)"
    
    st.markdown(f"### Verdict : {statut}")
    
    rapport_expert = f"""
    RAPPORT D'EXPERTISE DENTAIRE - SYSTÈME CAD v3.0
    --------------------------------------------------
    EXPERT RESPONSABLE : JENHI .M
    RESULTAT           : {statut}
    INDICE H FINAL     : {h_final:.4f} (Seuil : 0.45)
    --------------------------------------------------
    """
    st.code(rapport_expert, language="text")
    
    st.download_button(
        label="💾 Télécharger le Rapport .txt",
        data=rapport_expert,
        file_name="Expertise_JENHI.txt"
    )
else:
    st.info("💡 En attente du chargement d'une radio.")
