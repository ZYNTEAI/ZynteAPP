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
        <p style='color:#a0aaba;'>Descarga tu rutina profesional formateada y lista para imprimir.</p>
        </div>""", unsafe_allow_html=True)

def mostrar_login():
    """Página de Acceso"""
    st.markdown("## 🔐 Acceso Seguro")
    st.caption("Simulación de acceso. Utiliza cualquier dato.")
    
    st.write("")
    
    # Usamos columnas para centrar el login
    lc1, lc2, lc3 = st.columns([1,2,1])
    with lc2:
        tab1, tab2 = st.tabs(["Iniciar Sesión", "Crear Cuenta"])
        
        with tab1:
            st.write("")
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Contraseña", type="password", key="login_pass")
            st.write("")
            if st.button("Entrar ▶", type="primary", use_container_width=True):
                st.session_state.logged_in = True
                st.session_state.page = 'pricing'
                st.success("Acceso concedido.")
                time.sleep(0.5)
                st.rerun()
                
        with tab2:
            st.write("")
            st.text_input("Nuevo Email")
            st.text_input("Nueva Contraseña", type="password")
            st.write("")
            if st.button("Registrarse Gratis", use_container_width=True):
                st.success("Cuenta creada ficticia.")

    st.write("")
    st.write("---")
    if st.button("⬅️ Volver a Inicio"):
        st.session_state.page = 'landing'
        st.rerun()

def mostrar_pricing():
    """Página de Precios"""
    st.markdown("<h2 style='text-align: center; margin-top:20px;'>Elige tu Nivel</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color:#a0aaba; margin-bottom:40px;'>Invierte en ti mismo.</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class='price-card'>
            <h3>🌱 Starter</h3>
            <h1 style='font-size: 3.5rem; margin: 10px 0;'>0€</h1>
            <p style='color:#a0aaba;'>Acceso básico de prueba</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("Continuar Gratis", use_container_width=True):
             st.session_state.is_premium = False
             st.session_state.page = 'app'
             st.rerun()

    with col2:
        st.markdown("""
        <div class='price-card' style='border-color: #33ffaa; box-shadow: 0 0 30px rgba(51, 255, 170, 0.15);'>
            <h3 style='color: #33ffaa;'>🔥 Zynte PRO</h3>
            <h1 style='font-size: 3.5rem; margin: 10px 0;'>19.99€</h1>
            <p style='color:#a0aaba;'>Pago único. PDFs Ilimitados.</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("💳 SIMULAR PAGO PRO", type="primary", use_container_width=True):
            with st.spinner("Conectando con pasarela segura..."):
                time.sleep(2)
            st.session_state.is_premium = True
            st.session_state.page = 'app'
            st.balloons()
            st.rerun()

