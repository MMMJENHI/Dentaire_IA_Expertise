import streamlit as st

st.title("🦷 Diagnostic Système")
st.write("Le serveur fonctionne !")

import cv2
st.write(f"OpenCV est bien chargé (Version: {cv2.__version__})")

import numpy as np
st.write("Numpy est chargé.")
