import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, date
import json

# ============================================================
# SYNCFIT - aplicación local en Streamlit con almacenamiento CSV
# ============================================================

st.set_page_config(
    page_title="SyncFit",
    page_icon="💙",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = Path(__file__).parent
CATALOG_FILE = BASE_DIR / "datos.csv"
PROFILE_FILE = BASE_DIR / "perfil.csv"
ROUTINES_FILE = BASE_DIR / "rutinas.csv"
WORKOUTS_FILE = BASE_DIR / "entrenamientos.csv"
DONE_FILE = BASE_DIR / "ejercicios_realizados.csv"
REMINDERS_FILE = BASE_DIR / "recordatorios.csv"

# ------------------------- Diseño ----------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: #F4F6FA; color: #101820; }
[data-testid="stHeader"] { background: rgba(244,246,250,0.92); }
[data-testid="stSidebar"] { background: #101820; }
[data-testid="stSidebar"] * { color: #FFFFFF !important; }
[data-testid="stSidebar"] .stRadio label { color: #FFFFFF !important; }
h1, h2, h3 { color: #101820; letter-spacing: -0.5px; }
.hero {
    background: linear-gradient(120deg,#172B4D,#3978F6);
    padding: 30px 32px; border-radius: 22px; color: white; margin-bottom: 20px;
}
.hero h1, .hero p { color: white !important; }
.hero p { opacity: .9; margin-bottom: 0; }
.metric-card {
    background: white; border: 1px solid #E8ECF3; border-radius: 18px;
    padding: 18px 20px; min-height: 112px; box-shadow: 0 5px 18px rgba(16,24,32,.04);
}
.metric-label { color:#737B8C; font-size:13px; font-weight:600; }
.metric-value { color:#172B4D; font-size:27px; font-weight:800; margin-top:5px; }
.panel {
    background:white; border:1px solid #E8ECF3; border-radius:18px;
    padding:20px; margin-bottom:14px;
}
.small-muted { color:#737B8C; font-size:13px; }
.tag {
    display:inline-block; background:#EAF8F4; color:#167D68; padding:5px 10px;
    border-radius:20px; font-size:12px; font-weight:700; margin:3px 4px 3px 0;
}
.stButton > button {
    border-radius: 12px; border:0; background:#3978F6; color:white;
    font-weight:700; padding: .58rem 1rem;
}
.stButton > button:hover { background:#245FD0; color:white; border:0; }
div[data-testid="stForm"] { background:white; padding:18px; border-radius:16px; border:1px solid #E8ECF3; }
hr { border-color:#E6EAF1; }
</style>
""", unsafe_allow_html=True)

# --------------------- Utilidades CSV ------------------------
def ensure_csv(path, columns):
    if not path.exists():
        pd.DataFrame(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")

def read_csv(path, columns=None):
    if path.exists():
        try:
            data = pd.read_csv(path, encoding="utf-8-sig")
            if columns:
                for col in columns:
                    if col not in data.columns:
                        data[col] = ""
                return data[columns]
            return data
        except Exception:
            pass
    return pd.DataFrame(columns=columns or [])

def save_csv(data, path):
    data.to_csv(path, index=False, encoding="utf-8-sig")

ensure_csv(PROFILE_FILE, ["nombre","edad","peso","altura","nivel","objetivo","minutos","dias","lugar","equipo","preferencias"])
ensure_csv(ROUTINES_FILE, ["id","nombre","objetivo","nivel","duracion","lugar","equipo","ejercicios"])
ensure_csv(WORKOUTS_FILE, ["fecha","rutina","objetivo","duracion_min","completado"])
ensure_csv(DONE_FILE, ["fecha","rutina","ejercicio","completado"])
ensure_csv(REMINDERS_FILE, ["dia","hora","activo"])

# ------------------- Cargar catálogo -------------------------
if not CATALOG_FILE.exists():
    st.error("No se encontró datos.csv. Asegúrate de generar o colocar este archivo en la misma carpeta que app.py.")
    st.stop()

catalog = read_csv(CATALOG_FILE)
required_cols = ["Objetivo", "Ejercicios", "Ejecucion"]
if not all(c in catalog.columns for c in required_cols):
    st.error("El archivo datos.csv debe tener las columnas: Objetivo, Ejercicios y Ejecucion.")
    st.stop()
catalog = catalog.fillna("")
catalog["Objetivo"] = catalog["Objetivo"].astype(str).str.strip()
catalog["Ejercicios"] = catalog["Ejercicios"].astype(str).str.strip()
catalog["Ejecucion"] = catalog["Ejecucion"].astype(str).str.strip()

profile_df = read_csv(PROFILE_FILE)
profile = profile_df.iloc[0].to_dict() if not profile_df.empty else {}
workouts = read_csv(WORKOUTS_FILE)
done = read_csv(DONE_FILE)
reminders = read_csv(REMINDERS_FILE)

# ----------------------- Estado ------------------------------
if "page" not in st.session_state:
    st.session_state.page = "Inicio"
if "selected_exercise" not in st.session_state:
    st.session_state.selected_exercise = None
if "selected_routine" not in st.session_state:
    st.session_state.selected_routine = None
if "workout_started" not in st.session_state:
    st.session_state.workout_started = False

# ---------------------- Funciones ----------------------------
def metric(label, value, note=""):
    st.markdown(f"""<div class="metric-card">
<div class="metric-label">{label}</div>
<div class="metric-value">{value}</div>
<div class="small-muted">{note}</div>
</div>""", unsafe_allow_html=True)

def make_routine(objetivo, level="Principiante", minutes=25):
    exercises = catalog[catalog["Objetivo"].str.casefold() == str(objetivo).casefold()]
    if exercises.empty:
        exercises = catalog
    count = min(len(exercises), max(3, min(6, minutes // 5)))
    selected = exercises.head(count)
    return selected.to_dict("records")

def show_exercise(row):
    st.markdown(f"<div class='panel'><h3>{row['Ejercicios']}</h3><p>{row['Ejecucion']}</p></div>", unsafe_allow_html=True)

def save_profile(values):
    save_csv(pd.DataFrame([values]), PROFILE_FILE)

def get_goal():
    return profile.get("objetivo", "Mejorar salud") if profile else "Mejorar salud"

# ---------------------- Barra lateral -----------------------
with st.sidebar:
    st.markdown("# 💙 SyncFit")
    st.caption("Organiza tu actividad física")
    st.divider()
    pages = ["Inicio", "Mi perfil", "Mis rutinas", "Progreso", "Recordatorios"]
    selected_page = st.radio("MENÚ", pages, index=pages.index(st.session_state.page) if st.session_state.page in pages else 0)
    st.session_state.page = selected_page
    st.divider()
    st.markdown("**Explorar ejercicios**")
    goal_filter = st.selectbox("Filtrar por objetivo", ["Todos"] + sorted(catalog["Objetivo"].dropna().unique().tolist()))
    search_text = st.text_input("Buscar ejercicio", placeholder="Ej. sentadillas")
    level_filter = st.selectbox("Nivel", ["Todos", "Principiante", "Intermedio", "Avanzado"])
    st.caption("Los ejercicios se consultan desde datos.csv.")

filtered_catalog = catalog.copy()
if goal_filter != "Todos":
    filtered_catalog = filtered_catalog[filtered_catalog["Objetivo"] == goal_filter]
if search_text:
    filtered_catalog = filtered_catalog[filtered_catalog["Ejercicios"].str.contains(search_text, case=False, na=False)]

# -------------------------- Inicio ---------------------------
if st.session_state.page == "Inicio":
    st.markdown("""<div class="hero">
<h1>Entrena a tu ritmo con SyncFit</h1>
<p>Organiza tus rutinas, consulta ejercicios y registra tu actividad.</p>
</div>""", unsafe_allow_html=True)

    if not profile:
        st.info("Para comenzar, completa tu perfil. Así SyncFit podrá mostrarte ejercicios relacionados con tu objetivo.")
        if st.button("Configurar mi perfil", use_container_width=True):
            st.session_state.page = "Mi perfil"
            st.rerun()
    else:
        st.subheader(f"¡Hola, {profile.get('nombre','')}!")
        st.write("Este es tu resumen de actividad.")
        c1,c2,c3 = st.columns(3)
        with c1: metric("Entrenamientos registrados", len(workouts), "Sesiones guardadas")
        with c2: metric("Ejercicios disponibles", len(catalog), "En tu catálogo")
        with c3: metric("Objetivo", profile.get("objetivo","—"), "Objetivo seleccionado")
        st.markdown("### Ejercicios recomendados")
        recommended = catalog[catalog["Objetivo"].str.casefold() == str(get_goal()).casefold()].head(3)
        if recommended.empty: recommended = catalog.head(3)
        cols = st.columns(3)
        for i, (_, row) in enumerate(recommended.iterrows()):
            with cols[i]:
                st.markdown(f"<div class='panel'><span class='tag'>{row['Objetivo']}</span><h3>{row['Ejercicios']}</h3><p>{row['Ejecucion']}</p></div>", unsafe_allow_html=True)
        if st.button("Ver mis rutinas"):
            st.session_state.page = "Mis rutinas"
            st.rerun()

# ------------------------- Mi perfil -------------------------
elif st.session_state.page == "Mi perfil":
    st.markdown("## Mi perfil")
    st.write("Completa tus datos para organizar las recomendaciones. Los datos se guardan localmente en archivos CSV.")
    with st.form("profile_form"):
        a,b = st.columns(2)
        with a:
            name = st.text_input("Nombre", value=str(profile.get("nombre","")))
            age = st.number_input("Edad", min_value=10, max_value=100, value=int(float(profile.get("edad",15) or 15)))
            weight = st.number_input("Peso (kg) — opcional", min_value=0.0, max_value=300.0, value=float(profile.get("peso",0) or 0), step=0.5)
            height = st.number_input("Altura (cm) — opcional", min_value=0.0, max_value=250.0, value=float(profile.get("altura",0) or 0), step=0.5)
            level = st.selectbox("Experiencia", ["Principiante","Intermedio","Avanzado"], index=["Principiante","Intermedio","Avanzado"].index(profile.get("nivel","Principiante")) if profile.get("nivel","Principiante") in ["Principiante","Intermedio","Avanzado"] else 0)
        with b:
            objectives = catalog["Objetivo"].dropna().unique().tolist()
            old_goal = profile.get("objetivo", objectives[0] if objectives else "")
            goal = st.selectbox("Objetivo", objectives, index=objectives.index(old_goal) if old_goal in objectives else 0)
            minutes = st.selectbox("Tiempo disponible", [10,15,20,25,30,40,45,60], index=[10,15,20,25,30,40,45,60].index(int(float(profile.get("minutos",25) or 25))) if int(float(profile.get("minutos",25) or 25)) in [10,15,20,25,30,40,45,60] else 3)
            days = st.selectbox("Días por semana", [1,2,3,4,5,6,7], index=max(0,min(6,int(float(profile.get("dias",3) or 3))-1)))
            place = st.selectbox("Lugar para entrenar", ["Casa","Gimnasio","Exterior","Otro"], index=["Casa","Gimnasio","Exterior","Otro"].index(profile.get("lugar","Casa")) if profile.get("lugar","Casa") in ["Casa","Gimnasio","Exterior","Otro"] else 0)
            equipment = st.text_input("Equipo disponible", value=str(profile.get("equipo","Ninguno")), placeholder="Ej. ninguno, banda elástica, mancuernas")
            preferences = st.text_input("Preferencias", value=str(profile.get("preferencias","")), placeholder="Ej. caminata, ejercicios tranquilos")
        submitted = st.form_submit_button("Guardar perfil", use_container_width=True)
    if submitted:
        if not name.strip():
            st.error("Escribe tu nombre para guardar el perfil.")
        else:
            save_profile({"nombre":name.strip(),"edad":age,"peso":weight,"altura":height,"nivel":level,"objetivo":goal,"minutos":minutes,"dias":days,"lugar":place,"equipo":equipment,"preferencias":preferences})
            st.success("Perfil guardado.")
            st.rerun()
    st.markdown("""<div class="panel"><b>Nota de seguridad</b><p class="small-muted">SyncFit ofrece información general y no sustituye la orientación de un profesional. Elige actividades adecuadas a tu experiencia, realiza los movimientos con control y detente si sientes dolor, mareo o malestar. Si eres menor de edad, consulta tus planes de actividad con un adulto responsable.</p></div>""", unsafe_allow_html=True)

# ------------------------ Mis rutinas ------------------------
elif st.session_state.page == "Mis rutinas":
    st.markdown("## Mis rutinas")
    if not profile:
        st.warning("Primero completa tu perfil para personalizar las rutinas.")
        if st.button("Ir a mi perfil"):
            st.session_state.page = "Mi perfil"; st.rerun()
    else:
        st.write(f"Objetivo seleccionado: **{profile.get('objetivo','')}** · Tiempo disponible: **{profile.get('minutos',25)} minutos**")
        options = ["Mi objetivo"] + sorted(catalog["Objetivo"].dropna().unique().tolist())
        chosen_goal = st.selectbox("Selecciona el objetivo de la rutina", options)
        objective = profile.get("objetivo","") if chosen_goal == "Mi objetivo" else chosen_goal
        rows = make_routine(objective, profile.get("nivel","Principiante"), int(profile.get("minutos",25)))
        st.markdown(f"<div class='panel'><span class='tag'>{objective}</span><h3>Rutina sugerida</h3><p class='small-muted'>Selección de ejercicios de tu catálogo. Ajusta la intensidad a tu capacidad y descansa cuando lo necesites.</p></div>", unsafe_allow_html=True)
        for idx, row in enumerate(rows, start=1):
            with st.expander(f"{idx}. {row['Ejercicios']}"):
                st.write(row["Ejecucion"])
                st.caption("Realiza el movimiento de forma controlada y descansa si lo necesitas.")
        if st.button("Registrar esta rutina como entrenamiento", use_container_width=True):
            new_row = {"fecha":datetime.now().strftime("%Y-%m-%d %H:%M"),"rutina":f"Rutina - {objective}","objetivo":objective,"duracion_min":profile.get("minutos",25),"completado":"Sí"}
            workouts = pd.concat([workouts, pd.DataFrame([new_row])], ignore_index=True)
            save_csv(workouts, WORKOUTS_FILE)
            for row in rows:
                done = pd.concat([done, pd.DataFrame([{"fecha":new_row["fecha"],"rutina":new_row["rutina"],"ejercicio":row["Ejercicios"],"completado":"Sí"}])], ignore_index=True)
            save_csv(done, DONE_FILE)
            st.success("Entrenamiento registrado en tu historial.")

        st.markdown("### Catálogo de ejercicios")
        st.dataframe(filtered_catalog[["Objetivo","Ejercicios","Ejecucion"]], use_container_width=True, hide_index=True)

# -------------------------- Progreso -------------------------
elif st.session_state.page == "Progreso":
    st.markdown("## Mi progreso")
    if workouts.empty:
        st.info("Todavía no tienes entrenamientos registrados. Cuando registres una rutina, aparecerá aquí.")
    else:
        c1,c2 = st.columns(2)
        with c1: metric("Entrenamientos", len(workouts), "Total registrado")
        with c2: metric("Minutos registrados", pd.to_numeric(workouts["duracion_min"], errors="coerce").fillna(0).sum(), "Tiempo acumulado")
        st.markdown("### Historial")
        st.dataframe(workouts.sort_values("fecha", ascending=False), use_container_width=True, hide_index=True)
        if not done.empty:
            st.markdown("### Ejercicios realizados")
            st.dataframe(done.sort_values("fecha", ascending=False), use_container_width=True, hide_index=True)
        chart_data = workouts.copy()
        chart_data["fecha"] = pd.to_datetime(chart_data["fecha"], errors="coerce")
        chart_data = chart_data.dropna(subset=["fecha"]).set_index("fecha")
        if not chart_data.empty:
            st.markdown("### Entrenamientos por fecha")
            daily = chart_data.resample("D").size().rename("Entrenamientos")
            st.line_chart(daily)

# ----------------------- Recordatorios ----------------------
elif st.session_state.page == "Recordatorios":
    st.markdown("## Recordatorios")
    st.write("Guarda los días y horarios en los que te gustaría recibir un recordatorio dentro de la app.")
    with st.form("reminder_form"):
        day = st.selectbox("Día", ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"])
        hour = st.time_input("Hora")
        active = st.checkbox("Recordatorio activo", value=True)
        add = st.form_submit_button("Guardar recordatorio")
    if add:
        reminders = pd.concat([reminders, pd.DataFrame([{"dia":day,"hora":hour.strftime("%H:%M"),"activo":"Sí" if active else "No"}])], ignore_index=True)
        save_csv(reminders, REMINDERS_FILE)
        st.success("Recordatorio guardado.")
        st.rerun()
    if reminders.empty:
        st.info("Aún no has creado recordatorios.")
    else:
        st.dataframe(reminders, use_container_width=True, hide_index=True)
        st.caption("Los recordatorios quedan guardados en el archivo CSV; esta versión no envía notificaciones fuera de la aplicación.")

st.divider()
st.caption("SyncFit · Aplicación local de organización de actividad física · Los datos se guardan en archivos CSV.")
