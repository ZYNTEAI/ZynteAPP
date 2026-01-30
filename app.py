import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import datetime
import time
import sqlite3
import re  # <--- Librería para validación matemática de emails

# --- 1. CONFIGURACIÓN INICIAL ---
st.set_page_config(
    page_title="Zynte | Elite Coach", 
    page_icon="logo.png", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- 2. GESTIÓN DE BASE DE DATOS Y SEGURIDAD ---
def init_db():
    conn = sqlite3.connect('zynte_users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            password TEXT,
            fecha_registro TEXT,
            plan TEXT
        )
    ''')
    conn.commit()
    conn.close()

def validar_email_estricto(email):
    """Valida formato real y dominios permitidos"""
    email = email.strip().lower()
    
    # 1. Validación Matemática (Regex): Debe tener formato a@b.c
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(patron, email):
        return False, "Eso no parece un correo electrónico real."
    
    # 2. Lista de Dominios Permitidos
    dominios_validos = ["gmail.com", "yahoo.com", "yahoo.es", "hotmail.com", "outlook.com", "icloud.com", "protonmail.com"]
    dominio_usuario = email.split('@')[-1]
    
    if dominio_usuario not in dominios_validos:
        return False, f"Solo aceptamos proveedores seguros: {', '.join(dominios_validos)}"
        
    return True, "OK"

def verificar_login(email, password):
    """Busca si el usuario existe en la DB"""
    try:
        conn = sqlite3.connect('zynte_users.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password))
        usuario = c.fetchone()
        conn.close()
        return usuario is not None # Devuelve True si encontró al usuario
    except:
        return False

def registrar_usuario_sql(email, password):
    try:
        conn = sqlite3.connect('zynte_users.db')
        c = conn.cursor()
        fecha = str(datetime.date.today())
        c.execute('INSERT INTO users (email, password, fecha_registro, plan) VALUES (?, ?, ?, ?)', 
                  (email, password, fecha, "Free"))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

init_db()

# --- 3. ESTILOS CSS ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    [data-testid="stAppViewContainer"] {background: radial-gradient(ellipse at top, #1b2735 0%, #090a0f 100%);}
    [data-testid="stHeader"] {background: transparent;}
    .hero-title {
        font-size: 3.5rem; font-weight: 800; background: linear-gradient(to right, #ffffff, #33ffaa);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center;
        margin-bottom: 10px; text-shadow: 0 0 30px rgba(51, 255, 170, 0.2);
    }
    .hero-subtitle {font-size: 1.3rem; text-align: center; color: #a0aaba; margin-bottom: 40px;}
    .price-card {
        background-color: rgba(26, 26, 26, 0.8); backdrop-filter: blur(10px);
        border: 1px solid #333; border-radius: 15px; padding: 25px;
        text-align: center; transition: 0.3s; box-shadow: 0 4px 15px rgba(0,0,0,0.2); height: 100%;
    }
    .price-card:hover {border-color: #33ffaa; transform: translateY(-5px); box-shadow: 0 8px 25px rgba(51, 255, 170, 0.2);}
    .stTextInput input {background-color: rgba(255,255,255,0.05) !important; border: 1px solid #333 !important; color: white !important;}
    div.stButton > button {border-radius: 8px; font-weight: bold; transition: all 0.2s;}
    </style>
    """, unsafe_allow_html=True)

# --- 4. API ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except: pass
MODELO_USADO = 'models/gemini-flash-latest'

# ==============================================================================
# VISTAS PRINCIPALES
# ==============================================================================

def mostrar_landing():
    st.write(""); st.write("") 
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        try: st.image("logo.png", use_column_width=True)
        except: st.title("ZYNTE")
    st.markdown('<p class="hero-title">TU ENTRENADOR DE ÉLITE</p>', unsafe_allow_html=True)
    st.markdown('<p class="hero-subtitle">Planes de entrenamiento personalizados generados en segundos.</p>', unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns([1, 1, 1])
    with col_b:
        if st.button("🚀 COMENZAR AHORA", use_container_width=True, type="primary"):
            st.session_state.page = 'login'; st.rerun()
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown("<div class='price-card'><h3>🧠 Personalización</h3><p style='color:#aaa'>Análisis biométrico único.</p></div>", unsafe_allow_html=True)
    with c2: st.markdown("<div class='price-card'><h3>⚡ Velocidad</h3><p style='color:#aaa'>Sin esperas innecesarias.</p></div>", unsafe_allow_html=True)
    with c3: st.markdown("<div class='price-card'><h3>📄 Documentación</h3><p style='color:#aaa'>Exportación profesional PDF.</p></div>", unsafe_allow_html=True)

def mostrar_login():
    st.markdown("## 🔐 Área de Miembros")
    st.caption("Accede a tu panel de control de alto rendimiento.")
    st.write("")
    lc1, lc2, lc3 = st.columns([1,2,1])
    with lc2:
        tab1, tab2 = st.tabs(["Iniciar Sesión", "Nuevo Registro"])
        
        # --- PESTAÑA 1: LOGIN REAL ---
        with tab1:
            st.write("")
            email_login = st.text_input("Correo Electrónico", key="login_email").strip().lower()
            pass_login = st.text_input("Contraseña", type="password", key="login_pass").strip()
            st.write("")
            if st.button("ENTRAR AL SISTEMA ▶", type="primary", use_container_width=True):
                # AQUI ESTÁ EL CAMBIO: Ahora verificamos en la base de datos
                if verificar_login(email_login, pass_login):
                    st.session_state.logged_in = True
                    st.session_state.page = 'pricing'
                    st.success("Credenciales verificadas.")
                    time.sleep(0.5); st.rerun()
                else:
                    st.error("❌ Usuario no encontrado o contraseña incorrecta.")
        
        # --- PESTAÑA 2: REGISTRO BLINDADO ---
        with tab2:
            st.write("")
            new_email = st.text_input("Tu Mejor Email", key="reg_email", placeholder="ejemplo@gmail.com")
            new_pass = st.text_input("Elige Contraseña", type="password", key="reg_pass")
            st.write("")
            
            if st.button("Crear Cuenta Gratuita", use_container_width=True):
                email_limpio = new_email.strip().lower()
                pass_limpio = new_pass.strip()

                if not email_limpio or not pass_limpio:
                    st.error("⚠️ Debes rellenar todos los campos.")
                else:
                    es_valido, mensaje = validar_email_estricto(email_limpio)
                    if not es_valido:
                        st.error(f"❌ {mensaje}")
                    else:
                        if registrar_usuario_sql(email_limpio, pass_limpio):
                            st.success("✅ ¡Cuenta creada! Ya puedes iniciar sesión.")
                            time.sleep(1.5)
                            # Opcional: Autologin
                            st.session_state.logged_in = True
                            st.session_state.page = 'pricing'
                            st.rerun()
                        else:
                            st.error("⛔ Este email ya está registrado.")

    st.write(""); st.write("---")
    if st.button("⬅️ Volver"): st.session_state.page = 'landing'; st.rerun()

def mostrar_pricing():
    st.markdown("<h2 style='text-align: center;'>Selecciona tu Plan</h2>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div class='price-card'><h3>🌱 Starter</h3><h1>0€</h1></div>", unsafe_allow_html=True)
        if st.button("Continuar Gratis", use_container_width=True):
             st.session_state.is_premium = False; st.session_state.page = 'app'; st.rerun()
    with col2:
        st.markdown("<div class='price-card' style='border-color:#33ffaa;'><h3>🔥 PRO</h3><h1>19.99€</h1></div>", unsafe_allow_html=True)
        if st.button("💳 ACTIVAR SUSCRIPCIÓN", type="primary", use_container_width=True):
            time.sleep(1); st.session_state.is_premium = True; st.session_state.page = 'app'; st.rerun()

def app_principal():
    class PDF(FPDF):
        def header(self):
            try: self.image('logo.png', 10, 8, 33)
            except: pass
            self.set_font('Arial', 'B', 15); self.cell(80); self.cell(30, 10, 'ZYNTE | INFORME', 0, 0, 'C'); self.ln(20)
    def crear_pdf(historial, nombre, peso, objetivo):
        pdf = PDF(); pdf.add_page(); pdf.set_font("Arial", size=12); pdf.set_fill_color(200, 220, 255)
        pdf.cell(0, 10, txt=f"CLIENTE: {nombre} | META: {objetivo}", ln=1, align='L', fill=True)
        pdf.ln(10)
        for msg in historial:
            if msg["role"] == "model":
                pdf.multi_cell(0, 7, txt=msg["content"].replace("**", "").replace("*", "-")); pdf.ln(5)
        return pdf.output(dest="S").encode("latin-1", "replace")

    with st.sidebar:
        try: st.image("logo.png", width=180)
        except: st.header("ZYNTE")
        if st.session_state.get('is_premium'): st.success("🌟 PRO")
        else: st.info("🌱 FREE"); st.button("⬆️ Mejorar", on_click=lambda: setattr(st.session_state, 'page', 'pricing'))
        st.write("---")
        nombre = st.text_input("Nombre", "Atleta")
        peso = st.slider("Peso", 40, 150, 70)
        objetivo = st.selectbox("Objetivo", ["Masa Muscular", "Perder Grasa"])
        if "history" in st.session_state and len(st.session_state.history) > 1 and st.session_state.get('is_premium'):
             pdf = crear_pdf(st.session_state.history, nombre, peso, objetivo)
             st.download_button("📥 PDF", pdf, "Rutina.pdf")
        st.write("---"); st.button("Cerrar Sesión", on_click=lambda: setattr(st.session_state, 'logged_in', False) or setattr(st.session_state, 'page', 'landing'))

    if "history" not in st.session_state: st.session_state.history = [{"role": "model", "content": f"Hola {nombre}. Listo."}]
    for msg in st.session_state.history: st.chat_message("assistant" if msg["role"] == "model" else "user").markdown(msg["content"])
    if prompt := st.chat_input("Escribe aquí..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.history.append({"role": "user", "content": prompt})
        try:
            model = genai.GenerativeModel(MODELO_USADO)
            response = model.generate_content(prompt)
            st.chat_message("assistant").markdown(response.text)
            st.session_state.history.append({"role": "model", "content": response.text})
        except: st.warning("Error IA")

# --- ROUTER ---
if 'page' not in st.session_state: st.session_state.page = 'landing'
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'is_premium' not in st.session_state: st.session_state.is_premium = False

if st.session_state.page == 'landing': mostrar_landing()
elif st.session_state.page == 'login': mostrar_login()
elif st.session_state.page == 'pricing': mostrar_pricing()
elif st.session_state.page == 'app': app_principal()
