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

# --- CONEXIÓN A GOOGLE SHEETS (El Motor ) ---
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
            
            # Limpiamos el valor del status para evitar errores de espacios o mayúsculas
            raw_status = row_values[12] if len(row_values) > 12 else "free"
            status_limpio = str(raw_status).strip().lower() 

            datos = {
                "nombre": row_values[3] if len(row_values) > 3 else "Usuario",
                "peso": float(row_values[4]) if len(row_values) > 4 else 70.0,
                "altura": int(row_values[5]) if len(row_values) > 5 else 170,
                "edad": int(row_values[6]) if len(row_values) > 6 else 25,
                "genero": row_values[7] if len(row_values) > 7 else "Hombre",
                "objetivo": row_values[8] if len(row_values) > 8 else "Hipertrofia",
                "nivel": row_values[9] if len(row_values) > 9 else "Intermedio",
                "dias": int(row_values[10]) if len(row_values) > 10 else 4,
                "status": status_limpio # <--- Aquí está la clave
            }
            return datos
    except Exception as e:
        print(f"Error cargando perfil: {e}")
    
    # Valores por defecto si falla la lectura
    return {"nombre": "Usuario", "status": "free", "peso": 70.0, "altura": 170, "edad": 25, "genero": "Hombre", "objetivo": "Hipertrofia", "nivel": "Intermedio", "dias": 4}

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
# --- FUNCIÓN DE ADMINISTRADOR (CAMBIAR STATUS) ---
def admin_update_status(email_usuario, nuevo_status):
    """
    Cambia el status de un usuario a 'pro', 'free' o 'banned'
    """
    try:
        sheet = get_db_sheet()
        cell = sheet.find(email_usuario, in_column=1)
        if cell:
            # La columna M (Status) es la número 13
            sheet.update_cell(cell.row, 13, nuevo_status)
            return True
    except Exception as e:
        st.error(f"Error admin: {e}")
    return False
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
# --- BOTÓN DE ENTRAR (Lógica de Negocio: Free vs Pro) ---
        if st.button("Entrar", use_container_width=True):
            if verificar_login(email, password):
                # 1. Guardamos el email fundamental
                st.session_state.email = email
                
                # 2. Cargamos el perfil YA para saber si es PRO o FREE
                # (Esto lee la columna M de tu Google Sheet)
                datos = cargar_perfil(email)
                st.session_state.datos_usuario = datos
                
                # 3. Verificamos el estado
                es_pro = (datos.get("status") == "pro")
                st.session_state.is_premium = es_pro
                
                # 4. El Semáforo de acceso 🚦
                if es_pro:
                    st.session_state.page = 'app'  # Al gimnasio directo
                    st.success(f"¡Bienvenido de nuevo, {datos['nombre']}! 🌟")
                else:
                    st.session_state.page = 'pricing'  # A la tienda
                    st.info("Cuenta verificada. Selecciona tu plan.")

                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Usuario o contraseña incorrectos")
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
    # --- 1. SEGURIDAD ---
    if "email" not in st.session_state or not st.session_state.email:
        st.session_state.page = "login"
        st.rerun()
        return

    # --- 2. GESTIÓN INTELIGENTE DE DATOS ---
    email_actual = st.session_state.email
    EMAIL_JEFE = "pablonavarrorui@gmail.com" # <--- TU EMAIL

    # Si no tenemos datos, los cargamos del Excel
    if "datos_usuario" not in st.session_state:
        st.session_state.datos_usuario = cargar_perfil(email_actual)

    # Referencia corta para usar en el código
    datos = st.session_state.datos_usuario
    
    # === SINCRONIZACIÓN WEB VS EXCEL ===
    # Aquí está la clave: La variable de sesión 'is_premium' manda sobre el Excel
    # para dar esa sensación de "instantáneo".
    status_excel = str(datos.get("status", "free")).lower().strip()
    
    # Si acabamos de forzar el PRO en el admin panel, 'is_premium' será True
    # aunque 'status_excel' todavía pudiera ser antiguo por caché.
    if "is_premium" not in st.session_state:
        # Solo si no existe, confiamos en el Excel
        st.session_state.is_premium = (status_excel == "pro")
    
    # Si el Excel dice PRO, forzamos PRO (por si entras desde otro PC)
    if status_excel == "pro" and not st.session_state.is_premium:
        st.session_state.is_premium = True
        st.rerun()

    # --- 3. VARIABLES GLOBALES (Arreglado el error de 'peso') ---
    # Usamos .get() para que nunca falle si el campo está vacío en el Excel
    nombre = datos.get('nombre', 'Atleta')
    
    # Usamos bloques try/except para evitar que un texto rompa el slider numérico
    try: peso = float(datos.get('peso', 70.0))
    except: peso = 70.0
    
    try: altura = int(datos.get('altura', 170))
    except: altura = 170
    
    try: edad = int(datos.get('edad', 25))
    except: edad = 25
    
    genero = datos.get('genero', 'Hombre')
    objetivo_actual = datos.get('objetivo', 'Hipertrofia')
    nivel_actual = datos.get('nivel', 'Intermedio')

    # --- 4. FUNCIONES INTERNAS (Sin cambios) ---
    def calcular_macros(p, a, e, g, obj, niv):
        if g == "Hombre": tmb = 88.36 + (13.4 * p) + (4.8 * a) - (5.7 * e)
        else: tmb = 447.6 + (9.2 * p) + (3.1 * a) - (4.3 * e)
        fact = {"Principiante": 1.2, "Intermedio": 1.55, "Avanzado": 1.725}
        tdee = tmb * fact.get(niv, 1.2)
        if "Grasa" in obj: return int(tdee - 400), int(p*2.2), int((tdee-400 - p*2.2*4 - p*0.9*9)/4), int(p*0.9)
        elif "Hipertrofia" in obj: return int(tdee + 300), int(p*2.0), int((tdee+300 - p*2*4 - p*1*9)/4), int(p*1)
        else: return int(tdee), int(p*1.6), int((tdee - p*1.6*4 - p*1*9)/4), int(p*1)

    # --- 5. SIDEBAR ---
    with st.sidebar:
        # === BOTÓN JEFE (Indestructible) ===
        if email_actual == EMAIL_JEFE:
            st.warning("👑 ZONA ADMIN")
            if st.button("⚙️ PANEL DE CONTROL", type="primary", use_container_width=True):
                st.session_state.page = 'admin'
                st.rerun()
            st.divider()
        # ===================================

        try: st.image("logo.png", width=180)
        except: st.header("ZYNTE")
        
        # VISOR DE ESTADO (Feedback inmediato)
        if st.session_state.is_premium:
            st.success("🌟 PLAN PRO ACTIVO")
        else:
            st.info("🌱 PLAN GRATUITO")
            if st.button("⬆️ Mejorar Plan"): st.session_state.page='pricing'; st.rerun()

        st.divider()
        st.caption("CONFIGURACIÓN")
        
        # Sliders conectados a las variables seguras
        peso_new = st.slider("Peso (kg)", 40.0, 150.0, peso, 0.5)
        altura_new = st.slider("Altura (cm)", 120, 220, altura, 1)
        edad_new = st.slider("Edad", 16, 80, edad)
        
        obj_ops = ["Hipertrofia", "Pérdida de Grasa", "Fuerza Máxima", "Resistencia"]
        niv_ops = ["Principiante", "Intermedio", "Avanzado"]
        
        # Índices seguros
        idx_o = obj_ops.index(objetivo_actual) if objetivo_actual in obj_ops else 0
        idx_n = niv_ops.index(nivel_actual) if nivel_actual in niv_ops else 1
        
        objetivo_new = st.selectbox("Objetivo:", obj_ops, index=idx_o)
        nivel_new = st.select_slider("Nivel:", options=niv_ops, value=niv_ops[idx_n])
        
        if st.button("💾 Guardar Datos", use_container_width=True):
            if guardar_perfil_db(email_actual, nombre, peso_new, altura_new, edad_new, genero, objetivo_new, nivel_new, 4):
                st.toast("✅ Guardado")
                # Actualizamos memoria local al instante
                st.session_state.datos_usuario.update({"peso": peso_new, "altura": altura_new, "objetivo": objetivo_new})
                time.sleep(0.5); st.rerun()
            else: st.error("Error guardando")

        st.write("---")
        if st.button("Cerrar Sesión", use_container_width=True):
            st.session_state.clear() # Borramos todo para evitar conflictos
            st.session_state.page = "landing"
            st.rerun()

    # --- 6. CUERPO DE LA APP ---
    try: st.image("banner.jpg", use_column_width=True)
    except: st.title("ZYNTE COACH")
    
    tab_train, tab_nutri, tab_prog = st.tabs(["🏋️ ENTRENAMIENTO", "🥗 NUTRICIÓN", "📈 PROGRESO"])

    with tab_train:
        imc = peso_new / ((altura_new/100)**2)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("IMC", f"{imc:.1f}")
        c2.metric("Peso", f"{peso_new}kg")
        c3.metric("Meta", objetivo_new)
        c4.metric("Nivel", nivel_new)
        st.divider()

        # Chat IA
        st.subheader("💬 Chat con tu preparador")
        if "history" not in st.session_state: st.session_state.history = []
        for msg in st.session_state.history:
            if msg.get("role") != "system": st.chat_message(msg["role"]).markdown(msg["content"])

        if prompt := st.chat_input("Pregunta algo..."):
            st.chat_message("user").markdown(prompt)
            st.session_state.history.append({"role": "user", "content": prompt})
            
            with st.chat_message("assistant"):
                try:
                    # Configuración IA
                    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    
                    # Contexto actualizado al segundo
                    ctx = f"Cliente {peso_new}kg, {altura_new}cm. Meta: {objetivo_new}."
                    
                    # Llamada IA
                    hist = [{"role": ("user" if m["role"]=="user" else "model"), "parts": [{"text": m["content"]}]} for m in st.session_state.history]
                    chat = model.start_chat(history=hist[:-1])
                    res = chat.send_message(f"{ctx}\nUsuario: {prompt}")
                    st.markdown(res.text)
                    st.session_state.history.append({"role": "model", "content": res.text})
                except Exception as e: st.error(f"Error IA: {e}")

    with tab_nutri:
        # 1. BLOQUEO PRO: Si no es premium, mostramos el candado
        if not st.session_state.get('is_premium'):
            mostrar_bloqueo_pro("Nutrición Avanzada")
        
        # 2. CONTENIDO PRO: Si paga, ve la herramienta completa
        else:
            st.header("🥗 Tu Plan Nutricional Inteligente")
            
            # A) Cálculo de Macros en tiempo real
            kcal, p, ch, g = calcular_macros(peso_new, altura_new, edad_new, genero, objetivo_new, nivel_new)
            
            # Tarjetas de Macros
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Kcal Diarias", kcal, help="Calorías objetivo para tu meta")
            c2.metric("Proteínas", f"{p}g", help="Base para construir músculo")
            c3.metric("Carbos", f"{ch}g", help="Energía para entrenar")
            c4.metric("Grasas", f"{g}g", help="Regulación hormonal")
            
            st.divider()
            
            # B) CONFIGURADOR DE MENÚ (Lo que faltaba)
            col_izq, col_der = st.columns([1, 2], gap="large")
            
            with col_izq:
                st.subheader("⚙️ Configura tu Menú")
                
                # Selectores que pediste
                tipo_dieta = st.selectbox("Tipo de Alimentación", 
                                          ["Omnívora (Todo)", "Vegetariana", "Vegana", "Keto", "Paleo", "Sin Gluten"],
                                          key="nutri_tipo")
                
                alergias = st.text_input("Alergias o Intolerancias", 
                                         placeholder="Ej: Nueces, Lactosa, Marisco...",
                                         key="nutri_alergias")
                
                comidas = st.slider("Comidas al día", 3, 6, 4, key="nutri_comidas")
                
                st.write("") # Espacio
                
                # BOTÓN GENERADOR
                if st.button("🥑 GENERAR DIETA AHORA", type="primary", use_container_width=True):
                    with st.spinner("El Chef Zynte está calculando raciones..."):
                        try:
                            # Configuración de IA
                            genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
                            model = genai.GenerativeModel("gemini-1.5-flash")
                            
                            # Prompt Avanzado con Alergias
                            texto_alergias = f"EVITAR ESTRICTAMENTE: {alergias}" if alergias else "Sin alergias."
                            
                            prompt_diet = f"""
                            Actúa como Nutricionista Deportivo Experto.
                            Crea un plan de alimentación de 1 DÍA completo.
                            
                            🎯 OBJETIVOS:
                            - Calorías: {kcal} kcal.
                            - Macros: {p}g Proteína, {ch}g Carbos, {g}g Grasas.
                            - Estilo: {tipo_dieta}.
                            - Estructura: {comidas} comidas.
                            - ⚠️ {texto_alergias}
                            
                            FORMATO DE RESPUESTA (Usa Markdown bonito):
                            1. 🥗 MENÚ DETALLADO:
                               - Desglose por comidas (Desayuno, etc).
                               - PESOS EXACTOS en crudo (ej: 150g Pechuga).
                            2. 🛒 LISTA DE LA COMPRA:
                               - Organizada por pasillos (Verdulería, Carnicería...).
                            
                            Sé preciso con las cantidades para cuadrar los macros.
                            """
                            
                            res = model.generate_content(prompt_diet)
                            st.session_state.plan_nutri = res.text
                            st.rerun() # Recargamos para mostrar el resultado
                            
                        except Exception as e:
                            st.error(f"Error al conectar con la IA: {e}")

            # C) VISOR DE RESULTADOS
            with col_der:
                if "plan_nutri" in st.session_state:
                    st.markdown(st.session_state.plan_nutri)
                    
                    st.write("---")
                    # Botón extra para descargar/copiar (simulado)
                    st.download_button("📥 Descargar Dieta (TXT)", 
                                       st.session_state.plan_nutri, 
                                       "dieta_zynte.txt")
                else:
                    # Mensaje de espera bonito
                    st.info("👈 **Instrucciones:**\n1. Selecciona tu tipo de dieta.\n2. Escribe tus alergias (si tienes).\n3. Pulsa 'Generar' para ver tu plan aquí.")

    with tab_prog:
        if not st.session_state.is_premium:
            mostrar_bloqueo_pro("Gráficas de Progreso")
        else:
            st.header("📈 Gráficas PRO")
            df = obtener_historial_df(email_actual)
            if df is not None: st.line_chart(df.set_index('fecha'))
            else: st.info("Sin datos aún.")

