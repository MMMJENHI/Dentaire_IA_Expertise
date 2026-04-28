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
**Développé dans le cadre d'un projet de Master | 2026**
