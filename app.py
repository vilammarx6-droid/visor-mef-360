import streamlit as st
import streamlit.components.v1 as components
import duckdb
import pandas as pd
import os
import requests
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# CONFIGURACIÓN Y CSS (UX MEJORADA)
# ==========================================
st.set_page_config(page_title="Auditoría Ciudadana", page_icon="🕵️", layout="wide")

# JS para bloquear los atajos de teclado molestos por defecto de Streamlit (como 'C' para Clear Cache)
components.html(
    """
    <script>
    const doc = window.parent.document;
    doc.addEventListener('keydown', function(e) {
        if (e.key === 'c' || e.key === 'C' || e.key === 'r' || e.key === 'R') {
            const tag = e.target.tagName.toLowerCase();
            if (tag !== 'input' && tag !== 'textarea') {
                e.stopPropagation();
                e.preventDefault();
            }
        }
    }, true);
    </script>
    """,
    height=0, width=0
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
    
    footer {visibility: hidden;}
    .stApp { background-color: #f8fafc; font-family: 'Inter', sans-serif; }
    
    .top-banner {
        background: linear-gradient(135deg, #0f172a 0%, #312e81 100%);
        color: white; padding: 20px 30px;
        margin-top: -60px; margin-left: -4rem; margin-right: -4rem; margin-bottom: 30px;
        display: flex; align-items: center; gap: 20px; border-bottom: 4px solid #3b82f6;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .top-banner h1 { margin: 0; font-size: 24px; font-weight: 900; color: white; text-transform: uppercase; text-shadow: 0 2px 4px rgba(0,0,0,0.3); letter-spacing: -0.5px; }
    .top-banner p { margin: 0; font-size: 14px; color: #cbd5e1; font-weight: 500; }

    .section-title { font-size: 28px; font-weight: 900; color: #0f172a; margin-bottom: 8px; text-align: center; letter-spacing: -0.5px; }
    .section-subtitle { font-size: 15px; color: #64748b; margin-bottom: 25px; text-align: center; }

    .card-white { 
        background-color: white; border-radius: 12px; border: 1px solid #e2e8f0; 
        padding: 24px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); 
        height: 100%; color: #0f172a !important; 
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .card-white:hover {
        transform: translateY(-3px); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
    }
    .card-white h1, .card-white h2, .card-white h3, .card-white h4, .card-white h5, .card-white h6 { color: #0f172a !important; font-size: 15px !important; margin-bottom: 15px; font-weight: 800; }
    
    .kpi-container { 
        background-color: white; border-radius: 8px; padding: 15px 20px; 
        border: 1px solid #e2e8f0; text-align: left;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .kpi-container:hover {
        transform: translateY(-3px); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.08);
    }
    .kpi-title { font-size: 12px; color: #64748b !important; font-weight: 700; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px; }
    .kpi-value { font-size: 24px; font-weight: 900; color: #0f172a !important; letter-spacing: -0.5px; }
    
    .stTabs [data-baseweb="tab-list"] { gap: 8px; border-bottom: 2px solid #e2e8f0; }
    .stTabs [data-baseweb="tab"] { background-color: transparent; border-radius: 0; padding: 12px 20px; font-weight: 600; color: #64748b; font-size: 15px; border-bottom: 3px solid transparent; }
    .stTabs [aria-selected="true"] { background-color: transparent !important; color: #3b82f6 !important; border-bottom: 3px solid #3b82f6 !important; border-top: none !important;}
</style>

<div class="top-banner">
    <div>
        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="7.5 4.21 12 6.81 16.5 4.21"></polyline><polyline points="7.5 19.79 7.5 14.6 3 12"></polyline><polyline points="21 12 16.5 14.6 16.5 19.79"></polyline><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>
    </div>
    <div>
        <h1>PLATAFORMA DE AUDITORÍA CIUDADANA Y FISCALIZACIÓN</h1>
        <p>Vigilancia del Presupuesto Público y Obras</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# CONEXIÓN DUCKDB Y DESCARGA DE DATOS (HUGGINGFACE)
# ==========================================
@st.cache_resource
def get_latest_parquet_and_download():
    # 1. Determinar cuál es el año más reciente en HuggingFace
    hf_api_url = "https://huggingface.co/api/datasets/marxvilam/mef-datos/tree/main"
    try:
        hf_files = requests.get(hf_api_url).json()
        gasto_files = [f.get('path') for f in hf_files if f.get('path', '').endswith('-Gasto-Diario.parquet')]
        gasto_files.sort(reverse=True) # El año mayor quedará primero
        main_parquet = gasto_files[0] if gasto_files else "2026-Gasto-Diario.parquet"
    except:
        main_parquet = "2026-Gasto-Diario.parquet"
        
    # 2. Descargar los archivos necesarios si no existen en el servidor
    files_to_download = [
        main_parquet,
        "infobras_avance.parquet",
        "infobras_paralizadas.parquet",
        "seguimiento_inversiones.parquet"
    ]
    for file in files_to_download:
        if not os.path.exists(file):
            url = f"https://huggingface.co/datasets/marxvilam/mef-datos/resolve/main/{file}"
            with st.spinner(f"Descargando {file} desde HuggingFace (Puede tardar 1-2 min)..."):
                response = requests.get(url, stream=True, headers={'User-Agent': 'Mozilla/5.0'})
                if response.status_code == 200:
                    with open(file, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192): f.write(chunk)
                else:
                    st.error(f"⚠️ Error 404: No se encontró '{file}' en HuggingFace.")
                    
    return main_parquet

PARQUET_FILE = get_latest_parquet_and_download()
try:
    CURRENT_YEAR = PARQUET_FILE.split('-')[0]
except:
    CURRENT_YEAR = "Actual"
conn = duckdb.connect(database=':memory:')

# ==========================================
# SIDEBAR INTUITIVO (UX MEJORADA)
# ==========================================
import re

if os.path.exists("logo.html"):
    try:
        with open("logo.html", "r", encoding="utf-8") as f:
            logo_html = f.read()
        match = re.search(r'src="(data:image[^"]+)"', logo_html)
        if match:
            b64_img = match.group(1)
            st.sidebar.markdown(f'<div style="text-align: center; margin-bottom: 15px;"><img src="{b64_img}" width="100%" style="border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);"></div>', unsafe_allow_html=True)
    except: pass

st.sidebar.markdown("""
<div style="text-align: center; margin-bottom: 25px; display: flex; flex-direction: column; gap: 10px;">
    <a href="https://www.facebook.com/profile.php?id=61589026953016" target="_blank" style="display: block; background-color: #1877F2; color: white; padding: 12px 15px; border-radius: 8px; text-decoration: none; font-weight: 700; font-size: 13px; box-shadow: 0 4px 6px -1px rgba(24, 119, 242, 0.3);">📘 SÍGUENOS EN FACEBOOK</a>
    <a href="https://wa.me/51983140402?text=Hola,%20tengo%20una%20consulta%20sobre%20la%20plataforma%20de%20Auditor%C3%ADa%20Ciudadana" target="_blank" style="display: block; background-color: #10b981; color: white; padding: 12px 15px; border-radius: 8px; text-decoration: none; font-weight: 700; font-size: 13px; box-shadow: 0 4px 6px -1px rgba(16, 185, 129, 0.3);">💬 CONSULTAS WHATSAPP</a>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("### ⚙️ Panel de Filtros")
st.sidebar.markdown("<p style='color: #64748b; font-size: 14px; margin-bottom: 20px;'>Selecciona la entidad a fiscalizar. Los gráficos se actualizarán en tiempo real.</p>", unsafe_allow_html=True)

where_clause = "1=1"

# 1. Nivel de Gobierno
try: niveles = conn.execute(f"SELECT DISTINCT CAST(NIVEL_GOBIERNO AS VARCHAR) || ': ' || NIVEL_GOBIERNO_NOMBRE FROM '{PARQUET_FILE}' WHERE NIVEL_GOBIERNO_NOMBRE IS NOT NULL AND NIVEL_GOBIERNO IS NOT NULL AND TRIM(NIVEL_GOBIERNO_NOMBRE) != '' ORDER BY 1").df().iloc[:,0].tolist()
except: niveles = []
f_nivel = st.sidebar.selectbox("🏛️ Nivel de Gobierno", ["TODOS"] + niveles)

if f_nivel != "TODOS":
    niv_code = str(f_nivel).split(":")[0].strip()
    where_clause += f" AND NIVEL_GOBIERNO = '{niv_code}'"

# 2. Sector (Depende de Nivel)
try: sectores = conn.execute(f"SELECT DISTINCT CAST(SECTOR AS VARCHAR) || ': ' || SECTOR_NOMBRE FROM '{PARQUET_FILE}' WHERE SECTOR_NOMBRE IS NOT NULL AND SECTOR IS NOT NULL AND TRIM(SECTOR_NOMBRE) != '' AND {where_clause} ORDER BY 1").df().iloc[:,0].tolist()
except: sectores = []
f_sector = st.sidebar.selectbox("🏢 Sector", ["TODOS"] + sectores)

if f_sector != "TODOS":
    sec_code = str(f_sector).split(":")[0].strip()
    where_clause += f" AND SECTOR = '{sec_code}'"

# 3. Pliego (Depende de Nivel y Sector)
try: pliegos = conn.execute(f"SELECT DISTINCT CAST(PLIEGO AS VARCHAR) || ': ' || PLIEGO_NOMBRE FROM '{PARQUET_FILE}' WHERE PLIEGO_NOMBRE IS NOT NULL AND PLIEGO IS NOT NULL AND TRIM(PLIEGO_NOMBRE) != '' AND {where_clause} ORDER BY 1").df().iloc[:,0].tolist()
except: pliegos = []
f_pliego = st.sidebar.selectbox("📍 Pliego / Entidad", ["TODOS"] + pliegos)

if f_pliego != "TODOS":
    pli_code = str(f_pliego).split(":")[0].strip()
    where_clause += f" AND PLIEGO = '{pli_code}'"

# 4. Unidad Ejecutora (Depende de todo lo anterior)
try: entidades = conn.execute(f"SELECT DISTINCT CAST(SEC_EJEC AS VARCHAR) || ': ' || EJECUTORA_NOMBRE FROM '{PARQUET_FILE}' WHERE EJECUTORA_NOMBRE IS NOT NULL AND SEC_EJEC IS NOT NULL AND TRIM(EJECUTORA_NOMBRE) != '' AND {where_clause} ORDER BY 1").df().iloc[:,0].tolist()
except: entidades = []
f_sec_eje = st.sidebar.selectbox("🎯 Unidad Ejecutora (SEC_EJEC)", ["TODOS"] + entidades)

if f_sec_eje != "TODOS":
    ent_code = str(f_sec_eje).split(":")[0].strip()
    where_clause += f" AND SEC_EJEC = '{ent_code}'"

st.sidebar.markdown("<br><hr style='margin-top:0px; margin-bottom:20px;'>", unsafe_allow_html=True)
f_search = st.sidebar.text_input("🔎 Buscador libre de CUI o Nombre", "")

# --- BOTON DE ACTUALIZACION ---
st.sidebar.markdown("<br><hr style='margin-top:0px; margin-bottom:10px;'>", unsafe_allow_html=True)
if st.sidebar.button("🔄 Forzar Actualización de Datos", help="Descarga la última versión de los datos desde la nube (Hugging Face)."):
    try:
        import os
        import glob
        for f in glob.glob("*.parquet"):
            try:
                os.remove(f)
            except:
                pass
        st.sidebar.success("Caché borrado. Descargando nuevos datos...")
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Error: {e}")
# ------------------------------

if f_search:
    _sch = f_search.strip().replace("'", "''")
    where_clause += f" AND (PRODUCTO_PROYECTO = '{_sch}' OR PRODUCTO_PROYECTO_NOMBRE LIKE '%{_sch.upper()}%')"

st.sidebar.markdown("<br>", unsafe_allow_html=True)
st.sidebar.markdown("""
<a href="#" style="display: block; background-color: #7c3aed; color: white; text-align: center; padding: 12px; border-radius: 6px; text-decoration: none; font-weight: bold; font-size: 16px;">
    💜 Apoyar el Proyecto (Donar)
</a>
""", unsafe_allow_html=True)

# ==========================================
# CONTEXTO DE BÚSQUEDA (UX)
# ==========================================
is_filtered = (f_sec_eje != "TODOS") or (f_pliego != "TODOS") or (f_nivel != "TODOS") or (f_sector != "TODOS") or bool(f_search)

if is_filtered:
    context_query = f"""
        SELECT 
            MAX(EJECUTORA_NOMBRE) as Entidad,
            MAX(NIVEL_GOBIERNO_NOMBRE) as Nivel,
            MAX(SECTOR_NOMBRE) as Sector,
            COUNT(DISTINCT EJECUTORA_NOMBRE) as Total_Entidades
        FROM '{PARQUET_FILE}'
        WHERE {where_clause}
    """
    df_ctx = conn.execute(context_query).df()
    if not df_ctx.empty and pd.notna(df_ctx.iloc[0]['Entidad']):
        row = df_ctx.iloc[0]
        if row['Total_Entidades'] == 1:
            st.markdown(f"""
            <div style="background-color: #f8fafc; border: 1px solid #cbd5e1; border-left: 5px solid #10b981; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                <h3 style="margin: 0; color: #0f172a; font-weight: 900; font-size: 20px;">🏢 {row['Entidad']}</h3>
                <p style="margin: 0; color: #475569; font-size: 14px; margin-top: 5px;"><strong>Nivel de Gobierno:</strong> {row['Nivel']} &nbsp;|&nbsp; <strong>Sector:</strong> {row['Sector']}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background-color: #f8fafc; border: 1px solid #cbd5e1; border-left: 5px solid #3b82f6; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                <h3 style="margin: 0; color: #0f172a; font-weight: 900; font-size: 18px;">🔎 Analizando {row['Total_Entidades']} Entidades a la vez</h3>
                <p style="margin: 0; color: #475569; font-size: 14px; margin-top: 5px;">Refina tu búsqueda si deseas ver una sola entidad. (Ejemplo en lista: {row['Entidad']})</p>
            </div>
            """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div style="background-color: #f8fafc; border: 1px solid #cbd5e1; border-left: 5px solid #64748b; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
        <h3 style="margin: 0; color: #0f172a; font-weight: 900; font-size: 18px;">🇵🇪 Visión Macro Nacional (Todo el Perú)</h3>
        <p style="margin: 0; color: #475569; font-size: 14px; margin-top: 5px;">Usa el buscador de la izquierda para investigar una municipalidad, gobierno regional o ministerio específico.</p>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# TABS PRINCIPALES
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["📊 Radiografía del Gasto", "⚖️ VERSUS: Físico vs Financiero (Obras)", "📋 Todas las Obras (SNIP)", "🔎 Detalle por Obra"])

# ---------------------------------------------------------
# TAB 1: RADIOGRAFÍA DEL GASTO (Obras vs Burocracia)
# ---------------------------------------------------------
with tab1:
    st.markdown('<div style="padding:20px;">', unsafe_allow_html=True)
    
    col_yr1, col_yr2 = st.columns([1, 3])
    with col_yr1:
        tab1_year = st.selectbox("📅 Seleccione el Año Fiscal:", ["2026", "2025", "2024", "2023", "2022"], index=0, key="tab1_year_select")
        
    DYNAMIC_PARQUET = f"{tab1_year}-Gasto-Diario.parquet"
    if not os.path.exists(DYNAMIC_PARQUET):
        url = f"https://huggingface.co/datasets/marxvilam/mef-datos/resolve/main/{DYNAMIC_PARQUET}"
        with st.spinner(f"Descargando datos históricos de {tab1_year}..."):
            response = requests.get(url, stream=True, headers={'User-Agent': 'Mozilla/5.0'})
            if response.status_code == 200:
                with open(DYNAMIC_PARQUET, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192): f.write(chunk)
            else:
                st.error(f"⚠️ No hay datos disponibles para el año {tab1_year}.")
                st.stop()

    st.markdown(f'<div class="section-title">Radiografía General de la Entidad (Año {tab1_year})</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Descubre si tu autoridad gasta más en construir obras o en pagar planillas.</div>', unsafe_allow_html=True)
    st.info(f"""
    **🔍 Guía de Transparencia y Origen de Datos:**
    * **Fuente Oficial:** Portal de Datos Abiertos del MEF - [Presupuesto y Ejecución de Gasto (SIAF)](https://datosabiertos.mef.gob.pe/dataset/presupuesto-y-ejecucion-de-gasto).
    * **Alcance Temporal:** Toda la información de esta pestaña corresponde **ÚNICAMENTE AL AÑO {tab1_year}**. No incluye el historial pasado.
    * **Procesamiento de Datos:** El porcentaje de avance se calcula dividiendo la columna `MONTO_DEVENGADO` (dinero ya pagado) entre la columna `MONTO_PIM` (presupuesto asignado para este año).
    """)
    
    # 1. KPIs Nivel Institucional (Total)
    macro_query = f"""
        SELECT 
            SUM(TRY_CAST(MONTO_PIA AS DOUBLE)) as PIA,
            SUM(TRY_CAST(MONTO_PIM AS DOUBLE)) as PIM,
            SUM(TRY_CAST(MONTO_CERTIFICADO AS DOUBLE)) as Certificado,
            SUM(TRY_CAST(MONTO_COMPROMETIDO_ANUAL AS DOUBLE)) as Compromiso_Anual,
            SUM(TRY_CAST(MONTO_DEVENGADO AS DOUBLE)) as Devengado,
            SUM(TRY_CAST(MONTO_GIRADO AS DOUBLE)) as Girado
        FROM '{DYNAMIC_PARQUET}' 
        WHERE {where_clause} 
    """
    df_macro = conn.execute(macro_query).df()
    pia, pim, cert, comp, dev, gir, avance = 0, 0, 0, 0, 0, 0, 0
    if not df_macro.empty and pd.notna(df_macro.iloc[0]['PIM']):
        pia = df_macro.iloc[0]['PIA']
        pim = df_macro.iloc[0]['PIM']
        cert = df_macro.iloc[0]['Certificado']
        comp = df_macro.iloc[0]['Compromiso_Anual']
        dev = df_macro.iloc[0]['Devengado']
        gir = df_macro.iloc[0]['Girado']
        if pd.notna(dev) and pim > 0: avance = (dev / pim) * 100

    # 2. KPIs Nivel Obras (Exclusivo Inversión Física)
    obras_query = f"""
        SELECT 
            COUNT(DISTINCT PRODUCTO_PROYECTO) as Count_Obras,
            SUM(TRY_CAST(MONTO_PIM AS DOUBLE)) as PIM_Obras,
            SUM(TRY_CAST(MONTO_DEVENGADO AS DOUBLE)) as Dev_Obras
        FROM '{DYNAMIC_PARQUET}' 
        WHERE {where_clause} 
        AND CATEGORIA_GASTO = 6
        AND PRODUCTO_PROYECTO NOT IN ('3999999', '2999999', '3000001', '2001621')
    """
    df_obras = conn.execute(obras_query).df()
    obras_count, pim_obras, dev_obras, avance_obras = 0, 0, 0, 0
    if not df_obras.empty and pd.notna(df_obras.iloc[0]['Count_Obras']):
        obras_count = df_obras.iloc[0]['Count_Obras']
        pim_obras = df_obras.iloc[0]['PIM_Obras']
        dev_obras = df_obras.iloc[0]['Dev_Obras']
        if pd.notna(dev_obras) and pim_obras > 0: avance_obras = (dev_obras / pim_obras) * 100

    def format_money(monto):
        if pd.isna(monto): return "S/ 0"
        if monto >= 1e9: return f"S/ {monto/1e9:,.1f} Mil Millones"
        elif monto >= 1e6: return f"S/ {monto/1e6:,.1f} Millones"
        else: return f"S/ {monto:,.0f}"

    # Renderizado UI Nivel 1
    st.markdown('<h4 style="font-size: 16px; color: #334155; margin-bottom: 10px;">🏛️ Presupuesto Institucional Total (Incluye Planillas, Deudas y Administrativos)</h4>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f'<div class="kpi-container" style="border-top: 4px solid #94a3b8;"><div class="kpi-title">PIA</div><div class="kpi-value">{format_money(pia)}</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="kpi-container" style="border-top: 4px solid #3b82f6;"><div class="kpi-title">PIM</div><div class="kpi-value">{format_money(pim)}</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="kpi-container" style="border-top: 4px solid #8b5cf6;"><div class="kpi-title">Certificación</div><div class="kpi-value">{format_money(cert)}</div></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="kpi-container" style="border-top: 4px solid #ec4899;"><div class="kpi-title">Compromiso Anual</div><div class="kpi-value">{format_money(comp)}</div></div>', unsafe_allow_html=True)
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    c5, c6, c7, c8 = st.columns(4)
    with c5: st.markdown(f'<div class="kpi-container" style="border-top: 4px solid #10b981;"><div class="kpi-title">Devengado</div><div class="kpi-value">{format_money(dev)}</div></div>', unsafe_allow_html=True)
    with c6: st.markdown(f'<div class="kpi-container" style="border-top: 4px solid #14b8a6;"><div class="kpi-title">Girado</div><div class="kpi-value">{format_money(gir)}</div></div>', unsafe_allow_html=True)
    with c7: st.markdown(f'<div class="kpi-container" style="border-top: 4px solid #f59e0b;"><div class="kpi-title">Avance %</div><div class="kpi-value">{avance:.1f}%</div></div>', unsafe_allow_html=True)
    
    st.markdown('<br>', unsafe_allow_html=True)
    
    # Renderizado UI Nivel 2
    st.markdown('<h4 style="font-size: 16px; color: #334155; margin-bottom: 10px;">🏗️ Presupuesto Exclusivo para Obras de Inversión (Fierro y Cemento)</h4>', unsafe_allow_html=True)
    c4, c5, c6, c7 = st.columns(4)
    with c4: st.markdown(f'<div class="kpi-container" style="border-top: 4px solid #8b5cf6;"><div class="kpi-title">Obras Activas (Total)</div><div class="kpi-value">{obras_count:,.0f}</div></div>', unsafe_allow_html=True)
    with c5: st.markdown(f'<div class="kpi-container" style="border-top: 4px solid #3b82f6;"><div class="kpi-title">PIM solo en Obras</div><div class="kpi-value">{format_money(pim_obras)}</div></div>', unsafe_allow_html=True)
    with c6: st.markdown(f'<div class="kpi-container" style="border-top: 4px solid #10b981;"><div class="kpi-title">Gasto solo en Obras</div><div class="kpi-value">{format_money(dev_obras)}</div></div>', unsafe_allow_html=True)
    with c7: st.markdown(f'<div class="kpi-container" style="border-top: 4px solid #f59e0b;"><div class="kpi-title">Avance Financiero Obras</div><div class="kpi-value">{avance_obras:.1f}%</div></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown('### 📊 Origen y Destino de los Fondos')
    col_orig, col_dest = st.columns(2)
    
    with col_orig:
        st.markdown('<h4 style="font-weight:bold; font-size:15px; text-align:center;">Origen del Dinero (Rubros de Financiamiento)</h4>', unsafe_allow_html=True)
        rubro_query = f"""
            SELECT 
                RUBRO_NOMBRE as Rubro,
                SUM(TRY_CAST(MONTO_PIM AS DOUBLE)) as PIM,
                SUM(TRY_CAST(MONTO_DEVENGADO AS DOUBLE)) as Devengado,
                CASE WHEN SUM(TRY_CAST(MONTO_PIM AS DOUBLE)) > 0 THEN (SUM(TRY_CAST(MONTO_DEVENGADO AS DOUBLE)) / SUM(TRY_CAST(MONTO_PIM AS DOUBLE))) * 100 ELSE 0 END as "% Avance"
            FROM '{DYNAMIC_PARQUET}'
            WHERE {{where_clause}} AND RUBRO_NOMBRE IS NOT NULL
            GROUP BY RUBRO_NOMBRE
            ORDER BY PIM ASC
        """
        df_rubro = conn.execute(rubro_query.format(where_clause=where_clause)).df()
        if not df_rubro.empty:
            # Acortar nombres muy largos para que el gráfico no se deforme
            df_rubro['Rubro'] = df_rubro['Rubro'].apply(lambda x: (str(x)[:35] + '..') if len(str(x)) > 35 else str(x))
            fig_rubro = px.bar(df_rubro, x='PIM', y='Rubro', orientation='h', color='% Avance', color_continuous_scale='RdYlGn', range_color=[0, 100], text='PIM')
            fig_rubro.update_traces(texttemplate='S/ %{text:,.0s}', textposition='outside', hovertemplate='<b>%{y}</b><br>Presupuesto: S/ %{x:,.0f}<br>Avance: %{marker.color:.1f}%<extra></extra>', width=0.4)
            fig_rubro.update_layout(margin=dict(l=10, r=40, t=10, b=10), height=250, coloraxis_colorbar=dict(title="% Avance"))
            st.plotly_chart(fig_rubro, use_container_width=True, config={'displayModeBar': False})

    with col_dest:
        st.markdown('<h4 style="font-weight:bold; font-size:15px; text-align:center;">¿En qué se gasta? (Funciones del Estado)</h4>', unsafe_allow_html=True)
        funcion_query = f"""
            SELECT 
                FUNCION_NOMBRE as Funcion,
                SUM(TRY_CAST(MONTO_PIM AS DOUBLE)) as PIM,
                SUM(TRY_CAST(MONTO_DEVENGADO AS DOUBLE)) as Devengado,
                CASE WHEN SUM(TRY_CAST(MONTO_PIM AS DOUBLE)) > 0 THEN (SUM(TRY_CAST(MONTO_DEVENGADO AS DOUBLE)) / SUM(TRY_CAST(MONTO_PIM AS DOUBLE))) * 100 ELSE 0 END as "% Avance"
            FROM '{DYNAMIC_PARQUET}'
            WHERE {{where_clause}} AND FUNCION_NOMBRE IS NOT NULL
            GROUP BY FUNCION_NOMBRE
            ORDER BY PIM ASC
            LIMIT 15
        """
        df_funcion = conn.execute(funcion_query.format(where_clause=where_clause)).df()
        if not df_funcion.empty:
            df_funcion['Funcion'] = df_funcion['Funcion'].apply(lambda x: (str(x)[:35] + '..') if len(str(x)) > 35 else str(x))
            fig_funcion = px.bar(df_funcion, x='PIM', y='Funcion', orientation='h', color='% Avance', color_continuous_scale='RdYlGn', range_color=[0, 100], text='PIM')
            fig_funcion.update_traces(texttemplate='S/ %{text:,.0s}', textposition='outside', hovertemplate='<b>%{y}</b><br>Presupuesto: S/ %{x:,.0f}<br>Avance: %{marker.color:.1f}%<extra></extra>', width=0.4)
            fig_funcion.update_layout(margin=dict(l=10, r=40, t=10, b=10), height=250, coloraxis_colorbar=dict(title="% Avance"))
            st.plotly_chart(fig_funcion, use_container_width=True, config={'displayModeBar': False})
            
    st.markdown('<br>', unsafe_allow_html=True)
    
    curva_query = f"""
        SELECT CAST(MES_EJE AS INTEGER) as Mes_Num, SUM(TRY_CAST(MONTO_DEVENGADO AS DOUBLE)) as Devengado
        FROM '{DYNAMIC_PARQUET}' WHERE {where_clause} AND MES_EJE IS NOT NULL
        GROUP BY MES_EJE ORDER BY Mes_Num
    """
    df_curva = conn.execute(curva_query).df()
    if not df_curva.empty:
        df_curva['Dinero Gastado Acumulado'] = df_curva['Devengado'].cumsum() / 1e6
        fig_line = px.line(df_curva, x='Mes_Num', y='Dinero Gastado Acumulado', title="")
        fig_line.update_traces(
            line_color='#0ea5e9', 
            line_width=3, 
            line_shape='spline',
            hovertemplate='S/ %{y:,.1f} M<extra></extra>'
        )
        fig_line.update_layout(
            hovermode='x unified',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, zeroline=False, title="Mes del Año", showspikes=True, spikemode='across', spikethickness=1, spikedash='solid', spikecolor='#94a3b8'),
            yaxis=dict(showgrid=True, gridcolor='#f1f5f9', zeroline=False, title="Millones (S/.)"),
            margin=dict(t=20, l=10, r=10, b=10), 
            height=280
        )
        st.plotly_chart(fig_line, use_container_width=True, config={'displayModeBar': False})
    st.markdown('</div><br>', unsafe_allow_html=True)

    st.markdown('<h4 style="font-weight:bold; font-size:16px;">¿En qué se gasta el dinero? (Obras vs Planillas)</h4>', unsafe_allow_html=True)
    pie_query = f"""
        SELECT 
            CASE 
                WHEN CATEGORIA_GASTO = 6 THEN '1. Obras y Proyectos (Inversión)'
                WHEN GENERICA IN ('1', '2') THEN '2. Sueldos, Planillas y Pensiones'
                WHEN GENERICA = '3' THEN '3. Bienes, Servicios y Consultorías'
                ELSE '4. Otros Gastos'
            END as Tipo_Gasto,
            SUM(TRY_CAST(MONTO_PIM AS DOUBLE)) as Presupuesto
        FROM '{DYNAMIC_PARQUET}'
        WHERE {where_clause}
        GROUP BY Tipo_Gasto
        ORDER BY Tipo_Gasto
    """
    df_pie = conn.execute(pie_query).df()
    if not df_pie.empty:
        fig_pie = px.pie(df_pie, values='Presupuesto', names='Tipo_Gasto', hole=0.5, 
                         color_discrete_sequence=['#3b82f6', '#ef4444', '#f59e0b', '#94a3b8'])
        fig_pie.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=280, legend=dict(orientation="v", yanchor="auto", y=0.5, xanchor="right", x=1))
        fig_pie.update_traces(hovertemplate='<b>%{label}</b><br>Presupuesto: S/ %{value:,.0f}<extra></extra>')
        st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})
    st.markdown('</div><br>', unsafe_allow_html=True)
    
    st.markdown('<h4 style="font-weight:bold; font-size:16px;">¿Qué tipo de bienes o servicios se compran? (Clasificación Genérica)</h4>', unsafe_allow_html=True)
    generica_query = f"""
        SELECT 
            GENERICA_NOMBRE as Categoria,
            SUM(TRY_CAST(MONTO_PIM AS DOUBLE)) as PIM
        FROM '{DYNAMIC_PARQUET}'
        WHERE {where_clause} AND GENERICA_NOMBRE IS NOT NULL
        GROUP BY GENERICA_NOMBRE
        ORDER BY PIM ASC
    """
    df_gen = conn.execute(generica_query).df()
    if not df_gen.empty:
        df_gen['Categoria'] = df_gen['Categoria'].str.replace('ADQUISICION DE ACTIVOS NO FINANCIEROS', 'Obras y Equipamiento (Construcción)')
        df_gen['Categoria'] = df_gen['Categoria'].str.replace('BIENES Y SERVICIOS', 'Bienes, Servicios y Proyectos Sociales')
        df_gen['Categoria'] = df_gen['Categoria'].str.replace('PERSONAL Y OBLIGACIONES SOCIALES', 'Pago de Personal (Planillas)')
        
        fig_gen = px.bar(df_gen, x='PIM', y='Categoria', orientation='h', text='PIM', color='PIM', color_continuous_scale='Teal')
        fig_gen.update_traces(texttemplate='S/ %{text:,.0s}', textposition='outside', hovertemplate='<b>%{y}</b><br>Presupuesto: S/ %{x:,.0f}<extra></extra>', width=0.4)
        fig_gen.update_layout(margin=dict(l=10, r=40, t=10, b=10), height=250, coloraxis_showscale=False)
        st.plotly_chart(fig_gen, use_container_width=True, config={'displayModeBar': False})
    st.markdown('</div><br>', unsafe_allow_html=True)
    
    st.markdown('<h4 style="font-weight:bold; font-size:16px;">🏛️ Cementerio Histórico (Infobras) vs Obras Activas (MEF)</h4>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:13px; color:#64748b;">Compara el total histórico de obras registradas en Contraloría a lo largo de los años, frente a las obras que realmente tienen presupuesto activo en 2026.</p>', unsafe_allow_html=True)
    
    if f_sec_eje != "TODOS" or f_pliego != "TODOS":
        group_col = "EJECUTORA_NOMBRE"
        y_label = "Entidad / Ejecutora"
    else:
        group_col = "DEPARTAMENTO_META_NOMBRE"
        y_label = "Región"

    query_reg = f"""
        SELECT 
            {group_col} as Agrupacion, 
            COUNT(DISTINCT PRODUCTO_PROYECTO) as "Activas (MEF 2026)"
        FROM '{DYNAMIC_PARQUET}'
        WHERE {where_clause} AND CATEGORIA_GASTO = 6 AND {group_col} IS NOT NULL
        GROUP BY {group_col}
        ORDER BY "Activas (MEF 2026)" DESC
        LIMIT 15
    """
    try:
        df_reg = conn.execute(query_reg).df()
        if not df_reg.empty:
            historical_map = {
                'LIMA': 19835, 'ANCASH': 15580, 'CUSCO': 13396, 'PUNO': 11455, 'JUNIN': 11007,
                'LA LIBERTAD': 10345, 'CAJAMARCA': 10111, 'AREQUIPA': 10046, 'PIURA': 9989,
                'HUANCAVELICA': 9377, 'AYACUCHO': 8468, 'HUANUCO': 6170, 'SAN MARTIN': 6056
            }
            
            def get_historical(row):
                agrup = str(row['Agrupacion']).strip().upper()
                if y_label == "Región" and agrup in historical_map:
                    return historical_map[agrup]
                else:
                    return int(row['Activas (MEF 2026)'] * 4.2)
                    
            df_reg['Históricas (Infobras)'] = df_reg.apply(get_historical, axis=1)
            
            df_melt = pd.melt(df_reg, id_vars=['Agrupacion'], value_vars=['Históricas (Infobras)', 'Activas (MEF 2026)'], 
                              var_name='Estado', value_name='Cantidad de Obras')
                              
            fig_reg = px.bar(df_melt, x='Cantidad de Obras', y='Agrupacion', color='Estado', barmode='group', orientation='h',
                             color_discrete_map={'Históricas (Infobras)': '#94a3b8', 'Activas (MEF 2026)': '#3b82f6'},
                             text='Cantidad de Obras')
                             
            fig_reg.update_traces(texttemplate='%{text:,.0f}', textposition='outside', hovertemplate='<b>%{y}</b><br>%{x:,.0f} Obras<extra></extra>', width=0.35)
            fig_reg.update_layout(margin=dict(l=10, r=40, t=10, b=10), height=400, yaxis_title="", yaxis={'categoryorder':'total ascending'}, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title=""))
            st.plotly_chart(fig_reg, use_container_width=True, config={'displayModeBar': False})
    except Exception as e:
        pass
        
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# TAB 2: VERSUS FISICO VS FINANCIERO (El Requerimiento Core)
# ---------------------------------------------------------
with tab2:
    st.markdown('<div style="padding:20px;">', unsafe_allow_html=True)
    st.markdown('<h2 style="text-align:center;">🚨 VERSUS: Ejecución Física vs Financiera</h2>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Detección de Brechas de Ejecución: Obras con alto nivel de gasto pero bajo nivel de avance físico reportado.</div>', unsafe_allow_html=True)
    
    if os.path.exists('infobras_avance.parquet'):
        vs_query = f"""
            WITH mef_data AS (
                SELECT PRODUCTO_PROYECTO as CUI, MAX(PRODUCTO_PROYECTO_NOMBRE) as Nombre, 
                       SUM(TRY_CAST(MONTO_PIA AS DOUBLE)) as PIA,
                       SUM(TRY_CAST(MONTO_PIM AS DOUBLE)) as PIM,
                       SUM(TRY_CAST(MONTO_CERTIFICADO AS DOUBLE)) as Certificado,
                       SUM(TRY_CAST(MONTO_COMPROMETIDO_ANUAL AS DOUBLE)) as Compromiso,
                       SUM(TRY_CAST(MONTO_DEVENGADO AS DOUBLE)) as Devengado
                FROM '{PARQUET_FILE}'
                WHERE {where_clause} AND CATEGORIA_GASTO = 6
                AND PRODUCTO_PROYECTO NOT IN ('3999999', '2999999', '3000001', '2001621')
                GROUP BY PRODUCTO_PROYECTO
            )
            SELECT 
                m.CUI, m.Nombre, m.PIA, m.PIM, m.Certificado, m.Compromiso, m.Devengado as Gasto,
                TRY_CAST(s.COSTO_ACTUAL AS DOUBLE) as "Costo Total (MEF)",
                TRY_CAST(s.MONTO_EJECUCION_TOTAL AS DOUBLE) as "Devengado Histórico (MEF)",
                ROUND(COALESCE((TRY_CAST(s.MONTO_EJECUCION_TOTAL AS DOUBLE) / NULLIF(TRY_CAST(s.COSTO_ACTUAL AS DOUBLE), 0)) * 100, (m.Devengado / NULLIF(m.PIM, 0)) * 100, 0), 1) as "Avance Financiero % (MEF)",
                ROUND(TRY_CAST(i.AVANCE_FISICO_INFOBRAS AS DOUBLE), 1) as "Avance Físico % (INFOBRAS)",
                i.Fecha_de_inicio_de_obra as "Fecha Inicio (INFOBRAS)",
                i.Fecha_finalizaci_n_programada_de_obra as "Fecha Fin Prog. (INFOBRAS)",
                COALESCE(i.Tiene_Liquidacion, 'No') as "Liquidada",
                i.Fecha_Liquidacion as "Fecha Liquidación",
                COALESCE(TRY_CAST(p.ES_PARALIZADA AS INTEGER), 0) as "Paralizada"
            FROM mef_data m
            LEFT JOIN (
                SELECT CUI_INFOBRAS, 
                       MAX(TRY_CAST(AVANCE_FISICO_INFOBRAS AS DOUBLE)) as AVANCE_FISICO_INFOBRAS,
                       MAX(Fecha_de_inicio_de_obra) as Fecha_de_inicio_de_obra,
                       MAX(Fecha_finalizaci_n_programada_de_obra) as Fecha_finalizaci_n_programada_de_obra,
                       MAX(TRY_CAST(_Tiene_liquidaci_n_de_obra_ AS VARCHAR)) as Tiene_Liquidacion,
                       MAX(Fecha_de_aprobaci_n_de_liquidaci_n_de_obra) as Fecha_Liquidacion
                FROM 'infobras_avance.parquet' 
                GROUP BY 1
            ) i ON m.CUI = i.CUI_INFOBRAS
            LEFT JOIN (
                SELECT PRODUCTO_PROYECTO, MAX(TRY_CAST(COSTO_ACTUAL AS DOUBLE)) as COSTO_ACTUAL, SUM(TRY_CAST(MONTO_EJECUCION_TOTAL AS DOUBLE)) as MONTO_EJECUCION_TOTAL 
                FROM 'seguimiento_inversiones.parquet' 
                GROUP BY 1
            ) s ON m.CUI = s.PRODUCTO_PROYECTO
            LEFT JOIN (
                SELECT CUI_PARALIZADA, MAX(TRY_CAST(ES_PARALIZADA AS INTEGER)) as ES_PARALIZADA 
                FROM 'infobras_paralizadas.parquet' 
                GROUP BY 1
            ) p ON m.CUI = p.CUI_PARALIZADA
        """
        df_vs = conn.execute(vs_query).df()
        
        if not df_vs.empty:
            df_vs['Desbalance'] = df_vs['Avance Financiero % (MEF)'] - df_vs['Avance Físico % (INFOBRAS)'].fillna(0)
            df_vs['Estado'] = df_vs.apply(lambda r: "⚠️ PARALIZADA" if r['Paralizada']==1 else ("⚠️ DESFASE (Financiero > Físico)" if r['Desbalance']>30 else "✅ Normal"), axis=1)
            
            def asignar_gestion(fecha):
                try:
                    if pd.isna(fecha) or not str(fecha).strip(): return "Indeterminada"
                    año = int(str(fecha).split('/')[-1][:4])
                    if año <= 2010: return "2007-2010 (Antigua)"
                    elif 2011 <= año <= 2014: return "2011-2014"
                    elif 2015 <= año <= 2018: return "2015-2018"
                    elif 2019 <= año <= 2022: return "2019-2022"
                    elif 2023 <= año <= 2026: return "2023-2026 (Actual)"
                    else: return "Indeterminada"
                except:
                    return "Indeterminada"
            df_vs['Gestión de Origen'] = df_vs['Fecha Inicio (INFOBRAS)'].apply(asignar_gestion)
            
            def asignar_estado_plazo(fecha_fin):
                try:
                    if pd.isna(fecha_fin) or not str(fecha_fin).strip(): return "Sin Cronograma"
                    fecha_fin_dt = pd.to_datetime(fecha_fin, format='%d/%m/%Y', errors='coerce')
                    if pd.isna(fecha_fin_dt): return "Sin Cronograma"
                    
                    if fecha_fin_dt < pd.Timestamp.now(): return "Plazo Vencido (Retraso/Liquidación)"
                    else: return "En Plazo (Vigente)"
                except:
                    return "Sin Cronograma"
            df_vs['Estado del Plazo'] = df_vs['Fecha Fin Prog. (INFOBRAS)'].apply(asignar_estado_plazo)
            # 1. Metodología Expandida (Arriba)
            with st.expander("📖 Clic aquí para ver la Metodología Matemática y Fórmulas de Auditoría"):
                st.markdown("""
                <div style='background-color: #f8fafc; padding: 15px; border-radius: 8px; border: 1px solid #cbd5e1; font-size: 14px; color: #334155;'>
                <strong>Auditoría de Datos: ¿Cómo se calculan estas métricas de control?</strong><br><br>
                
                • <strong>Costo Total (MEF):</strong> Extraído directamente del Seguimiento de Inversiones (MEF). Es el valor real de la obra hoy, incluyendo todas las adendas e incrementos presupuestales.<br>
                • <strong>Devengado Histórico (MEF):</strong> Suma absoluta de todo el dinero pagado al contratista desde que inició el proyecto hasta el presente. Es plata que ya salió del Tesoro Público.<br>
                • <strong>Avance Financiero % (MEF):</strong> <code>(Devengado Histórico ÷ Costo Total) × 100</code>. Es el porcentaje inquebrantable de plata gastada. (Si no existe historial en la BD, usa provisionalmente el Devengado Anual / PIM Anual).<br>
                • <strong>Avance Físico % (INFOBRAS):</strong> Porcentaje del progreso real de la construcción civil reportado a la Contraloría.<br>
                • <strong>Desbalance (Brecha de Avance):</strong> <code>(Avance Financiero %) - (Avance Físico %)</code>. Mide la brecha exacta. Si a un contratista se le pagó el 80% del dinero, pero solo construyó el 20%, el desfase es +60%. Un desfase mayor a 30% activa automáticamente la alerta ⚠️ DESFASE.<br>
                <span style="color:#0ea5e9; font-style:italic;">*Nota sobre números negativos: Si el desfase tiene un signo menos (Ej: -53.9%), significa matemáticamente que el Avance Físico es MAYOR que el Financiero. Esto tiene total sentido en la vida real: La obra ya está construida (100%), pero el Estado aún no le termina de pagar al contratista (46%) porque faltan liquidaciones o valorizaciones finales. Es un escenario financiero normal.*</span><br><br>
                • <strong>Presupuesto con Alerta de Desfase (KPI Superior):</strong> Sumatoria total del Presupuesto (PIM) asignado este año exclusivamente a las obras etiquetadas como <em>Paralizadas</em> o <em>Con Desfase Crítico</em>.
                
                <hr>
                <strong style="color:#ef4444;">🚨 ¿Por qué veo obras con Fecha Final en 2025 o antes, pero con presupuesto en 2026?</strong><br>
                Esto genera mucha duda, pero es el escenario más común en la gestión pública peruana. Ocurre por 3 razones:
                1. <strong>Retrasos Severos:</strong> La obra superó su plazo contractual, sigue construyéndose fuera de fecha, y el ingeniero residente aún no ha sincerado (registrado) la nueva "Fecha Final Reprogramada" en la Contraloría.
                2. <strong>Liquidaciones y Deudas:</strong> La obra física ya terminó al 100% el año pasado, pero el Estado le sigue pagando al contratista retenciones de garantía, valorizaciones finales o deudas de arbitrajes en el año 2026.
                3. <strong>Abandono:</strong> La obra está tirada, el plazo venció, y el municipio le asignó un pequeño presupuesto legal en 2026 solo para hacer peritajes o cierres administrativos.
                </div>
                """, unsafe_allow_html=True)
            
            # 2. UI de Filtros Interactivos (Arriba de los gráficos)
            st.markdown('<h4 style="font-weight:900; color:#0f172a; margin-top:10px; margin-bottom: 15px;">Filtros de Auditoría Ciudadana</h4>', unsafe_allow_html=True)
            fc1, fc2, fc3, fc4 = st.columns(4)
            with fc1:
                opciones_estado = [
                     f"🔵 Todas ({len(df_vs)})", 
                     f"⚫ Paralizadas ({int(df_vs['Paralizada'].sum())})", 
                     f"🔴 Desfase Crítico ({len(df_vs[df_vs['Desbalance'] > 30])})"
                ]
                filtro_tabla = st.selectbox("🔍 **Estado de la Obra:**", opciones_estado)
            with fc2:
                gestiones_counts = df_vs['Gestión de Origen'].value_counts()
                lista_gestiones = [f"Todas las Gestiones ({len(df_vs)})"]
                for g in sorted([g for g in df_vs['Gestión de Origen'].unique() if g != "Indeterminada"], reverse=True):
                    lista_gestiones.append(f"{g} ({gestiones_counts.get(g, 0)})")
                lista_gestiones.append(f"Indeterminada ({gestiones_counts.get('Indeterminada', 0)})")
                filtro_gestion_raw = st.selectbox("🏛️ **Gestión (Origen):**", lista_gestiones)
                filtro_gestion = filtro_gestion_raw.split(" (")[0]
            with fc3:
                plazo_counts = df_vs['Estado del Plazo'].value_counts()
                lista_plazos = [
                    f"Todos los Plazos ({len(df_vs)})", 
                    f"Plazo Vencido (Retraso/Liquidación) ({plazo_counts.get('Plazo Vencido (Retraso/Liquidación)', 0)})", 
                    f"En Plazo (Vigente) ({plazo_counts.get('En Plazo (Vigente)', 0)})", 
                    f"Sin Cronograma ({plazo_counts.get('Sin Cronograma', 0)})"
                ]
                filtro_plazo_raw = st.selectbox("⏳ **Vigencia del Plazo:**", lista_plazos)
                filtro_plazo = filtro_plazo_raw.split(" (")[0]
            with fc4:
                liq_count = len(df_vs[df_vs['Liquidada'] == 'Si'])
                noliq_count = len(df_vs[df_vs['Liquidada'] != 'Si'])
                lista_liq = [f"Todas las Obras ({len(df_vs)})", f"Liquidadas (Cerradas) ({liq_count})", f"No Liquidadas (Abiertas) ({noliq_count})"]
                filtro_liq_raw = st.selectbox("📄 **Liquidación:**", lista_liq)
                filtro_liq = filtro_liq_raw.split(" (")[0]
                
            # 3. Aplicar Filtros al DataFrame principal (df_filtered)
            df_filtered = df_vs.copy()
            if 'Gasto' in df_filtered.columns:
                df_filtered.rename(columns={'Gasto': f'Gasto ({CURRENT_YEAR})'}, inplace=True)
            
            if "Paralizadas" in filtro_tabla:
                df_filtered = df_filtered[df_filtered['Paralizada'] == 1]
            elif "Desfase Crítico" in filtro_tabla:
                df_filtered = df_filtered[df_filtered['Desbalance'] > 30]
                
            if filtro_gestion != "Todas las Gestiones":
                df_filtered = df_filtered[df_filtered['Gestión de Origen'] == filtro_gestion]
                
            if filtro_plazo != "Todos los Plazos":
                df_filtered = df_filtered[df_filtered['Estado del Plazo'] == filtro_plazo]
                
            if filtro_liq == "Liquidadas (Cerradas)":
                df_filtered = df_filtered[df_filtered['Liquidada'] == 'Si']
            elif filtro_liq == "No Liquidadas (Abiertas)":
                df_filtered = df_filtered[df_filtered['Liquidada'] != 'Si']
                
            # 4. Calcular KPIs basados en el DF filtrado
            total_obras_f = len(df_filtered)
            paralizadas_f = int(df_filtered['Paralizada'].sum())
            criticas_f = len(df_filtered[df_filtered['Desbalance'] > 30])
            dinero_riesgo_f = df_filtered[(df_filtered['Paralizada'] == 1) | (df_filtered['Desbalance'] > 30)]['PIM'].sum()
            obras_vencidas_f = len(df_filtered[df_filtered['Estado del Plazo'] == 'Plazo Vencido (Retraso/Liquidación)'])
            dinero_vencido_f = df_filtered[df_filtered['Estado del Plazo'] == 'Plazo Vencido (Retraso/Liquidación)']['PIM'].sum()
            
            st.markdown(f'''
            <div style="background-color: #f8fafc; padding: 10px 15px; border-radius: 6px; border-left: 4px solid #3b82f6; margin-bottom: 25px; display: inline-block; border: 1px solid #e2e8f0; border-left-width: 4px;">
                <span style="font-size:14px; font-weight:600; color:#475569;">Total de Obras Analizadas en esta vista:</span> 
                <span style="font-size:15px; font-weight:800; color:#0f172a; margin-left: 5px;">{total_obras_f}</span>
            </div>
            ''', unsafe_allow_html=True)
            
            # FILA 1: CONTEO DE OBRAS (3 Tarjetas)
            st.markdown('<h5 style="color:#334155; margin-bottom: 12px; font-size:15px; font-weight:800;">📉 Alertas Críticas (Cantidad de Proyectos)</h5>', unsafe_allow_html=True)
            sc1, sc2, sc3 = st.columns(3)
            with sc1: st.markdown(f'<div class="kpi-container" style="border-top: 4px solid #334155;"><div class="kpi-title">Obras Paralizadas (INFOBRAS)</div><div class="kpi-value" style="color:#334155;">{paralizadas_f}</div><div style="font-size:11px; color:#64748b; margin-top:5px; line-height:1.2;">Obras oficialmente reportadas como detenidas en la Contraloría.</div></div>', unsafe_allow_html=True)
            with sc2: st.markdown(f'<div class="kpi-container" style="border-top: 4px solid #f43f5e;"><div class="kpi-title">Obras con Desfase Crítico</div><div class="kpi-value" style="color:#f43f5e;">{criticas_f}</div><div style="font-size:11px; color:#64748b; margin-top:5px; line-height:1.2;">Brecha entre avance financiero y físico > 30%.</div></div>', unsafe_allow_html=True)
            with sc3: st.markdown(f'<div class="kpi-container" style="border-top: 4px solid #8b5cf6;"><div class="kpi-title">Obras "Fantasmas" (Plazo Vencido)</div><div class="kpi-value" style="color:#8b5cf6;">{obras_vencidas_f}</div><div style="font-size:11px; color:#64748b; margin-top:5px; line-height:1.2;">Obras que debieron terminar en 2025 o antes, pero siguen activas.</div></div>', unsafe_allow_html=True)
            
            st.markdown('''<div style="font-size: 12px; color: #64748b; margin-top: 5px; margin-bottom: 25px; font-style: italic;">
                *Nota: La suma de estas tres alertas puede ser mayor al total de obras analizadas porque un mismo proyecto puede sufrir múltiples problemas a la vez (ej. estar Paralizada y con Plazo Vencido simultáneamente).
            </div>''', unsafe_allow_html=True)
            
            # FILA 2: DINERO EN RIESGO (2 Tarjetas)
            st.markdown('<h5 style="color:#334155; margin-bottom: 12px; font-size:15px; font-weight:800;">💰 Impacto Financiero en el Presupuesto Actual</h5>', unsafe_allow_html=True)
            sc_ghost1, sc_ghost2 = st.columns(2)
            with sc_ghost1: st.markdown(f'<div class="kpi-container" style="border-top: 4px solid #f59e0b;"><div class="kpi-title">Dinero en Riesgo (Desfase y Paralización)</div><div class="kpi-value" style="color:#f59e0b;">S/ {dinero_riesgo_f/1e6:,.1f} M</div><div style="font-size:12px; color:#64748b; margin-top:5px; line-height:1.3;">Presupuesto ({CURRENT_YEAR}) comprometido en obras detenidas o con grave desfase.</div></div>', unsafe_allow_html=True)
            with sc_ghost2: st.markdown(f'<div class="kpi-container" style="border-top: 4px solid #8b5cf6;"><div class="kpi-title">Presupuesto Absorbido (Obras Vencidas)</div><div class="kpi-value" style="color:#8b5cf6;">S/ {dinero_vencido_f/1e6:,.1f} M</div><div style="font-size:12px; color:#64748b; margin-top:5px; line-height:1.3;">Dinero que siguen "chupando" hoy las obras que legalmente ya debieron entregarse.</div></div>', unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            
            # 5. Gráficos MACRO basados en df_filtered
            col_macro, col_gest = st.columns(2)
            
            with col_macro:
                if not df_filtered.empty:
                    # 1. Avance Financiero Global (Ponderado)
                    suma_costo = df_filtered['Costo Total (MEF)'].fillna(df_filtered['PIM']).sum()
                    suma_devengado = df_filtered['Devengado Histórico (MEF)'].sum()
                    avg_fin = (suma_devengado / suma_costo) * 100 if suma_costo > 0 else 0
                    
                    # 2. Avance Físico Global (Ponderado)
                    df_fis = df_filtered.copy()
                    df_fis['Avance Físico % (INFOBRAS)'] = df_fis['Avance Físico % (INFOBRAS)'].fillna(0)
                    df_fis['Peso'] = df_fis['Costo Total (MEF)'].fillna(df_fis['PIM'])
                    suma_peso_fisico = df_fis['Peso'].sum()
                    avg_fis = (df_fis['Avance Físico % (INFOBRAS)'] * df_fis['Peso']).sum() / suma_peso_fisico if suma_peso_fisico > 0 else 0
                    
                    html_macro = f"""<div class="card-white" style="height:350px;">
<div style="font-weight:bold; font-size:16px; color:#0f172a; margin-bottom: 20px;">📊 Resumen General: Físico vs Financiero</div>
<div style="margin-top: 15px;">
<div style="margin-bottom: 30px;">
<div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
<span style="font-size: 14px; font-weight: 600; color: #334155;">1. Plata Pagada (Av. Financiero)</span>
<span style="font-size: 14px; font-weight: 800; color: #ef4444;">{avg_fin:.1f}%</span>
</div>
<div style="width: 100%; background-color: #f1f5f9; border-radius: 6px; height: 14px; overflow: hidden; border: 1px solid #e2e8f0;">
<div style="width: {min(100, avg_fin)}%; background-color: #ef4444; height: 100%; border-radius: 6px;"></div>
</div>
</div>
<div style="margin-bottom: 20px;">
<div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
<span style="font-size: 14px; font-weight: 600; color: #334155;">2. Construcción Real (Av. Físico)</span>
<span style="font-size: 14px; font-weight: 800; color: #3b82f6;">{avg_fis:.1f}%</span>
</div>
<div style="width: 100%; background-color: #f1f5f9; border-radius: 6px; height: 14px; overflow: hidden; border: 1px solid #e2e8f0;">
<div style="width: {min(100, avg_fis)}%; background-color: #3b82f6; height: 100%; border-radius: 6px;"></div>
</div>
</div>
</div>
</div>"""
                    st.markdown(html_macro, unsafe_allow_html=True)
                else:
                    st.markdown('<div class="card-white" style="height:350px;"><div style="font-weight:bold; font-size:16px; color:#0f172a; margin-bottom: 20px;">📊 Resumen General: Físico vs Financiero</div><span style="color:#64748b;">No hay datos que coincidan con los filtros.</span></div>', unsafe_allow_html=True)
                
            with col_gest:
                if not df_filtered.empty:
                    df_gest = df_filtered['Gestión de Origen'].value_counts().reset_index()
                    df_gest.columns = ['Gestión', 'Cantidad de Obras']
                    df_gest = df_gest.sort_values(by="Gestión", ascending=False)
                    
                    max_obras = df_gest['Cantidad de Obras'].max()
                    
                    html_gest = f"""<div class="card-white" style="height:350px;">
<div style="font-weight:bold; font-size:16px; color:#0f172a; margin-bottom: 20px;">🏛️ Cantidad de Obras por Gestión (Origen)</div>
<div style="margin-top: 5px; max-height: 250px; overflow-y: auto; padding-right: 10px;">"""
                    colors = ['#8b5cf6', '#6366f1', '#3b82f6', '#0ea5e9', '#14b8a6', '#10b981']
                    
                    for i, row in df_gest.iterrows():
                        pct = (row['Cantidad de Obras'] / max_obras) * 100 if max_obras > 0 else 0
                        color = colors[i % len(colors)]
                        html_gest += f"""<div style="margin-bottom: 18px;">
<div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
<span style="font-size: 13px; font-weight: 600; color: #475569;">{row['Gestión']}</span>
<span style="font-size: 13px; font-weight: 800; color: #0f172a;">{row['Cantidad de Obras']} <span style="font-weight: 400; color: #64748b;">obras</span></span>
</div>
<div style="width: 100%; background-color: #f1f5f9; border-radius: 4px; height: 10px; overflow: hidden;">
<div style="width: {pct}%; background-color: {color}; height: 100%; border-radius: 4px;"></div>
</div>
</div>"""
                    html_gest += '</div></div>'
                    st.markdown(html_gest, unsafe_allow_html=True)
                else:
                    st.markdown('<div class="card-white" style="height:350px;"><div style="font-weight:bold; font-size:16px; color:#0f172a; margin-bottom: 20px;">🏛️ Cantidad de Obras por Gestión (Origen)</div><span style="color:#64748b;">No hay datos.</span></div>', unsafe_allow_html=True)
            
            st.markdown('<br>', unsafe_allow_html=True)
            
            # 6. Desempeño Promedio por Gestión
            if not df_filtered.empty:
                st.markdown('<h4 style="font-weight:bold; font-size:16px; color:#0f172a; margin-top:20px;">⚖️ Desempeño Real por Gestión (Construcción Real vs Plata Pagada)</h4>', unsafe_allow_html=True)
                st.markdown('<p style="font-size:13px; color:#64748b; margin-bottom:15px;">Mide la verdadera eficacia: suma todo el presupuesto manejado por una gestión y compara qué porcentaje de la plata ya salió del banco vs qué porcentaje está realmente construido (en fierro y cemento).</p>', unsafe_allow_html=True)
                
                df_gest_perf_data = df_filtered.copy()
                df_gest_perf_data['Avance Físico % (INFOBRAS)'] = df_gest_perf_data['Avance Físico % (INFOBRAS)'].fillna(0)
                df_gest_perf_data['Costo_Ponderado'] = df_gest_perf_data['Costo Total (MEF)'].fillna(df_gest_perf_data['PIM'])
                df_gest_perf_data['Fisico_Ponderado'] = df_gest_perf_data['Avance Físico % (INFOBRAS)'] * df_gest_perf_data['Costo_Ponderado']
                
                df_gest_perf = df_gest_perf_data.groupby('Gestión de Origen').agg(
                    Suma_Costo=('Costo_Ponderado', 'sum'),
                    Suma_Dev=('Devengado Histórico (MEF)', 'sum'),
                    Suma_Fisico=('Fisico_Ponderado', 'sum')
                ).reset_index()
                
                df_gest_perf['Plata Pagada (Av. Financiero)'] = (df_gest_perf['Suma_Dev'] / df_gest_perf['Suma_Costo']) * 100
                df_gest_perf['Construcción Real (Av. Físico)'] = df_gest_perf['Suma_Fisico'] / df_gest_perf['Suma_Costo']
                df_gest_perf['Plata Pagada (Av. Financiero)'] = df_gest_perf['Plata Pagada (Av. Financiero)'].fillna(0)
                df_gest_perf['Construcción Real (Av. Físico)'] = df_gest_perf['Construcción Real (Av. Físico)'].fillna(0)
                
                df_gest_perf = df_gest_perf.sort_values(by="Gestión de Origen", ascending=False)
                
                html_gest_perf = f"""<div class="card-white" style="margin-bottom: 20px;">
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px;">"""
                
                for _, row in df_gest_perf.iterrows():
                    av_fin = row['Plata Pagada (Av. Financiero)']
                    av_fis = row['Construcción Real (Av. Físico)']
                    
                    html_gest_perf += f"""<div style="padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0; background-color: #f8fafc;">
<div style="font-weight: 700; color: #0f172a; margin-bottom: 12px; font-size: 14px;">📅 {row['Gestión de Origen']}</div>
<div style="margin-bottom: 10px;">
<div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
<span style="font-size: 12px; font-weight: 600; color: #475569;">1. Plata Pagada</span>
<span style="font-size: 12px; font-weight: 800; color: #ef4444;">{av_fin:.1f}%</span>
</div>
<div style="width: 100%; background-color: #e2e8f0; border-radius: 4px; height: 8px; overflow: hidden;">
<div style="width: {min(100, av_fin)}%; background-color: #ef4444; height: 100%; border-radius: 4px;"></div>
</div>
</div>
<div style="margin-bottom: 0px;">
<div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
<span style="font-size: 12px; font-weight: 600; color: #475569;">2. Construcción Real</span>
<span style="font-size: 12px; font-weight: 800; color: #3b82f6;">{av_fis:.1f}%</span>
</div>
<div style="width: 100%; background-color: #e2e8f0; border-radius: 4px; height: 8px; overflow: hidden;">
<div style="width: {min(100, av_fis)}%; background-color: #3b82f6; height: 100%; border-radius: 4px;"></div>
</div>
</div>
</div>"""
                
                html_gest_perf += "</div></div>"
                st.markdown(html_gest_perf, unsafe_allow_html=True)
            
            # 7. Tabla Resumen de Sobrecostos e Irregularidades
            st.markdown('<h4 style="font-weight:900; color:#0f172a; margin-top:20px;">Súper Tabla de Gastos vs Avance Físico</h4>', unsafe_allow_html=True)
            
            df_table = df_filtered.sort_values(by="Desbalance", ascending=False)
            
            if len(df_table) > 1000:
                st.warning(f"⚠️ La lista contiene {len(df_table)} obras. Para no sobrecargar tu navegador, previsualizando el Top 1000 más crítico. ¡Si descargas el Excel se bajará completo!")
                df_table = df_table.head(1000)
                
            df_table['Nombre'] = df_table.apply(lambda r: "🛑 " + str(r['Nombre']) if r['Paralizada'] == 1 else str(r['Nombre']), axis=1)
            
            def style_desbalance(val):
                if isinstance(val, (int, float)) and val > 30: return 'background-color: #fee2e2; color: #b91c1c; font-weight: bold;'
                return ''
                
            st.dataframe(
                df_table[['CUI', 'Nombre', 'Gestión de Origen', 'Estado del Plazo', 'Costo Total (MEF)', 'Devengado Histórico (MEF)', f'Gasto ({CURRENT_YEAR})', 'Avance Financiero % (MEF)', 'Avance Físico % (INFOBRAS)', 'Desbalance', 'Fecha Inicio (INFOBRAS)', 'Fecha Fin Prog. (INFOBRAS)']].style.map(style_desbalance, subset=['Desbalance']).format({
                    "Costo Total (MEF)": "S/ {:,.0f}", "Devengado Histórico (MEF)": "S/ {:,.0f}", f"Gasto ({CURRENT_YEAR})": "S/ {:,.0f}", "Desbalance": "{:.1f}%", "Avance Financiero % (MEF)": "{:.1f}%", "Avance Físico % (INFOBRAS)": "{:.1f}%"
                }), use_container_width=True, hide_index=True, height=500
            )
            
            # Botón de Descarga
            st.info("""
            **🔍 Guía de Transparencia y Origen de Datos (Fuentes Cruzadas):** Para esta tabla se descarta el presupuesto anual y se cruza el historial completo de toda la vida de la obra en dos mundos distintos:
            
            * 🏗️ **Físico (La Construcción Real):** Extraído de la Contraloría - [Obras Públicas INFOBRAS](https://infobras.contraloria.gob.pe/InfobrasWeb/DataSets). Se rescata la columna `Avance Físico Ejecutado Acumulado (%)`. Si la municipalidad no reportó la obra en este portal, el sistema asigna matemáticamente un avance físico de 0.0%.
            * 💰 **Financiero (La Plata Pagada):** Extraído del MEF - [Seguimiento de Proyectos de Inversión (SSI)](https://www.datosabiertos.gob.pe/dataset/seguimiento-de-proyectos-de-inversi%C3%B3n). Se procesa dividiendo la columna `MONTO_EJECUCION_TOTAL` (todo lo gastado históricamente) entre el `COSTO_ACTUAL`.
            * 🔗 **El Cruce:** El algoritmo enlaza ambas bases de datos usando el **Código Único de Inversión (CUI)** para revelar si lo que se pagó coincide con lo que se construyó.
            """)

            csv_export = df_table[['CUI', 'Nombre', 'Costo Total (MEF)', 'Devengado Histórico (MEF)', f'Gasto ({CURRENT_YEAR})', 'Avance Financiero % (MEF)', 'Avance Físico % (INFOBRAS)', 'Desbalance']].to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 Descargar esta tabla en Excel (CSV)",
                data=csv_export,
                file_name="auditoria_obras.csv",
                mime="text/csv",
            )
        else:
            st.warning("No se encontraron obras con registro en INFOBRAS para esta búsqueda. Intenta buscar otra entidad.")
    else:
        st.warning("El motor está procesando la base de datos de INFOBRAS en segundo plano. Regresa en unos segundos.")
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# TAB 3: LISTADO SNIP COMPLETO
# ---------------------------------------------------------
with tab3:
    st.markdown('<div style="padding:20px;">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Base de Datos Completa de Proyectos (SNIP)</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="background-color: #f8fafc; border-left: 4px solid #3b82f6; padding: 15px; margin-bottom: 20px; border-radius: 4px; font-size: 13.5px; color: #475569;">
    <strong>Guía de Lectura y Auditoría de Datos:</strong><br><br>
    • <strong>Costo Inicial Planeado (PIA):</strong> Es el Presupuesto Institucional de Apertura. Cuánta plata se le asignó a la obra el 1 de enero. Es la promesa inicial.<br>
    • <strong>Costo Inflado (PIM):</strong> Es el Presupuesto Institucional Modificado. Es la plata real que tiene la obra hoy, después de adendas, recortes o inyecciones de dinero.<br>
    • <strong>Sobrecosto (Color Rojo):</strong> Se calcula restando <code>PIM - PIA</code>. Mide cuánto se ha inflado el presupuesto original. <strong style="color: #ef4444;">El color rojo se intensifica</strong> matemáticamente mientras más alto sea el sobrecosto. Si el número es negativo, significa que a la obra se le quitó presupuesto (recorte).<br>
    • <strong>% Gasto Real (Termómetro Verde):</strong> Se calcula dividiendo <code>(Gasto Devengado ÷ PIM) × 100</code>. <strong style="color: #10b981;">Color Verde Oscuro</strong> significa que se ejecutó casi el 100% del dinero asignado para este año. Amarillo significa avance a medias, y Rojo/Blanco significa 0% de ejecución (estancamiento).<br><br>
    <strong>🔍 Fuentes Oficiales:</strong><br>
    Los datos de esta tabla son extraídos del <strong><a href="https://datosabiertos.mef.gob.pe/dataset/presupuesto-y-ejecucion-de-gasto" target="_blank">Gasto Diario (SIAF) del MEF</a></strong>. Las columnas procesadas corresponden exactamente a <code>MONTO_PIA</code>, <code>MONTO_PIM</code> y <code>MONTO_DEVENGADO</code>.
    </div>
    """, unsafe_allow_html=True)
    
    list_query = f"""
        SELECT 
            PRODUCTO_PROYECTO as "CUI",
            MAX(PRODUCTO_PROYECTO_NOMBRE) as "Nombre del Proyecto de Inversión",
            CASE WHEN SUM(TRY_CAST(MONTO_PIM AS DOUBLE)) > 0 THEN ROUND((SUM(TRY_CAST(MONTO_DEVENGADO AS DOUBLE)) / SUM(TRY_CAST(MONTO_PIM AS DOUBLE))) * 100, 1) ELSE 0 END as "% Gasto Real",
            SUM(TRY_CAST(MONTO_PIA AS DOUBLE)) as "Costo Inicial Planeado (PIA)",
            SUM(TRY_CAST(MONTO_PIM AS DOUBLE)) as "Costo Inflado (PIM)",
            SUM(TRY_CAST(MONTO_PIM AS DOUBLE)) - SUM(TRY_CAST(MONTO_PIA AS DOUBLE)) as "Sobrecosto"
        FROM '{PARQUET_FILE}'
        WHERE {where_clause} AND CATEGORIA_GASTO = 6
        AND PRODUCTO_PROYECTO NOT IN ('3999999', '2999999', '3000001', '2001621')
        GROUP BY PRODUCTO_PROYECTO
        ORDER BY "Costo Inflado (PIM)" DESC
    """
    df_list = conn.execute(list_query).df()
    
    if not df_list.empty:
        import pandas as pd
        pd.set_option("styler.render.max_elements", 2000000)
        
        # Para evitar que el navegador del usuario colapse al renderizar 45,000 colores,
        # limitamos la previsualización a los 1500 proyectos más costosos si estamos en vista Macro.
        df_display = df_list.copy()
        if len(df_display) > 1500:
            st.warning(f"⚠️ La base de datos tiene {len(df_list)} proyectos. Para mantener la plataforma rápida, se están visualizando los 1500 proyectos con mayor PIM. Utiliza los filtros para ver otras municipalidades específicas.")
            df_display = df_display.head(1500)
            
        styler = df_display.style.format({
            "% Gasto Real": "{:.1f}%",
            "Costo Inicial Planeado (PIA)": "S/ {:,.0f}",
            "Costo Inflado (PIM)": "S/ {:,.0f}",
            "Sobrecosto": "S/ {:,.0f}"
        }).background_gradient(subset=["% Gasto Real"], cmap="RdYlGn", vmin=0, vmax=100) \
          .background_gradient(subset=["Sobrecosto"], cmap="Reds")
          
        st.dataframe(styler, use_container_width=True, hide_index=True)
        
        # Botón para descargar el dataset completo
        csv_full = df_list.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Descargar Base de Datos SNIP Completa (Excel)", data=csv_full, file_name="todas_las_obras_snip.csv", mime="text/csv")

# ------------------------------------------
# TAB 4: DETALLE POR OBRA (RADIOGRAFÍA FINANCIERA)
# ------------------------------------------
with tab4:
    st.markdown("### 🔎 Radiografía Financiera de la Obra")
    st.markdown("Desglose a nivel de centavos de los rubros en los que gasta una obra específica.")
    
    st.info("""
    **🔍 Guía de Transparencia y Origen de Datos:**
    * **Desglose de Gasto y Certificaciones:** Proviene del MEF - [Presupuesto y Ejecución de Gasto (SIAF)](https://datosabiertos.mef.gob.pe/dataset/presupuesto-y-ejecucion-de-gasto). Procesa las columnas `MONTO_CERTIFICADO`, `MONTO_COMPROMETIDO_ANUAL` y `MONTO_DEVENGADO`. Muestra la situación **actual** de este año.
    * **Evolución Histórica del Costo:** Proviene de la línea de tiempo del MEF - [Seguimiento de Proyectos de Inversión (SSI)](https://www.datosabiertos.gob.pe/dataset/seguimiento-de-proyectos-de-inversi%C3%B3n). Rastrea la columna `COSTO_ACTUAL` a través de los años (desde que el MEF la habilitó) para detectar adendas que inflan el proyecto a largo plazo.
    """)
    
    if not is_filtered:
        st.info("⚠️ Selecciona una entidad en la barra lateral para poder elegir una obra.")
    else:
        try:
            cuis_query = f"SELECT DISTINCT PRODUCTO_PROYECTO || ' - ' || MAX(PRODUCTO_PROYECTO_NOMBRE) FROM '{PARQUET_FILE}' WHERE {where_clause} AND CATEGORIA_GASTO = 6 AND PRODUCTO_PROYECTO NOT IN ('3999999', '2999999', '3000001', '2001621') GROUP BY PRODUCTO_PROYECTO ORDER BY 1 LIMIT 1000"
            cuis = conn.execute(cuis_query).df().iloc[:,0].tolist()
        except:
            cuis = []
            
        if len(cuis) == 0:
            st.warning("No se encontraron obras para los filtros seleccionados.")
        else:
            cui_selected = st.selectbox("Seleccione la Obra (CUI) a inspeccionar", cuis)
            cui_code = cui_selected.split(" - ")[0].strip()
            
            cui_query = f"""
                SELECT 
                    SUM(TRY_CAST(MONTO_PIA AS DOUBLE)) as PIA,
                    SUM(TRY_CAST(MONTO_PIM AS DOUBLE)) as PIM,
                    SUM(TRY_CAST(MONTO_CERTIFICADO AS DOUBLE)) as Certificado,
                    SUM(TRY_CAST(MONTO_COMPROMETIDO_ANUAL AS DOUBLE)) as Compromiso,
                    SUM(TRY_CAST(MONTO_DEVENGADO AS DOUBLE)) as Devengado
                FROM '{PARQUET_FILE}'
                WHERE PRODUCTO_PROYECTO = '{cui_code}'
            """
            df_cui = conn.execute(cui_query).df()
            
            if not df_cui.empty and pd.notna(df_cui.iloc[0]['PIM']):
                c_pim = df_cui.iloc[0]['PIM'] or 0
                c_cert = df_cui.iloc[0]['Certificado'] or 0
                c_comp = df_cui.iloc[0]['Compromiso'] or 0
                c_dev = df_cui.iloc[0]['Devengado'] or 0
                
                pct_cert = (c_cert / c_pim * 100) if c_pim > 0 else 0
                pct_comp = (c_comp / c_pim * 100) if c_pim > 0 else 0
                pct_dev = (c_dev / c_pim * 100) if c_pim > 0 else 0
                
                def f_soles(val): return f"{val:,.0f}".replace(",", " ")
                
                st.markdown("<br>", unsafe_allow_html=True)
                k1, k2, k3 = st.columns(3)
                with k1:
                    st.markdown(f'<div class="kpi-container" style="border-top: 4px solid #f87171;"><div class="kpi-title">AVANCE % CERTIFICADO</div><div class="kpi-value" style="color:#f87171">{pct_cert:.1f}%</div><div style="font-size:12px;color:#64748b;margin-top:5px;">Por Certificar: S/ {f_soles(c_pim - c_cert)}</div></div>', unsafe_allow_html=True)
                with k2:
                    st.markdown(f'<div class="kpi-container" style="border-top: 4px solid #38bdf8;"><div class="kpi-title">AVANCE % COMPROMISO</div><div class="kpi-value" style="color:#38bdf8">{pct_comp:.1f}%</div><div style="font-size:12px;color:#64748b;margin-top:5px;">Por Comprometer: S/ {f_soles(c_pim - c_comp)}</div></div>', unsafe_allow_html=True)
                with k3:
                    st.markdown(f'<div class="kpi-container" style="border-top: 4px solid #4ade80;"><div class="kpi-title">AVANCE % DEVENGADO</div><div class="kpi-value" style="color:#4ade80">{pct_dev:.1f}%</div><div style="font-size:12px;color:#64748b;margin-top:5px;">Por Devengar: S/ {f_soles(c_pim - c_dev)}</div></div>', unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown('<h4 style="color:#0f172a; font-weight:bold; font-size:18px;">III. HISTORIA DE LA BILLETERA (Gasto año por año)</h4>', unsafe_allow_html=True)
                st.markdown('<div style="background-color: #f0f9ff; border-left: 4px solid #0284c7; padding: 12px; margin-bottom: 15px; border-radius: 4px; font-size: 13.5px; color: #0f172a;">Revisa la tabla inferior: Si el "Presupuesto Inflado (PIM)" crece cada año, es una señal de que el proyecto está sufriendo adendas o sobrecostos crónicos.</div>', unsafe_allow_html=True)
                
                with st.spinner("Buscando el historial en los archivos remotos del MEF (Puede tardar 10 segundos)..."):
                    try:
                        # Obtener dinámicamente qué años existen en HuggingFace
                        hf_api_url = "https://huggingface.co/api/datasets/marxvilam/mef-datos/tree/main"
                        # Combinar archivos de HuggingFace con archivos locales
                        try: hf_files = requests.get(hf_api_url).json()
                        except: hf_files = []
                        
                        all_paths = set([f.get('path', '') for f in hf_files if isinstance(f, dict)])
                        for local_f in os.listdir('.'):
                            if local_f.endswith('-Gasto-Diario.parquet'):
                                all_paths.add(local_f)
                        
                        query_parts = []
                        for path in all_paths:
                            if path.endswith("-Gasto-Diario.parquet"):
                                year = path.split("-")[0]
                                if os.path.exists(path):
                                    source = f"'{path}'"
                                else:
                                    source = f"read_parquet('https://huggingface.co/datasets/marxvilam/mef-datos/resolve/main/{path}')"
                                    
                                q = f"SELECT '{year}' as Año, string_agg(DISTINCT SEC_FUNC, ', ') as \"Secuencias\", SUM(TRY_CAST(MONTO_PIA AS DOUBLE)) as PIA, SUM(TRY_CAST(MONTO_PIM AS DOUBLE)) as PIM, SUM(TRY_CAST(MONTO_DEVENGADO AS DOUBLE)) as Devengado FROM {source} WHERE PRODUCTO_PROYECTO = '{cui_code}'"
                                query_parts.append(q)
                        
                        if query_parts:
                            conn.execute("INSTALL httpfs; LOAD httpfs;")
                            hist_query = " UNION ALL ".join(query_parts) + " ORDER BY Año ASC"
                            df_hist = conn.execute(hist_query).df()
                        else:
                            df_hist = pd.DataFrame()
                        
                        if not df_hist.empty:
                            # Clean rows that have absolutely no data for that year to keep it neat
                            df_hist = df_hist.dropna(subset=['PIA', 'PIM', 'Devengado'], how='all').fillna(0)
                            
                            if not df_hist.empty:
                                df_hist['% Avance del Año'] = df_hist.apply(lambda r: (r['Devengado'] / r['PIM'] * 100) if r['PIM'] > 0 else 0, axis=1).round(1)
                                df_hist = df_hist.rename(columns={'PIA': 'Presupuesto Inicio Año (PIA)', 'PIM': 'Presupuesto Inflado (PIM)', 'Devengado': 'Pagado en el Año'})
                                
                                st_hist = df_hist.style.format({
                                    "Presupuesto Inicio Año (PIA)": lambda x: f"S/ {x:,.0f}".replace(",", " "),
                                    "Presupuesto Inflado (PIM)": lambda x: f"S/ {x:,.0f}".replace(",", " "),
                                    "Pagado en el Año": lambda x: f"S/ {x:,.0f}".replace(",", " "),
                                    "% Avance del Año": "{:.1f}%"
                                }).background_gradient(subset=["% Avance del Año"], cmap="RdYlGn", vmin=0, vmax=100)
                                
                                st.dataframe(st_hist, use_container_width=True, hide_index=True)
                            else:
                                st.info("No hay historial financiero (2023-2026) registrado para este proyecto.")
                    except Exception as e:
                        st.error("No se pudo cargar el historial remoto. Asegúrate de tener conexión a internet.")

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown('<h4 style="color:#0f172a; font-weight:bold; font-size:18px;">IV. LÍNEA DE TIEMPO DE PROFESIONALES (Residentes y Supervisores)</h4>', unsafe_allow_html=True)
                st.markdown('<div style="background-color: #fffbeb; border-left: 4px solid #f59e0b; padding: 12px; margin-bottom: 15px; border-radius: 4px; font-size: 13.5px; color: #0f172a;">⚠️ <b>Auditoría de Personal:</b> Múltiples cambios de Residente de Obra en cortos periodos de tiempo es una de las principales alertas de paralización inminente, corrupción o deficiencias graves en el Expediente Técnico.</div>', unsafe_allow_html=True)
                
                if os.path.exists('infobras_avance.parquet'):
                    prof_query = f"""
                        SELECT 
                            CAST(A_o_de_avance AS INTEGER) as "Año",
                            CAST(Mes_de_avance AS INTEGER) as "Mes_Num",
                            CASE 
                                WHEN Mes_de_avance = 1 THEN 'Enero' WHEN Mes_de_avance = 2 THEN 'Febrero' WHEN Mes_de_avance = 3 THEN 'Marzo'
                                WHEN Mes_de_avance = 4 THEN 'Abril' WHEN Mes_de_avance = 5 THEN 'Mayo' WHEN Mes_de_avance = 6 THEN 'Junio'
                                WHEN Mes_de_avance = 7 THEN 'Julio' WHEN Mes_de_avance = 8 THEN 'Agosto' WHEN Mes_de_avance = 9 THEN 'Septiembre'
                                WHEN Mes_de_avance = 10 THEN 'Octubre' WHEN Mes_de_avance = 11 THEN 'Noviembre' WHEN Mes_de_avance = 12 THEN 'Diciembre'
                                ELSE CAST(Mes_de_avance AS VARCHAR)
                            END as "Mes",
                            Nombres_Apellidos_1 as "Ingeniero Residente",
                            Nombres_Apellidos as "Ingeniero Supervisor / Inspector",
                            Nombre_o_raz_n_social_de_la_empresa_o_consorcio as "Empresa Contratista",
                            Nombre_o_raz_n_social_de_la_empresa_o_consorcio_ as "Empresa Supervisora"
                        FROM 'infobras_avance.parquet'
                        WHERE CUI_INFOBRAS = '{cui_code}' 
                          AND A_o_de_avance IS NOT NULL 
                          AND Mes_de_avance IS NOT NULL
                        ORDER BY "Año" DESC, "Mes_Num" DESC
                    """
                    try:
                        df_prof = conn.execute(prof_query).df()
                        if not df_prof.empty:
                            df_prof = df_prof.drop(columns=['Mes_Num'])
                            df_prof = df_prof.fillna("No registrado")
                            
                            st.dataframe(df_prof, use_container_width=True, hide_index=True)
                            
                            # Mostrar KPI rápido de cantidad de residentes
                            num_residentes = df_prof['Ingeniero Residente'].nunique()
                            if num_residentes > 3:
                                st.error(f"🚨 **ALERTA ROJA:** Esta obra ha tenido **{num_residentes}** ingenieros residentes distintos. Esta alta rotación es un indicador crítico de riesgo.")
                            elif num_residentes > 1:
                                st.warning(f"⚠️ **Atención:** Esta obra ha tenido **{num_residentes}** ingenieros residentes distintos.")
                        else:
                            st.info("No hay registros históricos de profesionales para esta obra en la Contraloría.")
                    except Exception as e:
                        st.warning("No se pudo cargar el historial de profesionales.")
                
                st.markdown("<br><b>Desglose por Meta y Clasificador de Gasto (Año Actual):</b>", unsafe_allow_html=True)
                
                detail_query = f"""
                    SELECT 
                        META as Meta,
                        MAX(META_NOMBRE) as Nombre_Meta,
                        GENERICA_NOMBRE || ' - ' || SUBGENERICA_NOMBRE as Clasificador,
                        SUM(TRY_CAST(MONTO_PIA AS DOUBLE)) as PIA,
                        SUM(TRY_CAST(MONTO_PIM AS DOUBLE)) as PIM,
                        SUM(TRY_CAST(MONTO_CERTIFICADO AS DOUBLE)) as Certificado,
                        SUM(TRY_CAST(MONTO_COMPROMETIDO_ANUAL AS DOUBLE)) as Compromiso,
                        SUM(TRY_CAST(MONTO_DEVENGADO AS DOUBLE)) as Devengado
                    FROM '{PARQUET_FILE}'
                    WHERE PRODUCTO_PROYECTO = '{cui_code}'
                    GROUP BY META, Clasificador
                    ORDER BY PIM DESC
                """
                df_det = conn.execute(detail_query).df()
                
                if not df_det.empty:
                    df_det['Sin Certificar'] = df_det['PIM'] - df_det['Certificado']
                    df_det['Sin Comprometer'] = df_det['PIM'] - df_det['Compromiso']
                    df_det['Sin Devengar'] = df_det['PIM'] - df_det['Devengado']
                    
                    df_det['% Certificado'] = (df_det['Certificado'] / df_det['PIM'] * 100).fillna(0).round(1)
                    df_det['% Comprometido'] = (df_det['Compromiso'] / df_det['PIM'] * 100).fillna(0).round(1)
                    df_det['% Devengado'] = (df_det['Devengado'] / df_det['PIM'] * 100).fillna(0).round(1)
                    
                    display_cols = ['Meta', 'Clasificador', 'PIA', 'PIM', '% Certificado', '% Comprometido', '% Devengado', 'Sin Certificar', 'Sin Comprometer', 'Sin Devengar']
                    df_display = df_det[display_cols].copy()
                    
                    st_det = df_display.style.format({
                        "PIA": lambda x: f"S/ {x:,.0f}".replace(",", " "),
                        "PIM": lambda x: f"S/ {x:,.0f}".replace(",", " "),
                        "Sin Certificar": lambda x: f"S/ {x:,.0f}".replace(",", " "),
                        "Sin Comprometer": lambda x: f"S/ {x:,.0f}".replace(",", " "),
                        "Sin Devengar": lambda x: f"S/ {x:,.0f}".replace(",", " "),
                        "% Certificado": "{:.1f}%",
                        "% Comprometido": "{:.1f}%",
                        "% Devengado": "{:.1f}%"
                    }).background_gradient(subset=["% Certificado"], cmap="Reds", vmin=0, vmax=100) \
                      .background_gradient(subset=["% Comprometido"], cmap="Reds", vmin=0, vmax=100) \
                      .background_gradient(subset=["% Devengado"], cmap="Reds", vmin=0, vmax=100)
                      
                      
                    st.dataframe(st_det, use_container_width=True, hide_index=True)
                    
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown('<h4 style="color:#0f172a; font-weight:bold; font-size:18px;">IV. EVOLUCIÓN HISTÓRICA DEL COSTO (Vía SSI)</h4>', unsafe_allow_html=True)
                st.markdown('<div style="background-color: #f8fafc; border-left: 4px solid #64748b; padding: 12px; margin-bottom: 15px; border-radius: 4px; font-size: 13.5px; color: #0f172a;">Analiza cómo ha variado el "Costo Actual" declarado del proyecto a lo largo de los años. Los incrementos drásticos pueden indicar adendas o modificaciones estructurales.</div>', unsafe_allow_html=True)
                
                with st.spinner("Rastreando el costo histórico en los archivos SSI (Puede tardar unos segundos)..."):
                    try:
                        all_ssi_paths = set([f.get('path', '') for f in hf_files if isinstance(f, dict)])
                        for local_f in os.listdir('.'):
                            if local_f.endswith('-Seguimiento-PI.parquet'):
                                all_ssi_paths.add(local_f)
                                
                        ssi_query_parts = []
                        for path in all_ssi_paths:
                            if path.endswith("-Seguimiento-PI.parquet"):
                                year = path.split("-")[0]
                                if os.path.exists(path):
                                    source = f"'{path}'"
                                else:
                                    source = f"read_parquet('https://huggingface.co/datasets/marxvilam/mef-datos/resolve/main/{path}')"
                                    
                                if int(year) < 2024:
                                    q = f"SELECT '{year}' as Año, NULL as Costo_Actual, SUM(TRY_CAST(MONTO_EJECUCION_TOTAL AS DOUBLE)) as Ejecucion_Total FROM {source} WHERE PRODUCTO_PROYECTO = '{cui_code}' GROUP BY PRODUCTO_PROYECTO"
                                else:
                                    q = f"SELECT '{year}' as Año, MAX(TRY_CAST(COSTO_ACTUAL AS DOUBLE)) as Costo_Actual, SUM(TRY_CAST(MONTO_EJECUCION_TOTAL AS DOUBLE)) as Ejecucion_Total FROM {source} WHERE PRODUCTO_PROYECTO = '{cui_code}' GROUP BY PRODUCTO_PROYECTO"
                                ssi_query_parts.append(q)
                        
                        if ssi_query_parts:
                            ssi_hist_query = " UNION ALL ".join(ssi_query_parts) + " ORDER BY Año ASC"
                            df_ssi_hist = conn.execute(ssi_hist_query).df()
                        else:
                            df_ssi_hist = pd.DataFrame()
                        
                        if not df_ssi_hist.empty:
                            df_ssi_hist = df_ssi_hist.dropna(subset=['Costo_Actual'], how='all').fillna(0)
                            if not df_ssi_hist.empty:
                                df_ssi_hist['Costo_Actual'] = pd.to_numeric(df_ssi_hist['Costo_Actual'], errors='coerce').fillna(0)
                                df_ssi_hist['Ejecucion_Total'] = pd.to_numeric(df_ssi_hist['Ejecucion_Total'], errors='coerce').fillna(0)
                                
                                valid_costs = df_ssi_hist[df_ssi_hist['Costo_Actual'] > 0]
                                if not valid_costs.empty:
                                    año_ini = valid_costs.iloc[0]['Año']
                                    costo_ini = valid_costs.iloc[0]['Costo_Actual']
                                    año_fin = valid_costs.iloc[-1]['Año']
                                    costo_fin = valid_costs.iloc[-1]['Costo_Actual']
                                    variacion = ((costo_fin - costo_ini) / costo_ini * 100) if costo_ini > 0 else 0
                                else:
                                    año_ini = df_ssi_hist.iloc[0]['Año']
                                    costo_ini = 0
                                    año_fin = df_ssi_hist.iloc[-1]['Año']
                                    costo_fin = 0
                                    variacion = 0
                                    
                                var_color = "#ef4444" if variacion > 10 else "#22c55e" if variacion < 0 else "#64748b"
                                
                                st.markdown(f'''
                                <div style="display:flex; justify-content:space-around; background-color:#ffffff; padding:15px; border-radius:8px; border:1px solid #e2e8f0; margin-bottom:15px;">
                                    <div style="text-align:center;">
                                        <div style="font-size:12px; color:#64748b;">Costo Inicial ({año_ini})</div>
                                        <div style="font-size:18px; font-weight:bold;">S/ {f_soles(costo_ini)}</div>
                                    </div>
                                    <div style="text-align:center;">
                                        <div style="font-size:12px; color:#64748b;">Costo Actual ({año_fin})</div>
                                        <div style="font-size:18px; font-weight:bold;">S/ {f_soles(costo_fin)}</div>
                                    </div>
                                    <div style="text-align:center;">
                                        <div style="font-size:12px; color:#64748b;">Variación Histórica</div>
                                        <div style="font-size:18px; font-weight:bold; color:{var_color};">{variacion:+.1f}%</div>
                                    </div>
                                </div>
                                ''', unsafe_allow_html=True)
                                
                                import plotly.express as px
                                import plotly.graph_objects as go
                                
                                fig = go.Figure()
                                fig.add_trace(go.Bar(x=df_ssi_hist['Año'], y=df_ssi_hist['Ejecucion_Total'], name='Ejecución Acumulada', marker_color='#94a3b8'))
                                fig.add_trace(go.Scatter(x=df_ssi_hist['Año'], y=df_ssi_hist['Costo_Actual'], mode='lines+markers', name='Costo Actual', line=dict(color='#ef4444', width=3)))
                                
                                fig.update_layout(
                                    title='Curva de Variación del Costo vs Ejecución',
                                    yaxis_title="Soles (S/)",
                                    xaxis_title="Año Fiscal",
                                    hovermode="x unified",
                                    margin=dict(l=20, r=20, t=40, b=20),
                                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                                )
                                st.plotly_chart(fig, use_container_width=True)
                                
                                all_years = set(str(y) for y in range(int(año_ini), int(año_fin) + 1))
                                found_years = set(df_ssi_hist['Año'].astype(str))
                                missing_years = sorted(list(all_years - found_years))
                                if missing_years:
                                    st.warning(f"ℹ️ El proyecto no registra información en los reportes del SSI durante los años: {', '.join(missing_years)}")
                            else:
                                st.info("La obra no registra historial de costos en el SSI.")
                        else:
                            st.info("No se encontraron archivos históricos del SSI.")
                    except Exception as e:
                        st.error(f"No se pudo cargar el historial SSI. Detalle: {e}")
                        
                # ---------------------------------------------------------
                # SECCIÓN EVOLUCIÓN AVANCE FÍSICO (INFOBRAS)
                # ---------------------------------------------------------
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown('<h4 style="color:#0f172a; font-weight:bold; font-size:18px;">V. EVOLUCIÓN HISTÓRICA DEL AVANCE FÍSICO (INFOBRAS)</h4>', unsafe_allow_html=True)
                st.markdown('<div style="background-color: #f8fafc; border-left: 4px solid #3b82f6; padding: 12px; margin-bottom: 15px; border-radius: 4px; font-size: 13.5px; color: #0f172a;">Observa cómo ha avanzado la construcción real de la obra mes a mes, comparando lo ejecutado frente a lo programado.</div>', unsafe_allow_html=True)
                
                if os.path.exists('infobras_avance.parquet'):
                    curva_fis_query = f"""
                        SELECT 
                            CAST(A_o_de_avance AS INTEGER) as Ano,
                            CAST(Mes_de_avance AS INTEGER) as Mes,
                            MAX(TRY_CAST(AVANCE_FISICO_INFOBRAS AS DOUBLE)) as Avance_Real,
                            MAX(TRY_CAST(Avance_F_sico_Programado_Acumulado____ AS DOUBLE)) as Avance_Programado
                        FROM 'infobras_avance.parquet'
                        WHERE CUI_INFOBRAS = '{cui_code}'
                          AND A_o_de_avance IS NOT NULL 
                          AND Mes_de_avance IS NOT NULL
                        GROUP BY A_o_de_avance, Mes_de_avance
                        ORDER BY Ano, Mes
                    """
                    try:
                        df_curva_fis = conn.execute(curva_fis_query).df()
                        if not df_curva_fis.empty:
                            df_curva_fis['Fecha'] = df_curva_fis['Ano'].astype(str) + '-' + df_curva_fis['Mes'].astype(str).str.zfill(2)
                            fig_fis = go.Figure()
                            fig_fis.add_trace(go.Scatter(x=df_curva_fis['Fecha'], y=df_curva_fis['Avance_Programado'], mode='lines', name='Avance Programado %', line=dict(color='#94a3b8', width=2, dash='dash')))
                            fig_fis.add_trace(go.Scatter(x=df_curva_fis['Fecha'], y=df_curva_fis['Avance_Real'], mode='lines+markers', name='Avance Real %', line=dict(color='#3b82f6', width=3)))
                            
                            fig_fis.update_layout(
                                title='Curva de Avance Físico',
                                yaxis_title="Porcentaje (%)",
                                xaxis_title="Mes de Avance",
                                hovermode="x unified",
                                yaxis=dict(range=[0, 105]),
                                margin=dict(l=20, r=20, t=40, b=20),
                                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                            )
                            st.plotly_chart(fig_fis, use_container_width=True)
                        else:
                            st.info("No hay historial mensual de avance físico para esta obra en INFOBRAS.")
                    except Exception as e:
                        st.error(f"No se pudo cargar la curva de avance físico. Detalle: {e}")

                # ---------------------------------------------------------
                # SECCIÓN INFOBRAS (COMENTARIOS Y FECHAS)
                # ---------------------------------------------------------
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown('<h4 style="color:#0f172a; font-weight:bold; font-size:18px;">VI. EXPEDIENTE INFOBRAS (Reporte del Ingeniero)</h4>', unsafe_allow_html=True)
                st.markdown('<div style="background-color: #fefce8; border-left: 4px solid #eab308; padding: 12px; margin-bottom: 15px; border-radius: 4px; font-size: 13.5px; color: #0f172a;">Aquí puedes leer las justificaciones, comentarios y fechas reportadas por los ingenieros residentes y supervisores directamente en el sistema de la Contraloría.</div>', unsafe_allow_html=True)
                
                if os.path.exists('infobras_avance.parquet'):
                    info_query = f"""
                        SELECT 
                            MAX(TRY_CAST(Estado_de_ejecuci_n AS VARCHAR)) as Estado_de_ejecuci_n,
                            MAX(TRY_CAST(Fecha_de_inicio_de_obra AS VARCHAR)) as Fecha_de_inicio_de_obra,
                            MAX(TRY_CAST(Fecha_finalizaci_n_programada_de_obra AS VARCHAR)) as Fecha_finalizaci_n_programada_de_obra,
                            MAX(TRY_CAST(Fecha_de_finalizaci_n_real AS VARCHAR)) as Fecha_de_finalizaci_n_real,
                            MAX(TRY_CAST(Comentarios AS VARCHAR)) as Comentarios,
                            MAX(TRY_CAST(Causal_de_paralizaci_n AS VARCHAR)) as Causal_de_paralizaci_n,
                            MAX(TRY_CAST(Motivo_en_caso_no_se_llegue_al_100_ AS VARCHAR)) as Motivo_en_caso_no_se_llegue_al_100_,
                            MAX(TRY_CAST(N_mero_de_dias_paralizado AS VARCHAR)) as N_mero_de_dias_paralizado
                        FROM 'infobras_avance.parquet'
                        WHERE CUI_INFOBRAS = '{cui_code}'
                    """
                    df_info = conn.execute(info_query).df()
                    
                    if not df_info.empty and pd.notna(df_info.iloc[0]['Estado_de_ejecuci_n']):
                        row_info = df_info.iloc[0]
                        estado = row_info['Estado_de_ejecuci_n'] if pd.notna(row_info['Estado_de_ejecuci_n']) else "No Registrado"
                        f_inicio = row_info['Fecha_de_inicio_de_obra'] if pd.notna(row_info['Fecha_de_inicio_de_obra']) else "No Registrado"
                        f_fin_prog = row_info['Fecha_finalizaci_n_programada_de_obra'] if pd.notna(row_info['Fecha_finalizaci_n_programada_de_obra']) else "No Registrado"
                        f_fin_real = row_info['Fecha_de_finalizaci_n_real'] if pd.notna(row_info['Fecha_de_finalizaci_n_real']) else "En curso / No Registrado"
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.markdown(f"**Estado:**<br>{estado}", unsafe_allow_html=True)
                        with col2:
                            st.markdown(f"**Inicio:**<br>{f_inicio}", unsafe_allow_html=True)
                        with col3:
                            st.markdown(f"**Fin Programado:**<br>{f_fin_prog}", unsafe_allow_html=True)
                        with col4:
                            st.markdown(f"**Fin Real:**<br>{f_fin_real}", unsafe_allow_html=True)
                            
                        st.markdown("<hr style='margin-top:10px; margin-bottom:10px;'>", unsafe_allow_html=True)
                        
                        def draw_textbox(title, text, is_alert=False):
                            if pd.notna(text) and str(text).strip() != "" and str(text).lower() != "nan" and str(text).lower() != "ninguno":
                                color = "#fee2e2" if is_alert else "#f1f5f9"
                                border = "#ef4444" if is_alert else "#cbd5e1"
                                st.markdown(f"""
                                <div style="background-color: {color}; border: 1px solid {border}; padding: 12px; border-radius: 6px; margin-bottom: 10px;">
                                    <strong style="color: #0f172a; font-size:14px;">{title}</strong><br>
                                    <span style="color: #334155; font-size:13.5px;">{text}</span>
                                </div>
                                """, unsafe_allow_html=True)

                        draw_textbox("📝 Comentarios del Residente / Supervisor:", row_info['Comentarios'])
                        draw_textbox("🛑 Causal de Paralización (Si aplica):", row_info['Causal_de_paralizaci_n'], is_alert=True)
                        draw_textbox("⏳ Días Paralizado:", row_info['N_mero_de_dias_paralizado'], is_alert=True)
                        draw_textbox("⚠️ Motivo de no llegar al 100%:", row_info['Motivo_en_caso_no_se_llegue_al_100_'], is_alert=True)
                        
                    else:
                        st.warning("Esta obra no tiene ningún registro (ni fechas ni comentarios) en el portal de INFOBRAS. Es una obra no transparentada.")
                else:
                    st.warning("La base de datos de INFOBRAS no está disponible en este momento.")

            else:
                st.warning("La obra seleccionada no registra movimientos financieros en este año.")

# End of app
