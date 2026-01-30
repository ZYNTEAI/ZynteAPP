import streamlit as st
import google.generativeai as genai
import time

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Zynte Coach",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS (Modo Oscuro/Pro)
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
    st.error("Error: API Key no configurada.")
    st.stop()

MODELO_USADO = 'models/gemini-flash-latest'

# --- 3. BARRA LATERAL ---
with st.sidebar:
    try: st.image("logo.png", width=180)
    except: st.header("ZYNTE")
    
    st.write("---")
    st.caption("DATOS DEL CLIENTE")
    
    nombre = st.text_input("Nombre", "Usuario")
    
    with st.expander("Biometría", expanded=True):
        peso = st.slider("Peso (kg)", 40.0, 150.0, 72.5, 0.5)
        altura = st.slider("Altura (cm)", 120, 220, 176, 1)
        edad = st.slider("Edad", 16, 80, 25)
            
    with st.expander("Planificación", expanded=True):
        objetivo = st.selectbox("Objetivo:", 
                              ["Ganar Masa Muscular", "Perder Grasa", "Fuerza", "Resistencia", "Salud"])
        nivel = st.select_slider("Nivel:", options=["Principiante", "Intermedio", "Avanzado"])

    st.write("---")
    if st.button("Reiniciar Chat"):
        st.session_state.history = []
        st.rerun()

# --- 4. CÁLCULOS ---
imc = peso / ((altura/100)**2)
estado_imc = "Normal"
color_delta = "off"
if imc >= 25: 
    estado_imc = "Sobrepeso"
if imc >= 30:
    estado_imc = "Obesidad"
    color_delta = "inverse"
elif imc < 18.5: 
    estado_imc = "Bajo peso"

# --- 5. DASHBOARD VISUAL ---
try: st.image("banner.jpg", use_column_width=True)
except: st.title("ZYNTE COACH")

col1, col2, col3, col4 = st.columns(4)
with col1: st.metric("IMC Actual", f"{imc:.1f}", estado_imc, delta_color=color_delta)
with col2: st.metric("Peso", f"{peso} kg")
with col3: st.metric("Objetivo", objetivo)
with col4: st.metric("Nivel", nivel)

st.divider()

# --- 6. CHAT (RECUPERADO) ---

if "history" not in st.session_state:
    st.session_state.history = []
    # Línea corregida y corta para evitar errores
    inicio = f"Sesión iniciada. Usuario: {nombre}. Objetivo: {objetivo}. Esperando comandos."
    st.session_state.history.append({"role": "model", "content": inicio})

# Pintar historial
for msg in st.session_state.history:
    role = "assistant" if msg["role"] == "model" else "user"
    avatar = "logo.png" if role == "assistant" else None
    try: st.chat_message(role, avatar=avatar).markdown(msg["content"])
    except: st.chat_message(role).markdown(msg["content"])

# --- CAJA DE TEXTO (LO QUE FALTABA) ---
# --- CAJA DE TEXTO (CON PERSONALIDAD "TÚ A TÚ") ---
if prompt := st.chat_input("Consulta a Zynte..."):
    
    st.chat_message("user").markdown(prompt)
    st.session_state.history.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant", avatar="logo.png"):
        placeholder = st.empty()
        placeholder.markdown("...")
        
        try:
            # NUEVAS INSTRUCCIONES: Trato directo y cercano
            ctx = f"""
            Eres Zynte, entrenador personal de élite de la marca ZYNTE.
            Estás hablando directamente con tu cliente: {nombre}.
            
            SUS DATOS ACTUALES:
            - Peso: {peso} kg, Altura: {altura} cm.
            - Objetivo: {objetivo}. Nivel: {nivel}.
            
            REGLAS DE COMUNICACIÓN OBLIGATORIAS:
            1. HÁBLALE DE "TÚ": Usa la segunda persona (ej: "Tu plan...", "Debes hacer...", "Te recomiendo...").
            2. PROHIBIDO hablar en tercera persona (Nunca digas "El usuario" o "El cliente").
            3. TONO: Profesional, técnico, pero cercano y motivador. Eres su coach, no un libro.
            4. ESTRUCTURA: Usa negritas para resaltar claves y listas para pasos. Sé conciso.
            """
            
            model = genai.GenerativeModel(MODELO_USADO, system_instruction=ctx)
            
            # Construcción del historial correcta
            chat_history = [{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} for m in st.session_state.history[:-1]]
            chat = model.start_chat(history=chat_history)
            
            response = chat.send_message(prompt)
            
            placeholder.markdown(response.text)
            st.session_state.history.append({"role": "model", "content": response.text})
            
        except Exception as e:
            placeholder.error(f"Error de conexión: {e}")



