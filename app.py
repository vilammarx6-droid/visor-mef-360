import streamlit as st
import pandas as pd
pd.set_option("styler.render.max_elements", 2000000)
import plotly.express as px
import plotly.graph_objects as go
from data_processor import MEFDataProcessor
import os

st.set_page_config(page_title="Visor MEF 360 - Lupa Ciudadana", page_icon="👁️", layout="wide")

@st.cache_resource(show_spinner=False)
def get_processor():
    csv_path = r"C:\Users\marx_\Downloads\2026-Gasto-Diario.csv"
    parquet_path = "2026-Gasto-Diario.parquet"
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
    .metric-value { font-size: 2em; font-weight: bold; color: #4CAF50; }
    .metric-label { font-size: 1.1em; color: #B0BEC5; }
    div.stButton > button { width: 100%; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

# ----------------- MAIN HEADER -------------------------------
col_logo, col_title = st.columns([1, 8])
with col_logo:
    if os.path.exists("logo_aynibrava.png"):
        st.image("logo_aynibrava.png", use_container_width=True)
    else:
        st.markdown("<h1 style='text-align: right; font-size: 3em; margin: 0;'>👁️</h1>", unsafe_allow_html=True)
with col_title:
    st.markdown("<h1 style='color: #1565c0; margin-bottom: 0; font-family: Arial, sans-serif; font-size: 2.5em;'>Visor MEF 360</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #555; font-size: 18px; margin-top: 0;'><b>Plataforma de Fiscalización y Transparencia del Gasto Público</b></p>", unsafe_allow_html=True)

st.markdown("---")

# ----------------- TOP BAR: FILTROS GLOBALES -----------------
st.markdown("### 🔍 Filtros Globales (Selecciona tu Entidad a Fiscalizar)")

# Helper function to format dropdowns
where_clauses = []

colF1, colF2, colF3, colF4 = st.columns(4)
with colF1:
    anios_disponibles = processor.get_anios_disponibles()
    anio_seleccionado = st.selectbox("📅 Año Fiscal", anios_disponibles, index=0)
    if anio_seleccionado:
        where_clauses.append(f"ANO_EJE = {anio_seleccionado}")
with colF2:
    niveles = processor.get_filter_options("NIVEL_GOBIERNO_NOMBRE", " AND ".join(where_clauses) if where_clauses else "")
    sel_gobierno = st.selectbox("Nivel de Gobierno", ["Todos"] + niveles, index=0)
    if sel_gobierno != "Todos":
        where_clauses.append(f"NIVEL_GOBIERNO_NOMBRE = '{sel_gobierno}'")
with colF3:
    sectores = processor.get_filter_options("SECTOR_NOMBRE", " AND ".join(where_clauses) if where_clauses else "")
    sel_sector = st.selectbox("Sector", ["Todos"] + sectores, index=0)
    if sel_sector != "Todos":
        where_clauses.append(f"SECTOR_NOMBRE = '{sel_sector}'")
with colF4:
    pliegos = processor.get_filter_options("PLIEGO_NOMBRE", " AND ".join(where_clauses) if where_clauses else "")
    sel_pliego = st.selectbox("Pliego / Municipalidad", ["Todos"] + pliegos, index=0)
    if sel_pliego != "Todos":
        where_clauses.append(f"PLIEGO_NOMBRE = '{sel_pliego}'")

# Construct final WHERE clauses
final_where = "WHERE " + " AND ".join(where_clauses) if where_clauses else "WHERE 1=1"
where_sin_anio = [c for c in where_clauses if not c.startswith("ANO_EJE")]
final_where_sin_anio = "WHERE " + " AND ".join(where_sin_anio) if where_sin_anio else "WHERE 1=1"

st.markdown("---")

# ----------------- SIDEBAR: NAVEGACION Y FOOTER -----------------
st.sidebar.markdown("<h2 style='color: #1565c0; margin-bottom: 0;'>Navegación</h2>", unsafe_allow_html=True)
modulo_seleccionado = st.sidebar.radio("", [
    "🏢 1. Lupa Ciudadana (Obras)",
    "📊 2. Tablero Macro (Resumen)",
    "🕵️ 3. Análisis Profundo (KPIs)",
    "🏗️ 4. Ficha Técnica SSI"
])

# Sidebar Footer
st.sidebar.markdown("<hr>", unsafe_allow_html=True)
st.sidebar.markdown("<div style='text-align:center; font-size:12px; color:gray; margin-bottom: 10px;'>📊 Datos extraídos en tiempo real de Consulta Amigable (Gasto Diario) del MEF.</div>", unsafe_allow_html=True)

if os.path.exists("yape.png"):
    st.sidebar.image("yape.png", use_container_width=True)
    st.sidebar.markdown("<div style='text-align:center; background:#1a1a2e; color:white; padding:5px; border-radius:5px;'>Yape: <b>963 301 301</b><br><i>Apoya el mantenimiento del servidor</i></div>", unsafe_allow_html=True)

st.sidebar.markdown("<br><div style='text-align:center; font-size:12px;'>Desarrollado en <b>Chumbivilcas</b> por <b>AyniBrava</b></div>", unsafe_allow_html=True)
st.sidebar.markdown("<div style='text-align:center; font-size:12px; margin-top: 5px;'><a href='#' style='color:#1565c0; text-decoration: none;'>🚨 ¿Sugerencias o errores? Contáctanos</a></div>", unsafe_allow_html=True)

# Helper para formato
def format_millones(valor):
    if pd.isna(valor): return "0.00 M"
    return f"{valor / 1000000:.2f} M"

# ----------------- MODULO 1: LUPA CIUDADANA -----------------
if modulo_seleccionado == "🏢 1. Lupa Ciudadana (Obras)":
    st.markdown("<h2 style='color: #1565c0;'>🏢 Lupa Ciudadana: Fiscalización Directa</h2>", unsafe_allow_html=True)
    st.info("💡 **Objetivo:** Descubre rápidamente si las obras de tu municipalidad o entidad están paralizadas o sufren de sobrecostos inflados. Busca obras sospechosas aquí.")
    
    entidad_mostrar = sel_pliego if sel_pliego != "Todos" else (sel_sector if sel_sector != "Todos" else "Nivel Nacional")
    
    df_proy = processor.get_avance_proyectos(final_where)
    
    if not df_proy.empty:
        total_obras = len(df_proy)
        presupuesto_total = df_proy['PIM'].sum()
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"<div style='background-color: #e3f2fd; padding: 20px; border-left: 5px solid #1976d2; border-radius: 5px;'><h4>Obras activas en {entidad_mostrar}</h4><h1 style='color:#1565c0; margin:0;'>{total_obras}</h1></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div style='background-color: #fff3e0; padding: 20px; border-left: 5px solid #ff9800; border-radius: 5px;'><h4>Presupuesto de Obras (PIM)</h4><h1 style='color:#e65100; margin:0;'>S/ {presupuesto_total/1000000:,.1f} Millones</h1></div>", unsafe_allow_html=True)
        
        st.markdown("### 📋 Semáforo de Obras y Sobrecostos")
        
        df_proy['% Avance'] = (df_proy['Devengado'] / df_proy['PIM'] * 100).fillna(0)
        df_proy['Salto_Presupuestal'] = df_proy['PIM'] - df_proy['PIA']
        df_proy['% Incremento Costo'] = ((df_proy['PIM'] - df_proy['PIA']) / df_proy['PIA'] * 100).fillna(0)
        
        # Clasificar la salud
        def salud(row):
            if row['% Avance'] < 15: return "🔴 Paralizada / Lenta"
            elif row['% Avance'] < 50: return "🟡 Avance Medio"
            else: return "🟢 Avanzando"
        df_proy['Salud'] = df_proy.apply(salud, axis=1)
        
        # Filtro de texto para la tabla
        busqueda = st.text_input("🔍 Filtrar lista por nombre de obra o CUI:", "")
        if busqueda:
            df_proy = df_proy[df_proy['Proyecto'].str.contains(busqueda, case=False) | df_proy['CUI'].astype(str).str.contains(busqueda)]
            
        st.write("Copia el **CUI** de cualquier obra y pégalo en el **Módulo 4 (Ficha Técnica SSI)** para ver su historia completa.")
        
        df_mostrar = df_proy[['CUI', 'Proyecto', 'Salud', '% Avance', 'PIA', 'PIM', 'Salto_Presupuestal']].copy()
        
        # Renombrar columnas para el ciudadano
        df_mostrar.columns = ['Código CUI', 'Nombre de la Obra', 'Estado de la Obra', '% Gasto Real', 'Costo Inicial (PIA)', 'Costo Inflado (PIM)', 'Sobrecosto / Adendas']
        
        st.dataframe(
            df_mostrar.style
            .background_gradient(subset=['% Gasto Real'], cmap='RdYlGn', vmin=0, vmax=100)
            .background_gradient(subset=['Sobrecosto / Adendas'], cmap='Reds', vmin=0)
            .format({
                '% Gasto Real': '{:.1f}%',
                'Costo Inicial (PIA)': 'S/ {:,.0f}',
                'Costo Inflado (PIM)': 'S/ {:,.0f}',
                'Sobrecosto / Adendas': 'S/ {:,.0f}'
            }),
            use_container_width=True, height=600
        )
    else:
        st.warning("No se encontraron obras o proyectos de inversión para esta selección.")

# ----------------- MODULO 2: TABLERO MACRO -----------------
elif modulo_seleccionado == "📊 2. Tablero Macro (Resumen)":
    st.markdown("<h2 style='color: #1565c0;'>📊 Tablero Macro: Visión de Pájaros</h2>", unsafe_allow_html=True)
    st.info("💡 **Objetivo:** Mira la 'Billetera Grande'. Descubre con un vistazo cómo va el avance de TODO el gasto de la entidad sumado (obras, sueldos, bienes, etc).")
    
    resumen = processor.get_kpis_resumen(final_where)
    pim_total = resumen['PIM']
    dev_total = resumen['Devengado']
    pct_ejec = (dev_total / pim_total * 100) if pim_total > 0 else 0
    
    colA, colB = st.columns(2)
    with colA:
        st.markdown(f"""
        <div style="background-color: {'#ffebee' if pct_ejec < 50 else '#e8f5e9'}; padding: 30px; border-radius: 10px; text-align: center; border: 2px solid {'#f44336' if pct_ejec < 50 else '#4caf50'};">
            <h4 style="color: {'#c62828' if pct_ejec < 50 else '#2e7d32'};" title="Es la plata que ya se pagó (Devengado) respecto al total asignado (PIM)">Porcentaje de Ejecución Total ❓</h4>
            <h1 style="font-size: 5em; margin:0; font-weight: 900; color: {'#c62828' if pct_ejec < 50 else '#2e7d32'};">{pct_ejec:.1f}%</h1>
        </div>
        """, unsafe_allow_html=True)
    with colB:
        st.markdown(f"""
        <div style="background-color: #f5f5f5; padding: 30px; border-radius: 10px; text-align: center; border: 2px solid #ddd;">
            <h4 style="color: #333;" title="El Presupuesto Institucional Modificado (PIM) es el tope máximo de dinero que puede gastar la entidad este año.">Presupuesto Disponible (PIM) ❓</h4>
            <h1 style="font-size: 4em; margin:0; font-weight: bold; color: #1565c0;">S/ {pim_total/1000000:,.0f} M</h1>
            <h5 style="color: #666; margin-top: 10px;" title="Dinero ya pagado a contratistas y empleados">Ya se pagó (Devengado): S/ {dev_total/1000000:,.0f} M ❓</h5>
        </div>
        """, unsafe_allow_html=True)
        
    df_evo = processor.get_curva_evolucion(final_where)
    if not df_evo.empty:
        st.markdown("### 📈 Curva de Velocidad Mensual")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_evo['Mes'], y=df_evo['Devengado'], mode='lines+markers', name='Gasto Real (Devengado)', line=dict(color='green', width=4)))
        fig.add_trace(go.Scatter(x=df_evo['Mes'], y=df_evo['Compromiso_Anual'], mode='lines+markers', name='Contratos Firmados (Compromiso)', line=dict(color='orange', dash='dash')))
        fig.update_layout(xaxis_title="Mes (1 = Ene, 12 = Dic)", yaxis_title="Monto (Soles)", template="plotly_white", legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01))
        st.plotly_chart(fig, use_container_width=True)

