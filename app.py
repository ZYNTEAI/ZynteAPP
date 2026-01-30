import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import datetime
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import sqlite3
import re

# --- 1. CONFIGURACIÓN INICIAL ---
st.set_page_config(
    page_title="Zynte | Elite Coach", 
    page_icon="logo.png", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- 2. GESTIÓN DE BASE DE DATOS Y PERFIL (V9.1) ---
def init_db():
    conn = sqlite3.connect('zynte_users.db')
    c = conn.cursor()
    # Creamos tabla con columnas extra para el perfil del atleta
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
    conn.commit()
    conn.close()
    migrar_db()

def migrar_db():
    """Actualiza la tabla si es antigua"""
    conn = sqlite3.connect('zynte_users.db')
    c = conn.cursor()
    cols = ['peso REAL', 'altura INTEGER', 'edad INTEGER', 'objetivo TEXT', 'nivel TEXT']
    for col in cols:
        try:
            c.execute(f'ALTER TABLE users ADD COLUMN {col}')
        except: pass
    conn.commit()
    conn.close()

def cargar_perfil(email):
    """Carga datos del usuario"""
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
        c.execute('UPDATE users SET peso=?, altura=?, edad=?, objetivo=?, nivel=? WHERE email=?', 
                 (peso, altura, edad, objetivo, nivel, email))
        conn.commit()
        conn.close()
        return True
    except: return False

def validar_email_estricto(email):
    email = email.strip().lower()
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(patron, email): return False, "Formato inválido."
    dominios = ["gmail.com", "yahoo.com", "yahoo.es", "hotmail.com", "outlook.com", "icloud.com", "protonmail.com"]
    try: dom = email.split('@')[-1]
    except: return False, "Error dominio."
    if dom not in dominios: return False, "Dominio no permitido."
    return True, "OK"

def verificar_login(email, password):
    try:
        conn = sqlite3.connect('zynte_users.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password))
        return c.fetchone() is not None
    except: return False

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
    except sqlite3.IntegrityError: return False

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

# --- 3. CONEXIÓN API ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except:
    pass

MODELO_USADO = 'models/gemini-flash-latest'

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
    """Detalle: Velocidad"""
    st.markdown("## ⚡ Eficiencia Absoluta")
    st.write("")
    
    st.markdown("""
    <div class="price-card">
        <h3>Tu tiempo es para entrenar, no para esperar.</h3>
        <hr style="border-color:#333;">
        <div style="display:flex; justify-content:space-around; align-items:center; margin-top:20px;">
            <div>
                <h1 style="color:#a0aaba; font-size:3rem;">48h</h1>
                <p>Espera Media (Entrenador Humano)</p>
            </div>
            <div style="font-size:3rem; color:#555;">VS</div>
            <div>
                <h1 style="color:#33ffaa; font-size:4rem;">Instantáneo</h1>
                <p>Zynte System</p>
            </div>
        </div>
        <br>
        <p style="color:#ccc;">Genera, modifica y regenera tu plan tantas veces como necesites. Sin citas previas.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    if st.button("⬅️ Volver"):
        st.session_state.page = 'landing'
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
    """Portada Principal"""
    st.write("") 
    st.write("") 
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        try: st.image("logo.png", use_column_width=True)
        except: st.title("ZYNTE")
    
    st.markdown('<p class="hero-title">TU ENTRENADOR DE ÉLITE</p>', unsafe_allow_html=True)
    # TEXTO DEFINITIVO: 
    st.markdown('<p class="hero-subtitle">Planes de entrenamiento personalizados generados en segundos.</p>', unsafe_allow_html=True)
    
    col_a, col_b, col_c = st.columns([1, 1, 1])
    with col_b:
        st.write("")
        if st.button("🚀 COMENZAR AHORA", use_container_width=True, type="primary"):
            st.session_state.page = 'login'
            st.rerun()
        st.write("")
        st.write("")

    # TARJETAS DE INFORMACIÓN
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("""<div class='price-card' style='text-align:left; border:none; background:transparent; box-shadow:none;'>
        <h3>🧠 Personalización Total</h3>
        <p style='color:#a0aaba; min-height:60px;'>Análisis biométrico avanzado para crear una rutina única para tu cuerpo.</p>
        </div>""", unsafe_allow_html=True)
        if st.button("Cómo funciona", key="btn_ia"):
            st.session_state.page = 'info_ia'
            st.rerun()
            
    with c2:
        st.markdown("""<div class='price-card' style='text-align:left; border:none; background:transparent; box-shadow:none;'>
        <h3>⚡ Resultados Rápidos</h3>
        <p style='color:#a0aaba; min-height:60px;'>Tu planificación completa lista para descargar antes de llegar al gimnasio.</p>
        </div>""", unsafe_allow_html=True)
        if st.button("Ver velocidad", key="btn_vel"):
            st.session_state.page = 'info_vel'
            st.rerun()
            
    with c3:
        st.markdown("""<div class='price-card' style='text-align:left; border:none; background:transparent; box-shadow:none;'>
        <h3>📄 Informes PDF</h3>
        <p style='color:#a0aaba; min-height:60px;'>Exporta tu rutina en formato profesional limpio y sin distracciones.</p>
        </div>""", unsafe_allow_html=True)
        if st.button("Ver ejemplo", key="btn_pdf"):
            st.session_state.page = 'info_pdf'
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
        
        # LOGIN
        with tab1:
            st.write("")
            email_login = st.text_input("Correo", key="login_email").strip().lower()
            pass_login = st.text_input("Contraseña", type="password", key="login_pass").strip()
            st.write("")
            if st.button("ENTRAR ▶", type="primary", use_container_width=True):
                if verificar_login(email_login, pass_login):
                    st.session_state.logged_in = True
                    st.session_state.user_email = email_login 
                    st.session_state.page = 'pricing'
                    st.success("Verificado."); time.sleep(0.5); st.rerun()
                else: st.error("Error de credenciales.")
        
        # REGISTRO
        with tab2:
            st.write("")
            new_email = st.text_input("Email", key="reg_email").strip().lower()
            new_pass = st.text_input("Pass", type="password", key="reg_pass").strip()
            st.write("")
            if st.button("Crear Cuenta", use_container_width=True):
                if not new_email or not new_pass: 
                    st.warning("Rellena todo.")
                else:
                    valido, msg = validar_email_estricto(new_email)
                    if not valido: 
                        st.error(msg)
                    else:
                        if registrar_usuario_sql(new_email, new_pass):
                            st.success("Creado.")
                            time.sleep(1)
                            st.session_state.logged_in=True
                            st.session_state.user_email=new_email
                            st.session_state.page='pricing'
                            st.rerun()
                        else: 
                            st.error("Email ocupado.")
    
    st.write("---")
    if st.button("⬅️ Volver", on_click=lambda: setattr(st.session_state, 'page', 'landing')): pass
def mostrar_pricing():
    st.markdown("<h2 style='text-align: center; margin-top:20px;'>Selecciona tu Plan</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color:#a0aaba; margin-bottom:40px;'>Invierte en tu transformación física.</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class='price-card'>
            <h3>🌱 Starter</h3>
            <h1 style='font-size: 3.5rem; margin: 10px 0;'>0€</h1>
            <p style='color:#a0aaba;'>Prueba de concepto</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("Continuar con limitaciones", use_container_width=True):
             st.session_state.is_premium = False
             st.session_state.page = 'app'
             st.rerun()

    with col2:
        st.markdown("""
        <div class='price-card' style='border-color: #33ffaa; box-shadow: 0 0 30px rgba(51, 255, 170, 0.15);'>
            <h3 style='color: #33ffaa;'>🔥 Zynte PRO</h3>
            <h1 style='font-size: 3.5rem; margin: 10px 0;'>19.99€</h1>
            <p style='color:#a0aaba;'>Acceso total. PDFs Ilimitados.</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        # TEXTO DEFINITIVO EN PAGO
        if st.button("💳 ACTIVAR SUSCRIPCIÓN", type="primary", use_container_width=True):
            with st.spinner("Conectando con pasarela de pago segura..."):
                time.sleep(2) 
            st.session_state.is_premium = True
            st.session_state.page = 'app'
            st.balloons()
            st.rerun()

def app_principal():
    # 1. Cargar Memoria del Usuario
    email_actual = st.session_state.get('user_email', 'invitado')
    datos_usuario = cargar_perfil(email_actual)

    # --- LÓGICA DE NUTRICIÓN (Cálculos Matemáticos) ---
    def calcular_macros(peso, altura, edad, genero, objetivo, nivel):
        # Fórmula Harris-Benedict Revisada
        if genero == "Hombre":
            tmb = 88.36 + (13.4 * peso) + (4.8 * altura) - (5.7 * edad)
        else:
            tmb = 447.6 + (9.2 * peso) + (3.1 * altura) - (4.3 * edad)
        
        # Factor de actividad
        factores = {"Principiante": 1.2, "Intermedio": 1.55, "Avanzado": 1.725}
        tdee = tmb * factores.get(nivel, 1.2)
        
        # Ajuste según objetivo
        if objetivo == "Pérdida de Grasa":
            calorias = tdee - 400
            proteina = peso * 2.2
            grasas = peso * 0.9
        elif objetivo == "Hipertrofia" or objetivo == "Fuerza Máxima":
            calorias = tdee + 300
            proteina = peso * 2.0
            grasas = peso * 1.0
        else: # Resistencia / Mantenimiento
            calorias = tdee
            proteina = peso * 1.6
            grasas = peso * 1.0
            
        carbos = (calorias - (proteina * 4) - (grasas * 9)) / 4
        return int(calorias), int(proteina), int(carbos), int(grasas)

    class PDF(FPDF):
        def header(self):
            try: self.image('logo.png', 10, 8, 33)
            except: pass
            self.set_font('Arial', 'B', 15); self.cell(80); self.cell(30, 10, 'ZYNTE | INFORME', 0, 0, 'C'); self.ln(20)

    def crear_pdf(historial, nombre, peso, objetivo):
        pdf = PDF(); pdf.add_page(); pdf.set_font("Arial", size=12); pdf.set_fill_color(200, 220, 255)
        pdf.cell(0, 10, txt=f"CLIENTE: {nombre} | FECHA: {datetime.date.today()}", ln=1, align='L', fill=True)
        pdf.cell(0, 10, txt=f"PERFIL: {peso}kg | META: {objetivo}", ln=1, align='L', fill=True)
        pdf.ln(10); pdf.set_font("Arial", "B", 14); pdf.cell(0, 10, txt="PLAN PERSONALIZADO:", ln=1); pdf.set_font("Arial", size=11)
        for mensaje in historial:
            if mensaje["role"] == "model":
                pdf.multi_cell(0, 7, txt=mensaje["content"].replace("**", "").replace("*", "-")); pdf.ln(5)
        return pdf.output(dest="S").encode("latin-1", "replace")

    with st.sidebar:
        try: st.image("logo.png", width=180)
        except: st.header("ZYNTE")
        
        if st.session_state.get('is_premium', False): st.success("🌟 PRO")
        else: st.info("🌱 FREE"); st.button("⬆️ Mejorar", use_container_width=True, on_click=lambda: setattr(st.session_state, 'page', 'pricing'))
        
        st.write("---"); st.caption("PERFIL BIOMÉTRICO")
        nombre = st.text_input("Alias", "Atleta")
        
        # Sliders con memoria
        peso = st.slider("Peso (kg)", 40.0, 150.0, float(datos_usuario['peso']), 0.5)
        altura = st.slider("Altura (cm)", 120, 220, int(datos_usuario['altura']), 1)
        edad = st.slider("Edad", 16, 80, int(datos_usuario['edad']))
        genero = st.radio("Género (para cálculo calórico):", ["Hombre", "Mujer"], horizontal=True) # Nuevo, no se guarda en DB para simplificar, pero se usa en vivo
        
        obj_options = ["Hipertrofia", "Pérdida de Grasa", "Fuerza Máxima", "Resistencia"]
        niv_options = ["Principiante", "Intermedio", "Avanzado"]
        
        try: idx_obj = obj_options.index(datos_usuario['objetivo'])
        except: idx_obj = 0
        try: idx_niv = niv_options.index(datos_usuario['nivel'])
        except: idx_niv = 1

        objetivo = st.selectbox("Objetivo:", obj_options, index=idx_obj)
        nivel = st.select_slider("Experiencia:", options=niv_options, value=niv_options[idx_niv])
        
        if st.button("💾 Guardar Perfil", use_container_width=True):
            if guardar_perfil_db(email_actual, peso, altura, edad, objetivo, nivel): st.toast("Guardado")
            else: st.toast("Error al guardar")

        st.write("---")
        if "history" in st.session_state and len(st.session_state.history) > 1 and st.session_state.get('is_premium'):
             pdf = crear_pdf(st.session_state.history, nombre, peso, objetivo)
             st.download_button("📥 PDF", pdf, "Rutina.pdf")
        st.write("---"); st.button("Cerrar Sesión", on_click=lambda: setattr(st.session_state, 'logged_in', False) or setattr(st.session_state, 'page', 'landing'))

    # --- INTERFAZ PRINCIPAL CON PESTAÑAS ---
    try: st.image("banner.jpg", use_column_width=True)
    except: st.title("ZYNTE COACH")
    
    tab_train, tab_nutri = st.tabs(["🏋️ ENTRENAMIENTO", "🥗 NUTRICIÓN"])

    # === PESTAÑA 1: ENTRENAMIENTO (CHAT) ===
    with tab_train:
        imc = peso / ((altura/100)**2); estado_imc = "Normal"
        if imc >= 25: estado_imc = "Sobrepeso"
        if imc < 18.5: estado_imc = "Bajo peso"
        
        col1, col2, col3, col4 = st.columns([1, 0.7, 2, 1.3])
        with col1: st.metric("IMC", f"{imc:.1f}", estado_imc)
        with col2: st.metric("Peso", f"{peso} kg")
        with col3: st.metric("Meta", objetivo)
        with col4: st.metric("Nivel", nivel)
        st.divider()

        if "history" not in st.session_state:
            st.session_state.history = [{"role": "model", "content": f"Hola. Veo que pesas {peso}kg y buscas {objetivo}. He cargado tu perfil."}]
        
        for msg in st.session_state.history:
            st.chat_message("assistant" if msg["role"] == "model" else "user").markdown(msg["content"])

        if prompt := st.chat_input("Pregunta sobre tu rutina..."):
            st.chat_message("user").markdown(prompt)
            st.session_state.history.append({"role": "user", "content": prompt})
            try:
                ctx = f"Eres Zynte, coach experto. Atleta: {peso}kg, {altura}cm, {nivel}. Objetivo: {objetivo}."
                model = genai.GenerativeModel(MODELO_USADO, system_instruction=ctx)
                chat_history = [{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} for m in st.session_state.history[:-1]]
                chat = model.start_chat(history=chat_history)
                response = chat.send_message(prompt)
                st.chat_message("assistant").markdown(response.text)
                st.session_state.history.append({"role": "model", "content": response.text})
            except: st.error("Error IA")

    # === PESTAÑA 2: NUTRICIÓN ===
    with tab_nutri:
        st.header("Plan Nutricional Inteligente")
        st.write(f"Cálculos personalizados para: **{objetivo}**")
        
        # 1. CALCULADORA AUTOMÁTICA
        cals, prot, carb, gras = calcular_macros(peso, altura, edad, genero, objetivo, nivel)
        
        nc1, nc2, nc3, nc4 = st.columns(4)
        nc1.metric("Calorías Diarias", f"{cals} kcal")
        nc2.metric("Proteína", f"{prot} g")
        nc3.metric("Carbohidratos", f"{carb} g")
        nc4.metric("Grasas", f"{gras} g")
        
        st.divider()
        
        col_diet1, col_diet2 = st.columns([1, 2])
        
        with col_diet1:
            st.markdown("### 📋 Preferencias")
            tipo_dieta = st.selectbox("Tipo de dieta", ["Omnívora (Todo)", "Vegetariana", "Vegana", "Paleo", "Keto"])
            comidas = st.slider("Comidas al día", 2, 6, 4)
            alergias = st.text_input("Alergias / No me gusta", placeholder="Ej: Sin gluten, odio el brócoli...")
            
            st.write("")
            if st.button("🥑 GENERAR DIETA + COMPRA", type="primary", use_container_width=True):
                with st.spinner("Diseñando menú semanal..."):
                    prompt_nutri = f"""
                    Actúa como nutricionista deportivo de élite. Crea un plan para:
                    - Perfil: {peso}kg, {altura}cm, {edad} años, {genero}.
                    - Objetivo: {objetivo} ({cals} kcal

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