def app_principal():
    """La App Principal"""
    
    # --- PDF Class ---
    class PDF(FPDF):
        def header(self):
            try: self.image('logo.png', 10, 8, 33)
            except: pass
            self.set_font('Arial', 'B', 15)
            self.cell(80)
            self.cell(30, 10, 'ZYNTE | INFORME DE ENTRENAMIENTO', 0, 0, 'C')
            self.ln(20)
        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Pagina {self.page_no()} - Generado por Zynte AI', 0, 0, 'C')

    def crear_pdf(historial, nombre, peso, objetivo):
        pdf = PDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.set_fill_color(200, 220, 255)
        pdf.cell(0, 10, txt=f"CLIENTE: {nombre} | FECHA: {datetime.date.today()}", ln=1, align='L', fill=True)
        pdf.cell(0, 10, txt=f"PERFIL: {peso}kg | META: {objetivo}", ln=1, align='L', fill=True)
        pdf.ln(10)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, txt="PLAN PERSONALIZADO:", ln=1)
        pdf.set_font("Arial", size=11)
        for mensaje in historial:
            if mensaje["role"] == "model":
                texto_limpio = mensaje["content"].replace("**", "").replace("*", "-")
                pdf.multi_cell(0, 7, txt=texto_limpio)
                pdf.ln(5)
                pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                pdf.ln(5)
        return pdf.output(dest="S").encode("latin-1", "replace")

    # --- Sidebar ---
    with st.sidebar:
        try: st.image("logo.png", width=180)
        except: st.header("ZYNTE")
        
        if st.session_state.get('is_premium', False):
            st.success("🌟 PLAN PRO ACTIVO")
        else:
            st.info("🌱 PLAN GRATUITO")
            if st.button("⬆️ Pasar a PRO", use_container_width=True):
                st.session_state.page = 'pricing'
                st.rerun()

        st.write("---")
        nombre = st.text_input("Nombre", "Atleta")
        with st.expander("Biometría", expanded=True):
            peso = st.slider("Peso (kg)", 40.0, 150.0, 72.5, 0.5)
            altura = st.slider("Altura (cm)", 120, 220, 176, 1)
            edad = st.slider("Edad", 16, 80, 25)
        with st.expander("Planificación", expanded=True):
            objetivo = st.selectbox("Objetivo:", ["Ganar Masa Muscular", "Perder Grasa", "Fuerza", "Resistencia"])
            nivel = st.select_slider("Nivel:", options=["Principiante", "Intermedio", "Avanzado"])

        st.write("---")
        if "history" in st.session_state and len(st.session_state.history) > 1:
            if st.session_state.get('is_premium', False):
                pdf_bytes = crear_pdf(st.session_state.history, nombre, peso, objetivo)
                st.download_button("📄 DESCARGAR PDF", pdf_bytes, f"Plan_{nombre}.pdf", "application/pdf", use_container_width=True)
            else:
                st.warning("🔒 PDF solo para PROs")
        
        st.write("---")
        if st.button("Cerrar Sesión", use_container_width=True):
            st.session_state.page = 'landing'
            st.session_state.logged_in = False
            st.rerun()
            
        st.caption("© 2026 Zynte AI Coach")

    # --- Dashboard ---
    imc = peso / ((altura/100)**2)
    estado_imc = "Normal"
    if imc >= 25: estado_imc = "Sobrepeso"
    if imc < 18.5: estado_imc = "Bajo peso"

    try: st.image("banner.jpg", use_column_width=True)
    except: st.title("ZYNTE COACH")

    col1, col2, col3, col4 = st.columns([1, 0.7, 2, 1.3])
    with col1: st.metric("IMC", f"{imc:.1f}", estado_imc)
    with col2: st.metric("Peso", f"{peso} kg")
    with col3: st.metric("Objetivo", objetivo)
    with col4: st.metric("Nivel", nivel)
    st.divider()
    st.caption("⚠️ **Aviso:** Zynte es un asistente informativo. Consulta siempre con un profesional.")

    # --- Chat ---
    if "history" not in st.session_state:
        st.session_state.history = []
        st.session_state.history.append({"role": "model", "content": f"Hola {nombre}. Listo para diseñar tu plan de {objetivo}. ¿Empezamos?"})

    for msg in st.session_state.history:
        role = "assistant" if msg["role"] == "model" else "user"
        avatar = "logo.png" if role == "assistant" else None
        try: st.chat_message(role, avatar=avatar).markdown(msg["content"])
        except: st.chat_message(role).markdown(msg["content"])

    if prompt := st.chat_input("Consulta a Zynte..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.history.append({"role": "user", "content": prompt})
        
        with st.chat_message("assistant", avatar="logo.png"):
            placeholder = st.empty()
            placeholder.markdown("...")
            try:
                ctx = f"Eres Zynte, entrenador de élite. Hablas con {nombre}. Datos: {peso}kg, {objetivo}."
                model = genai.GenerativeModel(MODELO_USADO, system_instruction=ctx)
                chat_history = [{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} for m in st.session_state.history[:-1]]
                chat = model.start_chat(history=chat_history)
                
                try:
                    response = chat.send_message(prompt)
                except Exception as e:
                    if "429" in str(e):
                        placeholder.warning("⏳ Tráfico alto, pensando...")
                        time.sleep(6)
                        response = chat.send_message(prompt)
                    else: raise e
                
                placeholder.markdown(response.text)
                st.session_state.history.append({"role": "model", "content": response.text})
            except Exception as e:
                placeholder.error(f"Error: {e}")

# ==============================================================================
# 🚀 MAIN
# ==============================================================================

def main():
    if 'page' not in st.session_state:
        st.session_state.page = 'landing'
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'is_premium' not in st.session_state:
        st.session_state.is_premium = False

    if st.session_state.page == 'landing':
        mostrar_landing()
    elif st.session_state.page == 'login':
        mostrar_login()
    elif st.session_state.page == 'pricing':
        mostrar_pricing()
    elif st.session_state.page == 'app':
        app_principal()
    else:
        st.session_state.page = 'landing'
        st.rerun()

if __name__ == "__main__":
    main()
