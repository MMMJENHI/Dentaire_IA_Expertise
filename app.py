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
    sm_norm = np.clip(sm / 255.0, 0, 1)
    return sm_norm

def label_from_class(classe: int) -> str:
    if classe == 0:
        return "ZONE NOIRE (H < 0.25)"
    if classe == 1:
        return "ZONE INTERMÉDIAIRE (0.25 ≤ H < 0.45)"
    return "ZONE DENSE (H ≥ 0.45)"

def verdict_tier(H_mean: float, seuil: float = 0.45) -> str:
    if H_mean < seuil:
        return "NON CONFORME (H moyen < 0.45)"
    elif H_mean < seuil + 0.05:
        return "LIMITE (H moyen légèrement ≥ 0.45)"
    else:
        return "CONFORME (H moyen confortablement ≥ 0.45)"

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

    # Carte de densité normalisée
    H_map = img_gray.astype(np.float32) / 255.0

    # Cartographie densité : 0 = noire, 1 = intermédiaire, 2 = dense
    map_classes = np.zeros_like(H_map, dtype=np.uint8)
    map_classes[H_map < 0.25] = 0
    map_classes[(H_map >= 0.25) & (H_map < 0.45)] = 1
    map_classes[H_map >= 0.45] = 2

    # ========= AXE RÉEL DU CANAL (2 POINTS) =========
    st.sidebar.subheader("📍 Axe réel du canal (2 points)")
    # Point coronal : entrée du canal
    x1 = st.sidebar.slider("X (entrée canal)", 0, w_img - 1, w_img // 2)
    y1 = st.sidebar.slider("Y (entrée canal)", 0, h_img - 1, int(h_img * 0.20))
    # Point apical : apex radiographique / Point Blanc
    x2 = st.sidebar.slider("X (apex)", 0, w_img - 1, w_img // 2)
    y2 = st.sidebar.slider("Y (apex)", 0, h_img - 1, int(h_img * 0.80))

    L = int(np.hypot(x2 - x1, y2 - y1))
    st.sidebar.caption(f"Longueur axe canal ≈ {L} px")

    # Détection tenon/couronne au point apical
    h_at_apex = float(H_map[y2, x2])
    st.sidebar.caption(f"H au Point Blanc (apex) = {h_at_apex:.3f}")
    PROTHESIS_THRESHOLD = 0.70
    is_on_prosthesis = h_at_apex >= PROTHESIS_THRESHOLD

    # ========= PROFILS LE LONG DE L’AXE =========
    # On considère le profil du canal de l'entrée (point 1) vers l'apex (point 2)
    sig_cyan = profile_line(img_gray, (y1, x1), (y2, x2), linewidth=3)
    H_smooth_cyan = smooth(sig_cyan)

    # Profil latéral, légèrement décalé en X (structure radiculaire)
    sig_rouge = profile_line(img_gray, (y1, x1 - 10), (y2, x2 - 10), linewidth=3)
    H_smooth_rouge = smooth(sig_rouge)

    n = len(H_smooth_cyan)
    # Ici : début = coronal, fin = apical
    h_coronal_mean = np.mean(H_smooth_cyan[:n//3]) if n > 0 else 0.0
    h_moyen_mean   = np.mean(H_smooth_cyan[n//3:2*n//3]) if n > 0 else 0.0
    h_apical_mean  = np.mean(H_smooth_cyan[2*n//3:]) if n > 0 else 0.0

    # H final au point apical (Point Blanc sur axe réel)
    h_final = float(H_smooth_cyan[-1]) if len(H_smooth_cyan) > 0 else 0.0
    h_critique = 0.45
    ratio_securite = (h_final / h_critique) * 100 if h_critique > 0 else 0
    ecart_seuil = h_final - h_critique

    classe_apex = int(map_classes[y2, x2])
    label_apex = label_from_class(classe_apex)

    verdict_apical  = verdict_tier(h_apical_mean, seuil=h_critique)
    verdict_moyen   = verdict_tier(h_moyen_mean,  seuil=h_critique)
    verdict_coronal = verdict_tier(h_coronal_mean, seuil=h_critique)

    expert_verdict = (
        f"Tiers coronal : {verdict_coronal}. "
        f"Tiers moyen : {verdict_moyen}. "
        f"Tiers apical : {verdict_apical}."
    )

    # ==============================
    # 5. CARTOGRAPHIE H (COULEUR)
    # ==============================
    overlay = np.zeros((h_img, w_img, 3), dtype=np.uint8)
    overlay[map_classes == 0] = (0, 0, 255)
    overlay[map_classes == 1] = (0, 255, 255)
    overlay[map_classes == 2] = (0, 255, 0)

    base_rgb = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)
    alpha = 0.35
    cartographie_rgb = cv2.addWeighted(base_rgb, 1.0, overlay, alpha, 0)

    display_img = cartographie_rgb.copy()

    # Dessin de l’axe réel du canal et du profil latéral
    if not is_on_prosthesis:
        cv2.line(display_img, (x1, y1), (x2, y2), (0, 255, 255), 6)        # axe canal
        cv2.line(display_img, (x1 - 10, y1), (x2 - 10, y2), (255, 0, 0), 3) # latéral
    # Points de repère
    cv2.circle(display_img, (x1, y1), 10, (255, 255, 255), -1)  # entrée canal
    cv2.circle(display_img, (x2, y2), 14, (0, 255, 0), -1)      # apex / Point Blanc

    # ==============================
    # 6. VISUALISATION
    # ==============================
    col1, col2 = st.columns([1, 1.2])

    with col1:
        st.markdown("### 🔎 Axe réel du canal & cartographie H")
        st.image(display_img, use_container_width=True)
        
        if is_on_prosthesis:
            st.warning("⚠️ Point apical suspecté sur TENON/COURONNE (H élevé, cas EXCLU).")

        st.markdown(f"""
        <div style="background-color: #1a1a1a; padding: 15px; border-radius: 15px; border: 1px solid #00fbff;">
            <p style="margin:0; color:#ff4b4b;">Rouge : H &lt; 0.25 (Zone noire)</p>
            <p style="margin:0; color:#ffff00;">Jaune : 0.25 ≤ H &lt; 0.45 (Zone intermédiaire)</p>
            <p style="margin:0; color:#00ff00;">Vert : H ≥ 0.45 (Zone dense / conforme)</p>
            <hr style="margin:10px 0; border-color: #333;">
            <p style="margin:0;"><b style="color:cyan;">━━━</b> Axe réel du canal (profil Cyan)</p>
            <p style="margin:0;"><b style="color:red;">━━━</b> Profil latéral radiculaire (Rouge)</p>
            <hr style="margin:10px 0; border-color: #333%;">
            <p style="margin:0; font-weight:bold; color:#00fbff;">
            📍 Classe H au Point Apical : {label_apex} — Hf = {h_final:.4f}
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        if is_on_prosthesis:
            st.warning("Profil densitométrique non interprétable : cas EXCLU (Point apical sur Tenon/Couronne).")
        else:
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(
                x=np.arange(len(H_smooth_cyan)),
                y=H_smooth_cyan,
                name="Profil le long de l'axe canal (Cyan)",
                line=dict(color='cyan', width=4)
            ))
            fig1.add_hrect(
                y0=h_critique, y1=1.0,
                fillcolor="green", opacity=0.1,
                annotation_text="ZONE CONFORME"
            )
            fig1.add_hline(
                y=h_critique,
                line_dash="dash",
                line_color="white",
                annotation_text="SEUIL H = 0.45"
            )
            fig1.update_layout(
                template="plotly_dark",
                height=400,
                title="Profil densitométrique le long de l'axe réel du canal",
                xaxis_title="Distance le long de l'axe (px)",
                yaxis_title="Densité H"
            )
            st.plotly_chart(fig1, use_container_width=True)

    st.divider()
    col3, col4 = st.columns([1.2, 1])

    with col3:
        if is_on_prosthesis:
            st.info("Profil de continuité latérale non affiché (Point apical sur Tenon/Couronne — cas EXCLU).")
        else:
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=np.arange(len(H_smooth_rouge)),
                y=H_smooth_rouge,
                name="Profil latéral radiculaire (Rouge)",
                line=dict(color='red', width=4)
            ))
            fig2.update_layout(
                template="plotly_dark",
                height=400,
                title="Profil de continuité structurelle (latéral au canal)",
                xaxis_title="Distance le long de l'axe (px)",
                yaxis_title="Densité H"
            )
            st.plotly_chart(fig2, use_container_width=True)

    with col4:
        st.markdown("### 📝 Bilan Scientifique")
        st.latex(f"L_{{canal}} = {L} \\, \\text{{px}}")
        st.metric("Indice Apical (Hf)", f"{h_final:.4f}", delta=f"{ecart_seuil:.4f}")

        tiers_coronal_ok = h_coronal_mean >= h_critique
        tiers_moyen_ok   = h_moyen_mean   >= h_critique
        tiers_apical_ok  = h_apical_mean  >= h_critique

        # 3 cas : EXCLU / CONFORME / NON CONFORME
        if is_on_prosthesis:
            statut_diag_ui = "🟡 EXCLU (Point apical sur tenon/couronne)"
            st.warning("VERDICT : 🟡 EXCLU — Point apical sur TENON/COURONNE, apex non analysable (repositionner le repère).")
        else:
            final_conforme = tiers_coronal_ok and tiers_moyen_ok and tiers_apical_ok
            if final_conforme:
                statut_diag_ui = "✅ CONFORME"
                st.success("VERDICT : ✅ CONFORME (tiers coronal, moyen et apical denses).")
            else:
                statut_diag_ui = "🚨 NON CONFORME"
                st.error("VERDICT : 🚨 NON CONFORME (au moins un tiers insuffisamment dense).")
                if not tiers_coronal_ok:
                    st.caption(f"Raison : Tiers coronal défectueux (H moyen = {h_coronal_mean:.2f}).")
                if not tiers_moyen_ok:
                    st.caption(f"Raison : Tiers moyen défectueux (H moyen = {h_moyen_mean:.2f}).")
                if not tiers_apical_ok:
                    st.caption(f"Raison : Tiers apical défectueux (H moyen = {h_apical_mean:.2f}).")

    # ==============================
    # 7. RAPPORT D'EXPERTISE
    # ==============================
    if is_on_prosthesis:
        statut_diag = "🟡 EXCLU (Point apical sur tenon/couronne, apex non analysable)"
    else:
        final_conforme = tiers_coronal_ok and tiers_moyen_ok and tiers_apical_ok
        if final_conforme:
            statut_diag = "✅ CONFORME"
        else:
            statut_diag = "🚨 NON CONFORME"

    rapport_expert = f"""==================================================
RAPPORT D'EXPERTISE DENTAIRE - SYSTÈME CAD IA v4.7
==================================================
PATIENT / CAS      : {patient_id}
DATE DE L'ANALYSE  : {datetime.now().strftime('%d/%m/%Y %H:%M')}
==================================================

[1] AXE DU CANAL :
--------------------------------------------------
- Axe défini entre (x1={x1}, y1={y1}) = entrée canal
  et (x2={x2}, y2={y2}) = apex radiographique
- Longueur projetée L_canal ≈ {L} px

[2] PARAMÈTRES DENSITOMÉTRIQUES (le long de l'axe) :
--------------------------------------------------
- H(Apex sur axe réel) = {h_final:.4f} (Classe: {label_apex})
- H(Point apical brut, carte H) = {h_at_apex:.4f}
- H moyen Tiers coronal : {h_coronal_mean:.4f}
- H moyen Tiers moyen   : {h_moyen_mean:.4f}
- H moyen Tiers apical  : {h_apical_mean:.4f}

[3] ANALYSE PAR TIERS (VERDICT EXPERT) :
--------------------------------------------------
- Tiers coronal : {verdict_coronal}
- Tiers moyen   : {verdict_moyen}
- Tiers apical  : {verdict_apical}

Synthèse expert :
"{expert_verdict}"

[4] FACTEURS DE SÉCURITÉ ET ALERTES :
--------------------------------------------------
- Ratio de sécurité apical (Hf / 0.45) : {ratio_securite:.1f} %
- ΔH = Hf - 0.45 = {ecart_seuil:.4f}
- Point apical sur tenon/couronne : {"OUI" if is_on_prosthesis else "NON"}
- Seuil prothèse utilisé : H ≥ {PROTHESIS_THRESHOLD:.2f}

[5] DÉCISION FINALE (3 CATÉGORIES) :
--------------------------------------------------
DIAGNOSTIC FINAL :
{statut_diag}

==================================================
Logiciel CAD IA v4.7 | Analyse Densitométrique CLAHE | 2026
==================================================
"""
    st.subheader("📋 Rapport Final")
    st.code(rapport_expert, language="text")
    st.download_button("💾 Exporter le Rapport", rapport_expert, file_name="Expertise_CAD.txt")

else:
    st.info("💡 Système CAD IA v4.7 : Prêt pour analyse locale ou via URL.")
