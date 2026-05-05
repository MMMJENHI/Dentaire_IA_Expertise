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
    page_title="CAD IA v4.7 - Analyse Densitométrique Canal Radiculaire",
    layout="wide",
    initial_sidebar_state="expanded"
)

GITHUB_DEFAULT = "https://raw.githubusercontent.com/MMMJENHI/Dentaire_IA_Expertise/main/dent.jpg"

# ==============================
# 2. PRÉTRAITEMENT IMAGE
# ==============================
@st.cache_data(show_spinner=False)
def preprocess_image(_image: Image.Image) -> np.ndarray:
    img_array = np.array(_image.convert('L'))
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    return clahe.apply(img_array)

def smooth(sig: np.ndarray) -> np.ndarray:
    sig = sig.astype(float)
    if len(sig) > 5:
        w_len = 11 if len(sig) > 11 else (len(sig) - 1 if len(sig) % 2 == 0 else len(sig))
        sm = savgol_filter(sig, window_length=max(3, w_len), polyorder=2)
    else:
        sm = sig
    return np.clip(sm / 255.0, 0, 1)

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
# 4. ANALYSE DENSITOMÉTRIQUE CANALAIRE
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

    # --- Positionnement CAD (Canal radiculaire) ---
    st.sidebar.subheader("📍 Positionnement CAD (Canal radiculaire)")

    x_default = w_img // 2
    x_c = st.sidebar.slider("Axe d'analyse (X)", 0, w_img - 1, x_default)

    # Origine canalaire = apex (point blanc, EN HAUT sur la radio)
    y_apex_default = int(h_img * 0.20)
    Y_apex = st.sidebar.slider(
        "Y_apex : Apex (origine du canal, extrémité radiculaire, EN HAUT sur la radio)",
        0, h_img - 1, y_apex_default
    )

    # Bas du canal analysé (vers collet/couronne, plus bas sur l'image)
    MARGE_MIN = 20
    MARGE_MAX = 700

    Y_bas_min = min(h_img - 1, Y_apex + MARGE_MIN)
    Y_bas_max = min(h_img - 1, Y_apex + MARGE_MAX)
    if Y_bas_min >= Y_bas_max:
        Y_bas_max = min(h_img - 1, Y_bas_min + 20)

    Y_bas = st.sidebar.slider(
        "Y_bas : Bas du canal analysé (vers collet/couronne)",
        Y_bas_min, Y_bas_max, Y_bas_max
    )

    # Vérification du sens canal (apex -> bas)
    if Y_bas <= Y_apex:
        st.error(
            f"❌ Canal invalide : Y_bas = {Y_bas} px ≤ Y_apex = {Y_apex} px.\n"
            "Le canal doit être défini de l'apex (point blanc) vers la couronne (plus bas sur l'image).\n"
            "➡ Augmente Y_bas ou remonte Y_apex."
        )
        st.stop()

    # --- Géométrie canal ---
    Y_origine_canal   = Y_apex      # origine clinique = apex = point blanc
    Y_coronaire_canal = Y_bas       # bas du canal analysé (vers collet/couronne)
    H_canal           = Y_coronaire_canal - Y_origine_canal
    L                 = H_canal

    if L < 20:
        st.sidebar.warning("Hauteur de canal analysée très faible, ajuster les sliders.")

    W_exp = max(10, int(L * 0.34))
    y_lim_cyan = min(h_img - 1, Y_origine_canal + W_exp)

    # --- Profils canalaire (origine = Y_apex) ---
    sig_cyan = profile_line(img_gray, (Y_origine_canal, x_c), (Y_coronaire_canal, x_c), linewidth=3)
    H_smooth_cyan = smooth(sig_cyan)

    sig_rouge = profile_line(img_gray, (Y_origine_canal, x_c - 20), (Y_coronaire_canal, x_c - 20), linewidth=3)
    H_smooth_rouge = smooth(sig_rouge)

    # Axe des distances canalaire : 0 → L (0 à Y_apex, L à Y_bas)
    n_points = len(H_smooth_cyan)
    if n_points > 1:
        distances = np.linspace(0, L, n_points)
    else:
        distances = np.array([0.0])

    # Hf = densité à l'origine du canal (distance 0 = apex)
    h_final = float(H_smooth_cyan[0]) if len(H_smooth_cyan) > 0 else 0.0
    h_critique = 0.45
    ratio_securite = (h_final / h_critique) * 100 if h_critique > 0 else 0
    ecart_seuil = h_final - h_critique

    # Classe locale à l’apex
    classe_apex = int(map_classes[Y_origine_canal, x_c])
    label_apex = label_from_class(classe_apex)

    # --- Warnings tenon / métal ---
    SEUIL_METAL = 0.80
    SEUIL_ZONE_TENON = int(h_img * 0.65)

    if h_final > SEUIL_METAL:
        st.warning(
            f"⚠ H(Apex) = {h_final:.3f} (> {SEUIL_METAL}) : densité très élevée, "
            "compatible avec un matériau métallique (tenon/couronne). "
            "Vérifie que le point blanc n'est pas posé sur le tenon."
        )

    if Y_origine_canal > SEUIL_ZONE_TENON:
        st.warning(
            f"⚠ Y_apex = {Y_origine_canal} px se situe dans la zone basale de l'image "
            f"(≥ {SEUIL_ZONE_TENON}px : probable tenon/couronne). "
            "L'apex anatomique doit être plus haut sur la racine."
        )

    if (h_final > SEUIL_METAL) and (Y_origine_canal > SEUIL_ZONE_TENON):
        st.error(
            "❌ Apex très probablement mal placé : densité métallique ET position basale.\n"
            "➡ Replace le point blanc au niveau de l'extrémité radiculaire, au-dessus du tenon."
        )
        st.stop()

    # ==============================
    # 5. DÉCISION & RÉACTION APICALE
    # ==============================
    if h_final < 0.45 or classe_apex == 0:
        statut_diag = "🚨 NON CONFORME (Hf < 0.45 à l’apex)"
        interpretation = (
            "L’analyse densitométrique met en évidence une densité insuffisante au niveau de l’extrémité "
            "radiculaire (apex, point blanc). Cette configuration traduit une obturation apicale peu compacte "
            "et/ou une herméticité douteuse dans la zone critique du tiers apical. Ce profil est décrit comme "
            "associé à un risque accru de persistance ou de développement d’une parodontite apicale "
            "(réaction apicale inflammatoire), et doit être corrélé aux signes cliniques (douleur, percussion, "
            "palpation) et à l’imagerie péri-apicale (radiographie de contrôle, voire CBCT en cas de doute)."
        )
    else:
        statut_diag = "✅ CONFORME (Hf ≥ 0.45 à l’apex)"
        interpretation = (
            "L’analyse densitométrique montre une densité satisfaisante au niveau de l’extrémité radiculaire "
            "(apex, point blanc), compatible avec une obturation apicale compacte et une herméticité correcte. "
            "Ce profil est en accord avec les critères radiologiques de succès endodontique, sous réserve de "
            "l’absence de lésion péri-apicale évolutive ou de réaction apicale pathologique, et d’une concordance "
            "avec les données cliniques."
        )

    # ==============================
    # 6. CARTOGRAPHIE H (COULEUR)
    # ==============================
    overlay = np.zeros((h_img, w_img, 3), dtype=np.uint8)
    overlay[map_classes == 0] = (0, 0, 255)
    overlay[map_classes == 1] = (0, 255, 255)
    overlay[map_classes == 2] = (0, 255, 0)

    base_rgb = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)
    cartographie_rgb = cv2.addWeighted(base_rgb, 1.0, overlay, 0.35, 0)

    display_img = cartographie_rgb.copy()
    cv2.line(display_img, (x_c - 20, Y_origine_canal), (x_c - 20, Y_coronaire_canal), (255, 0, 0), 4)   # canal rouge
    cv2.line(display_img, (x_c, Y_origine_canal), (x_c, int(y_lim_cyan)), (0, 255, 255), 8)              # fenêtre cyan
    cv2.circle(display_img, (x_c, Y_origine_canal), 18, (255, 255, 255), -1)                             # point blanc

    # ==============================
    # 7. VISUALISATION
    # ==============================
    col1, col2 = st.columns([1, 1.2])

    with col1:
        st.markdown("### 🔎 Cartographie Densitométrique H (canal radiculaire)")
        st.image(display_img, use_container_width=True)

        st.markdown(f"""
        <div style="background-color: #1a1a1a; padding: 15px; border-radius: 10px; border: 1px solid #00fbff;">
            <p style="margin:0; color:#ff4b4b;">Rouge : H &lt; 0.25 (Zone noire)</p>
            <p style="margin:0; color:#ffff00;">Jaune : 0.25 ≤ H &lt; 0.45 (Zone intermédiaire)</p>
            <p style="margin:0; color:#00ff00;">Vert : H ≥ 0.45 (Zone dense / conforme)</p>
            <hr style="margin:10px 0; border-color: #333;">
            <p style="margin:0;"><b style="color:red;">━━━</b> Profil Rouge : Canal complet (Y_apex → Y_bas)</p>
            <p style="margin:0;"><b style="color:cyan;">━━━</b> Profil Cyan : Fenêtre d'expertise W={W_exp}px</p>
            <p style="margin:0;"><b style="color:white;">●</b> Point Blanc : Apex (origine clinique du canal, Y_apex={Y_apex})</p>
            <hr style="margin:10px 0; border-color: #333%;">
            <p style="margin:0; font-weight:bold; color:#00fbff;">
            📍 H à l’Apex (distance 0) : {label_apex} — Hf = {h_final:.4f}
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x=distances,
            y=H_smooth_cyan,
            name="Densité canal",
            line=dict(color='cyan', width=4)
        ))
        fig1.add_hrect(y0=0.45, y1=1.0, fillcolor="green", opacity=0.1,
                       annotation_text="ZONE CONFORME (H ≥ 0.45)")
        fig1.add_hline(y=0.45, line_dash="dash", line_color="white",
                       annotation_text="SEUIL H = 0.45")
        fig1.update_layout(
            template="plotly_dark",
            height=400,
            title="Figure 1 : Profil d'Étanchéité (0 = apex, L = Y_bas)",
            xaxis_title="Distance canalaire depuis l'apex (px)",
            yaxis_title="Densité H"
        )
        st.plotly_chart(fig1, use_container_width=True)

    st.divider()
    col3, col4 = st.columns([1.2, 1])

    with col3:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=distances,
            y=H_smooth_rouge,
            name="Densité Rouge",
            line=dict(color='red', width=4)
        ))
        fig2.update_layout(
            template="plotly_dark",
            height=400,
            title="Figure 2 : Profil de Continuité Structurelle (0 = apex)",
            xaxis_title="Distance canalaire depuis l'apex (px)",
            yaxis_title="Densité H"
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col4:
        st.markdown("### 📝 Bilan Scientifique (Réf. H = 0.45)")
        st.latex(r"H_{\text{canal}} = Y_{\text{bas}} - Y_{\text{apex}} = " + f"{H_canal}")
        st.latex(r"W_{\text{fenêtre}} = L \times 0.34 = " + f"{W_exp}" + r"\ \text{px}")
        st.latex(r"Ratio_{\text{sécurité}} = \frac{H_{f}}{0.45} \times 100 = " + f"{ratio_securite:.1f}" + r"\ \%")

        st.divider()
        st.metric("Indice H final à l’Apex (Hf)", f"{h_final:.4f}", delta=f"{ecart_seuil:.4f}")

        if h_final >= 0.45:
            st.success("VERDICT : ✅ CONFORME (Hf ≥ 0.45 à l’apex)")
        else:
            st.error("VERDICT : 🚨 NON CONFORME (Hf < 0.45 à l’apex)")

    # ==============================
    # 8. RAPPORT D'EXPERTISE
    # ==============================
    rapport_expert = f"""==================================================
RAPPORT D'EXPERTISE DENTAIRE - CANAL RADICULAIRE
==================================================
PATIENT / CAS      : {patient_id}
DATE DE L'ANALYSE  : {datetime.now().strftime('%d/%m/%Y %H:%M')}
==================================================

[1] GÉOMÉTRIE DU CANAL :
--------------------------------------------------
- Axe d'analyse (X)                        : {x_c} px
- Y_apex  (origine du canal, point blanc)  : {Y_apex} px
- Y_bas   (bas du canal analysé)           : {Y_bas} px
- Hauteur du canal analysé (H = Y_bas - Y_apex) : {H_canal} px
- Distance canalaire 0 → L (0 = apex, L = Y_bas) : L = {L} px
- Fenêtre d'expertise (W)                  : {W_exp} px

[2] PARAMÈTRES DENSITOMÉTRIQUES APICAUX :
--------------------------------------------------
- Origine du profil 1D                     : Y_apex (distance 0 sur le canal)
- Système de coordonnées canalaire         : 0 à L (0 = apex, L = Y_bas)
- H(Apex)                                  : {h_final:.4f}
- Classe H à l’Apex                        : {label_apex}
- Seuil de référence                       : H = 0.45
- Ratio de sécurité Rs                     : {ratio_securite:.1f} %
- ΔH = Hf - 0.45                           : {ecart_seuil:.4f}

[3] DÉCISION & INTERPRÉTATION :
--------------------------------------------------
{statut_diag}

INTERPRÉTATION CLINIQUE :
{interpretation}

[4] REMARQUES SUR LE POSITIONNEMENT :
--------------------------------------------------
Les coordonnées Y_apex (point blanc) et Y_bas (bas du canal analysé) sont définies manuellement
par l’opérateur sur la radiographie. En fonction des déformations géométriques du cliché, des
superpositions anatomiques ou de la présence de matériaux radio-opaques (tenon, pilier, couronne),
ces points peuvent être partiellement ou totalement en dehors de l’axe réel du canal radiculaire.
Dans ce cas, l’analyse densitométrique décrit la zone effectivement traversée par le segment d’étude
et doit être interprétée avec prudence, en complément du localisateur d’apex et des autres données
cliniques et radiologiques.

==================================================
Logiciel CAD IA v4.7 | Analyse Densitométrique CLAHE | 2026
==================================================
"""

    st.subheader("📋 Rapport d'Expertise Densitométrique")
    st.code(rapport_expert, language="text")

    st.download_button(
        label="💾 Exporter le Rapport (.txt)",
        data=rapport_expert,
        file_name=f"Expertise_Canal_{datetime.now().strftime('%Y%m%d')}.txt",
        mime="text/plain"
    )

else:
    st.info("💡 Système CAD IA v4.7 prêt. Veuillez charger une radiographie RVG pour démarrer l'analyse.")
