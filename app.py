import streamlit as st
import cv2
import numpy as np
import plotly.graph_objects as go
from skimage.measure import profile_line
from scipy.signal import savgol_filter
from PIL import Image
import pandas as pd
import time
import qrcode
import requests
from io import BytesIO

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="IA Expertise Dentaire", layout="wide")

# --- 2. FONCTIONS TECHNIQUES ---
def generer_qr_statique(url):
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf

def preprocess_image(image):
    img_array = np.array(image.convert('L'))
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    return clahe.apply(img_array)

# --- 3. INTERFACE DE CHARGEMENT ---
st.title("🦷 Système Expert : Analyse de la Dent 16")
st.markdown("Diagnostic automatisé du **Tiers Apical** et de l'herméticité.")

st.sidebar.header("📁 Source de la Radio")
source_radio = st.sidebar.radio(
    "Choisir la méthode :",
    ("Upload (Local)", "Lien URL / GitHub", "Mode Démo (dent.jpg)")
)

raw_img = None

if source_radio == "Upload (Local)":
    uploaded_file = st.file_uploader("Charger la radio", type=["jpg", "png", "jpeg"])
    if uploaded_file:
        raw_img = Image.open(uploaded_file)
elif source_radio == "Lien URL / GitHub":
    url_input = st.text_input("URL de l'image (Lien Raw GitHub) :", 
                              value="https://raw.githubusercontent.com/MMMJENHI/Dentaire_IA_Expertise/main/dent.jpg")
    if url_input:
        try:
            response = requests.get(url_input, timeout=10)
            raw_img = Image.open(BytesIO(response.content))
        except:
            st.error("Impossible de charger l'image via l'URL.")
else:
    try:
        raw_img = Image.open("dent.jpg")
    except FileNotFoundError:
        st.warning("Fichier 'dent.jpg' introuvable.")
        st.stop()

# --- 4. TRAITEMENT ET ANALYSE ---
if raw_img is not None:
    img_gray = preprocess_image(raw_img)
    h, w = img_gray.shape

    # Réglages Sidebar
    st.sidebar.markdown("---")
    st.sidebar.header("📍 Réglages de l'Expert")
    x_c = st.sidebar.slider("Position X (Centre Canal)", 0, w, int(w/2))
    y_haut = st.sidebar.slider("Haut du Canal (Y)", 0, h, int(h*0.2))
    y_apex = st.sidebar.slider("Position de l'Apex (Tache Rouge)", 0, h, int(h*0.8))

    # QR Code Interactif
    st.sidebar.markdown("---")
    url_app = "https://dentaireiaexpertise-eg4mdsd9cguhyhc4idk7rn.streamlit.app/"
    qr_img = generer_qr_statique(url_app)
    st.sidebar.image(qr_img, caption="Expertise Mobile", width=150)

    # Calcul du tiers apical
    y_tiers_apical = int(y_haut + (y_apex - y_haut) * 0.66)

    # --- 5. VISUALISATION ET COURBE ---
    col1, col2 = st.columns([1, 1.2])

    with col1:
        st.subheader("🔎 Zone de Scan")
        img_visu = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)
        # La ligne et la tache rouge se mettent à jour avec les sliders
        cv2.line(img_visu, (x_c, y_tiers_apical), (x_c, y_apex), (0, 255, 255), 10)
        cv2.circle(img_visu, (x_c, y_apex), 20, (255, 0, 0), -1) 
        st.image(img_visu, use_container_width=True)

    with col2:
        st.subheader("📈 Courbe de Densité H")
        signal = profile_line(img_gray, (y_tiers_apical, x_c), (y_apex, x_c), linewidth=5)
        
        if len(signal) > 5:
            w_len = 11 if len(signal) > 11 else (len(signal)-1 if len(signal)%2==0 else len(signal))
            signal_clean = savgol_filter(signal, window_length=max(3, w_len), polyorder=2)
            H_values = signal_clean / 255.0
        else:
            H_values = np.array([0.0])

        fig = go.Figure()
        fig.add_trace(go.Scatter(y=H_values, mode='lines', line=dict(color='cyan', width=4), name="Profil H"))
        fig.add_shape(type="line", x0=0, y0=0.45, x1=len(H_values), y1=0.45, line=dict(color="Red", dash="dash"))
        fig.update_layout(template="plotly_dark", height=350, yaxis=dict(range=[0, 1.1]), yaxis_title="Densité H")
        st.plotly_chart(fig, use_container_width=True)

    # --- 6. DIAGNOSTIC ET RAPPORT .TXT ---
    st.divider()
    h_min = np.min(H_values)
    h_apex = H_values[-1]

    col_btn1, col_btn2 = st.columns(2)

    with col_btn1:
        if st.button("✨ LANCER LE DIAGNOSTIC MAGIQUE"):
            with st.spinner('Analyse...'):
                time.sleep(1) 
                if h_apex < 0.45:
                    st.snow()
                    st.error(f"### 🚨 PATHOLOGIE DÉTECTÉE (H_apex={h_apex:.2f})")
                elif h_min < 0.60:
                    st.warning(f"### ⚠️ ÉTANCHÉITÉ DOUTEUSE (H_min={h_min:.2f})")
                else:
                    st.balloons()
                    st.success(f"### ✅ ÉTANCHÉITÉ VALIDÉE (H_min={h_min:.2f})")

    with col_btn2:
        # Génération du fichier texte sans erreur de syntaxe
        lignes_rapport = [
            "RAPPORT D'EXPERTISE DENTAIRE",
            "="*30,
            f"Date : {time.strftime('%Y-%m-%d %H:%M')}",
            f"Source : {source_radio}",
            f"Position X : {x_c}",
            f"Position Apex (Y) : {y_apex}",
            f"Densite H a l'Apex : {h_apex:.4f}",
            f"Densite H Minimum : {h_min:.4f}",
            "-"*30,
            f"RESULTAT : {'VALIDE' if h_apex >= 0.45 else 'ECHEC / PATHOLOGIE'}",
            "="*30
        ]
        rapport_final = "\n".join(lignes_rapport)

        st.download_button(
            label="💾 Télécharger le Rapport (.txt)",
            data=rapport_final,
            file_name=f"expertise_dentaire_{int(time.time())}.txt",
            mime="text/plain"
        )

    # --- 7. RAPPORT TECHNIQUE ---
    with st.expander("📊 Rapport de mesures"):
        st.table(pd.DataFrame({
            "Indicateur": ["H Minimum", "H Apex", "Seuil Critique"],
            "Valeur": [f"{h_min:.2f}", f"{h_apex:.2f}", "0.45"]
        }))
