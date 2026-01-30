import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import datetime
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. CONFIGURACIÓN INICIAL ---
st.set_page_config(
    page_title="Zynte | Elite Coach", 
    page_icon="logo.png", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- 2. ESTILOS CSS ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stAppViewContainer"] {background: radial-gradient(ellipse at top, #1b2735 0%, #090a0f 100%);}
    [data-testid="stHeader"] {background: transparent;}
    .hero-title {
        font-size: 3.5rem; font-weight: 800;
        background: linear-gradient(to right, #ffffff, #33ffaa);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-align: center; margin-bottom: 10px; text-shadow: 0 0 30px rgba(51, 255, 170, 0.2);
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

# --- 3. CONEXIÓN API & DATABASE ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except:
    pass

MODELO_USADO = 'models/gemini-flash-latest'

# --- FUNCIÓN DE CONEXIÓN (YA CONFIGURADA CON TU ID) ---
def conectar_db():
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # TU ID REAL (NO TOCAR)
        SHEET_ID = "1KZR8mmuRPTSaqlDi1VyRdG_ZaC20UUMqZd0jDdKE-OM"
        
        sheet = client.open_by_key(SHEET_ID).sheet1
        return sheet
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

# ==============================================================================
# VISTAS
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

def mostrar_login():
    st.markdown("## 🔐 Área de Miembros")
    st.caption("Accede a tu panel de control de alto rendimiento.")
    st.write("")
    lc1, lc2, lc3 = st.columns([1,2,1])
    with lc2:
        tab1, tab2 = st.tabs(["Iniciar Sesión", "Nuevo Registro"])
        
        with tab1: # LOGIN
            st.write("")
            st.text_input("Correo Electrónico", key="login_email")
            st.text_input("Contraseña", type="password", key="login_pass")
            st.write("")
            if st.button("ENTRAR AL SISTEMA ▶", type="primary", use_container_width=True):
                st.session_state.logged_in = True
                st.session_state.page = 'pricing'
                st.rerun()
        
        with tab2: # REGISTRO (AQUÍ ES DONDE SE GUARDAN LOS DATOS)
            st.write("")
            new_email = st.text_input("Tu Mejor Email", key="reg_email")
            new_pass = st.text_input("Elige Contraseña", type="password", key="reg_pass")
            st.write("")
            
            if st.button("Crear Cuenta Gratuita", use_container_width=True):
                if new_email and new_pass:
                    with st.spinner("Creando usuario..."):
                        sheet = conectar_db()
                        if sheet:
                            try:
                                # ESTA LÍNEA ES LA QUE ESCRIBE EN EL EXCEL 👇
                                sheet.append_row([new_email, str(datetime.date.today()), "Free"])
                                st.success("¡Cuenta creada! Revisa tu Google Sheet ahora.")
                                time.sleep(2)
                                st.session_state.logged_in = True
                                st.session_state.page = 'pricing'
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error escribiendo: {e}")
                        else:
                            st.error("No se pudo conectar con la hoja.")
                else:
                    st.warning("Rellena los campos.")
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
            self.set_font('Arial', 'B', 15); self.cell(0, 10, 'ZYNTE | INFORME', 0, 1, 'C'); self.ln(10)
    def crear_pdf(historial, nombre):
        pdf = PDF(); pdf.add_page(); pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, txt=f"Cliente: {nombre}\nFecha: {datetime.date.today()}")
        pdf.ln(10)
        for msg in historial:
            if msg["role"] == "model": pdf.multi_cell(0, 7, txt=msg["content"].replace("*", "")); pdf.ln(5)
        return pdf.output(dest="S").encode("latin-1", "replace")

    with st.sidebar:
        st.header("ZYNTE")
        if st.session_state.get('is_premium'): st.success("🌟 PRO")
        else: st.info("🌱 FREE")
        st.write("---")
        nombre = st.text_input("Nombre", "Atleta")
        peso = st.slider("Peso", 40, 150, 70)
        objetivo = st.selectbox("Objetivo", ["Masa Muscular", "Perder Grasa"])
        st.write("---")
        if st.button("Cerrar Sesión"): st.session_state.logged_in = False; st.session_state.page = 'landing'; st.rerun()

    if "history" not in st.session_state:
        st.session_state.history = [{"role": "model", "content": f"Hola {nombre}. Listo para entrenar."}]

    for msg in st.session_state.history:
        st.chat_message("assistant" if msg["role"] == "model" else "user").markdown(msg["content"])

    if prompt := st.chat_input("Escribe aquí..."):
        st.session_state.history.append({"role": "user", "content": prompt})
        st.chat_message("user").markdown(prompt)
        try:
            model = genai.GenerativeModel(MODELO_USADO)
            response = model.generate_content(prompt)
            st.session_state.history.append({"role": "model", "content": response.text})
            st.chat_message("assistant").markdown(response.text)
        except: st.warning("Error de IA")

# --- MAIN ---
if 'page' not in st.session_state: st.session_state.page = 'landing'
if st.session_state.page == 'landing': mostrar_landing()
elif st.session_state.page == 'login': mostrar_login()
elif st.session_state.page == 'pricing': mostrar_pricing()
elif st.session_state.page == 'app': app_principal()
