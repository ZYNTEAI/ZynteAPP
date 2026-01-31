import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import datetime
import time
import gspread
from google.oauth2.service_account import Credentials
import sqlite3
import re
import pandas as pd  

# --- PEGA ESTO AL PRINCIPIO DEL ARCHIVO (Línea 12 aprox) ---
import requests

# 1. DEFINE TU API KEY AQUÍ PARA QUE TODO EL CÓDIGO LA VEA
API_KEY_GLOBAL = st.secrets["GOOGLE_API_KEY"]

# 2. CONFIGURA LA IA INMEDIATAMENTE
genai.configure(api_key=API_KEY_GLOBAL)

# --- GENERADORES RÁPIDOS (FREE) ---
st.caption("⚡ Generadores Rápidos (Pruébalos gratis)")
col_b1, col_b2, col_b3 = st.columns(3)

# 1. Definimos la variable al principio para evitar NameError
prompt_rapido = None 

# 2. Botones con 'key' única para evitar DuplicateElementId
if col_b1.button("🔥 Rutina HIIT 20'", key="btn_hiit_free", use_container_width=True):
    prompt_rapido = "Créame una rutina de HIIT de 20 minutos intensa para hacer en casa."
if col_b2.button("🧘 Estiramientos", key="btn_estira_free", use_container_width=True):
    prompt_rapido = "Dame una tabla de estiramientos de espalda y cuello para después de trabajar."
if col_b3.button("💪 Reto de Flexiones", key="btn_flex_free", use_container_width=True):
    prompt_rapido = "Dime un reto de flexiones para hacer hoy según mi nivel."

# 3. Lógica de envío directo (Salta el error 404)
if prompt_rapido:
    # 1. Aseguramos que el historial exista con la NUEVA PERSONALIDAD
    if "history" not in st.session_state:
        st.session_state.history = [
            # --- INSTRUCCIÓN OCULTA AL CEREBRO DE LA IA ---
            {"role": "user", "content": """
            Actúa como Zynte AI, un entrenador personal de élite y experto en nutrición.
            TU PERSONALIDAD:
            - Eres enérgico, motivador y vas al grano.
            - NUNCA respondas con un simple "Hola, ¿cómo estás?".
            - Cuando el usuario salude, preséntate con fuerza y lanza un reto. 
            Ejemplo: "¡Hola! Soy Zynte AI. ¿Listo para romper tus límites hoy?"
            """},
            
            # --- RESPUESTA DE CONFIRMACIÓN (TAMBIÉN OCULTA) ---
            {"role": "model", "content": "¡Entendido! Soy Zynte AI. Modo motivación activado. ¡A entrenar!"}
        ]
        try:
            # Tienes que añadir 4 espacios antes de 'url' para que esté DENTRO del try
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={API_KEY_GLOBAL}"
            
            # Estas líneas TAMBIÉN deben estar alineadas con 'url'
            payload = {"contents": [{"parts": [{"text": prompt_rapido}]}]}
            
            res = requests.post(url, json=payload)
            
            if res.status_code == 200:
                respuesta_ia = res.json()['candidates'][0]['content']['parts'][0]['text']
                st.session_state.history.append({"role": "model", "content": respuesta_ia})
                st.rerun()
            else:
                st.error(f"Error de Google: {res.status_code}")
                
        except Exception as e:
            st.error(f"Error de red: {e}")
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

# --- CONEXIÓN A GOOGLE SHEETS (El Motor Nuevo) ---
def get_db_sheet():
    # 1. Definimos permisos para acceder a Drive y Sheets
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    
    # 2. Leemos las credenciales desde el archivo secrets.toml
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    client = gspread.authorize(creds)
    
    # 3. Abrimos la hoja "Zynte_DB" (Asegúrate de haberla creado con ese nombre exacto)
    return client.open("Zynte_DB").sheet1

# --- FUNCIONES DE SEGURIDAD Y DATOS (Versión Google Sheets) ---

def validar_email_estricto(email):
    # (Esta función no cambia, es lógica pura)
    email = email.strip().lower()
    patron = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(patron, email):
        return False, "Formato inválido."
    dominios = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com", "protonmail.com"]
    try:
        dom = email.split("@")[-1]
        if dom not in dominios: return False, "Dominio no permitido (Usa Gmail, Hotmail, etc)."
    except: return False, "Error dominio."
    return True, "OK"

