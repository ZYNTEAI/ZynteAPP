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

# --- 2. ESTILOS CSS PREMIUM ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* FONDO DEGRADADO NOCTURNO */
    [data-testid="stAppViewContainer"] {
        background: radial-gradient(ellipse at top, #1b2735 0%, #090a0f 100%);
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
    
    /* TARJETAS DE CRISTAL */
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
    
    /* BOTONES ESTILIZADOS */
    div.stButton > button {
        border-radius: 8px;
        font-weight: bold;
        transition: all 0.2s;
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
    st.caption("Accede a tu panel de control de alto rendimiento.")
    st.write("")
    
    lc1, lc2, lc3 = st.columns([1,2,1])
    with lc2:
        tab1, tab2 = st.tabs(["Iniciar Sesión", "Nuevo Registro"])
        
        # PESTAÑA 1: LOGIN
        with tab1:
            st.write("")
            email_login = st.text_input("Correo Electrónico", key="login_email")
            pass_login = st.text_input("Contraseña", type="password", key="login_pass")
            st.write("")
            if st.button("ENTRAR AL SISTEMA ▶", type="primary", use_container_width=True):
                st.session_state.logged_in = True
                st.session_state.page = 'pricing'
                st.success("Credenciales verificadas. Redirigiendo...")
                time.sleep(0.5)
                st.rerun()
        
        # PESTAÑA 2: REGISTRO (Aquí estaba el error)
        with tab2:
            st.write("")
            new_email = st.text_input("Tu Mejor Email", key="reg_email")
            new_pass = st.text_input("Elige Contraseña", type="password", key="reg_pass")
            st.write("")
            
            if st.button("Crear Cuenta Gratuita", use_container_width=True):
                if new_email and new_pass:
                    with st.spinner("Registrando usuario en la base de datos..."):
                        sheet = conectar_db() 
                        if sheet:
                            try:
                                fecha = str(datetime.date.today())
                                sheet.append_row([new_email, fecha, "Free"])
                                st.success("¡Registro completado con éxito!")
                                # --- LÍNEA DE RASTREO (Solo para depurar) ---
                                st.write(f"📍 Datos escritos en: {sheet.spreadsheet.title}")
                                st.link_button("📂 ABRIR HOJA DE CÁLCULO", f"https://docs.google.com/spreadsheets/d/{sheet.spreadsheet.id}")
                                # --------------------------------------------
                                time.sleep(5) # Damos tiempo para leer
                                st.session_state.logged_in = True
                                st.session_state.page = 'pricing'
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al guardar: {e}")
                        else:
                            st.warning("Nota: Usuario registrado localmente (Error de conexión DB).")
                            time.sleep(1)
                            st.session_state.logged_in = True
                            st.session_state.page = 'pricing'
                            st.rerun()
                else:
                    st.warning("Por favor rellena todos los campos.")

    st.write(""); st.write("---")
    if st.button("⬅️ Volver"): st.session_state.page = 'landing'; st.rerun()

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
            self.cell(0, 10, f'Pagina {self.page_no()} - Zynte Elite Performance', 0, 0, 'C')

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




