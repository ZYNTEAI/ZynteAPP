import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import time
import datetime

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

# Modelo estable
MODELO_USADO = 'models/gemini-flash-latest'

# --- 3. MOTOR PDF ---
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
            # Limpiamos símbolos de markdown para el PDF
            texto_limpio = mensaje["content"].replace("**", "").replace("*", "-").replace("##", "")
            pdf.multi_cell(0, 7, txt=texto_limpio)
            pdf.ln(5)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
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

    # ZONA DE DESCARGA
    st.write("---")
    st.subheader("📂 Zona de Descargas")
    if "history" in st.session_state and len(st.session_state.history) > 1:
        pdf_bytes = crear_pdf(st.session_state.history, nombre, peso, objetivo)
        st.download_button("📄 DESCARGAR PDF", pdf_bytes, f"Plan_Zynte_{nombre}.pdf", "application/pdf")
    else:
        st.info("ℹ️ Habla con Zynte para generar tu PDF.")

    st.write("---")
    if st.button("Reiniciar Chat"):
        st.session_state.history = []
        st.rerun()

# --- 5. DASHBOARD VISUAL ---
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

# --- 6. CHAT CON SISTEMA "ANTI-CAÍDAS" AMABLE ---
if "history" not in st.session_state:
    st.session_state.history = []
    st.session_state.history.append({"role": "model", "content": f"Bienvenido {nombre}. Estoy listo para crear tu plan de {objetivo}. ¿
