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

# --- 2. GESTIÓN DE BASE DE DATOS, SEGURIDAD Y PAGOS ---
def init_db():
    conn = sqlite3.connect('zynte_users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY, password TEXT, fecha_registro TEXT, plan TEXT,
            peso REAL, altura INTEGER, edad INTEGER, objetivo TEXT, nivel TEXT
        )
    ''')
    c.execute('''CREATE TABLE IF NOT EXISTS historial (email TEXT, fecha DATE, peso REAL)''')
    conn.commit()
    conn.close()
    migrar_db()

def migrar_db():
    conn = sqlite3.connect('zynte_users.db')
    c = conn.cursor()
    columnas = [('peso', 'REAL'), ('altura', 'INTEGER'), ('edad', 'INTEGER'), ('objetivo', 'TEXT'), ('nivel', 'TEXT')]
    for col, tipo in columnas:
        try: c.execute(f'ALTER TABLE users ADD COLUMN {col} {tipo}')
        except: pass
    conn.commit()
    conn.close()

def validar_email_estricto(email):
    email = email.strip().lower()
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(patron, email): return False, "Formato inválido."
    dominios = ["gmail.com", "yahoo.com", "yahoo.es", "hotmail.com", "outlook.com", "icloud.com", "protonmail.com"]
    try:
        dom = email.split('@')[-1]
        if dom not in dominios: return False, "Dominio no permitido."
    except: return False, "Error dominio."
    return True, "OK"

def verificar_login(email, password):
    try:
        conn = sqlite3.connect('zynte_users.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password))
        res = c.fetchone() is not None
        conn.close()
        return res
    except: return False

def registrar_usuario_sql(email, password):
    try:
        conn = sqlite3.connect('zynte_users.db')
        c = conn.cursor()
        fecha = str(datetime.date.today())
        c.execute('INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', 
                  (email, password, fecha, "Free", 70.0, 175, 25, "Hipertrofia", "Intermedio"))
        conn.commit(); conn.close()
        return True
    except: return False

def registrar_peso_historico(email, peso):
    try:
        conn = sqlite3.connect('zynte_users.db')
        c = conn.cursor()
        fecha = str(datetime.date.today())
        c.execute('DELETE FROM historial WHERE email = ? AND fecha = ?', (email, fecha))
        c.execute('INSERT INTO historial VALUES (?, ?, ?)', (email, fecha, peso))
        conn.commit(); conn.close()
        return True
    except: return False

def obtener_historial_df(email):
    try:
        conn = sqlite3.connect('zynte_users.db')
        df = pd.read_sql_query("SELECT fecha, peso FROM historial WHERE email = ? ORDER BY fecha ASC", conn, params=(email,))
        conn.close()
        return df
    except: return None

def cargar_perfil(email):
    try:
        conn = sqlite3.connect('zynte_users.db')
        c = conn.cursor()
        c.execute('SELECT peso, altura, edad, objetivo, nivel FROM users WHERE email = ?', (email,))
        data = c.fetchone()
        conn.close()
        return {"peso": data[0] or 70.0, "altura": data[1] or 175, "edad": data[2] or 25, "objetivo": data[3] or "Hipertrofia", "nivel": data[4] or "Intermedio"}
    except: return {"peso": 70.0, "altura": 175, "edad": 25, "objetivo": "Hipertrofia", "nivel": "Intermedio"}

def guardar_perfil_db(email, peso, altura, edad, objetivo, nivel):
    try:
        conn = sqlite3.connect('zynte_users.db')
        c = conn.cursor()
        c.execute('UPDATE users SET peso=?, altura=?, edad=?, objetivo=?, nivel=? WHERE email=?', (peso, altura, edad, objetivo, nivel, email))
        conn.commit(); conn.close()
        registrar_peso_historico(email, peso) 
        return True
    except: return False

def activar_plan_pro(email):
    try:
        conn = sqlite3.connect('zynte_users.db')
        c = conn.cursor()
        c.execute("UPDATE users SET plan = 'Pro' WHERE email = ?", (email,))
        conn.commit(); conn.close()
        return True
    except: return False

def revocar_plan_pro(email):
    try:
        conn = sqlite3.connect('zynte_users.db')
        c = conn.cursor()
        c.execute("UPDATE users SET plan = 'Free' WHERE email = ?", (email,))
        conn.commit(); conn.close()
        return True
    except: return False

def eliminar_usuario_total(email):
    try:
        conn = sqlite3.connect('zynte_users.db')
        c = conn.cursor()
        c.execute("DELETE FROM users WHERE email = ?", (email,))
        c.execute("DELETE FROM historial WHERE email = ?", (email,))
        conn.commit(); conn.close()
        return True
    except: return False

def comprobar_plan(email):
    try:
        conn = sqlite3.connect('zynte_users.db')
        c = conn.cursor()
        c.execute("SELECT plan FROM users WHERE email = ?", (email,))
        res = c.fetchone()
        conn.close()
        return res and res[0] == 'Pro'
    except: return False

init_db()

# --- 3. ESTILOS CSS ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stAppViewContainer"] {
        background-image: linear-gradient(rgba(0, 0, 0, 0.85), rgba(0, 0, 0, 0.95)), 
                          url("https://images.unsplash.com/photo-1534438327276-14e5300c3a48?q=80&w=2070&auto=format&fit=crop");
        background-size: cover; background-position: center; background-attachment: fixed;
    }
    .hero-title { font-size: 3.5rem; font-weight: 800; background: linear-gradient(to right, #ffffff, #33ffaa); -webkit-background-clip: text; -webkit-fill-color: transparent; text-align: center; }
    .price-card { background-color: rgba(20, 20, 20, 0.6); backdrop-filter: blur(15px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 15px; padding: 25px; transition: 0.3s; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. CLASE PDF ---
class PDF(FPDF):
    def header(self):
        try: self.image('logo.png', 10, 8, 33)
        except: pass
        self.set_font('Arial', 'B', 15); self.cell(80); self.cell(30, 10, 'ZYNTE | INFORME', 0, 0, 'C'); self.ln(20)

def crear_pdf(historial, nombre, peso, objetivo):
    pdf = PDF(); pdf.add_page(); pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, txt=f"CLIENTE: {nombre} | PESO: {peso}kg | META: {objetivo}", ln=1)
    for mensaje in historial:
        if mensaje["role"] == "model":
            pdf.multi_cell(0, 7, txt=mensaje["content"].replace("**", "").replace("*", "-")); pdf.ln(5)
    return pdf.output(dest="S").encode("latin-1", "replace")

# --- 5. VISTAS ---
def mostrar_landing():
    st.markdown('<p class="hero-title">TU ENTRENADOR DE ÉLITE</p>', unsafe_allow_html=True)
    if st.button("🚀 COMENZAR AHORA", type="primary"):
        st.session_state.page = 'login'; st.rerun()

def mostrar_login():
    email = st.text_input("Correo").lower()
    password = st.text_input("Contraseña", type="password")
    if st.button("ENTRAR"):
        if verificar_login(email, password):
            st.session_state.logged_in = True; st.session_state.user_email = email
            st.session_state.is_premium = comprobar_plan(email)
            st.session_state.page = 'app' if st.session_state.is_premium else 'pricing'; st.rerun()

def mostrar_pricing():
    st.title("Selecciona tu Plan")
    if st.button("Continuar Gratis"): st.session_state.page = 'app'; st.rerun()

def app_principal():
    EMAIL_JEFE = "pablonavarrorui@gmail.com"
    email_actual = st.session_state.get('user_email', 'invitado')
    datos_usuario = cargar_perfil(email_actual)
    
    try: api_key_zynte = st.secrets["GOOGLE_API_KEY"]
    except: api_key_zynte = "TU_CLAVE_AQUI"

    def calcular_macros(peso, altura, edad, genero, objetivo, nivel):
        tmb = (88.36 + (13.4 * peso) + (4.8 * altura) - (5.7 * edad)) if genero == "Hombre" else (447.6 + (9.2 * peso) + (3.1 * altura) - (4.3 * edad))
        tdee = tmb * {"Principiante": 1.2, "Intermedio": 1.55, "Avanzado": 1.725}.get(nivel, 1.2)
        return int(tdee), int(peso*2), int(peso*2), int(peso*1)

    with st.sidebar:
        st.header("ZYNTE PRO" if st.session_state.is_premium else "ZYNTE FREE")
        nombre_atleta = st.text_input("Alias", "Atleta")
        peso_v = st.slider("Peso (kg)", 40.0, 150.0, float(datos_usuario['peso']))
        altura_v = st.slider("Altura (cm)", 120, 220, int(datos_usuario['altura']))
        objetivo_v = st.selectbox("Objetivo", ["Hipertrofia", "Pérdida de Grasa", "Fuerza"], index=0)
        nivel_v = st.select_slider("Nivel", options=["Principiante", "Intermedio", "Avanzado"])
        
        if st.button("💾 Guardar"):
            guardar_perfil_db(email_actual, peso_v, altura_v, 25, objetivo_v, nivel_v); st.toast("Guardado")
        
        if email_actual == EMAIL_JEFE:
            with st.expander("🔐 ADMIN GOD MODE"):
                acc = st.radio("Acción:", ["Dar VIP", "Quitar VIP", "Borrar"])
                tgt = st.text_input("Email objetivo:")
                if st.button("EJECUTAR"):
                    if acc == "Dar VIP": activar_plan_pro(tgt)
                    elif acc == "Quitar VIP": revocar_plan_pro(tgt)
                    else: eliminar_usuario_total(tgt)
                    st.rerun()

        if "history" in st.session_state and len(st.session_state.history) > 1 and st.session_state.is_premium:
            pdf_data = crear_pdf(st.session_state.history, nombre_atleta, peso_v, objetivo_v)
            st.download_button("📥 Descargar Rutina PDF", pdf_data, "Rutina.pdf")
        
        st.button("Cerrar Sesión", on_click=lambda: setattr(st.session_state, 'logged_in', False))

    tab_train, tab_nutri, tab_prog = st.tabs(["🏋️ ENTRENAMIENTO", "🥗 NUTRICIÓN", "📈 PROGRESO"])

    with tab_train:
        st.caption("⚡ Generadores Rápidos")
        c1, c2, c3 = st.columns(3)
        prompt_rapido = None
        if c1.button("🔥 HIIT 20'"): prompt_rapido = "Rutina HIIT 20 min intensa"
        if c2.button("🧘 Estirar"): prompt_rapido = "Tabla estiramientos espalda"
        if c3.button("💪 Flexiones"): prompt_rapido = "Reto flexiones nivel intermedio"

        # --- SECCIÓN DE CHAT CORREGIDA ---
        st.write("---"); st.subheader("💬 Chat con Zynte AI")
        if "history" not in st.session_state: st.session_state.history = []

        chat_in = st.chat_input("¿En qué puedo ayudarte?")
        mensaje_final = prompt_rapido or chat_in

        if mensaje_final:
            st.session_state.history.append({"role": "user", "content": mensaje_final})
            with st.chat_message("assistant"):
                with st.spinner("Zynte pensando..."):
                    try:
                        url_v1 = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key_zynte}"
                        payload = {"contents": [{"parts": [{"text": mensaje_final}]}]}
                        res = requests.post(url_v1, json=payload, timeout=30)
                        if res.status_code == 200:
                            txt = res.json()['candidates'][0]['content']['parts'][0]['text']
                            st.session_state.history.append({"role": "model", "content": txt})
                            st.rerun()
                        else: st.error(f"Error 404/API: {res.status_code}")
                    except Exception as e: st.error(f"Fallo red: {e}")

        for msg in reversed(st.session_state.history):
            with st.chat_message("assistant" if msg["role"] == "model" else "user"):
                st.markdown(msg["content"])

    with tab_nutri:
        kcal, p, ch, g = calcular_macros(peso_v, altura_v, 25, "Hombre", objetivo_v, nivel_v)
        st.header("Plan Nutricional"); st.metric("Kcal", kcal)
        if st.button("🥑 GENERAR DIETA"):
            with st.spinner("Creando..."):
                try:
                    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key_zynte}"
                    payload = {"contents": [{"parts": [{"text": f"Dieta {kcal}kcal para {objetivo_v}"}]}]}
                    r = requests.post(url, json=payload)
                    if r.status_code == 200: st.markdown(r.json()['candidates'][0]['content']['parts'][0]['text'])
                except: st.error("Error")

    with tab_prog:
        df_p = obtener_historial_df(email_actual)
        if df_p is not None: st.area_chart(df_p.set_index('fecha'))

def main():
    if 'page' not in st.session_state: st.session_state.page = 'landing'
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False
    if st.session_state.page == 'landing': mostrar_landing()
    elif st.session_state.page == 'login': mostrar_login()
    elif st.session_state.page == 'pricing': mostrar_pricing()
    elif st.session_state.page == 'app': app_principal()

if __name__ == "__main__": main()


















