def verificar_login(email, password):
    try:
        sheet = get_db_sheet()
        # Buscamos el email en la Columna A (1)
        cell = sheet.find(email, in_column=1)
        if cell:
            # La contraseña está en la Columna B (2) de la misma fila
            real_pass = sheet.cell(cell.row, 2).value
            if real_pass == password:
                return True
    except Exception as e:
        print(f"Error login: {e}")
    return False

def registrar_usuario_sql(email, password):
    try:
        sheet = get_db_sheet()
        # Verificamos si ya existe
        try:
            cell = sheet.find(email, in_column=1)
            if cell: return False # Ya existe
        except gspread.exceptions.CellNotFound:
            pass # No existe, podemos continuar

        # Preparamos la fila nueva. 
        # Estructura: Email, Pass, Fecha, Nombre, Peso, Altura, Edad, Genero, Obj, Nivel, Plan, Historial
        fecha = str(datetime.date.today())
        # Valores por defecto para que no falle al principio
        nueva_fila = [email, password, fecha, "Usuario", 70, 170, 25, "Hombre", "Hipertrofia", "Intermedio", "", ""]
        
        sheet.append_row(nueva_fila)
        return True
    except Exception as e:
        st.error(f"Error registrando en Google Sheets: {e}")
        return False

# --- FUNCIONES DE PERFIL E HISTORIAL ---

def cargar_perfil(email):
    try:
        sheet = get_db_sheet()
        cell = sheet.find(email, in_column=1)
        if cell:
            row_values = sheet.row_values(cell.row)
            # Mapa de columnas (La lista empieza en 0):
            # 0:Email, 1:Pass, 2:Fecha, 3:Nombre, 4:Peso, 5:Altura, 6:Edad, 7:Genero, 8:Obj, 9:Nivel
            datos = {
                "nombre": row_values[3] if len(row_values) > 3 else "Usuario", # <--- NUEVO: Lee el nombre
                "peso": float(row_values[4]) if len(row_values) > 4 else 70.0,
                "altura": int(row_values[5]) if len(row_values) > 5 else 170,
                "edad": int(row_values[6]) if len(row_values) > 6 else 25,
                "genero": row_values[7] if len(row_values) > 7 else "Hombre",
                "objetivo": row_values[8] if len(row_values) > 8 else "Hipertrofia",
                "nivel": row_values[9] if len(row_values) > 9 else "Intermedio",
                "dias": int(row_values[10]) if len(row_values) > 10 and row_values[10].isdigit() else 4 # (Opcional si usas dias)
            }
            return datos
    except Exception as e:
        print(f"Error cargando perfil: {e}")
    # Valores por defecto si falla
    return {"nombre": "Usuario", "peso": 70.0, "altura": 170, "edad": 25, "genero": "Hombre", "objetivo": "Hipertrofia", "nivel": "Intermedio", "dias": 4}

def guardar_perfil_db(email, nombre, peso, altura, edad, genero, objetivo, nivel, dias):
    try:
        sheet = get_db_sheet()
        cell = sheet.find(email, in_column=1)
        if cell:
            r = cell.row
            # Actualizamos CADA columna correctamente
            sheet.update_cell(r, 4, nombre)    # Col D: Nombre (CORREGIDO)
            sheet.update_cell(r, 5, peso)      # Col E: Peso
            sheet.update_cell(r, 6, altura)    # Col F: Altura
            sheet.update_cell(r, 7, edad)      # Col G: Edad
            sheet.update_cell(r, 8, genero)    # Col H: Genero
            sheet.update_cell(r, 9, objetivo)  # Col I: Objetivo
            sheet.update_cell(r, 10, nivel)    # Col J: Nivel
            # (Opcional: Si quieres guardar los días en la Columna K, cambia el índice 11)
            
            # Historial de peso (Columna L / 12)
            fecha_hoy = str(datetime.date.today())
            nuevo_dato = f"{fecha_hoy}:{peso}|"
            historial_actual = sheet.cell(r, 12).value
            if not historial_actual: historial_actual = ""
            sheet.update_cell(r, 12, historial_actual + nuevo_dato)
            
            return True
    except Exception as e:
        st.error(f"Error guardando: {e}")
    return False

