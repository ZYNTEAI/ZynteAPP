import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import datetime
import time

# --- 1. CONFIGURACIÓN GLOBAL ---
st.set_page_config(page_title="Zynte | Elite AI Coach", page_icon="logo.png", layout="wide", initial_sidebar_state="collapsed")

# ESTILOS CSS PRO (Modo Oscuro + Landing Page)
st.markdown("""
    <style>
    /* Ocultar elementos de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
    
    /* Estilos Landing Page */
    .hero-title {
        font-size: 60px;
        font-weight: 800;
        background: -webkit-linear-gradient(#eee, #33ffaa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0px;
    }
    .hero-subtitle {
        font-size: 24px;
        text-align: center;
        color: #ddd;
        margin-bottom: 30px;
    }
    .price-card {
        background-color: #0e1117;
        border: 1px solid #333;
        border-radius: 15px;
        padding: 30px;
        text-align: center;
        transition: transform 0.3s;
    }
    .price-card:hover {
        transform: scale(1.05);
        border-color: #33ffaa;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. GESTIÓN DE ESTADO (SESIONES) ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'is_premium' not in st.session_state: st.session_state.is_premium = False
if 'page' not in st.session_state: st.session_state.page = 'landing'

# --- 3. CONEXIÓN API ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except:
    pass # No mostramos error en la landing page para no afear

MODELO_USADO = 'models/gemini-flash-latest'

# ==============================================================================
# 🌟 ZONA 1: LANDING PAGE (PORTADA)
# ==============================================================================
def mostrar_landing():
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        try: st.image("logo.png", use_column_width=True)
        except: pass
    
    st.markdown('<p class="hero-title">TU ENTRENADOR INTELIGENTE</p>', unsafe_allow_html=True)
    st.markdown('<p class="hero-subtitle">Planes de entrenamiento de élite generados por IA en segundos.</p>', unsafe_allow_html=True)
    
    st.write("---")
    
    col_a, col_b, col_c = st.columns([1, 1, 1])
    with col_b:
        if st.button("🚀 EMPEZAR AHORA", use_container_width=True, type="primary"):
            st.session_state.page = 'login'
            st.rerun()

    # Características (Feature Grid)
    st.write("")
    st.subheader("¿Por qué elegir Zynte?")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info("🧠 **Inteligencia Real**\n\nNo son plantillas. Zynte analiza tu biometría y crea algo único.")
    with c2:
        st.warning("⚡ **Velocidad Sónica**\n\nOlvídate de esperar días. Tu plan completo en menos de 10 segundos.")
    with c3:
        st.success("📄 **Informes PDF**\n\nDescarga tu rutina profesional formateada lista para imprimir.")

# ==============================================================================
# 🔐 ZONA 2: LOGIN / REGISTRO
# ==============================================================================
def mostrar_login():
    st.markdown("## 🔐 Acceso a Zynte")
    
    tab1, tab2 = st.tabs(["Iniciar Sesión", "Crear Cuenta"])
    
    with tab1:
        email = st.text_input("Email")
        password = st.text_input("Contraseña", type="password")
        if st.button("Entrar"):
            if email and password:
                st.session_state.logged_in = True
                st.session_state.page = 'pricing' # Al loguearse, va a pagar
                st.success("¡Bienvenido de nuevo!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Por favor rellena los campos.")
                
    with tab2:
        st.text_input("Nuevo Email")
        st.text_input("Nueva Contraseña", type="password")
        if st.button("Registrarse Gratis"):
            st.success("Cuenta creada. Por favor inicia sesión.")

    if st.button("⬅️ Volver al Inicio"):
        st.session_state.page = 'landing'
        st.rerun()

# ==============================================================================
# 💎 ZONA 3: PRICING (PAGOS)
# ==============================================================================
def mostrar_pricing():
    st.markdown("<h2 style='text-align: center;'>Elige tu Nivel</h2>", unsafe_allow_html=True)
    st.write("")
    
    col1, col2 = st.columns(2)
    
    # PLAN GRATUITO
    with col1:
        st.markdown("""
        <div class='price-card'>
            <h3>🌱 Starter</h3>
            <h1>0€</h1>
            <p>Para curiosos</p>
            <hr>
            <p>❌ Sin PDF descargable</p>
            <p>❌ Límite de mensajes</p>
            <p>✅ Chat básico</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Continuar Gratis"):
             st.session_state.is_premium = False
             st.session_state.page = 'app'
             st.rerun()

    # PLAN PRO
    with col2:
        st.markdown("""
        <div class='price-card' style='border-color: #33ffaa; box-shadow: 0 0 20px rgba(51, 255, 170, 0.2);'>
            <h3 style='color: #33ffaa;'>🔥 Zynte PRO</h3>
            <h1>9.99€</h1>
            <p>Pago único / mes</p>
            <hr>
            <p>✅ <b>PDFs Ilimitados</b></p>
            <p>✅ <b>Modo Entrenador Élite</b></p>
            <p>✅ <b>Prioridad de red</b></p>
        </div>
        """, unsafe_allow_html=True)
        # Aquí iría el enlace a Stripe real
        if st.button("💳 PAGAR AHORA (Simulación)", type="primary"):
            with st.spinner("Procesando pago seguro..."):
                time.sleep(2) # Simulamos tiempo de banco
            st.session_state.is_premium = True
            st.session_state.page = 'app'
            st.balloons()
            st.rerun()

# ==============================================================================
# 🤖 ZONA 4: LA APP (EL CEREBRO IA)
# ==============================================================================
def app_principal():
    # --- Clases y Funciones de la APP original ---
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
            self.cell(0, 10, f'Pagina {self.page_no()} - Zynte AI', 0, 0, 'C')

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
                texto_limpio = mensaje["content"].replace("**", "").replace("*", "-").replace("##", "")
                pdf.multi_cell(0, 7, txt=texto_limpio)
                pdf.ln(5)
                pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                pdf.ln(5)
        return pdf.output(dest="S").encode("latin-1", "replace")

    #
