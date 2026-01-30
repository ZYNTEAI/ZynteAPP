import streamlit as st
import google.generativeai as genai

# Configuración de la página
st.set_page_config(page_title="Zynte Coach 24/7", page_icon="⚡", layout="wide")

# --- GESTIÓN DE LA API KEY (SEGURIDAD) ---
# Intentamos leer la clave desde los "Secretos" de Streamlit Cloud
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("⚠️ Falta la API Key. Configúrala en los 'Secrets' de Streamlit Cloud.")
    st.stop()

# --- MODELO INTELIGENTE (GEMINI 2.0) ---
# Usamos uno de los modelos potentes que tienes en tu lista
MODELO_USADO = 'models/gemini-1.5-flash' 

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3048/3048122.png", width=100)
    st.title("⚙️ Configura tu Perfil")
    nombre = st.text_input("Nombre", "Atleta")
    peso = st.number_input("Peso (kg)", 70.0)
    altura = st.number_input("Altura (cm)", 175)
    objetivo = st.selectbox("Objetivo", ["Ganar Músculo", "Perder Grasa", "Salud General", "Fuerza"])
    
    if st.button("🗑️ Borrar Historial"):
        st.session_state.history = []
        st.rerun()

# --- CÁLCULOS ---
imc = peso / ((altura/100)**2)
estado_imc = "Normal"
if imc >= 25: estado_imc = "Sobrepeso"
elif imc < 18.5: estado_imc = "Bajo peso"

# --- INTERFAZ PRINCIPAL ---
st.title(f"⚡ Zynte Coach | {objetivo}")
st.caption(f"🧠 Motor activo: {MODELO_USADO} (Alta Velocidad)")

# --- CHAT ---
if "history" not in st.session_state:
    st.session_state.history = []
    mensaje_inicial = f"¡Hola {nombre}! Veo que tu IMC es {imc:.1f} ({estado_imc}). Soy experto en {objetivo}. ¿Rutina o Dieta?"
    st.session_state.history.append({"role": "model", "content": mensaje_inicial})

for msg in st.session_state.history:
    role = "assistant" if msg["role"] == "model" else "user"
    icon = "⚡" if role == "assistant" else "👤"
    st.chat_message(role, avatar=icon).markdown(msg["content"])

if prompt := st.chat_input("Pregunta a tu entrenador..."):
    st.chat_message("user", avatar="👤").markdown(prompt)
    st.session_state.history.append({"role": "user", "content": prompt})
    
    try:
        # Contexto del entrenador
        contexto = f"""
        Eres Zynte, un entrenador personal experto y motivador.
        DATOS CLIENTE: Nombre: {nombre}, Peso: {peso}kg, Altura: {altura}cm, IMC: {imc:.1f}.
        OBJETIVO ACTUAL: {objetivo}.
        Responde de forma concisa, usa listas y emojis.
        """
        
        model = genai.GenerativeModel(MODELO_USADO, system_instruction=contexto)
        chat = model.start_chat(history=[{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} for m in st.session_state.history[:-1]])
        response = chat.send_message(prompt)
        
        st.chat_message("assistant", avatar="⚡").markdown(response.text)
        st.session_state.history.append({"role": "model", "content": response.text})
        
    except Exception as e:
        st.error(f"Error de conexión: {e}")