def obtener_historial_df(email):
    try:
        sheet = get_db_sheet()
        cell = sheet.find(email, in_column=1)
        if cell:
            # Leemos la celda L (12)
            raw_data = sheet.cell(cell.row, 12).value
            if raw_data:
                # Convertimos el texto "fecha:peso|fecha:peso|" a Tabla
                registros = raw_data.split("|")
                data = []
                for r in registros:
                    if ":" in r:
                        f, p = r.split(":")
                        try: data.append({"fecha": f, "peso": float(p)})
                        except: pass
                
                if data:
                    df = pd.DataFrame(data)
                    return df.sort_values("fecha")
    except:
        pass
    return None

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
  .price-card h3 {
        font-size: 1.3rem !important; /* Reduce el tamaño del texto */
        word-wrap: normal !important; /* Evita que parta las palabras */
        margin-bottom: 10px;
    }
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


# Usamos el nombre sin el prefijo "models/" para que la librería lo gestione
MODELO_USADO = "gemini-flash-latest"

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
            <div style="text-align:center;">
                <h1 style="color:#a0aaba; font-size:2.5rem;">48h</h1>
                <p>Espera Media</p>
            </div>
            <div style="font-size:2rem; color:#555; margin: 0 10px;">VS</div>
            <div style="text-align:center;">
                <h1 style="color:#33ffaa; font-size:2.8rem;">Instantáneo</h1>
                <p>Zynte System</p>
            </div>
        </div>
        <br>
        <p style="color:#ccc;">Genera, modifica y regenera tu plan tantas veces como necesites.</p>
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
        
        # LOGIN CON DETECCIÓN DE PLAN PRO
        with tab1:
            st.write("")
            email_login = st.text_input("Correo", key="login_email").strip().lower()
            pass_login = st.text_input("Contraseña", type="password", key="login_pass").strip()
            st.write("")
            if st.button("ENTRAR ▶", type="primary", use_container_width=True):
          if verificar_login(email, password):
                st.session_state.page = 'app'   <-- ¡Empujado a la derecha!
                st.session_state.email = email
                st.rerun()
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
# --- FUNCIÓN VISUAL PARA BLOQUEAR PESTAÑAS (La pieza que falta) ---
def mostrar_bloqueo_pro(nombre_funcion):
    st.markdown(f"""
    <div style="background-color: rgba(255, 75, 75, 0.1); border: 1px solid #ff4b4b; border-radius: 10px; padding: 30px; text-align: center; margin: 20px 0;">
        <h2 style="color: #ff4b4b; margin-bottom: 10px;">🔒 Función PRO Bloqueada</h2>
        <p style="color: #ddd; font-size: 1.1rem;">
            El módulo de <b>{nombre_funcion}</b> es exclusivo para miembros Zynte PRO.
        </p>
        <hr style="border-color: #ff4b4b; opacity: 0.3; margin: 20px 0;">
        <p style="color: #aaa; font-size: 0.9rem;">
            Desbloquea Nutrición Avanzada, Exportación PDF y Soporte Prioritario.
        </p>
        <br>
        <a href="#" style="background-color: #ff4b4b; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">
            🚀 Desbloquear Todo por 19.99€
        </a>
    </div>
    """, unsafe_allow_html=True)
