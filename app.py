import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import datetime
import time

# --- 1. CONFIGURACIÓN INICIAL ---
st.set_page_config(
    page_title="Zynte | Elite Coach", 
    page_icon="logo.png", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- 2. ESTILOS CSS PREMIUM (FONDO NUEVO) ---
st.markdown("""
    <style>
    /* Ocultar elementos de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* --- NUEVO FONDO PREMIUM --- */
    [data-testid="stAppViewContainer"] {
        background: radial-gradient(ellipse at top, #1b2735 0%, #090a0f 100%);
    }
    [data-testid="stHeader"] {
        background: transparent;
    }
    /* --------------------------- */

    .hero-title {
        font-size: 3.5rem; /* Un poco más grande */
        font-weight: 800;
        background: linear-gradient(to right, #ffffff, #33ffaa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 10px;
        text-shadow: 0 0 30px rgba(51, 255, 170, 0.2); /* Brillo sutil */
    }
    .hero-subtitle {
        font-size: 1.3rem;
        text-align: center;
        color: #a0aaba; /* Color más suave */
        margin-bottom: 40px;
    }
    .price-card {
        background-color: rgba(26, 26, 26, 0.8); /* Semi-transparente para el fondo */
        backdrop-filter: blur(10px); /* Efecto cristal */
        border: 1px solid #333;
        border-radius: 15px;
        padding: 25px;
        text-align: center;
        transition: 0.3s;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .price-card:hover {
        border-color: #33ffaa;
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(51, 255, 170, 0.2);
    }
    /* Ajuste de los inputs para que peguen con el fondo */
    .stTextInput input {
        background-color: rgba(255,255,255,0.05) !important;
        border: 1px solid #333 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CONEXIÓN API ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.warning("⚠️ Nota: API Key no detectada.")

MODELO_USADO = 'models/gemini-flash-latest'

# ==============================================================================
# 🌟 VISTAS (PÁGINAS)
# ==============================================================================

def mostrar_landing():
    """Página de Portada"""
    st.write("") 
    st.write("") # Un poco más de espacio arriba
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        try: st.image("logo.png", use_column_width=True)
        except: st.title("ZYNTE")
    
    st.markdown('<p class="hero-title">TU ENTRENADOR INTELIGENTE</p>', unsafe_allow_html=True)
    st.markdown('<p class="hero-subtitle">Planes de entrenamiento de élite generados en segundos con IA.</p>', unsafe_allow_html=True)
    
    col_a, col_b, col_c = st.columns([1, 1, 1])
    with col_b:
        st.write("")
        if st.button("🚀 EMPEZAR AHORA", use_container_width=True, type="primary"):
            st.session_state.page = 'login'
            st.rerun()
        st.write("")
        st.write("")

    #st.write("---") # Quitamos la línea divisoria, queda mejor sin ella con el fondo nuevo
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""<div class='price-card' style='text-align:left; border:none; background:transparent; box-shadow:none;'>
        <h3>🧠 Inteligencia Real</h3>
        <p style='color:#a0aaba;'>No son plantillas. Zynte analiza tu biometría para crear algo único.</p>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("""<div class='price-card' style='text-align:left; border:none; background:transparent; box-shadow:none;'>
        <h3>⚡ Velocidad Sónica</h3>
        <p style='color:#a0aaba;'>Tu plan completo listo antes de que termines de atarte los cordones.</p>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown("""<div class='price-card' style='text-align:left; border:none; background:transparent; box-shadow:none;'>
        <h3>📄 Informes PDF</h3>
        <p style='color:#a0aaba
