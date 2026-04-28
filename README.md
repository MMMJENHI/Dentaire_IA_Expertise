# 🦷 IA Expertise Dentaire - Master (Analyse de la Dent 16)

<img width="400" height="400" alt="qrcode" src="https://github.com/user-attachments/assets/d792ee06-0386-4316-844c-5c13ca781df8" />





### 📲 Accès Direct à l'Application
[🚀 Lancer l'Expertise CAD](https://dentaireiaexpertiseia.streamlit.app/)

---

## 🔬 Présentation du Projet
Ce système de **Diagnostic Assisté par Ordinateur (CAD)** est conçu pour l'analyse automatisée de l'étanchéité apicale sur des radiographies dentaires. Le projet se concentre sur l'isolation anatomique du tiers apical et la mesure de la densité matricielle (Indice H).

## 🛠️ Innovations Techniques (Version Master)
Cette version intègre des algorithmes avancés de traitement du signal et d'imagerie :
1. **Auto-Center IA :** Recentrage dynamique de l'axe X pour compenser les erreurs de parallélisme.
2. **Segmentation Oblique :** Calcul d'un profil de ligne incliné pour suivre précisément l'anatomie de la racine.
3. **Isolation du Tiers Apical :** Analyse exclusive des derniers 33% de la zone radiculaire.
4. **Calcul de l'Indice H :** Normalisation des niveaux de gris et lissage via filtre Savitzky-Golay.

## 🚀 Fonctionnalités
- **Importation Multimodal :** PC Local, URL GitHub Raw ou Mode Démo.
- **Visualisation Dynamique :** Cartographie en temps réel (Trait Cyan pour le tiers apical).
- **Rapport d'Expertise :** Génération automatique d'un bilan technique téléchargeable (.txt).
- **Verdict Automatisé :** Comparaison à un seuil critique de pathologie (0.45).

## 📊 Structure du Dépôt
- `app.py` : Code source de l'application (Streamlit + OpenCV).
- `requirements.txt` : Dépendances (NumPy, Plotly, Scikit-image, Scipy).
- `dent.jpg` : Image échantillon pour les tests de démonstration.

---
# --- LÉGENDE HAUTE VISIBILITÉ ---
        st.markdown("""
        <div style="background-color: #1a1a1a; padding: 20px; border-radius: 15px; border: 2px solid #00fbff;">
            <h3 style="margin-top:0; color: #00fbff; text-align: center;">📊 TABLEAU DE BORD EXPERT</h3>
            <p style="font-size: 1.2em; margin: 10px 0;">
                <b style="color: #FF0000; text-shadow: 0 0 10px red;">━━━━</b> 
                <b style="color: white;">SCAN GLOBAL :</b> Continuité du canal
            </p>
            <p style="font-size: 1.2em; margin: 10px 0;">
                <b style="color: #00FFFF; text-shadow: 0 0 10px cyan;">━━━━</b> 
                <b style="color: white;">ZONE CYAN :</b> Expertise du Tiers Apical
            </p>
            <p style="font-size: 1.2em; margin: 10px 0;">
                <span style="color: white; background-color: white; border-radius: 50%; padding: 0 8px; box-shadow: 0 0 15px white;">.</span> 
                <b style="color: white; margin-left: 10px;">POINT BLANC :</b> Apex Cible (Étanchéité Totale)
            </p>
        </div>
        """, unsafe_allow_html=True)
**Développé dans le cadre d'un projet de Master | 2026**