def admin_panel():
    st.title("👮‍♂️ Panel de Control - Zynte God Mode")
    st.warning("⚠️ Zona restringida. Los cambios se aplican directamente a la Base de Datos.")

    try:
        sheet = get_db_sheet()
        all_data = sheet.get_all_values()
        
        if len(all_data) > 1:
            header = all_data[0]
            rows = all_data[1:]
            df = pd.DataFrame(rows, columns=header)
            
            # Filtro para ver solo lo importante
            try:
                st.dataframe(df[["email", "nombre", "status", "fecha_registro"]])
            except:
                st.dataframe(df) # Por si faltan columnas
            
            st.write("---")
            st.subheader("🛠️ Gestión de Usuarios")

            # Selector de Usuario
            lista_emails = df["email"].tolist() if "email" in df.columns else []
            if not lista_emails: st.error("No hay emails en la columna 'email'"); return

            usuario_elegido = st.selectbox("Seleccionar Usuario a Modificar:", lista_emails)
            
            # Botones de Acción
            col1, col2, col3 = st.columns(3)
            
            # === BOTÓN DE HACER PRO (Optimista) ===
            with col1:
                if st.button("🌟 Hacer PRO", use_container_width=True):
                    # 1. Actualizamos el Excel (Lento pero seguro)
                    if admin_update_status(usuario_elegido, "pro"):
                        
                        # 2. ¡TRUCO! Si soy yo mismo, me actualizo YA (Rápido)
                        # "Actualízate independientemente del Google Sheet"
                        if usuario_elegido == st.session_state.get('email'):
                            if "datos_usuario" in st.session_state:
                                st.session_state.datos_usuario["status"] = "pro"
                            st.session_state.is_premium = True
                            st.toast("⚡ ¡Modo PRO activado instantáneamente!")
                        else:
                            st.success(f"{usuario_elegido} ahora es PRO en la base de datos.")
                        
                        time.sleep(0.5)
                        st.rerun()
            
            # === BOTÓN DE HACER FREE ===
            with col2:
                if st.button("⬇️ Hacer FREE", use_container_width=True):
                    if admin_update_status(usuario_elegido, "free"):
                        # Truco de actualización inmediata
                        if usuario_elegido == st.session_state.get('email'):
                            if "datos_usuario" in st.session_state:
                                st.session_state.datos_usuario["status"] = "free"
                            st.session_state.is_premium = False
                            st.toast("⬇️ Vuelves a ser FREE al instante.")
                        else:
                            st.success(f"{usuario_elegido} bajado a FREE.")
                        time.sleep(0.5)
                        st.rerun()

            with col3:
                if st.button("🚫 BANEAR", type="primary", use_container_width=True):
                    if admin_update_status(usuario_elegido, "banned"):
                        st.error("Usuario Baneado.")
                        time.sleep(0.5)
                        st.rerun()
                        
    except Exception as e:
        st.error(f"Error cargando panel admin: {e}")
