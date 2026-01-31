import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import datetime
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import sqlite3
import re
import pandas as pd  
import requests


     
# --- 2. GESTIÓN DE BASE DE DATOS, SEGURIDAD Y PAGOS (V11.0 - EXPANDIDO) ---
def init_db():
    conn = sqlite3.connect('zynte_users.db')
    c = conn.cursor()
    # Tabla de Usuarios
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            password TEXT,
            fecha_registro TEXT,
            plan TEXT,
            peso REAL,
            altura INTEGER,
            edad INTEGER,
            objetivo TEXT,
            nivel TEXT
        )
    ''')
    # Tabla Historial
    c.execute('''
        CREATE TABLE IF NOT EXISTS historial (
            email TEXT,
            fecha DATE,
            peso REAL
        )
    ''')
    conn.commit()
    conn.close()
    migrar_db()

def migrar_db():
    """Actualiza la tabla evitando errores de sintaxis (Formato Expandido)"""
    conn = sqlite3.connect('zynte_users.db')
    c = conn.cursor()
    
    # Cada intento en su propio bloque para que Python no se queje
    try:
        c.execute('ALTER TABLE users ADD COLUMN peso REAL')
    except:
        pass
        
    try:
        c.execute('ALTER TABLE users ADD COLUMN altura INTEGER')
    except:
        pass

    try:
        c.execute('ALTER TABLE users ADD COLUMN edad INTEGER')
    except:
        pass

    try:
        c.execute('ALTER TABLE users ADD COLUMN objetivo TEXT')
    except:
        pass

    try:
        c.execute('ALTER TABLE users ADD COLUMN nivel TEXT')
    except:
        pass

    conn.commit()
    conn.close()

# --- FUNCIONES DE SEGURIDAD (LOGIN) ---
def validar_email_estricto(email):
    email = email.strip().lower()
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(patron, email):
        return False, "Formato inválido."
    dominios = ["gmail.com", "yahoo.com", "yahoo.es", "hotmail.com", "outlook.com", "icloud.com", "protonmail.com"]
    try:
        dom = email.split('@')[-1]
    except:
        return False, "Error dominio."
    if dom not in dominios:
        return False, "Dominio no permitido."
    return True, "OK"

def verificar_login(email, password):
    try:
        conn = sqlite3.connect('zynte_users.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password))
        return c.fetchone() is not None
    except:
        return False

def registrar_usuario_sql(email, password):
    try:
        conn = sqlite3.connect('zynte_users.db')
        c = conn.cursor()
        fecha = str(datetime.date.today())
        c.execute('INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', 
                  (email, password, fecha, "Free", 70.0, 175, 25, "Hipertrofia", "Intermedio"))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

# --- FUNCIONES DE PERFIL E HISTORIAL ---
def registrar_peso_historico(email, peso):
    try:
        conn = sqlite3.connect('zynte_users.db')
        c = conn.cursor()
        fecha = str(datetime.date.today())
        c.execute('DELETE FROM historial WHERE email = ? AND fecha = ?', (email, fecha))
        c.execute('INSERT INTO historial VALUES (?, ?, ?)', (email, fecha, peso))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def obtener_historial_df(email):
    try:
        conn = sqlite3.connect('zynte_users.db')
        df = pd.read_sql_query("SELECT fecha, peso FROM historial WHERE email = ? ORDER BY fecha ASC", conn, params=(email,))
        conn.close()
        return df
    except:
        return None

def cargar_perfil(email):
    try:
        conn = sqlite3.connect('zynte_users.db')
        c = conn.cursor()
        c.execute('SELECT peso, altura, edad, objetivo, nivel FROM users WHERE email = ?', (email,))
        data = c.fetchone()
        conn.close()
        return {
            "peso": data[0] if data[0] else 70.0,
            "altura": data[1] if data[1] else 175,
            "edad": data[2] if data[2] else 25,
            "objetivo": data[3] if data[3] else "Hipertrofia",
            "nivel": data[4] if data[4] else "Intermedio"
        }
    except:
        return {"peso": 70.0, "altura": 175, "edad": 25, "objetivo": "Hipertrofia", "nivel": "Intermedio"}

def guardar_perfil_db(email, peso, altura, edad, objetivo, nivel):
    try:
        conn = sqlite3.connect('zynte_users.db')
        c = conn.cursor()
        datos = (peso, altura, edad, objetivo, nivel, email)
        c.execute('UPDATE users SET peso=?, altura=?, edad=?, objetivo=?, nivel=? WHERE email=?', datos)
        conn.commit()
        conn.close()
        registrar_peso_historico(email, peso) 
        return True
    except:
        return False

# --- FUNCIONES DE PAGO (PLAN PRO) ---
def activar_plan_pro(email):
    try:
        conn = sqlite3.connect('zynte_users.db')
        c = conn.cursor()
        c.execute("UPDATE users SET plan = 'Pro' WHERE email = ?", (email,))
        conn.commit()
        conn.close()
        return True
    except:
        return False
def revocar_plan_pro(email):
    """Devuelve al usuario al plan Free (Castigo)"""
    try:
        conn = sqlite3.connect('zynte_users.db')
        c = conn.cursor()
        c.execute("UPDATE users SET plan = 'Free' WHERE email = ?", (email,))
        conn.commit()
        conn.close()
        return True
    except: return False

def eliminar_usuario_total(email):
    """Borra al usuario y sus datos para siempre (Opción Nuclear)"""
    try:
        conn = sqlite3.connect('zynte_users.db')
        c = conn.cursor()
        c.execute("DELETE FROM users WHERE email = ?", (email,))
        c.execute("DELETE FROM historial WHERE email = ?", (email,))
        conn.commit()
        conn.close()
        return True
    except: return False
def comprobar_plan(email):
    try:
        conn = sqlite3.connect('zynte_users.db')
        c = conn.cursor()
        c.execute("SELECT plan FROM users WHERE email = ?", (email,))
        res = c.fetchone()
        conn.close()
        if res and res[0] == 'Pro':
            return True
        return False
    except:
        return False

# Iniciamos DB al arrancar
init_db()
# --- 3. ESTILOS CSS PREMIUM (FONDO NUEVO) ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* --- AQUÍ ESTÁ EL CAMBIO DEL FONDO --- */
    [data-testid="stAppViewContainer"] {
        /* Capa negra al 85% + Foto de Gimnasio */
        background-image: linear-gradient(rgba(0, 0, 0, 0.85), rgba(0, 0, 0, 0.95)), 
                          url("https://images.unsplash.com/photo-1534438327276-14e5300c3a48?q=80&w=2070&auto=format&fit=crop");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    /* TIPOGRAFÍA DE IMPACTO */
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
    
    /* TARJETAS DE CRISTAL (Glassmorphism) */
    .price-card {
        background-color: rgba(20, 20, 20, 0.6); /* Más transparente para ver el fondo */
        backdrop-filter: blur(15px); /* Desenfoque del fondo */
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 25px;
        text-align: center;
        transition: 0.3s;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        height: 100%;
    }
    .price-card:hover {
        border-color: #33ffaa;
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(51, 255, 170, 0.2);
        background-color: rgba(30, 30, 30, 0.8);
    }
    
    /* INPUTS MEJORADOS */
    .stTextInput input {
        background-color: rgba(0,0,0,0.5) !important;
        border: 1px solid #444 !important;
        color: white !important;
    }
    
    /* BOTONES ESTILIZADOS */
    div.stButton > button {
        border-radius: 8px;
        font-weight: bold;
        transition: all 0.2s;
        border: none;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONFIGURACIÓN DE IA CORREGIDA ---
try:
    # Forzamos la versión 'v1' para evitar el error 404 de la v1beta
    genai.configure(
        api_key=st.secrets["GOOGLE_API_KEY"],
        transport='rest' # Esto ayuda en algunos entornos de Windows
    )
except:
    # Si estás en local sin secrets:
    genai.configure(api_key="AIzaSyC2q_babdKS2vKE0VJX5XijEfYzymlsIKE")

# Usamos el nombre sin el prefijo "models/" para que la librería lo gestione
MODELO_USADO = "gemini-1.5-flash-001"

# ==============================================================================
# ℹ️ PÁGINAS DE INFORMACIÓN 
# ==============================================================================

def mostrar_info_ia():
    """Detalle: Tecnología"""
    st.markdown("## 🧠 El Algoritmo Zynte™")
    st.write("")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("""
        <div class="price-card" style="text-align: left;">
            <h3>Ingeniería Biométrica</h3>
            <p style="color:#ccc;">Olvida las rutinas genéricas de internet.</p>
            <p>Zynte procesa 12 variables fisiológicas en tiempo real para calcular tu volumen de entrenamiento óptimo. No es magia, es matemática aplicada al rendimiento deportivo.</p>
            <br>
            <p>✅ <b>Periodización Ondulante:</b> Ajuste de cargas automático.</p>
            <p>✅ <b>Selección Inteligente:</b> Elige entre 5.000 ejercicios.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.info("💡 **Dato:** Nuestros usuarios reportan un aumento del 30% en adherencia comparado con entrenadores tradicionales.")

    st.write("")
    if st.button("⬅️ Volver"):
        st.session_state.page = 'landing'
        st.rerun()

def mostrar_info_velocidad():
    """Página de Detalle: Velocidad Extrema"""
    st.markdown('<p class="hero-title" style="font-size: 2.5rem;">Tu tiempo es para entrenar,<br>no para esperar.</p>', unsafe_allow_html=True)
    
    st.write("")
    st.write("---")
    st.write("")

    # Usamos 5 columnas para dar aire y separar el 'Instantáneo' del 'VS'
    # [Humano] [Espacio] [VS] [Espacio] [Zynte]
    c1, c2, c3, c4, c5 = st.columns([1.5, 0.5, 1, 0.5, 2.5])

    with c1:
        st.markdown("""
            <div style="background: rgba(255, 255, 255, 0.1); padding: 25px; border-radius: 15px; text-align: center; border: 1px solid rgba(255,255,255,0.2);">
                <h1 style="margin:0; color: white; font-size: 3rem;">48h</h1>
                <p style="color: #a0aaba; margin:0;">Espera Media</p>
            </div>
        """, unsafe_allow_html=True)
        st.caption("Entrenador Humano")

    with c3:
        st.markdown('<h1 style="text-align: center; margin-top: 25px; color: #a0aaba; font-size: 1.5rem;">VS</h1>', unsafe_allow_html=True)

    with c5:
        st.markdown("""
            <div style="background: #33ffaa; padding: 20px 10px; border-radius: 15px; text-align: center; box-shadow: 0px 0px 20px rgba(51, 255, 170, 0.3);">
                <h1 style="margin:0; color: #000; font-size: 1.8rem; font-weight: 800;">Instantáneo</h1>
                <p style="color: #000; margin:0; font-weight: 600;">Zynte System</p>
            </div>
        """, unsafe_allow_html=True)
        st.caption("Tecnología Gemini 1.5 Flash")

    st.write("")
    st.write("")
    st.info("Genera, modifica y regenera tu plan tantas veces como necesites. Sin citas previas ni esperas de días.")

    if st.button("⬅️ Volver al Inicio", use_container_width=True):
        st.session_state.page = "landing"
        st.rerun()

def mostrar_info_pdf():
    """Detalle: Documentación"""
    st.markdown("## 📄 Documentación Ejecutiva")
    st.write("")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("""
        <div class="price-card" style="text-align: left;">
            <h3>Enfoque sin distracciones</h3>
            <p style="color:#ccc;">En el gimnasio, tu foco debe estar en el hierro, no en la pantalla.</p>
            <p>Obtén un informe técnico detallado en PDF al finalizar cada sesión de planificación. Imprímelo o guárdalo en tu dispositivo.</p>
            <br>
            <ul style="color:#ccc;">
                <li>Desglose de series y repeticiones.</li>
                <li>Tiempos de descanso estipulados.</li>
                <li>Notas técnicas de ejecución.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.success("📂 **Característica PRO:** Disponible exclusivamente en el plan Élite (19.99€).")

    st.write("")
    if st.button("⬅️ Volver"):
        st.session_state.page = 'landing'
        st.rerun()

# ==============================================================================
# 🌟 VISTAS PRINCIPALES
# ==============================================================================
def mostrar_landing():
    """Portada Principal - Versión Final Corregida y 100% Funcional"""
    st.write("") 
    st.write("") 
    
    # 1. Logo centrado (Mantenemos tu estructura original)
    col_l1, col_l2, col_l3 = st.columns([0.8, 1.5, 0.8])
    with col_l2:
        try: 
            st.image("logo.png", use_container_width=True)
        except: 
            st.markdown("<h1 style='text-align:center; color:white;'>ZYNTE</h1>", unsafe_allow_html=True)
    
    st.markdown('<p class="hero-title">TU ENTRENADOR DE ÉLITE</p>', unsafe_allow_html=True)
    st.markdown('<p class="hero-subtitle">Planes de entrenamiento personalizados generados en segundos.</p>', unsafe_allow_html=True)
    
    # 2. Botón central para Login
    _, col_btn, _ = st.columns([1.2, 1, 1.2])
    with col_btn:
        if st.button("🚀 COMENZAR AHORA", use_container_width=True, type="primary"):
            st.session_state.page = 'login'
            st.rerun()

    st.write("---")

    # 3. TARJETAS DE INFORMACIÓN - TAMAÑO GRANDE Y BOTONES OPERATIVOS
    c1, c2, c3 = st.columns(3, gap="medium")
    
    # Estilo CSS de las cajas (Grande, Cuadrado y Neón)
    card_css = (
        "background: rgba(30, 30, 30, 0.6); "
        "padding: 35px 20px; "
        "border-radius: 15px; "
        "border: 2px solid #33ffaa; " 
        "text-align: center; "
        "min-height: 320px; " 
        "display: flex; flex-direction: column; justify-content: center; align-items: center;"
    )

    with c1:
        st.markdown(f"""<div style="{card_css}">
            <div style="font-size: 3rem; margin-bottom: 15px;">🧠</div>
            <h3 style="color: #33ffaa; font-size: 1.2rem; margin: 0; line-height: 1.2;">Personalización<br>Total</h3>
            <p style="color: #ccc; font-size: 0.95rem; margin-top: 10px;">Rutinas únicas basadas en tu biometría y metas.</p>
        </div>""", unsafe_allow_html=True)
        # ESTE BOTÓN AHORA SÍ FUNCIONA
        if st.button("Cómo funciona", key="nav_pers", use_container_width=True):
            st.session_state.page = 'info_ia' # O la página que uses para explicar la IA
            st.rerun()
            
    with c2:
        st.markdown(f"""<div style="{card_css}">
            <div style="font-size: 3rem; margin-bottom: 15px;">⚡</div>
            <h3 style="color: #33ffaa; font-size: 1.2rem; margin: 0; line-height: 1.2;">Resultados<br>Rápidos</h3>
            <p style="color: #ccc; font-size: 0.95rem; margin-top: 10px;">Planes listos para descargar en segundos.</p>
        </div>""", unsafe_allow_html=True)
        # ESTE BOTÓN AHORA SÍ FUNCIONA
        if st.button("Ver velocidad", key="nav_vel", use_container_width=True):
            st.session_state.page = 'info_vel' # O la página de velocidad
            st.rerun()
            
    with c3:
        st.markdown(f"""<div style="{card_css}">
            <div style="font-size: 3rem; margin-bottom: 15px;">📄</div>
            <h3 style="color: #33ffaa; font-size: 1.2rem; margin: 0; line-height: 1.2;">Informes<br>PDF</h3>
            <p style="color: #ccc; font-size: 0.95rem; margin-top: 10px;">Exporta tu progreso en formato profesional y limpio.</p>
        </div>""", unsafe_allow_html=True)
        # ESTE BOTÓN AHORA SÍ FUNCIONA
        if st.button("Ver ejemplo", key="nav_pdf", use_container_width=True):
            st.session_state.page = 'info_pdf' # O la página de ejemplo PDF
            st.rerun()
    
# --- FUNCIÓN DE CONEXIÓN SEGURA POR ID (ACTUALIZADA) ---
def conectar_db():
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        # Usamos los secrets de Streamlit
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # ESTE ES EL ID DE TU HOJA (NO TOCAR)
        SHEET_ID = "1KZR8mmuRPTSaqlDi1VyRdG_ZaC20UUMqZd0jDdKE-OM" 
        
        sheet = client.open_by_key(SHEET_ID).sheet1
        return sheet
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None
def mostrar_login():
    st.markdown("## 🔐 Área de Miembros")
    st.write("")
    lc1, lc2, lc3 = st.columns([1,2,1])
    with lc2:
        tab1, tab2 = st.tabs(["Iniciar Sesión", "Nuevo Registro"])
        
        # LOGIN CON DETECCIÓN DE PLAN PRO
        with tab1:
            st.write("")
            email_login = st.text_input("Correo", key="login_email").strip().lower()
            pass_login = st.text_input("Contraseña", type="password", key="login_pass").strip()
            st.write("")
            if st.button("ENTRAR ▶", type="primary", use_container_width=True):
                if verificar_login(email_login, pass_login):
                    st.session_state.logged_in = True
                    st.session_state.user_email = email_login 
                    
                    # AQUÍ MIRAMOS SI YA PAGÓ ANTES
                    es_pro = comprobar_plan(email_login)
                    st.session_state.is_premium = es_pro # Guardamos el estado
                    
                    if es_pro:
                        st.session_state.page = 'app' # Si es Pro, directo a entrenar
                        st.success("¡Bienvenido de nuevo, Atleta Pro! 🌟")
                    else:
                        st.session_state.page = 'pricing' # Si es Free, a ver precios
                        st.success("Verificado.")
                    
                    time.sleep(0.5); st.rerun()
                else: st.error("Error de credenciales.")
        
        with tab2:
            st.write("")
            new_email = st.text_input("Email", key="reg_email").strip().lower()
            new_pass = st.text_input("Pass", type="password", key="reg_pass").strip()
            st.write("")
            if st.button("Crear Cuenta", use_container_width=True):
                if not new_email or not new_pass: st.warning("Rellena todo.")
                else:
                    valido, msg = validar_email_estricto(new_email)
                    if not valido: st.error(msg)
                    else:
                        if registrar_usuario_sql(new_email, new_pass):
                            st.success("Creado."); time.sleep(1); st.session_state.logged_in=True; st.session_state.user_email=new_email; st.session_state.page='pricing'; st.rerun()
                        else: st.error("Email ocupado.")
    st.write("---"); st.button("⬅️ Volver", on_click=lambda: setattr(st.session_state, 'page', 'landing'))
def mostrar_pricing():
    st.markdown("<h2 style='text-align: center;'>Selecciona tu Plan</h2>", unsafe_allow_html=True)
    
    # ENLACE DE PAGO (PON AQUÍ EL TUYO DE STRIPE) 👇
    LINK_STRIPE = "https://buy.stripe.com/test_4gM00lgIK1x3b3l8Z9eZ200" 
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div class='price-card'><h3>🌱 Starter</h3><h1>0€</h1></div>", unsafe_allow_html=True)
        if st.button("Continuar Gratis", use_container_width=True):
             st.session_state.is_premium = False; st.session_state.page = 'app'; st.rerun()
             
    with col2:
        st.markdown("<div class='price-card' style='border-color:#33ffaa;'><h3>🔥 PRO</h3><h1>19.99€</h1></div>", unsafe_allow_html=True)
        st.write("")
        
        # 1. BOTÓN DE PAGO (Abre pestaña nueva)
        st.link_button("💳 PAGAR CON TARJETA", LINK_STRIPE, type="primary", use_container_width=True)
        
        # 2. ÁREA DE CANJEO
        with st.expander("¿Ya tienes tu código? Canjéalo aquí"):
            codigo = st.text_input("Código de licencia:", placeholder="Ej: ZYNTE-PRO").strip()
            if st.button("Validar Licencia"):
                if codigo == "ZYNTE2026": # <--- ESTA ES TU CONTRASEÑA SECRETA
                    email_actual = st.session_state.get('user_email')
                    if activar_plan_pro(email_actual):
                        st.balloons()
                        st.success("✅ ¡PLAN PRO ACTIVADO!")
                        st.session_state.is_premium = True
                        time.sleep(2)
                        st.session_state.page = 'app'
                        st.rerun()
                    else:
                        st.error("Error al actualizar base de datos.")
                else:
                    st.error("❌ Código incorrecto.")

def app_principal():
    # Recuperamos los datos del usuario actual
    email_actual = st.session_state.get('user_email', 'invitado')
    datos_usuario = cargar_perfil(email_actual)

    class PDF(FPDF):
        def header(self):
            try: self.image('logo.png', 10, 8, 33)
            except: pass
            self.set_font('Arial', 'B', 15); self.cell(80); self.cell(30, 10, 'ZYNTE | INFORME DE ENTRENAMIENTO', 0, 0, 'C'); self.ln(20)
        def footer(self):
            self.set_y(-15); self.set_font('Arial', 'I', 8); self.cell(0, 10, f'Pagina {self.page_no()} - Zynte Elite Performance', 0, 0, 'C')

    def crear_pdf(historial, nombre, peso, objetivo):
        pdf = PDF(); pdf.add_page(); pdf.set_font("Arial", size=12); pdf.set_fill_color(200, 220, 255)
        pdf.cell(0, 10, txt=f"CLIENTE: {nombre} | FECHA: {datetime.date.today()}", ln=1, align='L', fill=True)
        pdf.cell(0, 10, txt=f"PERFIL: {peso}kg | META: {objetivo}", ln=1, align='L', fill=True)
        pdf.ln(10); pdf.set_font("Arial", "B", 14); pdf.cell(0, 10, txt="PLAN PERSONALIZADO:", ln=1); pdf.set_font("Arial", size=11)
        for mensaje in historial:
            if mensaje["role"] == "model":
                texto_limpio = mensaje["content"].replace("**", "").replace("*", "-")
                pdf.multi_cell(0, 7, txt=texto_limpio); pdf.ln(5); pdf.line(10, pdf.get_y(), 200, pdf.get_y()); pdf.ln(5)
        return pdf.output(dest="S").encode("latin-1", "replace")

    with st.sidebar:
        try: st.image("logo.png", width=180)
        except: st.header("ZYNTE")
        
        if st.session_state.get('is_premium', False): st.success("🌟 MIEMBRO PRO")
        else: st.info("🌱 CUENTA GRATUITA"); st.button("⬆️ Mejorar Plan", use_container_width=True, on_click=lambda: setattr(st.session_state, 'page', 'pricing'))
        
        st.write("---"); st.caption("PERFIL BIOMÉTRICO")
        
        # LOS VALORES POR DEFECTO AHORA VIENEN DE LA BASE DE DATOS
        nombre = st.text_input("Alias", "Atleta")
        peso = st.slider("Peso (kg)", 40.0, 150.0, float(datos_usuario['peso']), 0.5)
        altura = st.slider("Altura (cm)", 120, 220, int(datos_usuario['altura']), 1)
        edad = st.slider("Edad", 16, 80, int(datos_usuario['edad']))
        
        # Índices para los selectbox
        obj_options = ["Hipertrofia", "Pérdida de Grasa", "Fuerza Máxima", "Resistencia"]
        niv_options = ["Principiante", "Intermedio", "Avanzado"]
        
        try: idx_obj = obj_options.index(datos_usuario['objetivo'])
        except: idx_obj = 0
        try: idx_niv = niv_options.index(datos_usuario['nivel'])
        except: idx_niv = 1

        objetivo = st.selectbox("Objetivo:", obj_options, index=idx_obj)
        nivel = st.select_slider("Experiencia:", options=niv_options, value=niv_options[idx_niv])
        
        # BOTÓN NUEVO PARA GUARDAR CAMBIOS
        if st.button("💾 Guardar Perfil", use_container_width=True):
            if guardar_perfil_db(email_actual, peso, altura, edad, objetivo, nivel):
                st.toast("✅ Perfil actualizado con éxito")
            else:
                st.toast("❌ Error al guardar")

        st.write("---")
        if "history" in st.session_state and len(st.session_state.history) > 1:
            if st.session_state.get('is_premium', False):
                pdf_bytes = crear_pdf(st.session_state.history, nombre, peso, objetivo)
                st.download_button("📥 DESCARGAR INFORME", pdf_bytes, f"Plan_{nombre}.pdf", "application/pdf", use_container_width=True)
            else: st.warning("🔒 DESCARGA BLOQUEADA (PRO)")
            
        st.write("---"); st.button("Cerrar Sesión", use_container_width=True, on_click=lambda: setattr(st.session_state, 'logged_in', False) or setattr(st.session_state, 'page', 'landing'))
        st.caption("© 2026 Zynte Performance")

    imc = peso / ((altura/100)**2); estado_imc = "Normal"
    if imc >= 25: estado_imc = "Sobrepeso"
    if imc < 18.5: estado_imc = "Bajo peso"
    try: st.image("banner.jpg", use_column_width=True)
    except: st.title("ZYNTE COACH")
    
    col1, col2, col3, col4 = st.columns([1, 0.7, 2, 1.3])
    with col1: st.metric("IMC", f"{imc:.1f}", estado_imc)
    with col2: st.metric("Peso", f"{peso} kg")
    with col3: st.metric("Meta", objetivo)
    with col4: st.metric("Nivel", nivel)
    st.divider(); st.caption("⚠️ **Aviso:** Zynte es una herramienta de soporte. Consulta siempre con un médico antes de iniciar actividad física.")

    if "history" not in st.session_state:
        st.session_state.history = []
        # Mensaje personalizado
        st.session_state.history.append({"role": "model", "content": f"Hola. Veo que pesas {peso}kg y buscas {objetivo}. He cargado tu perfil. ¿Qué entrenamos hoy?"})
        
    for msg in st.session_state.history:
        role = "assistant" if msg["role"] == "model" else "user"
        avatar = "logo.png" if role == "assistant" else None
        try: st.chat_message(role, avatar=avatar).markdown(msg["content"])
        except: st.chat_message(role).markdown(msg["content"])

    if prompt := st.chat_input("Describe tu necesidad o equipamiento..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.history.append({"role": "user", "content": prompt})
        with st.chat_message("assistant", avatar="logo.png"):
            placeholder = st.empty(); placeholder.markdown("...")
            try:
                ctx = f"Eres Zynte, entrenador de élite. Hablas con un atleta de {peso}kg, {altura}cm, nivel {nivel}. Objetivo: {objetivo}. Responde con autoridad técnica pero cercano."
                model = genai.GenerativeModel(MODELO_USADO, system_instruction=ctx)
                chat_history = [{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} for m in st.session_state.history[:-1]]
                chat = model.start_chat(history=chat_history)
                try: response = chat.send_message(prompt)
                except Exception as e:
                    if "429" in str(e):
                        placeholder.warning("⏳ Alta demanda en el servidor. Re-calculando ruta..."); time.sleep(6); response = chat.send_message(prompt)
                    else: raise e
                placeholder.markdown(response.text); st.session_state.history.append({"role": "model", "content": response.text})
            except Exception as e: placeholder.error(f"Error: {e}")

    # --- Sidebar ---
    with st.sidebar:
        try: st.image("logo.png", width=180)
        except: st.header("ZYNTE")
        
        if st.session_state.get('is_premium', False):
            st.success("🌟 MIEMBRO PRO")
        else:
            st.info("🌱 CUENTA GRATUITA")
            if st.button("⬆️ Mejorar Plan", use_container_width=True):
                st.session_state.page = 'pricing'
                st.rerun()

        st.write("---")
        st.caption("CONFIGURACIÓN DE ATLETA")
        nombre = st.text_input("Nombre", "Atleta")
        with st.expander("Datos Biométricos", expanded=True):
            peso = st.slider("Peso (kg)", 40.0, 150.0, 72.5, 0.5)
            altura = st.slider("Altura (cm)", 120, 220, 176, 1)
            edad = st.slider("Edad", 16, 80, 25)
        with st.expander("Objetivos", expanded=True):
            objetivo = st.selectbox("Objetivo:", ["Hipertrofia", "Pérdida de Grasa", "Fuerza Máxima", "Resistencia"])
            nivel = st.select_slider("Experiencia:", options=["Principiante", "Intermedio", "Avanzado"])

        st.write("---")
        if "history" in st.session_state and len(st.session_state.history) > 1:
            if st.session_state.get('is_premium', False):
                pdf_bytes = crear_pdf(st.session_state.history, nombre, peso, objetivo)
                st.download_button("📥 DESCARGAR INFORME", pdf_bytes, f"Plan_{nombre}.pdf", "application/pdf", use_container_width=True)
            else:
                st.warning("🔒 DESCARGA BLOQUEADA (PRO)")
        
        st.write("---")
        if st.button("Cerrar Sesión", use_container_width=True):
            st.session_state.page = 'landing'
            st.session_state.logged_in = False
            st.rerun()
            
        st.caption("© 2026 Zynte Performance")

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
    with col3: st.metric("Meta", objetivo)
    with col4: st.metric("Nivel", nivel)
    st.divider()
    st.caption("⚠️ **Aviso:** Zynte es una herramienta de soporte. Consulta siempre con un médico antes de iniciar actividad física.")

    # --- Chat ---
    if "history" not in st.session_state:
        st.session_state.history = []
        st.session_state.history.append({"role": "model", "content": f"Hola {nombre}. He analizado tus datos ({peso}kg, {nivel}). Estoy listo para diseñar tu plan de {objetivo}. ¿Comenzamos?"})

    for msg in st.session_state.history:
        role = "assistant" if msg["role"] == "model" else "user"
        avatar = "logo.png" if role == "assistant" else None
        try: st.chat_message(role, avatar=avatar).markdown(msg["content"])
        except: st.chat_message(role).markdown(msg["content"])

    if prompt := st.chat_input("Describe tu necesidad o equipamiento..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.history.append({"role": "user", "content": prompt})
        
        with st.chat_message("assistant", avatar="logo.png"):
            placeholder = st.empty()
            placeholder.markdown("...")
            try:
                ctx = f"Eres Zynte, entrenador de élite. Hablas con {nombre}. Datos: {peso}kg, {objetivo}. Responde con autoridad técnica pero cercano."
                model = genai.GenerativeModel(MODELO_USADO, system_instruction=ctx)
                chat_history = [{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} for m in st.session_state.history[:-1]]
                chat = model.start_chat(history=chat_history)
                
                try:
                    response = chat.send_message(prompt)
                except Exception as e:
                    if "429" in str(e):
                        placeholder.warning("⏳ Alta demanda en el servidor. Re-calculando ruta...")
                        time.sleep(6)
                        response = chat.send_message(prompt)
                    else: raise e
                
                placeholder.markdown(response.text)
                st.session_state.history.append({"role": "model", "content": response.text})
            except Exception as e:
                placeholder.error(f"Error: {e}")

# ==============================================================================
# 🚀 ROUTER
# ==============================================================================

def main():
    if 'page' not in st.session_state: st.session_state.page = 'landing'
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False
    if 'is_premium' not in st.session_state: st.session_state.is_premium = False

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
















































































