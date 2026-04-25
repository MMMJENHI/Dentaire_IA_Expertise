# 🦷 Expertise IA Dentaire : Analyse de la Variable H (Dent 16)

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_svg.svg)](URL_DE_TON_APP_STREAMLIT)

> **Projet de Master :** Système expert d'aide au diagnostic endodontique par analyse densitométrique automatisée.

---

## 🚀 Accès Direct à l'Expertise
Pour tester le système immédiatement sans installation, cliquez sur le bouton ci-dessous :  
### 👉 [LANCER L'ANALYSE MAGIQUE EN LIGNE](URL_DE_TON_APP_STREAMLIT)

---

## 📋 Présentation du Projet
Ce système IA est conçu pour assister les praticiens dans l'évaluation de l'étanchéité des traitements endodontiques. Il se focalise sur la **Dent 16** et analyse spécifiquement le **tiers apical**, zone critique pour la prévention des pathologies péri-apicales.

### 🔬 Concepts Scientifiques
Le moteur d'analyse repose sur le calcul de la **Variable H** (Indice de densité relative) :
* **Isolation du Tiers Apical** : Le système isole automatiquement les derniers 33% de la racine.
* **Profil Densitométrique** : Extraction d'une courbe de densité le long de l'axe du canal.
* **Détection Atipique** : Identification des chutes de densité signant une infiltration ou une lésion.

## 📊 Seuils de Diagnostic (Expertise)
| Valeur de H | Interprétation | Action IA |
| :--- | :--- | :--- |
| **H > 0.90** | Étanchéité Parfaite | ✅ Validation (Balloons) |
| **0.45 < H < 0.85** | Étanchéité Douteuse | ⚠️ Alerte de surveillance |
| **H < 0.45** | Réaction Apicale / Lésion | 🚨 Diagnostic Critique (Snow) |

## 🛠️ Fonctionnalités Techniques
- **Auto-Load** : Chargement automatique de la radio `dent.jpg` depuis GitHub.
- **Traitement d'Image** : Filtrage CLAHE et débruitage Savitzky-Golay.
- **Rapport Automatisé** : Génération d'un tableau de synthèse et export `.txt`.
- **Interface Interactive** : Ajustement dynamique des coordonnées de scan.

## ⚙️ Installation Locale (PC Toshiba)
Si vous souhaitez exécuter le projet sur votre machine :

1. **Cloner le projet** :
   ```bash
   git clone [https://github.com/ton-username/Dentaire_IA_Expertise.git](https://github.com/ton-username/Dentaire_IA_Expertise.git)
