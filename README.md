# 🦷 IA Expertise Dentaire - Master (Analyse de la Dent 16)

<img width="400" height="400" alt="qrcode" src="https://github.com/user-attachments/assets/d792ee06-0386-4316-844c-5c13ca781df8" />

### 📲 Accès Direct à l'Application
[🚀 Lancer l'Expertise CAD](https://dentaireiaexpertiseia.streamlit.app/)

### 🗄️ Accès à la Base de Données & Site

* [📊 Consulter la Base de Données (GitHub)](https://github.com/MMMJENHI/Dentaire_IA_Expertise)
* [📊 Consulter le Site d'Expertise](https://github.com/clemkoa/tooth-detection)
* [📊 Consulter le Site d'Expertise](https://github.com/topics/dental)

---

## 🔬 Présentation du Projet
Ce système de **Diagnostic Assisté par Ordinateur (CAD)** est conçu pour l'analyse automatisée de l'étanchéité apicale sur des radiographies dentaires. Le projet se concentre sur l'isolation anatomique du tiers apical et la mesure de la densité matricielle (**Indice H**) pour garantir un scellement hermétique sans infiltration.

## 🛠️ Innovations Techniques (Version Master)
Cette version intègre des algorithmes avancés de traitement du signal et d'imagerie développés pour optimiser la précision sur PC Toshiba :
1. **Auto-Center IA :** Recentrage dynamique de l'axe X pour compenser les erreurs de parallélisme.
2. **Segmentation Oblique :** Calcul d'un profil de ligne incliné pour suivre précisément l'anatomie de la racine.
3. **Isolation du Tiers Apical :** Analyse exclusive des derniers 33% de la zone radiculaire.
4. **Calcul de l'Indice H :** Normalisation des niveaux de gris et lissage via filtre **Savitzky-Golay**.

---

## ⏳ Historique des Versions

### 🔵 Le Système CAD v3.0
Initialement conçu pour assister l'expert dans l'évaluation de l'étanchéité et la segmentation anatomique.
*   **Double Échelle d'Analyse :** Utilisation d'un trait rouge pour le scan global et d'un trait cyan pour l'expertise précise du scellement.
*   **Calculs Automatisés :** Détermination de la longueur totale $L$ et de la fenêtre d'expertise $W$ (fixée à $L \times 0.34$).
*   **Traitement CLAHE :** Amélioration adaptative du contraste pour les radios RVG.

### 🔴 Le Système CAD v4.0 (Évolution Majeure)
Introduction d'une **logique adaptative robuste** permettant au système de "comprendre" l'anatomie dentaire :
*   **Identification Dynamique :** Reconnaissance automatique du **Tenon Métallique** ($H > 0.82$), de l'interface de **Couronne**, et détection immédiate des **Zones Noires** (lésions).
*   **Segmentation du Canal :** Division automatique en tiers (Apical, Moyen, Cervical).
*   **Stabilité Accrue :** Réduction de la sensibilité aux micro-mouvements pour une expertise plus fiable.

---

## 🚀 Fonctionnalités Clés
- **Importation Multimodal :** Chargement depuis un dossier local, une URL GitHub Raw ou via le mode Démo.
- **Visualisation CAD (Gris + CLAHE) :** Affichage haute netteté pour valider la position du **Point Blanc** sans artefacts de couleur.
- **Double Graphique :** Figures séparées pour l'analyse de l'étanchéité (Cyan) et de la continuité (Rouge).
- **Verdict Automatisé :** Comparaison instantanée à un seuil critique de pathologie fixé à **0.45**.

---

## 📋 Légende du Tableau de Bord Expert
Le système applique un code couleur strict pour l'interprétation clinique :
*   **━━━━ (ROUGE) SCAN GLOBAL :** Analyse de la continuité structurelle du canal.
*   **━━━━ (CYAN) ZONE CYAN :** Expertise focalisée sur l'étanchéité du Tiers Apical ($W = L \times 0.34$).
*   **. (POINT BLANC) :** Apex Cible servant d'origine mathématique immuable pour le calcul de l'Indice $H_f$.

---

## 📊 Structure du Dépôt
- `app.py` : Code source principal (Streamlit + OpenCV + Plotly).
- `requirements.txt` : Dépendances techniques (NumPy, Scikit-image, Scipy).
- `dent.jpg` : Image échantillon utilisée pour le mode démonstration.

**Développé par JENHI .M dans le cadre d'un projet de Master | 2026**
