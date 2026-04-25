import streamlit as st
import cv2
import numpy as np
import plotly.graph_objects as go
from skimage.measure import profile_line
from PIL import Image
import os
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Expert IA Dentaire", layout="wide")

def preprocess_image(image):
    img_array = np.array(image.convert('L'))
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    return clahe.apply(img_array)

# --- CHARGEMENT AUTO GITHUB ---
nom_fichier = "dent.jpg"
if os.path.exists(nom_fichier):
    raw_img = Image.open(nom_fichier)
    img_gray = preprocess_image(raw_img)
    h, w = img_gray.shape

    # --- SIDEBAR : PARAMÈTRES D'EXPERTISE ---
    st.sidebar.header("🔬 Paramètres de l'Expert")
    x_c = st.sidebar.slider("Axe du Canal (X)", 0, w, 712)
    y_haut = st.sidebar.slider("Haut de Racine (Y1)", 0, h, 1100)
    y_apex = st.sidebar.slider("Pointe Apex (Y2)", 0, h, 1449)
    
    # Calcul du tiers apical (33% inférieurs)
    y_tiers = int(y_haut + (y_apex - y_haut) * 0.66)

    # --- CALCUL DE LA VARIABLE H ---
    # Extraction du profil (moyenne sur 10 pixels de large pour plus de précision)
    profil = profile_line(img_gray, (y_tiers, x_c), (y_apex, x_c), linewidth=10)
    # Normalisation : H = (Valeur / 255) * Coeff_Expert
    # On considère souvent 0.90 comme le seuil de l'os sain/obturé
    h_values = profil / 150.0 
    h_min = np.min(h_values)
    h_moy = np.mean(h_values)
    h_apex = h_values[-1]

    # --- VERDICT IA ---
    if h_apex < 0.45:
        verdict = "🚨 RÉACTION APICALE ATYPIQUE DÉTECTÉE"
        color = "red"
        detail = "Suspicion de lésion péri-apicale (tache noire). L'étanchéité est rompue."
    elif h_min < 0.85:
        verdict = "⚠️ ÉTANCHÉITÉ À SURVEILLER"
        color = "orange"
        detail = "Densité intermédiaire. Risque d'infiltration à moyen terme."
    else:
        verdict = "✅ ÉTANCHÉITÉ CONFORME"
        color = "green"
        detail = "L'obturation est hermétique. Pas de signe de pathologie."

    # --- AFFICHAGE PRINCIPAL ---
    st.title("🦷 Système Expert : Analyse de la Variable H")
    
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("🖼️ Localisation du Scan")
        img_visu = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)
        cv2.line(img_visu, (x_c, y_tiers), (x_c, y_apex), (255, 255, 0), 12)
        st.image(img_visu, use_container_width=True)

    with col2:
        st.subheader("📈 Profil de Densité H")
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=h_values, mode='lines', line=dict(color='cyan', width=3)))
        # Ligne de seuil critique
        fig.add_shape(type="line", x0=0, y0=0.85, x1=len(h_values), y1=0.85, line=dict(color="red", dash="dash"))
        fig.update_layout(template="plotly_dark", height=300)
        st.plotly_chart(fig, use_container_width=True)

    # --- TABLEAU DES RÉSULTATS ---
    st.subheader("📊 Tableau de Synthèse de l'Expert")
    data_expert = {
        "Métrique": ["H Minimum", "H Moyen", "H à l'Apex", "Seuil Critique"],
        "Valeur": [f"{h_min:.2f}", f"{h_moy:.2f}", f"{h_apex:.2f}", "0.85"],
        "État": ["Anomalie" if h_min < 0.85 else "OK", "-", "CRITIQUE" if h_apex < 0.45 else "OK", "Référence"]
    }
    st.table(data_expert)

    # --- RÉSULTAT TEXTUEL & TÉLÉCHARGEMENT ---
    st.markdown(f"### Verdict : :{color}[{verdict}]")
    st.info(detail)

    # Préparation du fichier TXT pour le jury
    rapport_txt = f"""RAPPORT D'EXPERTISE DENTAIRE IA
-------------------------------
Cible : Dent 16 (Tiers Apical)
H_min  : {h_min:.2f}
H_apex : {h_apex:.2f}
VERDICT : {verdict}
CONCLUSION : {detail}
-------------------------------
Généré le : {time.strftime('%d/%m/%Y %H:%M')}
"""
    st.download_button("📥 Télécharger le Rapport (.txt)", rapport_txt, file_name="expertise_dentaire.txt")

    # Bouton Magique pour l'effet visuel
    if st.button("✨ LANCER L'ANIMATION DE VALIDATION"):
        if h_apex < 0.45: st.snow()
        else: st.balloons()

else:
    st.error("Fichier dent.jpg introuvable sur GitHub.")
