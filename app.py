import streamlit as st
import google.generativeai as genai
import time

# --- 1. CONFIGURACIÓN DE PÁGINA (Sobria) ---
st.set_page_config(
    page_title="Zynte Coach",
    page_icon="logo.png", # Usamos tu logo como icono de pestaña
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS para limpiar la interfaz al máximo
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            [data-testid="stSidebarNav"] {display: none!important;}
            .stDeployButton {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- 2. CONEXIÓN SEGURA ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("Error de configuración: API Key no encontrada.")
    st.stop()

# Modelo IA
MODELO_USADO = 'models/gemini-flash-latest'

# --- 3. BARRA LATERAL (PANEL DE CONTROL) ---
with st.sidebar:
    # Logo corporativo
    try: st.image("logo.png", width=180)
    except: st.header("ZYNTE")
    
    st.write("---") # Línea separadora simple
    st.subheader("Datos del Cliente")
    
    nombre = st.text_input("Nombre", "Usuario")
    
    # Secciones limpias sin emojis
    with st.expander("Biometría", expanded=True):
        peso = st.slider("Peso (kg)", 40.0, 150.0, 70.0, 0.5)
        altura = st.slider("Altura (cm)", 120, 220, 175, 1)
        edad = st.slider("Edad", 16, 80, 25)
            
    with st.expander("Planificación", expanded=True):
        objetivo = st.selectbox("Objetivo Principal:", 
                              ["Ganar Masa Muscular", "Perder Grasa", "Fuerza", "Resistencia", "Salud General"])
        nivel = st.select_slider("Nivel de Experiencia:", options=["Principiante", "Intermedio", "Avanzado"])

    st.write("---")
    if st.button("Reiniciar Sesión"):
        st.session_state.history = []
        st.rerun()

# --- 4. CÁLCULOS (BACKEND) ---
imc = peso / ((altura/100)**2)
estado_imc = "Normal"
# Lógica simple para colores de métrica (usando palabras clave de Streamlit)
color_delta = "off" 
if imc >= 25: 
    estado_imc = "Sobrepeso"
    color_delta = "off" # Gris/Neutro para ser más serio
if imc >= 30:
    estado_imc = "Obesidad"
    color_delta = "inverse" # Rojo si es crítico
elif imc < 18.5: 
    estado_imc = "Bajo peso"

# --- 5. INTERFAZ PRINCIPAL (DASHBOARD) ---
try: st.image("banner.jpg", use_column_width=True)
except: st.title(f"Zynte Coach | {objetivo}")

# Métricas limpias (Estilo Dashboard Financiero/Datos)
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("IMC Actual", f"{imc:.1f}", estado_imc, delta_color=color_delta)
with col2:
    st.metric("Peso", f"{peso} kg")
with col3:
    st.metric("Objetivo", objetivo)
with col4:
    st.metric("Nivel", nivel)

st.divider()

# --- 6. CHAT PROFESIONAL ---

if "history" not in st.session_state:
    st.session_state.history = []
    # Mensaje inicial puramente funcional, sin saludos excesivos
   # Bloque arreglado (Copia y pega esto en lugar de la línea que da error)
    mensaje_inicio = f"Bienvenido {nombre}. Datos: {peso}kg | {objetivo}. Esperando consulta."
    st.session_state.history.append({"role": "model", "content": mensaje_inicio})

