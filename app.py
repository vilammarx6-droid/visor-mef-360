import streamlit as st
import pandas as pd
pd.set_option("styler.render.max_elements", 2000000)
import plotly.express as px
import plotly.graph_objects as go
from data_processor import MEFDataProcessor
import os

st.set_page_config(page_title="Visor MEF 360 - AyniBrava", page_icon="👁️", layout="wide")

# Inicializar y cachear el procesador de datos para evitar reconexiones y lecturas costosas
@st.cache_resource(show_spinner=False)
def get_processor():
    # Cache thread-safe x50
    csv_path = r"C:\Users\marx_\Downloads\2026-Gasto-Diario.csv"
    parquet_path = "*Gasto-Diario.parquet"
    return MEFDataProcessor(csv_path, parquet_path)

processor = get_processor()

# Custom CSS for rich aesthetics
st.markdown("""
    <style>
    .metric-card {
        background-color: #1E1E1E;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        margin-bottom: 20px;
    }
    .metric-value {
        font-size: 2em;
        font-weight: bold;
        color: #4CAF50;
    }
    .metric-label {
        font-size: 1.1em;
        color: #B0BEC5;
    }
    /* Hace que las pestañas sean pegajosas (sticky) al hacer scroll hacia abajo */
    div[data-testid="stTabs"] > div:first-child {
        position: sticky;
        top: 0px;
        z-index: 999;
        background-color: white; /* Color de fondo de las pestañas */
        padding-top: 15px;
        padding-bottom: 10px;
        border-bottom: 1px solid #ddd;
    }
    </style>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR: FILTROS -----------------
st.sidebar.title("Visor MEF 360")
import os
if os.path.exists("logo_aynibrava.png"):
    st.sidebar.image("logo_aynibrava.png", width=150)
st.sidebar.markdown("<p style='text-align: center; color: #888; font-size: 14px; margin-bottom: 20px;'>Desarrollado por <b>AyniBrava</b></p>", unsafe_allow_html=True)
st.sidebar.markdown("---")
st.sidebar.header("Filtros Globales")

# Año Fiscal
anios_disponibles = processor.get_anios_disponibles()
anio_seleccionado = st.sidebar.selectbox("📅 Año Fiscal", anios_disponibles, index=0)

where_clauses = []
if anio_seleccionado:
    where_clauses.append(f"ANO_EJE = {anio_seleccionado}")
current_where = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

# Niveles de Gobierno
niveles = processor.get_filter_options("NIVEL_GOBIERNO_NOMBRE", " AND ".join(where_clauses))
sel_gobierno = st.sidebar.multiselect("Nivel de Gobierno", niveles)
if sel_gobierno:
    niv_str = ",".join([f"'{x}'" for x in sel_gobierno])
    where_clauses.append(f"NIVEL_GOBIERNO_NOMBRE IN ({niv_str})")

# Sector
sectores = processor.get_filter_options("SECTOR_NOMBRE", " AND ".join(where_clauses))
sel_sector = st.sidebar.multiselect("Sector", sectores)
if sel_sector:
    sec_str = ",".join([f"'{x}'" for x in sel_sector])
    where_clauses.append(f"SECTOR_NOMBRE IN ({sec_str})")

# Pliego
pliegos = processor.get_filter_options("PLIEGO_NOMBRE", " AND ".join(where_clauses))
sel_pliego = st.sidebar.multiselect("Pliego / Municipalidad", pliegos)
if sel_pliego:
    pli_str = ",".join([f"'{x}'" for x in sel_pliego])
    where_clauses.append(f"PLIEGO_NOMBRE IN ({pli_str})")

current_where = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

# Unidad Ejecutora
ejecs = processor.get_ejecutoras(current_where)
ejec_sel = st.sidebar.multiselect("Unidad Ejecutora (SEC_EJEC)", ejecs)
sel_ejecutora = []
if ejec_sel:
    sec_ejecs = [x.split(' - ')[0] for x in ejec_sel]
    sec_str = ",".join(sec_ejecs)
    where_clauses.append(f"SEC_EJEC IN ({sec_str})")
    sel_ejecutora = [x.split(' - ')[1] for x in ejec_sel]

current_where = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

# Meta / Secuencia Funcional
metas = processor.get_metas(current_where)
meta_sel = st.sidebar.multiselect("Meta (SEC_FUNC)", metas)
if meta_sel:
    sec_funcs = [x.split(' - ')[0] for x in meta_sel]
    func_str = ",".join(sec_funcs)
    where_clauses.append(f"SEC_FUNC IN ({func_str})")

# Categoria Presupuestal
cat_ppto = processor.get_filter_options("PROGRAMA_PPTO_NOMBRE", " AND ".join(where_clauses))
programa = st.sidebar.multiselect("Programa Presupuestal", cat_ppto)
if programa:
    prog_str = ",".join([f"'{x}'" for x in programa])
    where_clauses.append(f"PROGRAMA_PPTO_NOMBRE IN ({prog_str})")

# Función
funciones = processor.get_filter_options("FUNCION_NOMBRE", " AND ".join(where_clauses))
funcion = st.sidebar.multiselect("Función", funciones)
if funcion:
    func_str = ",".join([f"'{x}'" for x in funcion])
    where_clauses.append(f"FUNCION_NOMBRE IN ({func_str})")

# Rubro
rubros = processor.get_filter_options("RUBRO_NOMBRE", " AND ".join(where_clauses))
rubro = st.sidebar.multiselect("Fuente de Financiamiento (Rubro)", rubros)
if rubro:
    rub_str = ",".join([f"'{x}'" for x in rubro])
    where_clauses.append(f"RUBRO_NOMBRE IN ({rub_str})")

# Construct final WHERE clauses
final_where = "WHERE " + " AND ".join(where_clauses) if where_clauses else "WHERE 1=1"

# Para la Ficha Histórica, no filtramos por Año para poder ver toda la línea de vida del proyecto
where_sin_anio = [c for c in where_clauses if not c.startswith("ANO_EJE")]
final_where_sin_anio = "WHERE " + " AND ".join(where_sin_anio) if where_sin_anio else "WHERE 1=1"

# ----------------- MAIN HEADER -------------------------------
col_logo, col_title = st.columns([1, 8])
with col_logo:
    import os
    if os.path.exists("logo_aynibrava.png"):
        st.image("logo_aynibrava.png", use_container_width=True)
    else:
        st.markdown("<h1 style='text-align: right; font-size: 3em; margin: 0;'>👁️</h1>", unsafe_allow_html=True)
with col_title:
    st.markdown("<h1 style='color: #1565c0; margin-bottom: 0; font-family: Arial, sans-serif; font-size: 2.5em;'>Visor MEF 360</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #555; font-size: 18px; margin-top: 0;'>Desarrollado por <b>AyniBrava</b></p>", unsafe_allow_html=True)

# ----------------- ENTIDAD CONSULTADA -----------------
entidad_mostrar = "Todas las Entidades (Nivel Global)"
if sel_ejecutora:
    entidad_mostrar = f"{sel_ejecutora[0]} (Unidad Ejecutora)"
elif sel_pliego:
    entidad_mostrar = f"{sel_pliego[0]} (Pliego)"
elif sel_sector:
    entidad_mostrar = f"Sector: {sel_sector[0]}"
elif sel_gobierno:
    entidad_mostrar = f"{sel_gobierno[0]} (Nivel de Gobierno)"

st.markdown(f"""
<div style='background-color: #e3f2fd; padding: 15px; border-radius: 10px; border-left: 5px solid #1976d2; margin-bottom: 20px; text-align: center;'>
    <h2 style='color: #1565c0; margin: 0;'>🏢 Entidad Consultada: {entidad_mostrar} | 📅 Año Fiscal: {anio_seleccionado}</h2>
</div>
""", unsafe_allow_html=True)

st.markdown("<hr style='margin-top: 5px; margin-bottom: 20px;'>", unsafe_allow_html=True)

# ----------------- TABS -> SIDEBAR RADIO -----------------
st.sidebar.markdown("<hr>", unsafe_allow_html=True)
st.sidebar.markdown("<h3 style='color: #1565c0; margin-bottom: 0;'>🧭 Módulos de Análisis</h3>", unsafe_allow_html=True)
modulo_seleccionado = st.sidebar.radio("Navegación:", [
    "📊 1. Resumen Ejecutivo",
    "📈 2. Indicadores Clave (KPIs)",
    "⚖️ 3. Evaluación de Gestión",
    "🏗️ 4. Avance de Obras",
    "🏆 5. Ranking de Obras",
    "📅 6. Curva de Evolución",
    "🔮 7. Proyección de Cierre",
    "🚨 8. Alertas de Riesgo",
    "🧭 9. Explorador Total",
    "🔍 10. Ficha SSI"
])

import os
st.sidebar.markdown("<hr>", unsafe_allow_html=True)
if os.path.exists("yape.png"):
    st.sidebar.markdown("<div style='text-align:center; background:#00cfbf; color:white; padding:5px; border-radius:5px 5px 0 0;'><b>Apoya el Proyecto</b></div>", unsafe_allow_html=True)
    st.sidebar.image("yape.png", use_container_width=True)
    st.sidebar.markdown("<div style='text-align:center; background:#1a1a2e; color:white; padding:5px; border-radius:0 0 5px 5px;'>Yape: <b>963 301 301</b></div>", unsafe_allow_html=True)
else:
    st.sidebar.info("💡 Sugerencia: Guarda la imagen de tu QR como 'yape.png' en esta carpeta para que aparezca aquí automáticamente.")

def format_millones(valor):
    if pd.isna(valor): return "0.00 M"
    return f"{valor / 1000000:.2f} M"

# --- TAB 1: Resumen Ejecutivo ---
if modulo_seleccionado == "📊 1. Resumen Ejecutivo":
    st.markdown("<h2 style='text-align: center; font-family: Arial, sans-serif;'>Visión Ejecutiva Integral</h2>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background-color: #e3f2fd; padding: 15px; border-radius: 8px; border-left: 5px solid #1976d2; margin-bottom: 20px;">
        <h4 style="color: #1565c0; margin-top: 0;">💡 Guía Rápida para Entender el Gasto Público (Flujo de Ejecución)</h4>
        <p style="margin-bottom: 5px; color: #333;">Para entender estos gráficos de forma sencilla, imagina que tienes un proyecto personal:</p>
        <ul style="margin-bottom: 0; color: #333;">
            <li><b>1. Presupuesto (PIM):</b> Es tu <i>billetera</i> para el año. La plata total que tienes disponible.</li>
            <li><b>2. Certificado:</b> Es <i>separar o guardar</i> un dinero en un sobre porque ya decidiste hacer una compra (para que nadie más lo gaste).</li>
            <li><b>3. Comprometido (Verde):</b> Es cuando ya <i>firmaste el contrato</i> con el proveedor. ¡El dinero ya está comprometido legalmente!</li>
            <li><b>4. Gasto Real (Devengado - Rojo):</b> Ocurre cuando el servicio se terminó y das la <i>conformidad</i> de que el trabajo está hecho y listo para pagar. <b>Este es el indicador más importante que mide el avance real de la obra o servicio.</b></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    resumen = processor.get_kpis_resumen(final_where)
    pim_total = resumen['PIM']
    dev_total = resumen['Devengado']
    pct_ejec = (dev_total / pim_total * 100) if pim_total > 0 else 0
    
    df_evo_acum = processor.get_evolucion_acumulada(final_where, pim_total)
    
    if not df_evo_acum.empty:
        # Tarjetas de KPI gigantes tipo imagen
        colKPI1, colKPI2 = st.columns(2)
        with colKPI1:
            st.markdown(f"""
            <div style="background-color: {'#d32f2f' if pct_ejec < 80 else '#388e3c'}; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 10px; border: 2px solid {'#b71c1c' if pct_ejec < 80 else '#2e7d32'};">
                <h4 style="color: white; margin:0; text-transform: uppercase; font-family: Arial, sans-serif;">Porcentaje de Ejecución (Gasto Real) ACTUAL</h4>
                <h1 style="color: white; font-size: 4em; margin:0; font-weight: 900; font-family: Arial, sans-serif;">{pct_ejec:.2f} %</h1>
            </div>
            """, unsafe_allow_html=True)
        with colKPI2:
            st.markdown(f"""
            <div style="background-color: #f5f5f5; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 10px; border: 2px solid #ddd;">
                <h4 style="color: #333; margin:0; text-transform: uppercase; font-family: Arial, sans-serif;">Monto Total de Ejecución ACTUAL (Devengado)</h4>
                <h1 style="color: #333; font-size: 3.5em; margin:0; font-weight: bold; font-family: Arial, sans-serif;">S/ {dev_total:,.2f}</h1>
            </div>
            """, unsafe_allow_html=True)
            
        # Texto Explicativo Dinámico
        mes_actual = df_evo_acum['Mes_Nombre'].iloc[-1]
        st.markdown(f"""
        <div style="background-color: white; padding: 15px; border-radius: 5px; text-align: center; border: 1px solid #ccc; margin-bottom: 20px;">
            <h3 style="color: #444; margin:0; font-family: Arial, sans-serif;">Al cierre del mes de {mes_actual}, la ejecución real de tu billetera alcanza el <b style="color: {'#d32f2f' if pct_ejec < 80 else '#388e3c'};">{pct_ejec:.2f}%</b> del total del Presupuesto (PIM).</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Gráficos
        st.markdown("<h4 style='text-align: center; color: #FFF; margin-top: 30px;'>EVOLUCIÓN MENSUAL DE DEVENGADO POR MES</h4>", unsafe_allow_html=True)
        
        fig_line = px.line(df_evo_acum, x='Mes_Nombre', y='Devengado', text='Devengado', markers=True)
        fig_line.update_traces(textposition="top center", texttemplate="S/ %{y:,.0f}", line=dict(width=4, color='#2196F3'), marker=dict(size=10, color='white', line=dict(color='#2196F3', width=2)))
        fig_line.update_layout(template="plotly_dark", xaxis_title="", yaxis_title="S/", height=400)
        st.plotly_chart(fig_line, use_container_width=True)
        
        st.markdown("<h4 style='text-align: center; color: #FFF; margin-top: 30px;'>% COMPROMETIDO ACUMULADO vs % EJECUCIÓN ACUMULADA</h4>", unsafe_allow_html=True)
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            x=df_evo_acum['Mes_Nombre'], 
            y=df_evo_acum['pct_Comp_Acumulado'], 
            name='% Comprometido (Verde)', 
            marker_color='#388e3c',
            text=df_evo_acum['pct_Comp_Acumulado'].apply(lambda x: f"{x:.2f}%"),
            textposition='auto',
            textfont=dict(color='white', weight='bold')
        ))
        fig_bar.add_trace(go.Bar(
            x=df_evo_acum['Mes_Nombre'], 
            y=df_evo_acum['pct_Dev_Acumulado'], 
            name='% Ejecución (Rojo)', 
            marker_color='#d32f2f',
            text=df_evo_acum['pct_Dev_Acumulado'].apply(lambda x: f"{x:.2f}%"),
            textposition='auto',
            textfont=dict(color='white', weight='bold')
        ))
        fig_bar.update_layout(barmode='group', template="plotly_dark", height=450, xaxis_title="", yaxis_title="%")
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("No hay datos de ejecución para mostrar el Dashboard Ejecutivo.")

