import streamlit as st
import cv2
import numpy as np
import plotly.graph_objects as go
from skimage.measure import profile_line
from scipy.signal import savgol_filter
from PIL import Image
import requests
from io import BytesIO
from datetime import datetime

# ==============================
# 1. CONFIGURATION INTERFACE
# ==============================
st.set_page_config(
    page_title="CAD IA v4.7 - Analyse Densitométrique",
    layout="wide",
    initial_sidebar_state="expanded"
)

GITHUB_DEFAULT = "https://raw.githubusercontent.com/MMMJENHI/Dentaire_IA_Expertise/main/dent.jpg"

# ==============================
# 2. PRÉTRAITEMENT IMAGE
# ==============================
@st.cache_data(show_spinner=False)
def preprocess_image(_image: Image.Image) -> np.ndarray:
    """Prétraitement médical : Gris + CLAHE pour révéler les micro-structures."""
    img_array = np.array(_image.convert('L'))
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    return clahe.apply(img_array)

def smooth(sig: np.ndarray) -> np.ndarray:
    """Lissage du signal via filtre Savitzky-Golay + normalisation [0,1]."""
    sig = sig.astype(float)
    if len(sig) > 5:
        w_len = 11 if len(sig) > 11 else (len(sig) - 1 if len(sig) % 2 == 0 else len(sig))
        sm = savgol_filter(sig, window_length=max(3, w_len), polyorder=2)
    else:
        sm = sig
    sm_norm = np.clip(sm / 255.0, 0, 1)
    return sm_norm

def label_from_class(classe: int) -> str:
    if classe == 0:
        return "ZONE NOIRE (H < 0.25)"
    if classe == 1:
        return "ZONE INTERMÉDIAIRE (0.25 ≤ H < 0.45)"
    return "ZONE DENSE (H ≥ 0.45)"

# ==============================
# 3. BARRE LATÉRALE - CONTROLES
# ==============================
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3774/3774278.png", width=80)
st.sidebar.markdown("### 🦷 Système CAD IA v4.7")
st.sidebar.divider()

source = st.sidebar.radio("📁 Source de données :", ("Local", "URL / GitHub", "Démo"))
raw_img = None

if source == "URL / GitHub":
    url_input = st.sidebar.text_input("Lien GitHub Raw :", value=GITHUB_DEFAULT)
    try:
        res = requests.get(url_input, timeout=10)
        res.raise_for_status()
        raw_img = Image.open(BytesIO(res.content))
    except Exception as e:
        st.sidebar.error(f"Erreur de chargement : {e}")
elif source == "Local":
    up = st.file_uploader("Charger RVG (.jpg, .png, .jpeg)", type=["jpg", "png", "jpeg"])
    if up:
        raw_img = Image.open(up)
else:
    try:
        res = requests.get(GITHUB_DEFAULT, timeout=10)
        res.raise_for_status()
        raw_img = Image.open(BytesIO(res.content))
    except Exception as e:
        st.sidebar.error(f"Démonstration non disponible : {e}")

patient_id = st.sidebar.text_input("🧾 ID / Référence Patient", value="N/A")

