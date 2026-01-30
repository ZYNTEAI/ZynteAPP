import streamlit as st
import google.generativeai as genai
import time

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Zynte Coach Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS para limpiar la interfaz
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            [data-testid="stSidebarNav"] {display: none!important;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- 2. CONEXIÓN SEGURA (API KEY) ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("⚠️ Falta la API Key en los Secrets.")
    st.stop()

# Modelo Rápido
MODELO_USADO = 'models/gemini-flash-latest'

# --- 3. BARRA LATERAL (DATOS EN TIEMPO REAL) ---
with st.sidebar:
    # Intenta cargar tu logo, si falla no pasa nada
    try: st.image("logo.png", width=150)
    except: st.header("⚡ ZYNTE")
    
    st.markdown("### ⚙️ Tus Datos (Se actualizan solos)")
    
    # DATOS: Al mover esto, Streamlit recarga el script entero AL INSTANTE
    nombre = st.text_input("Nombre", "Atleta")
    
    with st.expander("📏 Medidas Corporales", expanded=True):
        # Usamos sliders para que sea más rápido cambiar
        peso = st.slider("Peso (kg)", 40.0, 150.0, 70.0, 0.5)
        altura = st.slider("Altura (cm)", 120, 220, 175, 1)
        edad = st.slider("Edad", 16, 80, 25)
            
    with st.expander("🎯 Tu Objetivo Hoy", expanded=True):
        objetivo = st.selectbox("Meta Actual:", 
                              ["Ganar Masa Muscular", "Perder Grasa", "Fuerza", "Resistencia", "Salud"])
        nivel = st.select_slider("Experiencia:", options=["Principiante", "Intermedio", "Pro"])

    st.divider()
    # Botón para limpiar chat (opcional)
    if st.button("🗑️ Limpiar Chat"):
        st.session_state.history = []
        st.rerun()

# --- 4. CEREBRO MATEMÁTICO (Cálculos automáticos) ---
# Esto se recalcula CADA VEZ que mueves un dedo en la barra lateral
imc = peso / ((altura/100)**2)
estado_imc = "Peso Normal"
color_imc = "normal" 

if imc >= 25: 
    estado_imc = "Sobrepeso"
    color_imc = "off"
if imc >= 30:
    estado_imc = "Obesidad"
    color_imc = "inverse"
elif imc < 18.5: 
    estado_imc = "Bajo peso"
    color_imc = "off"

# --- 5. INTERFAZ VISUAL (DASHBOARD) ---
# Intenta cargar banner
try: st.image("banner.jpg", use_column_width=True)
except: st.title(f"⚡ Zynte Coach | {objetivo}")

# Tarjetas de datos (Se actualizan al momento)
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("IMC (Tiempo Real)", f"{imc:.1f}", estado_imc, delta_color=color_imc)
with col2:
    st.metric("Peso Actual", f"{peso} kg")
with col3:
    st.metric("Objetivo", objetivo)
with col4:
    st.metric("Nivel", nivel)

st.divider()

# --- 6. CHAT INTELIGENTE (EL TRUCO DE MEMORIA) ---

if "history" not in st.session_state:
    st.session_state.history = []
    # Mensaje inicial neutro
    st.session_state.history.append({"role": "model", "content": f"¡Hola {nombre}! Veo tus datos en el panel. Estoy listo para ajustar el plan según lo que cambies ahí. ¿Empezamos?"})

# Mostrar historial previo
for msg in st.session_state.history:
    role = "assistant" if msg["role"] == "model" else "user"
    avatar = "logo.png" if role == "assistant" else "👤" # Intenta usar tu logo como avatar
    # Si falla el avatar imagen, usa iconos por defecto
    try: st.chat_message(role, avatar=avatar).markdown(msg["content"])
    except: st.chat_message(role).markdown(msg["content"])

# --- AQUÍ ESTÁ LA MAGIA ---
if prompt := st.chat_input("Pregunta lo que quieras..."):
    
    # 1. Mostramos tu pregunta
    st.chat_message("user", avatar="👤").markdown(prompt)
    st.session_state.history.append({"role": "user", "content": prompt})
    
    # 2. Preparamos la respuesta
    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("⚡ *Consultando datos actualizados...*")
        
        try:
            # TRUCO PRO: Creamos el cerebro DE NUEVO en cada mensaje
            # con los datos EXACTOS que hay ahora mismo en la barra lateral.
            instruccion_actualizada = f"""
            Eres Zynte, entrenador de élite.
            DATOS EN TIEMPO REAL DEL CLIENTE (ÚSALOS SIEMPRE):
            - Nombre: {nombre}
            - Peso ACTUAL: {peso} kg (¡Si esto cambia, ajusta tus consejos!)
            - Altura: {altura} cm
            - IMC: {imc:.1f}
            - Objetivo HOY: {objetivo}
            - Nivel: {nivel}
            
            Instrucciones: Responde a la pregunta del usuario "{prompt}" basándote en estos datos exactos.
            Sé breve, directo y usa listas.
            """
            
            # Usamos el modelo con la instrucción FRESCA
            model = genai.GenerativeModel(MODELO_USADO, system_instruction=instruccion_actualizada)
            
            # Pasamos el historial para que recuerde de qué hablábamos, pero el contexto es nuevo
            chat = model.start_chat(history=[{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} for m in st.session_state.history[:-1]])
            
            response = chat.send_message(prompt)
            
            # Efecto escritura
            placeholder.markdown(response.text)
            
            # Guardamos
            st.session_state.history.append({"role": "model", "content": response.text})
            
        except Exception as e:
            placeholder.error(f"Error: {e}")
