import streamlit as st
import google.generativeai as genai
import time

# --- CONFIGURACIÓN DE PÁGINA PRO ---
st.set_page_config(
    page_title="Zynte Coach | Elite AI Training",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS PERSONALIZADO PARA DAR TOQUE PRO ---
# Esto oculta el menú de hamburguesa de Streamlit y el pie de página para que se vea más "app propia"
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            .stDeployButton {visibility: hidden;}
            [data-testid="stSidebarNav"] {display: none!important;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- GESTIÓN DE LA API KEY ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("⚠️ Error crítico: No se encuentra la API Key en los Secrets.")
    st.stop()

# Modelo Rápido y Estable
MODELO_USADO = 'models/gemini-flash-latest'

# --- BARRA LATERAL (PANEL DE CONTROL DEL CLIENTE) ---
with st.sidebar:
    # Logo ficticio o icono pro
   # CAMBIO: Usamos tu logo.png
    st.image("logo.png", width=150) # He subido un poco el tamaño para que luzca
    st.title("Panel del Atleta")
    st.markdown("---")
    
    with st.expander("👤 Tus Datos Personales", expanded=True):
        nombre = st.text_input("Nombre o Apodo", "Atleta")
        genero = st.selectbox("Género", ["Masculino", "Femenino", "Otro"])
        edad = st.slider("Edad", 16, 70, 25)
        
    with st.expander("📏 Biometría y Estado", expanded=True):
        col_peso, col_altura = st.columns(2)
        with col_peso:
            peso = st.number_input("Peso (kg)", 40.0, 150.0, 70.0, step=0.5)
        with col_altura:
            altura = st.number_input("Altura (cm)", 120, 220, 175, step=1)
            
    with st.expander("🎯 Objetivo Principal", expanded=True):
        objetivo = st.selectbox("Selecciona tu meta:", 
                              ["Ganar Masa Muscular", "Perder Grasa Corporal", "Recomposición (Ambas)", "Fuerza y Potencia", "Salud y Mantenimiento"])
        nivel = st.select_slider("Nivel de Experiencia:", options=["Principiante", "Intermedio", "Avanzado"])

    st.markdown("---")
    if st.button("🔄 Reiniciar Sesión de Chat", type="primary"):
        st.session_state.history = []
        st.rerun()
    st.caption(f"🚀 Motor IA: {MODELO_USADO}")

# --- CÁLCULOS AUTOMÁTICOS (EL CEREBRO DETRÁS) ---
imc = peso / ((altura/100)**2)
estado_imc = "Peso Normal"
color_imc = "normal" # verde
if imc >= 25: 
    estado_imc = "Sobrepeso"
    color_imc = "off" # amarillo/naranja
if imc >= 30:
    estado_imc = "Obesidad"
    color_imc = "inverse" # rojo
elif imc < 18.5: 
    estado_imc = "Bajo peso"
    color_imc = "off"

# --- ÁREA PRINCIPAL (EL "DASHBOARD") ---

# 1. Banner de cabecera (Puedes cambiar la URL por una imagen tuya propia si la subes a internet)
st.image("banner.jpg", use_column_width=True)
st.title(f"⚡ Zynte Coach | {objetivo}")

# 2. Resumen Visual del Cliente (Usando columnas y métricas)
# Esto le da un aspecto mucho más "app de datos" y profesional.
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="Tu IMC Actual", value=f"{imc:.1f}", delta=estado_imc, delta_color=color_imc)
with col2:
    st.metric(label="Peso Objetivo (Aprox)", value=f"{peso} kg", delta="Mantener/Mejorar", delta_color="off")
with col3:
    st.metric(label="Nivel", value=nivel)
with col4:
    st.metric(label="Plan", value="Premium IA")

st.divider() # Línea separadora elegante

# --- ÁREA DE CHAT PROFESIONAL ---

# Mensaje de bienvenida condicional (solo si el historial está vacío)
if "history" not in st.session_state:
    st.session_state.history = []
    # Creamos un contexto inicial potente para la IA
    contexto_inicial = f"""
    Actúa como Zynte, un entrenador personal de élite y nutricionista deportivo con años de experiencia.
    Tu cliente se llama {nombre}. Es {genero}, de {edad} años. Nivel {nivel}.
    Sus datos actuales son: Peso {peso}kg, Altura {altura}cm. Su IMC es {imc:.1f} ({estado_imc}).
    Su OBJETIVO PRINCIPAL es: {objetivo}.
    
    Tu estilo de comunicación debe ser: Profesional pero motivador, basado en ciencia, directo y empático.
    Usa formato Markdown (negritas, listas) para que tus respuestas sean fáciles de leer.
    
    Dale una bienvenida breve, reconociendo sus datos y su objetivo, y pregúntale por dónde quiere empezar.
    """
    
    # Iniciamos el chat invisiblemente para obtener el primer mensaje
    try:
        model_init = genai.GenerativeModel(MODELO_USADO, system_instruction=contexto_inicial)
        chat_init = model_init.start_chat(history=[])
        response_init = chat_init.send_message(f"Hola, soy {nombre}. Ya he metido mis datos.")
        st.session_state.history.append({"role": "model", "content": response_init.text})
    except:
        st.session_state.history.append({"role": "model", "content": f"¡Hola {nombre}! Veo que tu objetivo es {objetivo}. ¿Empezamos por la dieta o el entrenamiento?"})

# Mostrar historial
for msg in st.session_state.history:
    role = "assistant" if msg["role"] == "model" else "user"
    # Iconos personalizados para que se vea más pro
    avatar = "https://cdn-icons-png.flaticon.com/512/3048/3048122.png" if role == "assistant" else "👤"
    with st.chat_message(role, avatar=avatar):
        st.markdown(msg["content"])

# Input del usuario
if prompt := st.chat_input("Escribe aquí tu consulta al entrenador..."):
    # 1. Mostrar mensaje del usuario
    st.chat_message("user", avatar="👤").markdown(prompt)
    st.session_state.history.append({"role": "user", "content": prompt})
    
    # 2. Generar respuesta IA
    with st.chat_message("assistant", avatar="https://cdn-icons-png.flaticon.com/512/3048/3048122.png"):
        message_placeholder = st.empty()
        message_placeholder.markdown("⚡ *Zynte está analizando tu caso...*") # Efecto de "pensando"
        
        try:
            # Re-inyectamos el contexto en cada turno para asegurar coherencia
            contexto_continuo = f"Recordatorio del perfil del cliente: {nombre}, {peso}kg, Objetivo: {objetivo}, Nivel: {nivel}."
            
            model = genai.GenerativeModel(MODELO_USADO, system_instruction=contexto_continuo)
            chat = model.start_chat(history=[{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} for m in st.session_state.history[:-1]])
            
            response = chat.send_message(prompt)
            
            # Efecto de escritura tipo máquina de escribir (opcional, lo hace más dinámico)
            full_response = ""
            for chunk in response.text.split():
                full_response += chunk + " "
                time.sleep(0.02) # Pequeña pausa para efecto visual
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
            
            st.session_state.history.append({"role": "model", "content": full_response})
            
        except Exception as e:
            message_placeholder.error(f"❌ Tuve un problema de conexión. Por favor, intenta preguntar de nuevo. (Error: {e})")