# ----------------- MODULO 3: ANALISIS PROFUNDO -----------------
elif modulo_seleccionado == "🕵️ 3. Análisis Profundo (KPIs)":
    st.markdown("<h2 style='color: #1565c0;'>🕵️ Análisis Profundo y Auditoría Técnica</h2>", unsafe_allow_html=True)
    st.info("💡 **Objetivo:** Para analistas y periodistas. Aquí encontrarás indicadores matemáticos de eficiencia, proyecciones de fin de año, y la distribución del presupuesto por Rubro y Función.")
    
    st.markdown("### 📊 1. Mapa de Calor (¿De dónde viene y a dónde va la plata?)")
    df_tree = processor.get_distribucion_rubro_funcion(final_where)
    if not df_tree.empty:
        df_tree['% Avance'] = (df_tree['Devengado'] / df_tree['PIM'] * 100).fillna(0)
        colTree1, colTree2 = st.columns(2)
        with colTree1:
            fig3 = px.treemap(df_tree, path=[px.Constant("Total"), 'Rubro'], values='PIM', color='% Avance', color_continuous_scale='RdYlGn', range_color=[0, 100], title="Origen del Dinero (Rubros)")
            fig3.update_layout(template="plotly_white", margin=dict(t=30, l=0, r=0, b=0))
            st.plotly_chart(fig3, use_container_width=True)
        with colTree2:
            fig4 = px.treemap(df_tree, path=[px.Constant("Total"), 'Funcion'], values='PIM', color='% Avance', color_continuous_scale='RdYlGn', range_color=[0, 100], title="Destino del Dinero (Funciones)")
            fig4.update_layout(template="plotly_white", margin=dict(t=30, l=0, r=0, b=0))
            st.plotly_chart(fig4, use_container_width=True)
            
    st.markdown("### 🚨 2. Alertas Tempranas (Spillovers / Dinero que se puede perder)")
    df_spill = processor.get_spillover_alerts(final_where)
    if not df_spill.empty:
        def evaluar_riesgo(row):
            if row['PIM'] == 0: return "Sin PIM"
            comp_pct = (row['Compromiso'] / row['PIM']) * 100
            if row['Certificado'] == 0: return "🔴 RIESGO EXTREMO (0% Certificado)"
            elif comp_pct < 40: return "🟠 RIESGO MEDIO (Compromiso Bajo)"
            else: return "🟢 SEGURO"
        df_spill['Riesgo Spillover'] = df_spill.apply(evaluar_riesgo, axis=1)
        st.dataframe(df_spill[['Proyecto', 'PIM', 'Certificado', 'Compromiso', 'Riesgo Spillover']].style.format({'PIM': "{:,.0f}", 'Certificado': "{:,.0f}", 'Compromiso': "{:,.0f}"}), use_container_width=True)
        
    st.markdown("### ⚖️ 3. Fórmulas de Gestión del MEF")
    col1, col2, col3 = st.columns(3)
    kpi_ieg = processor.get_kpi_1_ieg(final_where)
    kpi_iced = processor.get_kpi_5_iced(final_where)
    kpi_iopr = processor.get_kpi_3_iopr(final_where)
    with col1: st.metric("Avance General (IEG)", f"{kpi_ieg:.1f}%", help="Devengado Total / PIM Total")
    with col2: st.metric("Síndrome Diciembre (ICED)", f"{kpi_iced:.1f}%", help="Gasto concentrado en Diciembre vs Gasto Total del Año. Más de 20% es malo.")
    with col3: st.metric("Gasto Social (IOPR)", f"{kpi_iopr:.1f}%", help="Gasto en Programas Sociales vs Gasto Administrativo. Debe ser alto.")

