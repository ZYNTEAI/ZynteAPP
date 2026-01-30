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

# --- 2. ESTILOS CSS PREMIUM ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* FONDO DEGRADADO */
    [data-testid="stAppViewContainer"] {
        background: radial-gradient(ellipse at top, #1b2735 0%, #090a0f 100%);
    }
    [data-testid="stHeader"] {
        background: transparent;
    }

    /* TEXTOS */
    .hero-title {
        font-size: 3.5rem;
        font-weight: 800;
        background: linear-gradient(to right, #ffffff, #33ffaa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 10px;
        text-shadow: 0 0 30px rgba(51, 255, 170, 0.2);
    }
    .hero-subtitle {
        font-size: 1.3rem;
        text-align: center;
        color: #a0aaba;
        margin-bottom: 40px;
    }
    
    /* TARJETAS */
    .price-card {
        background-color: rgba(26, 26, 26, 0.8);
        backdrop-filter: blur(10px);
        border: 1px solid #333;
        border-radius: 15px;
        padding: 25px;
        text-align: center;
        transition: 0.3s;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        height: 100%;
    }
    .price-card:hover {
        border-color: #33ffaa;
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(51, 255, 170, 0.2);
    }
    
    /* INPUTS */
    .stTextInput input {
        background-color: rgba(255,255,255,0.05) !important;
        border: 1px solid #333 !important;
        color: white !important;
    }
    
    /* BOTONES */
    div.stButton > button {
        border-radius: 8px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CONEXIÓN API ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except:
    pass

MODELO_USADO = 'models/gemini-flash-latest'

# ==============================================================================
# ℹ️ PÁGINAS DE DETALLE (INFORMACIÓN)
# ==============================================================================

def mostrar_info_ia():
    """Detalle: Inteligencia Artificial"""
    st.markdown("## 🧠 El Cerebro de Zynte")
    st.write("")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("""
        <div class="price-card" style="text-align: left;">
            <h3>Adiós a las plantillas</h3>
            <p style="color:#ccc;">La mayoría de apps usan "Copy-Paste". Zynte es diferente.</p>
            <p>Utilizamos <b>Google Gemini Pro</b> para analizar 12 puntos de datos biométricos en tiempo real.
            La IA entiende si tienes una lesión, si prefieres entrenar fuerza o resistencia, y ajusta el volumen de cada serie matemáticamente.</p>
            <br>
            <p>✅ <b>Hiper-Personalización:</b> Ningún plan es igual a otro.</p>
            <p>✅ <b>Adaptación:</b> Entiende el contexto (edad, nivel, material).</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.info("💡 **Dato Curioso:** Zynte procesa más de 5.000 combinaciones de ejercicios posibles antes de elegir los 6-8 perfectos para tu sesión.")

    st.write("")
    if st.button("⬅️ Volver al Inicio"):
        st.session_state.page = 'landing'
        st.rerun()

def mostrar_info_velocidad():
    """Detalle: Velocidad"""
    st.markdown("## ⚡ Velocidad Sónica")
    st.write("")
    
    st.markdown("""
    <div class="price-card">
        <h3>El tiempo es el único recurso que no vuelve</h3>
        <hr style="border-color:#333;">
        <div style="display:flex; justify-content:space-around; align-items:center; margin-top:20px;">
            <div>
                <h1 style="color:red; font-size:4rem;">48h</h1>
                <p>Entrenador Online Tradicional</p>
            </div>
            <div style="font-size:3rem;">VS</div>
            <div>
                <h1 style="color:#33ffaa; font-size:4rem;">4.8s</h1>
                <p>Zynte AI Coach</p>
            </div>
        </div>
        <br>
        <p style="color:#ccc;">No esperes correos electrónicos. Tu rutina se genera en el mismo instante en que decides cambiar tu vida.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    if st.button("⬅️ Volver al Inicio"):
        st.session_state.page = 'landing'
        st.rerun()

def mostrar_info_pdf():
    """Detalle: PDF"""
    st.markdown("## 📄 Documentación Profesional")
    st.write("")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("""
        <div class="price-card" style="text-align: left;">
            <h3>Lleva tu plan al gimnasio</h3>
            <p style="color:#ccc;">Sabemos que mirar el móvil entre series distrae. Por eso creamos el <b>Informe Zynte</b>.</p>
            <p>Al terminar tu sesión con la IA, recibirás un documento PDF formateado en A4 listo para imprimir o guardar.</p>
            <br>
            <ul style="color:#ccc;">
                <li>Cabecera con tu Nombre y Fecha.</li>
                <li>Tabla de ejercicios clara.</li>
                <li>Resumen de objetivos y cargas.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.success("📂 **Exclusivo PRO:** Esta función está reservada para los miembros del plan Élite (19.99€).")
        st.caption("El diseño limpio y sin distracciones te ayuda a mantener el foco.")

    st.write("")
    if st.button("⬅️ Volver al Inicio"):
        st.session_state.page = 'landing'
        st.rerun()

# ==============================================================================
# 🌟 VISTAS PRINCIPALES
# ==============================================================================

def mostrar_landing():
    """Portada Principal"""
    st.write("") 
    st.write("") 
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        try: st.image("logo.png", use_column_width=True)
        except: st.title("ZYNTE")
    
    st.markdown('<p class="hero-title">TU ENTRENADOR INTELIGENTE</p>', unsafe_allow_html=True)
    st.markdown('<p class="hero-subtitle">Planes de entrenamiento de élite generados en segundos.</p>', unsafe_allow_html=True)
    
    col_a, col_b, col_c = st.columns([1, 1, 1])
    with col_b:
        st.write("")
        if st.button("🚀 EMPEZAR AHORA", use_container_width=True, type="primary"):
            st.session_state.page = 'login'
            st.rerun()
        st.write("")
        st.write("")

    # --- SECCIÓN DE TARJETAS INTERACTIVAS ---
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("""<div class='price-card' style='text-align:left; border:none; background:transparent; box-shadow:none;'>
        <h3>🧠 Inteligencia Real</h3>
        <p style='color:#a0aaba; min-height:60px;'>Zynte analiza tu biometría y crea algo único para ti.</p>
        </div>""", unsafe_allow_html=True)
        if st.button("Saber más sobre IA", key="btn_ia"):
            st.session_state.page = 'info_ia'
            st.rerun()
            
    with c2:
        st.markdown("""<div class='price-card' style='text-align:left; border:none; background:transparent; box-shadow:none;'>
        <h3>⚡ Velocidad Sónica</h3>
        <p style='color:#a0aaba; min-height:60px;'>Tu plan completo listo antes de que te ates los cordones.</p>
        </div>""", unsafe_allow_html=True)
        if st.button("Ver comparativa", key="btn_vel"):
            st.session_state.page = 'info_vel'
            st.rerun()
            
    with c3:
        st.markdown("""<div class='price-card' style='text-align:left; border:none; background:transparent; box-shadow:none;'>
        <h3>📄 Informes PDF</h3>
        <p style='color:#a0aaba; min-height:60px;'>Descarga tu rutina profesional lista para imprimir.</p>
        </div>""", unsafe_allow_html=True)
        if st.button("Ver ejemplo PDF", key="btn_pdf"):
            st.session_state.page = 'info_pdf'
            st.rerun()

def mostrar_login():
    st.markdown("## 🔐 Acceso Seguro")
    st.caption("Simulación de acceso.")
    st.write("")
    lc1, lc2, lc3 = st.columns([1,2,1])
    with lc2:
        tab1, tab2 = st.tabs(["Iniciar Sesión", "Crear Cuenta"])
        with tab1:
            st.write("")
            st.text_input("Email", key="login_email")
            st.text_input("Contraseña", type="password", key="login_pass")
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
            st.write("")
            if st.button("Registrarse Gratis", use_container_width=True):
                st.success("Cuenta creada ficticia.")
    st.write("")
    st.write("---")
    if st.button("⬅️ Volver a Inicio"):
        st.session_state.page = 'landing'
        st.rerun()

def mostrar_pricing():
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
# 🚀 ROUTER PRINCIPAL
# ==============================================================================

def main():
    if 'page' not in st.session_state: st.session_state.page = 'landing'
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False
    if 'is_premium' not in st.session_state: st.session_state.is_premium = False

    # SISTEMA DE NAVEGACIÓN
    if st.session_state.page == 'landing': mostrar_landing()
    elif st.session_state.page == 'info_ia': mostrar_info_ia()
    elif st.session_state.page == 'info_vel': mostrar_info_velocidad()
    elif st.session_state.page == 'info_pdf': mostrar_info_pdf()
    elif st.session_state.page == 'login': mostrar_login()
    elif st.session_state.page == 'pricing': mostrar_pricing()
    elif st.session_state.page == 'app': app_principal()
    else: st.session_state.page = 'landing'; st.rerun()

if __name__ == "__main__":
    main()