def app_principal():
    # --- MUEVE ESTO AQUÍ ARRIBA (Línea 335 aprox) ---
    EMAIL_JEFE = "pablonavarrorui@gmail.com" 
    email_actual = st.session_state.get('user_email', 'invitado')
    
    # ESTA LÍNEA ES LA CLAVE: Cargar los datos ANTES de cualquier 'try' o 'if'
    datos_usuario = cargar_perfil(email_actual)
    # ------------------------------------------------

    # Luego sigue con la configuración de la IA
    try:
        genai.configure(api_key=API_KEY_GLOBAL)
    except Exception as e:
        st.error(f"Error config: {e}")

    # ... (Resto de lógica nutricional y PDF igual que antes) ...
    def calcular_macros(peso, altura, edad, genero, objetivo, nivel):
        if genero == "Hombre": tmb = 88.36 + (13.4 * peso) + (4.8 * altura) - (5.7 * edad)
        else: tmb = 447.6 + (9.2 * peso) + (3.1 * altura) - (4.3 * edad)
        factores = {"Principiante": 1.2, "Intermedio": 1.55, "Avanzado": 1.725}
        tdee = tmb * factores.get(nivel, 1.2)
        if "Grasa" in objetivo: return int(tdee - 400), int(peso*2.2), int((tdee-400 - peso*2.2*4 - peso*0.9*9)/4), int(peso*0.9)
        elif "Hipertrofia" in objetivo: return int(tdee + 300), int(peso*2.0), int((tdee+300 - peso*2*4 - peso*1*9)/4), int(peso*1)
        else: return int(tdee), int(peso*1.6), int((tdee - peso*1.6*4 - peso*1*9)/4), int(peso*1)

    class PDF(FPDF):
        def header(self):
            try: self.image('logo.png', 10, 8, 33)
            except: pass
            self.set_font('Arial', 'B', 15); self.cell(80); self.cell(30, 10, 'ZYNTE | INFORME', 0, 0, 'C'); self.ln(20)

    def crear_pdf(historial, nombre, peso, objetivo):
        class PDF(FPDF):
            def header(self):
                try: self.image('logo.png', 10, 8, 33)
                except: pass
                self.set_font('Arial', 'B', 15)
                self.cell(80); self.cell(30, 10, 'ZYNTE | INFORME', 0, 0, 'C')
                self.ln(20)

        pdf = PDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.set_fill_color(200, 220, 255)

        # --- FUNCIÓN DE LIMPIEZA (El truco para que no falle) ---
        def limpiar_texto(texto):
            # Esto quita los emojis y caracteres raros que rompen el PDF
            return str(texto).encode('latin-1', 'replace').decode('latin-1')

        # Cabecera con datos limpios
        pdf.cell(0, 10, txt=limpiar_texto(f"CLIENTE: {nombre} | FECHA: {datetime.date.today()}"), ln=1, align='L', fill=True)
        pdf.cell(0, 10, txt=limpiar_texto(f"PERFIL: {peso}kg | META: {objetivo}"), ln=1, align='L', fill=True)
        pdf.ln(10)
        
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, txt="PLAN PERSONALIZADO:", ln=1)
        
        pdf.set_font("Arial", size=11)
        
        # Cuerpo del PDF (Limpiando cada mensaje)
        for mensaje in historial:
            if mensaje["role"] == "model":
                # 1. Quitamos negritas de Markdown (**texto**)
                texto_base = mensaje["content"].replace("**", "").replace("*", "-")
                # 2. Quitamos emojis
                texto_final = limpiar_texto(texto_base)
                
                pdf.multi_cell(0, 7, txt=texto_final)
                pdf.ln(5)
                
        return pdf.output(dest="S").encode("latin-1", "replace")

    # --- SIDEBAR ---
    with st.sidebar:
        try: st.image("logo.png", width=180)
        except: st.header("ZYNTE")
        
        if st.session_state.get('is_premium'): st.success("🌟 PRO")
        else: st.info("🌱 FREE"); st.button("⬆️ Mejorar", use_container_width=True, on_click=lambda: setattr(st.session_state, 'page', 'pricing'))
        
        st.write("---"); st.caption("PERFIL BIOMÉTRICO")
        nombre = st.text_input("Alias", "Atleta")
        peso = st.slider("Peso (kg)", 40.0, 150.0, float(datos_usuario['peso']), 0.5)
        altura = st.slider("Altura (cm)", 120, 220, int(datos_usuario['altura']), 1)
        edad = st.slider("Edad", 16, 80, int(datos_usuario['edad']))
        genero = st.radio("Género:", ["Hombre", "Mujer"], horizontal=True)
        
        obj_ops = ["Hipertrofia", "Pérdida de Grasa", "Fuerza Máxima", "Resistencia"]
        niv_ops = ["Principiante", "Intermedio", "Avanzado"]
        try: idx_o = obj_ops.index(datos_usuario['objetivo'])
        except: idx_o = 0
        try: idx_n = niv_ops.index(datos_usuario['nivel'])
        except: idx_n = 1
        objetivo = st.selectbox("Objetivo:", obj_ops, index=idx_o)
        nivel = st.select_slider("Experiencia:", options=niv_ops, value=niv_ops[idx_n])
        
        # --- NUEVO: DÍAS DISPONIBLES ---
        dias_entreno = st.slider("Días disponibles/semana:", 1, 7, 4)
        
        if st.button("💾 Guardar Perfil", use_container_width=True):
            with st.spinner("Guardando en la nube..."):
                # Fíjate que ahora enviamos TODOS los datos nuevos
                if guardar_perfil_db(st.session_state.email, nombre, peso, altura, edad, genero, objetivo, nivel, dias_entreno):
                    st.toast("✅ Perfil actualizado en Google Sheets")
                    
                    # Actualizamos la memoria local también
                    st.session_state.datos_usuario = {
                        "nombre": nombre, "peso": peso, "altura": altura, 
                        "edad": edad, "genero": genero, "objetivo": objetivo, 
                        "nivel": nivel, "dias": dias_entreno
                    }
                    time.sleep(1)
                    st.rerun()
                else:
                    st.toast("❌ Error al conectar con la base de datos")

        # --- NUEVO: BOTÓN PARA VACIAR CHAT ---
        st.write("---")
        if st.button("🗑️ Limpiar Conversación", use_container_width=True):
            # Reiniciamos el historial pero MANTENIENDO la personalidad de Zynte
            st.session_state.history = [
                {"role": "user", "content": """
                Actúa como Zynte AI, un entrenador personal de élite y experto en nutrición.
                TU PERSONALIDAD:
                - Eres enérgico, motivador y vas al grano.
                - NUNCA respondas con un simple "Hola, ¿cómo estás?".
                - Cuando el usuario salude, preséntate con fuerza y lanza un reto. 
                Ejemplo: "¡Hola! Soy Zynte AI. ¿Listo para romper tus límites hoy?"
                """},
                {"role": "model", "content": "¡Entendido! Soy Zynte AI. Modo motivación activado. ¡A entrenar!"}
            ]
            st.rerun()
        
        # ==========================================
        # 👑 PANEL DE CONTROL TOTAL (GOD MODE)
        # ==========================================
        if email_actual == EMAIL_JEFE:
            st.write("---")
            with st.expander("🔐 PANEL DE CONTROL"):
                accion = st.radio("Acción:", ["Dar VIP 🌟", "Quitar VIP 💀", "Borrar Usuario ❌"])
                email_target = st.text_input("Email objetivo:").strip().lower()
                
                if st.button("EJECUTAR ORDEN ⚡", type="primary"):
                    if not email_target:
                        st.error("Escribe un email.")
                    else:
                        if accion == "Dar VIP 🌟":
                            if activar_plan_pro(email_target): st.success(f"{email_target} ahora es PRO.")
                            else: st.error("No encontrado.")
                        
                        elif accion == "Quitar VIP 💀":
                            if revocar_plan_pro(email_target): st.warning(f"{email_target} vuelve a ser FREE.")
                            else: st.error("Error o no existe.")
                            
                        elif accion == "Borrar Usuario ❌":
                            if eliminar_usuario_total(email_target): st.error(f"{email_target} ha sido ELIMINADO.")
                            else: st.error("No se pudo borrar.")
        # ==========================================
        # ==========================================

        st.write("---")
        if "history" in st.session_state and len(st.session_state.history) > 1 and st.session_state.get('is_premium'):
             pdf = crear_pdf(st.session_state.history, nombre, peso, objetivo)
             st.download_button("📥 PDF", pdf, "Rutina.pdf")
        st.write("---"); st.button("Cerrar Sesión", on_click=lambda: setattr(st.session_state, 'logged_in', False) or setattr(st.session_state, 'page', 'landing'))

    # MAIN TABS (Igual que antes)
    try: st.image("banner.jpg", use_column_width=True)
    except: st.title("ZYNTE COACH")
    
    tab_train, tab_nutri, tab_prog = st.tabs(["🏋️ ENTRENAMIENTO", "🥗 NUTRICIÓN", "📈 PROGRESO"])

    with tab_train:
        imc = peso / ((altura/100)**2)
        col1, col2, col3, col4 = st.columns([0.8, 1.2, 1.8, 1.5])
        with col1: st.metric("IMC", f"{imc:.1f}", "Normal" if 18.5 < imc < 25 else "Atención")
        with col2: st.metric("Peso", f"{peso} kg")
        with col3: st.metric("Meta", objetivo)
        with col4: st.metric("Nivel", nivel)
        st.divider()

        st.divider()

