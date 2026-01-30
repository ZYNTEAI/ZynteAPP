import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import datetime
import time  # <--- AÑADIDO: Necesario para hacer la pausa de espera

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Zynte Coach", page_icon="logo.png", layout="wide")

# Estilos CSS (Modo Oscuro/Pro)
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stSidebarNav"] {display: none!important;}
    .stDeployButton {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONEXIÓN SEGURA ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("Error: API Key no configurada.")
    st.stop()

MODELO_USADO = 'models/gemini-flash-latest'

# --- 3. FUNCIÓN GENERADORA DE PDF ---
class PDF(FPDF):
    def header(self):
        # Intentamos poner el logo, si no existe, solo texto
        try: self.image('logo.png', 10, 8, 33)
        except: pass
        self.set_font('Arial', 'B', 15)
        self.cell(80) # Mover a la derecha
        self.cell(30, 10, 'ZYNTE | INFORME DE ENTRENAMIENTO', 0, 0, 'C')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()} - Generado por Zynte AI Coach', 0, 0, 'C')

def crear_pdf(historial, nombre, peso, objetivo):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # 1. Cabecera con datos del cliente
    pdf.set_fill_color(200, 220, 255) # Color azulito claro de fondo
    pdf.cell(0, 10, txt=f"CLIENTE: {nombre} | FECHA: {datetime.date.today()}", ln=1, align='L', fill=True)
    pdf.cell(0, 10, txt=f"PERFIL: {peso}kg | META: {objetivo}", ln=1, align='L', fill=True)
    pdf.ln(10)
    
    # 2. El contenido del chat
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, txt="PLAN PERSONALIZADO:", ln=1)
    pdf.set_font("Arial", size=11)
    
    # Limpieza de texto (Gemini usa **negritas**, las quitamos para el PDF simple)
    for mensaje in historial:
        if mensaje["role"] == "model": # Solo guardamos lo que dice el entrenador
            texto_limpio = mensaje["content"].replace("**", "").replace("*", "-")
            pdf.multi_cell(0, 7, txt=texto_limpio)
            pdf.ln(5)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y()) # Línea separadora
            pdf.ln(5)
            
    return pdf.output(dest="S").encode("latin-1", "replace") 

# --- 4. BARRA LATERAL ---
with st.sidebar:
    try: st.image("logo.png", width=180)
    except: st.header("ZYNTE")
    st.write("---")
    st.caption("DATOS DEL CLIENTE")
    nombre = st.text_input("Nombre", "Atleta")
    with st.expander("Biometría", expanded=True):
        peso = st.slider("Peso (kg)", 40.0, 150.0, 72.5, 0.5)
        altura = st.slider("Altura (cm)", 120, 220, 176, 1)
        edad = st.slider("Edad", 16, 80, 25)
    with st.expander("Planificación", expanded=True):
        objetivo = st.selectbox("Objetivo:", ["Ganar Masa Muscular", "Perder Grasa", "Fuerza", "Resistencia"])
        nivel = st.select_slider("Nivel:", options=["Principiante", "Intermedio", "Avanzado"])
    
    st.write("---")
    
    # --- BOTÓN DE PDF EN LA BARRA LATERAL ---
    if "history" in st.session_state and len(st.session_state.history) > 1:
        pdf_bytes = crear_pdf(st.session_state.history, nombre, peso, objetivo)
        st.download_button(
            label="📄 Descargar Informe PDF",
            data=pdf_bytes,
            file_name=f"Plan_Zynte_{nombre}.pdf",
            mime="application/pdf"
        )

    if st.button("Reiniciar Chat"):
        st.session_state.history = []
        st.rerun()

# --- 5. DASHBOARD ---
imc = peso / ((altura/100)**2)
estado_imc = "Normal"
if imc >= 25: estado_imc = "Sobrepeso"
if imc >= 30: estado_imc = "Obesidad"
elif imc < 18.5: estado_imc = "Bajo peso"

try: st.image("banner.jpg", use_column_width=True)
except: st.title("ZYNTE COACH")

col1, col2, col3, col4 = st.columns([1, 0.7, 2, 1.3])
with col1: st.metric("IMC", f"{imc:.1f}", estado_imc)
with col2: st.metric("Peso", f"{peso} kg")
with col3: st.metric("Objetivo", objetivo)
with col4: st.metric("Nivel", nivel)
st.divider()
# --- AVISO LEGAL IMPORTANTE ---
st.caption("⚠️ **Aviso:** Zynte AI es un asistente informativo. Consulta siempre con un profesional de la salud antes de iniciar un programa físico.")
# --- 6. CHAT ---
if "history" not in st.session_state:
    st.session_state.history = []
    # Usamos una frase corta y segura para evitar errores de corte de línea
    inicio = f"Sesión iniciada. Usuario: {nombre}. Objetivo: {objetivo}. Esperando comandos."
    st.session_state.history.append({"role": "model", "content": inicio})

for msg in st.session_state.history:
    role = "assistant" if msg["role"] == "model" else "user"
    avatar = "logo.png" if role == "assistant" else None
    try: st.chat_message(role, avatar=avatar).markdown(msg["content"])
    except: st.chat_message(role).markdown(msg["content"])

# --- 7. INPUT CON SISTEMA DE ESPERA AMABLE ---
if prompt := st.chat_input("Consulta a Zynte..."):
    
    st.chat_message("user").markdown(prompt)
    st.session_state.history.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant", avatar="logo.png"):
        placeholder = st.empty()
        placeholder.markdown("...")
        
        try:
            ctx = f"""
            Eres Zynte, entrenador de élite. Habla de TÚ a TÚ con {nombre}.
            DATOS: {peso}kg, {altura}cm, Objetivo: {objetivo}.
            Responde técnico pero motivador. Usa listas.
            """
            model = genai.GenerativeModel(MODELO_USADO, system_instruction=ctx)
            chat_history = [{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} for m in st.session_state.history[:-1]]
            chat = model.start_chat(history=chat_history)
            
            # --- AQUÍ EMPIEZA LA MAGIA DE LA ESPERA ---
            try:
                # Intento 1: Enviar mensaje normal
                response = chat.send_message(prompt)
            except Exception as e:
                # Si falla por cuota (Error 429), entramos aquí
                if "429" in str(e):
                    placeholder.warning("⏳ Estoy pensando intensamente, dame unos segundos...")
                    time.sleep(6) # Esperamos 6 segundos
                    try:
                        # Intento 2: Reintentar automáticamente
                        response = chat.send_message(prompt)
                    except:
                        placeholder.error("🐢 Sigo saturado. Por favor espera 1 minuto y vuelve a preguntar.")
                        st.stop()
                else:
                    raise e # Si es otro error distinto, que avise
            # ------------------------------------------

            placeholder.markdown(response.text)
            st.session_state.history.append({"role": "model", "content": response.text})
            
        except Exception as e:
            placeholder.error(f"Error técnico: {e}")

# --- NUEVO: FIRMA ---
    st.caption("© 2024 Zynte AI Coach v1.0")
