import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import time
import datetime

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Zynte Coach", page_icon="logo.png", layout="wide")

# Estilos CSS
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

# Modelo
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
            # Limpieza de texto
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
        objetivo = st.selectbox("Objet
