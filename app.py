import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import datetime
import time  # Necesario para hacer la pausa de espera

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

MODELO_USADO = 'models/gemini-flash-latest'

# --- 3. FUNCIÓN GENERADORA DE PDF ---
class PDF(FPDF):
    def header(self):
        # Intentamos poner el logo, si no existe, solo texto
        try: self.image('logo.png', 10, 8, 33)
        except: pass
        self.set_font('Arial', 'B', 15)
        self.cell(80) # Mover a la derecha
        self.cell(30, 10, 'ZYNTE | INFORME DE ENTRENAMIENTO', 0, 0, 'C')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()} - Generado por Zynte AI Coach', 0, 0, 'C')

def crear_pdf(historial, nombre, peso, objetivo):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # 1. Cabecera con datos del cliente
    pdf.set_fill_color(200, 220, 255) # Color azulito claro de fondo
    pdf.cell(0, 10, txt=f"CLIENTE: {nombre} | FECHA: {datetime.date.today()}", ln=1, align='L', fill=True)
    pdf.cell(0, 10, txt=f"PERFIL: {peso}kg | META: {objetivo}", ln=1, align='L', fill=True)
    pdf.ln(10)
    
    # 2. El contenido del chat
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, txt="PLAN PERSONALIZADO:", ln=1)
    pdf.set_font("Arial", size=11)
    
    # Limpieza de texto (Gemini usa **negritas**, las quitamos para el PDF simple)
    for mensaje in historial:
        if mensaje["role"] == "model": # Solo guardamos lo que dice el entrenador
            texto_limpio = mensaje["content"].replace("**", "").replace("*", "-")
            pdf.multi_cell(0, 7, txt=texto_limpio)
            pdf.ln(5)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y()) # Línea separadora
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
        peso = st.slider("Peso (kg)", 40.0, 15