# --- SECCIÓN DE CHAT ÚNICA ---
    st.write("---") 
    st.subheader("💬 Chat con tu preparador ZYNTE")

    # 1. Aseguramos que el historial exista
    if "history" not in st.session_state:
        st.session_state.history = [
            {"role": "user", "content": """
            Actúa como Zynte AI, un entrenador personal de élite y experto en nutrición.
            TU PERSONALIDAD:
            - Eres enérgico, motivador y vas al grano.
            - NUNCA respondas con un simple "Hola, ¿cómo estás?".
            - Cuando el usuario salude, preséntate con fuerza y lanza un reto. 
            Ejemplo: "¡Hola! Soy Zynte AI. ¿Listo para romper tus límites hoy?"
            """},
            {"role": "model", "content": "¡Entendido! Soy Zynte AI. Modo motivación activado. ¡A entrenar!"}
        ]

    # 2. Bucle de visualización (ALINEADO PERFECTO)
    for msg in st.session_state.history:
        texto = msg["content"]
        
        # Filtro: Ocultamos la instrucción técnica
        if "Actúa como Zynte AI" in texto and "TU PERSONALIDAD" in texto:
            continue
            
        # Mostramos el resto
        with st.chat_message(msg["role"]):
            st.markdown(texto)

    # 3. Caja de texto con Key única (evita el error de Duplicate ID)
    prompt_chat = st.chat_input("¿En qué puedo ayudarte hoy?", key="chat_zynte_final_fixed")

    if prompt_chat:
        st.session_state.history.append({"role": "user", "content": prompt_chat})
        with st.chat_message("user"):
            st.markdown(prompt_chat)

        with st.chat_message("assistant"):
            with st.spinner("Zynte está pensando..."):
                try:
                    # 1. Configuración básica
                    genai.configure(api_key=API_KEY_GLOBAL)
                    model = genai.GenerativeModel(MODELO_USADO)
                    
                    # 2. CONTEXTO INVISIBLE (El Puente de Datos Actualizado)
                    datos_usuario = f"""
                    DATOS ACTUALES DEL CLIENTE (Úsalos para personalizar, no preguntes lo que ya sabes):
                    - Nombre: {nombre}
                    - Peso: {peso} kg
                    - Altura: {altura} cm
                    - Edad: {edad} años
                    - Objetivo: {objetivo}
                    - Nivel: {nivel}
                    - Disponibilidad: {dias_entreno} días a la semana (ADÁPTATE A ESTO)
                    """

                    # 3. CONSTRUIMOS EL PAQUETE PARA GOOGLE
                    chat_history_google = []
                    
                    # A) Primero metemos los datos técnicos
                    chat_history_google.append({
                        "role": "user",
                        "parts": [{"text": datos_usuario}]
                    })

                    # B) Luego añadimos toda la conversación histórica
                    for msg in st.session_state.history:
                        role_google = "user" if msg["role"] == "user" else "model"
                        chat_history_google.append({
                            "role": role_google,
                            "parts": [{"text": msg["content"]}]
                        })
                    
                    # 4. ENVIAMOS Y MOSTRAMOS RESPUESTA
                    response = model.generate_content(chat_history_google)
                    
                    if response.text:
                        st.markdown(response.text)
                        st.session_state.history.append({"role": "model", "content": response.text})
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"Error de conexión: {e}")
    with tab_nutri:
        # --- 1. VERIFICAMOS SI ES PRO ---
        if not st.session_state.get('is_premium'):
            mostrar_bloqueo_pro("Plan Nutricional")
        
        # --- 2. SI ES PRO, MOSTRAMOS EL CONTENIDO ---
        else:
            st.header("Plan Nutricional")
            # ... AQUÍ SIGUE TODO TU CÓDIGO DE ANTES ...
            # ¡IMPORTANTE! Todo lo que había antes aquí tiene que tener
            # un TAB extra a la derecha para estar dentro del 'else'.
            c, p, ch, g = calcular_macros(peso, altura, edad, genero, objetivo, nivel)
            nc1, nc2, nc3, nc4 = st.columns(4)
            nc1.metric("Kcal", c); nc2.metric("Prot", f"{p}g"); nc3.metric("Carb", f"{ch}g"); nc4.metric("Grasa", f"{g}g")
            st.divider()
            # --- PEGA ESTO JUSTO DEBAJO DE 'st.divider()' ---
            col_d1, col_d2 = st.columns([1, 2])
            
            # COLUMNA 1: BOTONES Y LÓGICA
            with col_d1:
                dieta = st.selectbox("Tipo", ["Omnívora", "Vegetariana", "Vegana", "Keto"])
                if st.button("🥑 GENERAR DIETA", type="primary"):
                    with st.spinner("Creando menú..."):
                        try:
                            # 1. Configuramos el modelo (Variable Global)
                            model = genai.GenerativeModel(MODELO_USADO)
                            
                            # 2. Definimos el Prompt Experto
                            prompt_nutri = f"""
                            Actúa como un Nutricionista Deportivo de alto rendimiento.
                            Objetivo: Crear un plan de alimentación {dieta} perfecto de {c} kcal diarias.
                            Contexto del cliente: Objetivo {objetivo}.
    
                            Estructura de la respuesta obligatoria:
                            1. 📊 RESUMEN MACROS: Proteínas, Grasas, Carbohidratos totales.
                            2. 🍽️ MENÚ DIARIO (Desayuno, Almuerzo, Cena, Snacks):
                               - Usa formato Tabla Markdown.
                               - Indica peso exacto de los alimentos en crudo (gramos).
                               - Incluye una breve instrucción de cocinado.
                            3. 🛒 LISTA DE LA COMPRA SEMANAL:
                               - Agrupada por pasillos del supermercado (Verdulería, Carnicería, Varios).
                            4. 💡 CONSEJO PRO: Un tip específico para {objetivo}.
    
                            Mantén un tono motivador y profesional.
                            """
                            
                            # 3. Generamos y guardamos
                            res = model.generate_content(prompt_nutri)
                            st.session_state.plan_nutri = res.text
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Error detallado de la IA: {e}")
    
            # COLUMNA 2: RESULTADO (Perfectamente alineado ahora)
            with col_d2:
                if "plan_nutri" in st.session_state:
                    st.markdown(st.session_state.plan_nutri)
                else:
                    st.info("Configura y genera tu plan nutricional aquí.")

    with tab_prog:
        # --- 1. VERIFICAMOS SI ES PRO ---
        if not st.session_state.get('is_premium'):
            mostrar_bloqueo_pro("Análisis de Progreso")
            
        # --- 2. SI ES PRO, MOSTRAMOS EL CONTENIDO ---
        else:
            # Aquí va tu código antiguo de la gráfica, INDENTADO A LA DERECHA
            st.header("📈 Tu Evolución")
            st.write("Visualiza cómo te acercas a tu objetivo sesión tras sesión.")
            df_progreso = obtener_historial_df(email_actual)
            if df_progreso is not None and not df_progreso.empty:
                peso_inicial = df_progreso.iloc[0]['peso']
                peso_actual = df_progreso.iloc[-1]['peso']
                delta = peso_actual - peso_inicial
                pc1, pc2, pc3 = st.columns(3)
                pc1.metric("Peso Inicial", f"{peso_inicial} kg")
                pc2.metric("Peso Actual", f"{peso_actual} kg")
                pc3.metric("Cambio Total", f"{delta:.1f} kg", delta, delta_color="inverse" if "Grasa" in objetivo else "normal")
                st.write(""); st.area_chart(df_progreso.set_index('fecha'), color="#33ffaa")
                with st.expander("Ver historial detallado"): st.dataframe(df_progreso, use_container_width=True)
            else:
                st.info("👋 Guarda tu perfil hoy para ver tu primer punto en la gráfica.")

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



























































































































































