# --- TAB 2: KPIs de Eficiencia ---
if modulo_seleccionado == "📈 2. Indicadores Clave (KPIs)":
    st.header("Indicadores Clave de Desempeño (KPIs) del Gasto")
    st.info("💡 **¿Por qué existe esta pestaña?** Muestra el resumen global de los montos totales (desde la asignación inicial PIA hasta lo pagado final Girado) para que evalúes la eficiencia general del gasto con una vista panorámica.")
    
    resumen = processor.get_kpis_resumen(final_where)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div style="background-color: #37474f; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 10px;">
            <h5 style="color: #b0bec5; margin:0; text-transform: uppercase;">PIA (Presupuesto Inicial)</h5>
            <h3 style="color: white; margin:0;">S/ {resumen['PIA']:,.2f}</h3>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style="background-color: #263238; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 10px;">
            <h5 style="color: #b0bec5; margin:0; text-transform: uppercase;">PIM (Presupuesto Actual modificado)</h5>
            <h3 style="color: white; margin:0;">S/ {resumen['PIM']:,.2f}</h3>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div style="background-color: #37474f; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 10px;">
            <h5 style="color: #b0bec5; margin:0; text-transform: uppercase;">Certificado (Dinero Reservado)</h5>
            <h3 style="color: white; margin:0;">S/ {resumen['Certificado']:,.2f}</h3>
        </div>
        """, unsafe_allow_html=True)

    col4, col5, col6 = st.columns(3)
    with col4:
        st.markdown(f"""
        <div style="background-color: #2e7d32; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 10px;">
            <h5 style="color: #a5d6a7; margin:0; text-transform: uppercase;">Comprometido (Contratos)</h5>
            <h3 style="color: white; margin:0;">S/ {resumen['Compromiso_Anual']:,.2f}</h3>
        </div>
        """, unsafe_allow_html=True)
    with col5:
        st.markdown(f"""
        <div style="background-color: #c62828; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 10px;">
            <h5 style="color: #ffcdd2; margin:0; text-transform: uppercase;">Devengado (Gasto Realizado)</h5>
            <h3 style="color: white; margin:0;">S/ {resumen['Devengado']:,.2f}</h3>
        </div>
        """, unsafe_allow_html=True)
    with col6:
        st.markdown(f"""
        <div style="background-color: #1565c0; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 10px;">
            <h5 style="color: #bbdefb; margin:0; text-transform: uppercase;">Girado (Pagado al Proveedor)</h5>
            <h3 style="color: white; margin:0;">S/ {resumen['Girado']:,.2f}</h3>
        </div>
        """, unsafe_allow_html=True)

    kpi_ieg = processor.get_kpi_1_ieg(final_where)
    kpi_ieg_cap = processor.get_kpi_2_ieg_cap(final_where)
    kpi_iopr = processor.get_kpi_3_iopr(final_where)
    kpi_cert_comp, kpi_comp_dev = processor.get_kpi_4_idg(final_where)
    
    st.markdown("---")
    
    colA, colB, colC = st.columns(3)
    
    with colA:
        st.markdown(f"""
        <div style="background-color: #1e1e1e; padding: 20px; border-radius: 10px; border-top: 5px solid #4CAF50; margin-bottom: 10px;">
            <h4 style="color: #fff; margin-top: 0; margin-bottom: 5px; font-family: Arial, sans-serif;">KPI 1: Avance General</h4>
            <h1 style="color: #4CAF50; margin: 0; font-family: Arial, sans-serif;">{kpi_ieg:.1f}%</h1>
            <p style="color: #aaa; font-size: 14px; margin-top: 10px; line-height: 1.3;"><b>¿Qué significa?</b> Es la velocidad general del gasto de la entidad. Mide cuánto del total de tu billetera (PIM) ya gastaste de manera real (Devengado).</p>
        </div>
        """, unsafe_allow_html=True)
        with st.expander("🔍 Ver detalle por Unidad Ejecutora"):
            df_k1 = processor.get_kpi_breakdown(final_where, 'ieg')
            if not df_k1.empty:
                st.dataframe(df_k1.style.format({'PIM': '{:,.2f}', 'Devengado': '{:,.2f}', 'KPI_Pct': '{:.1f}%'}).background_gradient(subset=['KPI_Pct'], cmap='RdYlGn'), hide_index=True)

    with colB:
        st.markdown(f"""
        <div style="background-color: #1e1e1e; padding: 20px; border-radius: 10px; border-top: 5px solid #4CAF50; margin-bottom: 10px;">
            <h4 style="color: #fff; margin-top: 0; margin-bottom: 5px; font-family: Arial, sans-serif;">KPI 2: Avance en Obras</h4>
            <h1 style="color: #4CAF50; margin: 0; font-family: Arial, sans-serif;">{kpi_ieg_cap:.1f}%</h1>
            <p style="color: #aaa; font-size: 14px; margin-top: 10px; line-height: 1.3;"><b>¿Qué significa?</b> Mide si estás avanzando en construir obras reales. Solo toma en cuenta el dinero para Proyectos de Inversión.</p>
        </div>
        """, unsafe_allow_html=True)
        with st.expander("🔍 Ver detalle por Unidad Ejecutora"):
            df_k2 = processor.get_kpi_breakdown(final_where, 'ieg_cap')
            if not df_k2.empty:
                st.dataframe(df_k2.style.format({'PIM_Inversiones': '{:,.2f}', 'Devengado_Inversiones': '{:,.2f}', 'KPI_Pct': '{:.1f}%'}).background_gradient(subset=['KPI_Pct'], cmap='RdYlGn'), hide_index=True)

    with colC:
        st.markdown(f"""
        <div style="background-color: #1e1e1e; padding: 20px; border-radius: 10px; border-top: 5px solid #9C27B0; margin-bottom: 10px;">
            <h4 style="color: #fff; margin-top: 0; margin-bottom: 5px; font-family: Arial, sans-serif;">KPI 3: Calidad del Gasto</h4>
            <h1 style="color: #9C27B0; margin: 0; font-family: Arial, sans-serif;">{kpi_iopr:.1f}%</h1>
            <p style="color: #aaa; font-size: 14px; margin-top: 10px; line-height: 1.3;"><b>¿Qué significa?</b> Mide si tu gasto está resolviendo problemas. ¿Cuánto dinero fue a Programas Estratégicos (PpR) versus Gasto Administrativo?</p>
        </div>
        """, unsafe_allow_html=True)
        with st.expander("🔍 Ver detalle por Unidad Ejecutora"):
            df_k3 = processor.get_kpi_breakdown(final_where, 'iopr')
            if not df_k3.empty:
                st.dataframe(df_k3.style.format({'Gasto_Total': '{:,.2f}', 'Gasto_Resultados': '{:,.2f}', 'KPI_Pct': '{:.1f}%'}).background_gradient(subset=['KPI_Pct'], cmap='Purples'), hide_index=True)

    colD, colE = st.columns(2)
    with colD:
        st.markdown(f"""
        <div style="background-color: #1e1e1e; padding: 20px; border-radius: 10px; border-top: 5px solid #FF9800; margin-bottom: 10px;">
            <h4 style="color: #fff; margin-top: 0; margin-bottom: 5px; font-family: Arial, sans-serif;">KPI 4A: Velocidad Logística</h4>
            <h1 style="color: #FF9800; margin: 0; font-family: Arial, sans-serif;">{kpi_cert_comp:.1f}%</h1>
            <p style="color: #aaa; font-size: 14px; margin-top: 10px; line-height: 1.3;"><b>¿Qué significa?</b> De la plata que ya reservaste, ¿cuánto ya tiene contrato firmado? Si el número es bajo, tu área de Logística está lenta comprando.</p>
        </div>
        """, unsafe_allow_html=True)
        with st.expander("🔍 Ver detalle por Unidad Ejecutora"):
            df_k4a = processor.get_kpi_breakdown(final_where, 'logistica')
            if not df_k4a.empty:
                st.dataframe(df_k4a.style.format({'Certificado': '{:,.2f}', 'Compromiso': '{:,.2f}', 'KPI_Pct': '{:.1f}%'}).background_gradient(subset=['KPI_Pct'], cmap='Oranges'), hide_index=True)

    with colE:
        st.markdown(f"""
        <div style="background-color: #1e1e1e; padding: 20px; border-radius: 10px; border-top: 5px solid #03A9F4; margin-bottom: 10px;">
            <h4 style="color: #fff; margin-top: 0; margin-bottom: 5px; font-family: Arial, sans-serif;">KPI 4B: Eficacia de Contratistas</h4>
            <h1 style="color: #03A9F4; margin: 0; font-family: Arial, sans-serif;">{kpi_comp_dev:.1f}%</h1>
            <p style="color: #aaa; font-size: 14px; margin-top: 10px; line-height: 1.3;"><b>¿Qué significa?</b> De los contratos que ya firmaste, ¿cuánto trabajo ya entregaron y se pagó? Si es bajo, los proveedores o contratistas están retrasados con la obra.</p>
        </div>
        """, unsafe_allow_html=True)
        with st.expander("🔍 Ver detalle por Unidad Ejecutora"):
            df_k4b = processor.get_kpi_breakdown(final_where, 'ejecutiva')
            if not df_k4b.empty:
                st.dataframe(df_k4b.style.format({'Compromiso': '{:,.2f}', 'Devengado': '{:,.2f}', 'KPI_Pct': '{:.1f}%'}).background_gradient(subset=['KPI_Pct'], cmap='Blues'), hide_index=True)

# --- TAB 4: Avance de Obras (Proyectos) ---
if modulo_seleccionado == "🏗️ 4. Avance de Obras":
    st.header("Avance Presupuestal por Proyecto de Inversión")
    st.info("💡 **¿Por qué existe esta pestaña?** Aquí puedes ver el avance individual de cada obra o proyecto de inversión. Busca tu proyecto por CUI y mira si está paralizado (rojo) o avanzando (verde).")
    df_proy = processor.get_avance_proyectos(final_where)
    if not df_proy.empty:
        df_proy['% Devengado'] = (df_proy['Devengado'] / df_proy['PIM'] * 100).fillna(0)
        df_proy['Proyecto_Full'] = df_proy['CUI'].astype(str) + ' - ' + df_proy['Proyecto'].astype(str)
        
        busqueda_tab4 = st.text_input("🔍 Buscar Proyecto por CUI o palabra clave (ej. 'colegio', '2489312'):", key="search_tab4").strip().lower()
        
        if busqueda_tab4:
            df_mostrar = df_proy[df_proy['Proyecto_Full'].str.lower().str.contains(busqueda_tab4)]
            st.subheader(f"Resultados de búsqueda: '{busqueda_tab4}'")
        else:
            df_mostrar = df_proy
            
        st.dataframe(
            df_mostrar[['CUI', 'Proyecto', 'PIA', 'PIM', 'Certificado', 'Compromiso_Anual', 'Devengado', '% Devengado']].style.background_gradient(subset=['% Devengado'], cmap='RdYlGn', vmin=0, vmax=100)
            .format({'PIA': "{:,.2f}", 'PIM': "{:,.2f}", 'Certificado': "{:,.2f}", 'Compromiso_Anual': "{:,.2f}", 'Devengado': "{:,.2f}", '% Devengado': "{:.1f}%"}),
            use_container_width=True, height=500
        )
    else:
        st.info("No hay proyectos de inversión con PIM en esta selección.")

# --- TAB 5: Ranking de Proyectos ---
if modulo_seleccionado == "🏆 5. Ranking de Obras":
    st.header("Ranking de Obras (Podio de Inversiones)")
    st.info("💡 **¿Para qué sirve?** Arma un podio automático ordenando todos tus proyectos de inversión desde los más avanzados (Verde) hasta los más estancados (Rojo), para saber a qué ingenieros o residentes debes exigirles avance.")
    if 'df_proy' in locals() and not df_proy.empty:
        busqueda_tab5 = st.text_input("🔍 Buscar Proyecto por CUI o palabra clave:", key="search_tab5").strip().lower()
        df_ranking_proy = df_proy.sort_values(by='% Devengado', ascending=False)
        
        if busqueda_tab5:
            df_ranking_proy = df_ranking_proy[
                df_ranking_proy['CUI'].astype(str).str.contains(busqueda_tab5) | 
                df_ranking_proy['Proyecto'].str.lower().str.contains(busqueda_tab5)
            ]
            
        st.dataframe(
            df_ranking_proy[['CUI', 'Proyecto', 'PIM', 'Certificado', 'Devengado', '% Devengado']]
            .style.background_gradient(subset=['% Devengado'], cmap='RdYlGn', vmin=0, vmax=100)
            .format({'PIM': "{:,.2f}", 'Certificado': "{:,.2f}", 'Devengado': "{:,.2f}", '% Devengado': "{:.1f}%"}),
            use_container_width=True, height=600
        )
    else:
        st.info("No hay proyectos de inversión con PIM en esta selección para generar un ranking.")

# --- TAB 6: Evolución Mensual ---
if modulo_seleccionado == "📅 6. Curva de Evolución":
    st.header("Evolución Temporal del Gasto (Curvas S)")
    st.info("💡 **¿Por qué existe esta pestaña?** Muestra cómo ha avanzado el gasto mes a mes. Es vital para identificar si el gasto está estancado o si hay meses 'muertos' donde no se hizo nada.")
    df_evo = processor.get_curva_evolucion(final_where)
    if not df_evo.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_evo['Mes'], y=df_evo['Certificado'], mode='lines+markers', name='Certificado', line=dict(color='blue')))
        fig.add_trace(go.Scatter(x=df_evo['Mes'], y=df_evo['Compromiso_Anual'], mode='lines+markers', name='Compromiso Anual', line=dict(color='orange')))
        fig.add_trace(go.Scatter(x=df_evo['Mes'], y=df_evo['Devengado'], mode='lines+markers', name='Devengado', line=dict(color='green', width=3)))
        
        fig.update_layout(title="Acumulado Mensual de la Ejecución", xaxis_title="Mes (1 al 12)", yaxis_title="Monto (S/)", template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos para mostrar la curva mensual.")

# --- TAB 7: Proyecciones ---
if modulo_seleccionado == "🔮 7. Proyección de Cierre":
    st.header("Proyecciones de Gasto a Cierre de Año (Run Rate)")
    st.info("💡 **¿Por qué existe esta pestaña?** Calcula la 'velocidad' matemática a la que estás gastando actualmente para pronosticar con cuánto dinero llegarás a fin de año si no aceleras el ritmo.")
    df_proy_cierre = processor.get_proyecciones(final_where)
    if not df_proy_cierre.empty:
        st.dataframe(
            df_proy_cierre.style.format({
                'PIM': "{:,.2f}", 'Devengado_Actual': "{:,.2f}", 'RGM (Run Rate)': "{:,.2f}", 
                'Proyección_Cierre': "{:,.2f}", '%_Proyectado_Cierre': "{:.1f}%"
            }),
            use_container_width=True
        )
        
        fig2 = px.bar(df_proy_cierre, x='Categoria', y='%_Proyectado_Cierre', 
                     title="Proyección de Ejecución al Cierre de Año por Categoría de Gasto (%)",
                     color='%_Proyectado_Cierre', color_continuous_scale='RdYlGn', range_color=[0, 100])
        fig2.update_layout(template="plotly_dark")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No hay datos de proyección.")

# --- TAB 8: Alertas Spillover ---
if modulo_seleccionado == "🚨 8. Alertas de Riesgo":
    st.header("Alertas Tempranas de Saldos de Balance (Spillovers)")
    st.write("Evalúa los proyectos para identificar riesgo de que los recursos pasen al próximo año sin ejecutarse.")
    
    df_spill = processor.get_spillover_alerts(final_where)
    if not df_spill.empty:
        # Lógica simplificada de Spillovers (Ej: si en mes > 9 (octubre) el cert es 0 o comp < 40%)
        # Para propósitos de este dashboard, evaluaremos el estado actual.
        def evaluar_riesgo(row):
            if row['PIM'] == 0: return "Sin PIM"
            comp_pct = (row['Compromiso'] / row['PIM']) * 100
            dev_pct = (row['Devengado'] / row['PIM']) * 100
            
            if row['Certificado'] == 0:
                return "🔴 ALTO RIESGO (0% Certificado)"
            elif comp_pct < 40:
                return "🟠 RIESGO MEDIO (Compromiso Bajo)"
            elif dev_pct < 70:
                return "🟡 RIESGO PARCIAL (Lento Devengado)"
            else:
                return "🟢 EJECUCIÓN SEGURA"
                
        df_spill['Riesgo Spillover'] = df_spill.apply(evaluar_riesgo, axis=1)
        
        st.dataframe(
            df_spill[['Proyecto', 'PIM', 'Certificado', 'Compromiso', 'Devengado', 'Riesgo Spillover']]
            .style.format({'PIM': "{:,.2f}", 'Certificado': "{:,.2f}", 'Compromiso': "{:,.2f}", 'Devengado': "{:,.2f}"}),
            use_container_width=True, height=500
        )
    else:
        st.info("No hay proyectos para evaluar.")

# --- TAB 3: Dictamen de Gestión ---
if modulo_seleccionado == "⚖️ 3. Evaluación de Gestión":
    st.header("Evaluación Integral de Gestión Presupuestal")
    st.info("""
    💡 **¿Qué es esta pestaña y quién define estas reglas?**  
    Es un sistema de calificación **automática y objetiva** basado en las directivas de evaluación presupuestal del Ministerio de Economía y Finanzas (MEF) y lineamientos de SERVIR.  
    No solo mide *cuánto* se gasta, sino **CÓMO** se gasta la plata del Estado.
    """)
    
    kpi_iced = processor.get_kpi_5_iced(final_where)
    kpi_iv_pim = processor.get_kpi_6_iv_pim(final_where)
    kpi_auto = processor.get_kpi_7_autonomia(final_where)
    
    # KPIs from Fase 2 needed here
    kpi_ieg = processor.get_kpi_1_ieg(final_where)
    kpi_ieg_cap = processor.get_kpi_2_ieg_cap(final_where)
    kpi_iopr = processor.get_kpi_3_iopr(final_where)
    
    # Regla 1: Calidad sobre burocracia (IEG_cap > 70%)
    r1_pass = kpi_ieg_cap > 70
    # Regla 2: Constancia temporal (ICED < 20%)
    r2_pass = kpi_iced < 20
    # Regla 3: Gasto con Orientación Social (IOPR > 60%)
    r3_pass = kpi_iopr > 60
    
    # Extraemos los datos crudos para mostrar las fórmulas matemáticas
    raw_dict = processor.get_dictamen_data(final_where)
    
    dictamen = "✅ GESTIÓN EXCELENTE" if (r1_pass and r2_pass and r3_pass) else "❌ NECESITA MEJORAR (DEFICIENTE)"
    
    st.markdown(f"<h2 style='text-align: center; color: {'#4CAF50' if dictamen.startswith('✅') else '#F44336'}; background-color: {'#e8f5e9' if dictamen.startswith('✅') else '#ffebee'}; padding: 20px; border-radius: 10px;'>{dictamen}</h2>", unsafe_allow_html=True)
    
    colD, colE = st.columns(2)
    with colD:
        st.write("### Los 3 Criterios de Aprobación del MEF:")
        st.markdown(f"""
        <ul style="list-style: none; padding-left: 0;">
            <li style="margin-bottom: 20px;">
                <b style="color: {'green' if r1_pass else 'red'};">{'✅' if r1_pass else '❌'} 1. Avance Mínimo en Obras (Más de 70%)</b><br>
                Tu nivel actual: <b style="font-size: 1.2em;">{kpi_ieg_cap:.1f}%</b>.<br>
                <i>Por qué se mide:</i> El Estado exige que el presupuesto destinado a proyectos de inversión pública no se quede estancado. Si es menor a 70% al cierre, se considera ineficiente.<br>
                <code style="color:#1565c0; background:#e3f2fd; padding:3px 6px; border-radius:4px;">Fórmula: (Devengado Inversiones / PIM Inversiones) * 100</code><br>
                <span style="font-size: 0.9em; color: gray;">Datos usados: S/ {raw_dict['Dev_Cap']:,.2f} / S/ {raw_dict['PIM_Cap']:,.2f}</span>
            </li>
            <li style="margin-bottom: 20px;">
                <b style="color: {'green' if r2_pass else 'red'};">{'✅' if r2_pass else '❌'} 2. Cero "Síndrome de Diciembre" (Menor a 20%)</b><br>
                Tu nivel actual: <b style="font-size: 1.2em;">{kpi_iced:.1f}%</b>.<br>
                <i>Por qué se mide:</i> El MEF penaliza a las entidades que gastan todo el dinero de golpe a última hora en Diciembre (ICED). Un buen gestor planifica progresivamente.<br>
                <code style="color:#e65100; background:#fff3e0; padding:3px 6px; border-radius:4px;">Fórmula: (Devengado Diciembre / Devengado Total) * 100</code><br>
                <span style="font-size: 0.9em; color: gray;">Datos usados: S/ {raw_dict['Dev_Dic']:,.2f} / S/ {raw_dict['Dev_Total']:,.2f}</span>
            </li>
            <li style="margin-bottom: 20px;">
                <b style="color: {'green' if r3_pass else 'red'};">{'✅' if r3_pass else '❌'} 3. Orientación a Resultados (Más de 60%)</b><br>
                Tu nivel actual: <b style="font-size: 1.2em;">{kpi_iopr:.1f}%</b>.<br>
                <i>Por qué se mide:</i> La normativa exige que el dinero se use para programas sociales que solucionen problemas directos (PpR), no solo en pagar burocracia administrativa.<br>
                <code style="color:#4a148c; background:#f3e5f5; padding:3px 6px; border-radius:4px;">Fórmula: (Gasto en Programas PpR / Devengado Total) * 100</code><br>
                <span style="font-size: 0.9em; color: gray;">Datos usados: S/ {raw_dict['Dev_PpR']:,.2f} / S/ {raw_dict['Dev_Total']:,.2f}</span>
            </li>
        </ul>
        """, unsafe_allow_html=True)

    with colE:
        st.write("### Termómetros Financieros Extra:")
        st.info("Estos indicadores no te desaprueban, pero te dicen qué tan sana está la economía de la entidad.")
        st.metric("1. Desviación de Planificación (IV PIM)", f"{kpi_iv_pim:.1f}%", help="Si el PIM creció muchísimo respecto al PIA inicial (ej. más de 50%), significa que el área de Planeamiento planificó muy mal a inicios de año.")
        st.metric("2. Autonomía Financiera", f"{kpi_auto:.1f}%", help="Porcentaje del gasto que se paga con plata recaudada por ustedes mismos (RDR / Impuestos propios) frente a lo que les regala el gobierno central.")

# --- TAB 9: Explorador Total ---
if modulo_seleccionado == "🧭 9. Explorador Total":
    st.header("Ranking de Ejecución y Distribución Presupuestal")
    
    df_ranking = processor.get_ranking_ejecutora(final_where)
    if not df_ranking.empty:
        df_ranking['% Cert'] = (df_ranking['Cert'] / df_ranking['PIM'] * 100).fillna(0)
        df_ranking['% Comp'] = (df_ranking['Comp'] / df_ranking['PIM'] * 100).fillna(0)
        df_ranking['% Dev'] = (df_ranking['Dev'] / df_ranking['PIM'] * 100).fillna(0)
        
        st.write("### Ranking por Unidad Ejecutora")
        st.dataframe(
            df_ranking.style.background_gradient(subset=['% Dev'], cmap='RdYlGn', vmin=0, vmax=100)
            .format({
                'PIA': "{:,.2f}", 'PIM': "{:,.2f}", 'Cert': "{:,.2f}", 'Comp': "{:,.2f}", 'Dev': "{:,.2f}",
                '% Cert': "{:.1f}%", '% Comp': "{:.1f}%", '% Dev': "{:.1f}%"
            }),
            use_container_width=True, height=350
        )
    
    df_tree = processor.get_distribucion_rubro_funcion(final_where)
    if not df_tree.empty:
        df_tree['% Avance'] = (df_tree['Devengado'] / df_tree['PIM'] * 100).fillna(0)
        df_tree['PIM_M'] = df_tree['PIM'].apply(lambda x: f"S/ {x/1000000:,.1f} M")
        
        st.markdown("---")
        st.write("### Mapas de Calor Presupuestal")
        st.info("💡 **Guía de Lectura Visual:**\n"
                "* **Tamaño de los bloques:** Representa el Presupuesto (PIM). Los bloques más grandes son los que tienen más plata asignada.\n"
                "* **Color de los bloques:** Representa el % de Avance de Ejecución real (Semáforo de Rojo a Verde).\n"
                "* *Pasa el mouse sobre cualquier bloque para ver los montos exactos en Soles y el porcentaje exacto de avance.*")
        
        colTree1, colTree2 = st.columns(2)
        with colTree1:
            fig3 = px.treemap(
                df_tree, 
                path=[px.Constant("Presupuesto Total (Rubros)"), 'Rubro'], 
                values='PIM',
                color='% Avance',
                color_continuous_scale='RdYlGn',
                range_color=[0, 100],
                title="¿De dónde viene la plata? (Financiamiento)"
            )
            fig3.update_traces(
                textinfo="label",
                hovertemplate="<b>%{label}</b><br>Presupuesto (PIM): S/ %{value:,.0f}<br>Avance de Ejecución: %{color:.1f}%<extra></extra>"
            )
            fig3.update_layout(template="plotly_dark", margin=dict(t=50, l=0, r=10, b=10))
            st.plotly_chart(fig3, use_container_width=True)
            
        with colTree2:
            fig4 = px.treemap(
                df_tree, 
                path=[px.Constant("Presupuesto Total (Funciones)"), 'Funcion'], 
                values='PIM',
                color='% Avance',
                color_continuous_scale='RdYlGn',
                range_color=[0, 100],
                title="¿En qué servicios se gasta? (Educación, Salud, etc.)"
            )
            fig4.update_traces(
                textinfo="label",
                hovertemplate="<b>%{label}</b><br>Presupuesto (PIM): S/ %{value:,.0f}<br>Avance de Ejecución: %{color:.1f}%<extra></extra>"
            )
            fig4.update_layout(template="plotly_dark", margin=dict(t=50, l=10, r=0, b=10))
            st.plotly_chart(fig4, use_container_width=True)

# --- TAB 10: Ficha SSI (Buscador y Ranking de Riesgo) ---
if modulo_seleccionado == "🔍 10. Ficha SSI":
    st.markdown("<h2 style='text-align: center; font-family: Arial, sans-serif; color: #1565c0;'>Sistema de Seguimiento de Inversiones (Estilo SSI)</h2>", unsafe_allow_html=True)
    st.info("💡 **Buscador de Inversiones:** Consulta la situación institucional y financiera de un proyecto específico, tal como lo verías en el portal oficial del MEF.")
    
    # 1. Buscador
    proyectos_dict = processor.get_proyectos_dict(final_where)
    if not proyectos_dict:
        st.warning("No hay proyectos de inversión disponibles en esta selección.")
    else:
        # Preparar lista para el Selectbox
        opciones = list(proyectos_dict.keys())
        format_func = lambda x: proyectos_dict[x]
        
        cui_seleccionado = st.selectbox("Opciones de Búsqueda (Código CUI o Nombre):", options=opciones, format_func=format_func)
        
        if cui_seleccionado:
            ficha = processor.get_ficha_ssi(cui_seleccionado, final_where)
            if ficha:
                # Estilos CSS locales para replicar SSI
                st.markdown("""
                <style>
                .ssi-header { background-color: #e0e0e0; padding: 10px; font-size: 14px; font-weight: bold; border-top: 2px solid #bdbdbd; border-bottom: 2px solid #bdbdbd; }
                .ssi-cell { padding: 10px; font-size: 13px; border-bottom: 1px solid #eeeeee; }
                .ssi-title-blue { background-color: #0d3b66; color: white; padding: 10px; font-size: 14px; font-weight: bold; border-radius: 5px 5px 0 0; margin-top: 20px;}
                .ssi-alert-hex { 
                    background-color: white; border: 8px solid #0d3b66; padding: 20px; 
                    text-align: center; max-width: 400px; margin: 20px auto;
                    clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%);
                }
                </style>
                """, unsafe_allow_html=True)
                
                # Cabecera Gris (Datos Básicos)
                st.markdown(f"""
                <div style='display: flex; background-color: #e0e0e0; padding: 5px;'>
                    <div style='flex: 1; padding: 5px;'><b>CÓDIGO ÚNICO</b></div>
                    <div style='flex: 1; padding: 5px;'>{ficha['CUI']}</div>
                    <div style='flex: 1; padding: 5px;'><b>ESTADO DE LA INVERSIÓN</b></div>
                    <div style='flex: 1; padding: 5px;'>ACTIVO</div>
                </div>
                <div style='display: flex; background-color: #f5f5f5; padding: 5px; border-bottom: 2px solid #ccc;'>
                    <div style='flex: 1; padding: 5px;'><b>NOMBRE DE LA INVERSIÓN</b></div>
                    <div style='flex: 3; padding: 5px;'>{ficha['Nombre_Inversion']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # I. INSTITUCIONALIDAD
                st.markdown("<div class='ssi-title-blue'>I. INSTITUCIONALIDAD</div>", unsafe_allow_html=True)
                st.markdown(f"""
                <div style='display: flex; background-color: #f9f9f9;'>
                    <div style='flex: 1;' class='ssi-cell'><b>UNIDAD EJECUTORA (UEI)</b></div>
                    <div style='flex: 2;' class='ssi-cell'>{ficha['OPMI_UEI']}</div>
                </div>
                <div style='display: flex; background-color: #ffffff;'>
                    <div style='flex: 1;' class='ssi-cell'><b>FUNCIÓN / SECTOR</b></div>
                    <div style='flex: 2;' class='ssi-cell'>{ficha['Funcion']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # II. DATOS DE LA FASE EJECUCIÓN (Financiera)
                st.markdown("<div class='ssi-title-blue'>II. DATOS DE LA FASE EJECUCIÓN (FINANCIERA)</div>", unsafe_allow_html=True)
                pct_avance = (ficha['Devengado'] / ficha['PIM'] * 100) if ficha['PIM'] > 0 else 0
                st.markdown(f"""
                <div style='display: flex; background-color: #f9f9f9;'>
                    <div style='flex: 1;' class='ssi-cell'><b>COSTO DE INVERSIÓN ACTUALIZADO (PIM) (S/)</b></div>
                    <div style='flex: 1;' class='ssi-cell'>S/ {ficha['PIM']:,.2f}</div>
                </div>
                <div style='display: flex; background-color: #ffffff;'>
                    <div style='flex: 1;' class='ssi-cell'><b>PRESUPUESTO INICIAL (PIA) (S/)</b></div>
                    <div style='flex: 1;' class='ssi-cell'>S/ {ficha['PIA']:,.2f}</div>
                </div>
                <div style='display: flex; background-color: #f9f9f9;'>
                    <div style='flex: 1;' class='ssi-cell'><b>MONTO DEVENGADO (GASTO REAL) (S/)</b></div>
                    <div style='flex: 1;' class='ssi-cell'>S/ {ficha['Devengado']:,.2f}</div>
                </div>
                <div style='display: flex; background-color: #ffffff;'>
                    <div style='flex: 1;' class='ssi-cell'><b>AVANCE FINANCIERO (%)</b></div>
                    <div style='flex: 1;' class='ssi-cell'><b style='color: {"#d32f2f" if pct_avance < 20 else "#388e3c"};'>{pct_avance:.1f}%</b></div>
                </div>
                """, unsafe_allow_html=True)

                # III. ALERTAS DE RIESGO
                if ficha['PIM'] > 0 and pct_avance < 15.0:
                    st.markdown("""
                    <div class='ssi-alert-hex'>
                        <h4 style='color: #0d3b66; margin-top: 20px;'>SE IDENTIFICARON ALERTAS DE RIESGO:</h4>
                        <p style='color: white; background-color: #0d3b66; padding: 10px; margin: 10px 0;'>
                            <b>Baja Ejecución Financiera<br>(Menor al 15%)</b>
                        </p>
                        <p style='font-size: 12px; color: #333;'>
                            Un avance financiero tan bajo indica un riesgo inminente de paralización o de que los recursos pasen a saldo de balance.
                            <br><br>Esto afecta directamente el cumplimiento de los objetivos de la inversión.
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.success("✅ No se identificaron alertas de riesgo financiero crítico para esta obra.")

                # IV. HISTÓRICO DE DEVENGADO (Para todos los años)
                st.markdown("<div class='ssi-title-blue'>III. HISTÓRICO DE DEVENGADO DE LA INVERSIÓN (S/)</div>", unsafe_allow_html=True)
                
                df_hist = processor.get_historico_ssi(cui_seleccionado, final_where_sin_anio)
                if df_hist is not None and not df_hist.empty:
                    df_hist['ORIGEN'] = 'SIAF'
                    df_hist['% Ejecución'] = (df_hist['Devengado'] / df_hist['PIM'] * 100).fillna(0)
                    
                    # Fila de Total
                    total_row = pd.DataFrame([{
                        'Año': 'TOTAL (A la fecha)',
                        'PIA': df_hist['PIA'].sum(),
                        'PIM': df_hist['PIM'].sum(),
                        'Certificación': df_hist['Certificación'].sum(),
                        'Compromiso_Anual': df_hist['Compromiso_Anual'].sum(),
                        'Devengado': df_hist['Devengado'].sum(),
                        '% Ejecución': (df_hist['Devengado'].sum() / df_hist['PIM'].sum() * 100) if df_hist['PIM'].sum() > 0 else 0,
                        'ORIGEN': '-'
                    }])
                    df_hist = pd.concat([df_hist, total_row], ignore_index=True)

                    # Aplicar estilo resaltado al Total
                    def highlight_total(row):
                        if row['Año'] == 'TOTAL (A la fecha)':
                            return ['background-color: #0d3b66; color: white; font-weight: bold'] * len(row)
                        return [''] * len(row)

                    st.dataframe(
                        df_hist[['Año', 'PIA', 'PIM', 'Certificación', 'Compromiso_Anual', 'Devengado', '% Ejecución', 'ORIGEN']]
                        .style.format({
                            'PIA': "{:,.2f}", 'PIM': "{:,.2f}", 
                            'Certificación': "{:,.2f}", 'Compromiso_Anual': "{:,.2f}", 'Devengado': "{:,.2f}",
                            '% Ejecución': "{:.1f}%"
                        }).apply(highlight_total, axis=1),
                        use_container_width=True, hide_index=True
                    )
                else:
                    st.info("No se encontró data histórica para este proyecto.")

    st.markdown("---")
    st.header("Ranking de Riesgo SSI (Proyectos Críticos)")
    st.write("Lista de todos los proyectos de inversión ordenados por **mayor riesgo de paralización** (menor porcentaje de avance financiero respecto a su PIM).")
    
    df_riesgo = processor.get_ranking_riesgo_ssi(final_where)
    if not df_riesgo.empty:
        st.dataframe(
            df_riesgo.style.background_gradient(subset=['Pct_Avance'], cmap='Reds_r')
            .format({'PIM': "S/ {:,.2f}", 'Devengado': "S/ {:,.2f}", 'Pct_Avance': "{:.1f}%"}),
            use_container_width=True, height=400
        )
    else:
        st.info("No hay proyectos evaluables en esta selección.")

# ----------------- FOOTER INSTITUCIONAL -----------------
st.markdown("""
<style>
.footer {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    background-color: #1a1a2e;
    color: #ccc;
    text-align: center;
    padding: 8px 0;
    border-top: 2px solid #00cfbf;
    z-index: 9999;
    font-size: 12px;
    font-family: Arial, sans-serif;
}
.footer a { color: #00cfbf; text-decoration: none; font-weight: bold; }
.footer a:hover { text-decoration: underline; }
/* Agregamos padding al final de la página para que el footer no tape el contenido de las tablas */
.block-container {
    padding-bottom: 50px !important;
}
</style>

<div class="footer">
    🏛️ <b>Labor técnica y analítica para la provincia de Chumbivilcas.</b> &nbsp;&nbsp;|&nbsp;&nbsp; 
    &copy; Desarrollado por AyniBrava 2026 &nbsp;&nbsp;|&nbsp;&nbsp; 
    <a href="https://www.facebook.com/profile.php?id=61589026953016" target="_blank">
        <img src="https://upload.wikimedia.org/wikipedia/commons/5/51/Facebook_f_logo_%282019%29.svg" width="12" style="vertical-align: middle; margin-right: 3px;">
        Síguenos en Facebook
    </a>
</div>
""", unsafe_allow_html=True)