# ----------------- MODULO 4: FICHA SSI -----------------
elif modulo_seleccionado == "🏗️ 4. Ficha Técnica SSI":
    st.markdown("<h2 style='text-align: center; color: #1565c0;'>🏗️ Ficha Técnica SSI (Rayos X de una Obra)</h2>", unsafe_allow_html=True)
    st.info("💡 **Objetivo:** Pega aquí el CUI (antiguo SNIP) de la obra que detectaste en el Módulo 1 para ver todo su historial, quién es el contratista, y cómo ha subido su costo año tras año.")
    
    proyectos_dict = processor.get_proyectos_dict(final_where_sin_anio)
    if not proyectos_dict:
        st.warning("No hay proyectos disponibles en la base de datos para buscar.")
    else:
        opciones = list(proyectos_dict.keys())
        format_func = lambda x: proyectos_dict[x]
        
        cui_seleccionado = st.selectbox("🔍 Escribe o selecciona el Código Único de Inversión (CUI) o Nombre:", options=opciones, format_func=format_func)
        
        if cui_seleccionado:
            ficha = processor.get_ficha_ssi(cui_seleccionado, final_where_sin_anio)
            if ficha:
                st.markdown("""
                <style>
                .ssi-cell { padding: 10px; font-size: 14px; border-bottom: 1px solid #eeeeee; }
                .ssi-title-blue { background-color: #0d3b66; color: white; padding: 10px; font-size: 16px; font-weight: bold; border-radius: 5px 5px 0 0; margin-top: 20px;}
                </style>
                """, unsafe_allow_html=True)
                
                st.markdown(f"<div class='ssi-title-blue'>I. DATOS DE LA OBRA (CUI: {ficha['CUI']})</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='ssi-cell'><b>NOMBRE:</b> {ficha['Nombre_Inversion']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='ssi-cell'><b>MUNICIPALIDAD / ENTIDAD (UEI):</b> {ficha['OPMI_UEI']}</div>", unsafe_allow_html=True)
                
                pct_avance = (ficha['Devengado'] / ficha['PIM'] * 100) if ficha['PIM'] > 0 else 0
                st.markdown("<div class='ssi-title-blue'>II. DATOS FINANCIEROS ACUMULADOS (TODA LA HISTORIA)</div>", unsafe_allow_html=True)
                
                colA, colB, colC = st.columns(3)
                with colA: st.metric("Costo Actualizado (PIM Total)", f"S/ {ficha['PIM']:,.0f}")
                with colB: st.metric("Plata Pagada (Devengado Total)", f"S/ {ficha['Devengado']:,.0f}")
                with colC: 
                    st.markdown(f"<h3 style='color: {'red' if pct_avance < 30 else 'green'}; margin:0;'>Avance Financiero: {pct_avance:.1f}%</h3>", unsafe_allow_html=True)
                
                if ficha['PIM'] > 0 and pct_avance < 15.0:
                    st.error("🚨 **ALERTA CIUDADANA:** Esta obra tiene un avance crítico (menor a 15%). Altísima probabilidad de paralización o abandono.")
                
                st.markdown("<div class='ssi-title-blue'>III. HISTORIA DE LA BILLETERA (Gasto año por año)</div>", unsafe_allow_html=True)
                st.write("Verifica si el costo de la obra (PIM) ha ido inflando cada año debido a paralizaciones o adendas.")
                
                df_hist = processor.get_historico_ssi(cui_seleccionado, final_where_sin_anio)
                if df_hist is not None and not df_hist.empty:
                    df_hist['% Avance del Año'] = (df_hist['Devengado'] / df_hist['PIM'] * 100).fillna(0)
                    df_mostrar_hist = df_hist[['Año', 'PIA', 'PIM', 'Devengado', '% Avance del Año']].copy()
                    df_mostrar_hist.columns = ['Año', 'Presupuesto Inicio Año (PIA)', 'Presupuesto Inflado (PIM)', 'Pagado en el Año', '% Avance']
                    
                    st.dataframe(
                        df_mostrar_hist.style
                        .background_gradient(subset=['% Avance'], cmap='RdYlGn', vmin=0, vmax=100)
                        .format({
                            'Presupuesto Inicio Año (PIA)': 'S/ {:,.0f}',
                            'Presupuesto Inflado (PIM)': 'S/ {:,.0f}',
                            'Pagado en el Año': 'S/ {:,.0f}',
                            '% Avance': '{:.1f}%'
                        }),
                        use_container_width=True
                    )
                    
                    # Gráfico Histórico
                    fig_hist = px.bar(df_hist, x='Año', y=['PIA', 'PIM', 'Devengado'], barmode='group', title="Comparativo Histórico de Presupuestos vs Gasto Real")
                    fig_hist.update_layout(template="plotly_white")
                    st.plotly_chart(fig_hist, use_container_width=True)