# ==============================
# 4. ANALYSE DENSITOMÉTRIQUE
# ==============================
if raw_img is not None:
    img_gray = preprocess_image(raw_img)
    h_img, w_img = img_gray.shape
    st.sidebar.caption(f"Résolution image : {w_img} × {h_img} px")

    # Carte de densité H normalisée
    H_map = img_gray.astype(np.float32) / 255.0

    # Cartographie densité : 0 = noire, 1 = intermédiaire, 2 = dense
    map_classes = np.zeros_like(H_map, dtype=np.uint8)
    map_classes[H_map < 0.25] = 0
    map_classes[(H_map >= 0.25) & (H_map < 0.45)] = 1
    map_classes[H_map >= 0.45] = 2

    # Sliders de positionnement
    st.sidebar.subheader("📍 Positionnement CAD (Profil 1D)")
    x_default = w_img // 2
    y_apex_default = int(h_img * 0.65)
    y_bas_default = int(h_img * 0.2)

    x_c = st.sidebar.slider("Axe d'analyse (X)", 0, w_img - 1, x_default)
    y_apex_haut = st.sidebar.slider("Point Blanc / Apex (Y)", 0, h_img - 1, y_apex_default)
    y_bas = st.sidebar.slider("Limite Bas (Y)", 0, h_img - 1, y_bas_default)

    L = abs(y_bas - y_apex_haut)
    if L < 20:
        st.sidebar.warning("Distance Apex–Bas très faible, ajuster les sliders.")
    W_exp = max(10, int(L * 0.34))

    if y_apex_haut < y_bas:
        y_lim_cyan = min(h_img - 1, y_apex_haut + W_exp)
    else:
        y_lim_cyan = max(0, y_apex_haut - W_exp)

    # Extraction des signaux
    sig_cyan = profile_line(img_gray, (y_apex_haut, x_c), (y_bas, x_c), linewidth=3)
    H_smooth_cyan = smooth(sig_cyan)
    sig_rouge = profile_line(img_gray, (y_apex_haut, x_c - 20), (y_bas, x_c - 20), linewidth=3)
    H_smooth_rouge = smooth(sig_rouge)

    h_final = float(H_smooth_cyan[0]) if len(H_smooth_cyan) > 0 else 0.0
    h_critique = 0.45
    ratio_securite = (h_final / h_critique) * 100 if h_critique > 0 else 0
    ecart_seuil = h_final - h_critique

    # Classe locale
    classe_apex = int(map_classes[y_apex_haut, x_c])
    label_apex = label_from_class(classe_apex)

    # ==============================
    # 5. CARTOGRAPHIE H (COULEUR)
    # ==============================
    overlay = np.zeros((h_img, w_img, 3), dtype=np.uint8)
    overlay[map_classes == 0] = (0, 0, 255)      # rouge = H < 0.25
    overlay[map_classes == 1] = (0, 255, 255)    # jaune = 0.25 ≤ H < 0.45
    overlay[map_classes == 2] = (0, 255, 0)      # vert = H ≥ 0.45

    base_rgb = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)
    alpha = 0.35
    cartographie_rgb = cv2.addWeighted(base_rgb, 1.0, overlay, alpha, 0)

    # Ajout du profil d'analyse (traits + point blanc)
    display_img = cartographie_rgb.copy()
    cv2.line(display_img, (x_c - 20, y_apex_haut), (x_c - 20, y_bas), (255, 0, 0), 4)     # profil rouge
    cv2.line(display_img, (x_c, y_apex_haut), (x_c, int(y_lim_cyan)), (0, 255, 255), 8)   # profil cyan
    cv2.circle(display_img, (x_c, y_apex_haut), 18, (255, 255, 255), -1)

    # ==============================
    # 6. VISUALISATION
    # ==============================
    col1, col2 = st.columns([1, 1.2])

    with col1:
        st.markdown("### 🔎 Cartographie Densitométrique H (CLAHE gris, Réf. H = 0.45)")
        st.image(display_img, use_container_width=True)

        st.markdown(f"""
        <div style="background-color: #1a1a1a; padding: 15px; border-radius: 10px; border: 1px solid #00fbff;">
            <p style="margin:0; color:#ff4b4b;">Rouge : H &lt; 0.25 (Zone noire)</p>
            <p style="margin:0; color:#ffff00;">Jaune : 0.25 ≤ H &lt; 0.45 (Zone intermédiaire)</p>
            <p style="margin:0; color:#00ff00;">Vert : H ≥ 0.45 (Zone dense / conforme)</p>
            <hr style="margin:10px 0; border-color: #333;">
            <p style="margin:0;"><b style="color:red;">━━━</b> Profil Rouge : Scan global (continuité structurelle)</p>
            <p style="margin:0;"><b style="color:cyan;">━━━</b> Profil Cyan : Fenêtre d'expertise W={W_exp}px</p>
            <p style="margin:0;"><b style="color:white;">●</b> Point Blanc : Apex Cible (Y={y_apex_haut})</p>
            <hr style="margin:10px 0; border-color: #333%;">
            <p style="margin:0; font-weight:bold; color:#00fbff;">
            📍 Classe H au Point Blanc : {label_apex} — Hf = {h_final:.4f}
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(y=H_smooth_cyan, name="Densité Cyan", line=dict(color='cyan', width=4)))
        fig1.add_hrect(y0=0.45, y1=1.0, fillcolor="green", opacity=0.1, annotation_text="ZONE CONFORME (H ≥ 0.45)")
        fig1.add_hline(y=0.45, line_dash="dash", line_color="white", annotation_text="SEUIL H = 0.45")
        fig1.update_layout(
            template="plotly_dark",
            height=400,
            title="Figure 1 : Profil d'Étanchéité Apicale (Indice Hf)",
            xaxis_title="Profondeur Fenêtre W",
            yaxis_title="Densité H"
        )
        st.plotly_chart(fig1, use_container_width=True)

    st.divider()
    col3, col4 = st.columns([1.2, 1])

    with col3:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(y=H_smooth_rouge, name="Densité Rouge", line=dict(color='red', width=4)))
        fig2.update_layout(
            template="plotly_dark",
            height=400,
            title="Figure 2 : Profil de Continuité Structurelle (Rouge)",
            xaxis_title="Profondeur",
            yaxis_title="Densité H"
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col4:
        st.markdown("### 📝 Bilan Scientifique (Réf. H = 0.45)")
        st.latex(r"L_{total} = |Y_{bas} - Y_{apex}| = " + f"{L}")
        st.latex(r"W_{fenêtre} = L \times 0.34 = " + f"{W_exp}" + r"\text{ px}")
        st.latex(r"Ratio_{sécurité} = \frac{H_{f}}{0.45} \times 100 = " + f"{ratio_securite:.1f}" + r"\%")

        st.divider()
        st.metric("Indice H final (Hf)", f"{h_final:.4f}", delta=f"{ecart_seuil:.4f}")

        if h_final >= 0.45:
            st.success("VERDICT : ✅ CONFORME (Hf ≥ 0.45)")
        else:
            st.error("VERDICT : 🚨 NON CONFORME (Hf < 0.45)")

    # ==============================
    # 7. RAPPORT D'EXPERTISE
    # ==============================
    if h_final < 0.45 or classe_apex == 0:
        statut_diag = "🚨 NON CONFORME (ZONE NOIRE / Hf < 0.45)"
        interpretation = (
            f"L'analyse au Point Blanc (Y={y_apex_haut}) révèle une densité Hf = {h_final:.4f} "
            f"inférieure au seuil de référence (0.45). "
            f"La cartographie H montre une zone {label_apex} au niveau analysé."
        )
    else:
        statut_diag = "✅ CONFORME"
        interpretation = (
            f"L'obturation est validée jusqu'au Point Blanc (Y={y_apex_haut}) avec Hf = {h_final:.4f} (≥ 0.45). "
            f"La cartographie H confirme une zone {label_apex} au niveau analysé."
        )

    rapport_expert = f"""==================================================
RAPPORT D'EXPERTISE DENTAIRE - SYSTÈME CAD IA v4.7
==================================================
PATIENT / CAS      : {patient_id}
DATE DE L'ANALYSE  : {datetime.now().strftime('%d/%m/%Y %H:%M')}
==================================================

[1] CARTOGRAPHIE DENSITOMÉTRIQUE (Réf. H = 0.45) :
--------------------------------------------------
- Image CLAHE en niveaux de gris.
- H(x,y) ∈ [0,1] dérivé de I/255.
- H < 0.25 : zone noire (rouge).
- 0.25 ≤ H < 0.45 : zone intermédiaire (jaune).
- H ≥ 0.45 : zone dense / conforme (vert).

[2] PROFIL D'ANALYSE :
--------------------------------------------------
- Axe d'analyse (X) : {x_c} px
- Apex / Point Blanc (Y) : {y_apex_haut} px
- Limite Bas (Y) : {y_bas} px
- Fenêtre d'expertise (W) : {W_exp} px

[3] PARAMÈTRES DENSITOMÉTRIQUES :
--------------------------------------------------
- H(Point Blanc) = {h_final:.4f}
- Classe H au Point Blanc : {label_apex}
- Seuil de référence : H = 0.45
- Ratio de sécurité Rs = {ratio_securite:.1f} %
- ΔH = Hf - 0.45 = {ecart_seuil:.4f}

[4] DÉCISION FINALE :
--------------------------------------------------
DIAGNOSTIC FINAL :
{statut_diag}

INTERPRÉTATION CLINIQUE :
"{interpretation}"

==================================================
Logiciel CAD IA v4.7 | Analyse Densitométrique CLAHE | 2026
==================================================
"""

    st.subheader("📋 Rapport d'Expertise Densitométrique")
    st.code(rapport_expert, language="text")

    st.download_button(
        label="💾 Exporter le Rapport (.txt)",
        data=rapport_expert,
        file_name=f"Expertise_Densite_{datetime.now().strftime('%Y%m%d')}.txt",
        mime="text/plain"
    )

else:
    st.info("💡 Système CAD IA v4.7 prêt. Veuillez charger une radiographie RVG pour démarrer l'analyse.")