# ... (código anterior del panel donde banean usuarios) ...

    st.write("---")
    st.subheader("👤 Tu Zona Personal")
    
    col_a, col_b = st.columns([3, 1])
    with col_a:
        st.info("Como administrador, también tienes tu propio perfil de entrenamiento.")
    with col_b:
        # BOTÓN PUENTE: Cambia la página de 'admin' a 'app'
        if st.button("🚀 Ir a mi App / Entrenar", use_container_width=True):
            st.session_state.page = 'app'
            st.rerun()
# ==============================================================================
# 🚀 ROUTER
# ==============================================================================


# --- FUNCIÓN PRINCIPAL (El Cerebro de Navegación) ---
def main():
    # 1. Si no hay página definida, empezamos en Login
    if "page" not in st.session_state:
        st.session_state.page = "login"

    # =========================================================
    # ESCENA 1: PANTALLA DE LOGIN (COMPLETA)
    # =========================================================
    if st.session_state.page == "login":
        
        # 1. LOGO CENTRADO
        col_izq, col_centro, col_der = st.columns([1, 1, 1])
        with col_centro:
            try:
                st.image("logo.png", width=200) # Asegúrate que tu archivo se llama así
            except:
                st.markdown("<div style='text-align: center; font-size: 80px;'>💪</div>", unsafe_allow_html=True)

        st.markdown("<h1 style='text-align: center;'>Zynte AI Login</h1>", unsafe_allow_html=True)
        st.write("---")
        
        # 2. FORMULARIO DE ACCESO (Centrado también)
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            email = st.text_input("📧 Email")
            password = st.text_input("🔑 Contraseña", type="password")
            
            st.write("") # Espacio
            
            # --- BOTÓN DE ENTRAR (CON LÓGICA ADMIN Y BANEO) ---
            if st.button("Entrar", use_container_width=True):
                if verificar_login(email, password):
                    st.session_state.email = email
                    
                    # 1. ¿ERES EL JEFE? (Pon aquí tu email real de admin) 👇
                    if email == "pablonavarrorui@gmail.com":  # <--- CAMBIA ESTO POR TU EMAIL
                        st.session_state.page = 'admin'
                        st.rerun()

                    # 2. Si no eres el jefe, cargamos perfil normal
                    datos = cargar_perfil(email)
                    st.session_state.datos_usuario = datos
                    status = datos.get("status", "free")

                    # 3. FILTRO ANTI-BANEADOS 🛑
                    if status == "banned":
                        st.error("⛔ TU CUENTA HA SIDO SUSPENDIDA POR INFRINGIR LAS NORMAS.")
                        st.stop() # Detiene la ejecución aquí mismo

                    # 4. Lógica Pro vs Free
                    if status == "pro":
                        st.session_state.page = 'app'
                        st.toast(f"¡Hola de , {datos['nombre']}! 🌟")
                    else:
                        st.session_state.page = 'pricing'
                        st.toast("Verificado. Selecciona tu plan.")
                        
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("❌ Usuario o contraseña incorrectos")
            
            # --- BOTÓN DE REGISTRO ---
            if st.button("Crear Cuenta Gratis", use_container_width=True):
                if validar_email_estricto(email)[0]:
                    # Al registrarse, por defecto eres 'free' (ver función registrar_usuario_sql)
                    if registrar_usuario_sql(email, password):
                        st.success("✅ Cuenta creada. ¡Ahora pulsa 'Entrar'!")
                    else:
                        st.warning("⚠️ Ese email ya existe.")
                else:
                    st.error("Email inválido o dominio no permitido.")
            
    # =========================================================
    # ESCENA 2: PANTALLA DE PRECIOS (La que faltaba)
    # =========================================================
    elif st.session_state.page == "pricing":
        st.title("💎 Desbloquea tu Potencial")
        st.write("Tu cuenta actual es **Gratuita**. Elige cómo quieres entrenar.")
        
        col_free, col_pro = st.columns(2)
        
        # Columna Gratis
        with col_free:
            st.info("### Plan Básico\n* Acceso a Chat (Limitado)\n* Registro de Peso\n* Rutinas Estándar")
            if st.button("➡️ Continuar con Versión Gratis", use_container_width=True):
                st.session_state.page = 'app'
                st.rerun()
                
        # Columna Pro
        with col_pro:
            st.error("### 🚀 Zynte PRO (19.99€)\n* **IA Nutricionista Avanzada**\n* **Exportar PDF**\n* Soporte Prioritario")
            st.link_button("💳 Pagar Ahora (Stripe)", "https://stripe.com/es") 
            
            st.write("---")
            # TRUCO DE DESARROLLADOR: Botón para simular que pagaste
            if st.button("🛠️ Simular Pago Exitoso (Solo tú lo ves)"):
                # 1. Cambiamos el estado en la sesión
                st.session_state.datos_usuario['status'] = 'pro'
                # 2. (Opcional) Aquí deberíamos actualizar Google Sheets a 'pro' también
                st.session_state.page = 'app'
                st.rerun()

    # =========================================================
    # ESCENA 3: LA APP PRINCIPAL (Gimnasio)
    # =========================================================
    elif st.session_state.page == "app":
        # Ejecutamos toda la app que programaste antes
        app_principal()
    elif st.session_state.page == "admin":
        # Solo dibujamos el panel si estamos en modo admin
        admin_panel()
        
        if st.button("🔙 Salir al Login"):
            st.session_state.page = "login"
            st.rerun()
if __name__ == "__main__":
    main()


























































































































































































































