import streamlit as st
import pandas as pd
pd.set_option("styler.render.max_elements", 2000000)
import plotly.express as px
import plotly.graph_objects as go
from data_processor import MEFDataProcessor
import os

st.set_page_config(page_title="Visor MEF 360 - Dashboard Ciudadano", page_icon="👁️", layout="wide", initial_sidebar_state="expanded")

@st.cache_resource(show_spinner=False)
def get_processor():
    csv_path = r"C:\Users\marx_\Downloads\2026-Gasto-Diario.csv"
    parquet_path = "2026-Gasto-Diario.parquet"
    return MEFDataProcessor(csv_path, parquet_path)

processor = get_processor()

# Custom CSS for Corporate Teal/Blue Dashboard Aesthetic
st.markdown("""
    <style>
    /* Global Dashboard Styles */
    .block-container {
        padding-top: 2rem !important;
    }
    
    /* KPI Cards */
    .kpi-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-top: 4px solid #006080;
        border-radius: 5px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        text-align: center;
        height: 100%;
    }
    .kpi-title {
        color: #555555;
        font-size: 0.9rem;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 5px;
    }
    .kpi-value {
        color: #008B8B;
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
    }
    .kpi-sub {
        color: #888888;
        font-size: 0.8rem;
        margin-top: 5px;
    }
    
    /* Technical Sustenance Boxes */
    .tech-box {
        background-color: #f0f7fa;
        border-left: 4px solid #006080;
        padding: 15px;
        margin-bottom: 20px;
        border-radius: 0 5px 5px 0;
        font-size: 0.95rem;
    }
    
    /* Responsive DataFrames */
    div[data-testid="stDataFrame"] {
        width: 100%;
    }
    .dataframe-text {
        font-size: clamp(12px, 1vw, 14px);
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #006080;
    }
    
    /* Adjust Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        font-weight: 600;
        color: #555;
    }
    </style>
""", unsafe_allow_html=True)

# ----------------- MAIN HEADER -------------------------------
col_logo, col_title = st.columns([1, 10])
with col_logo:
    try:
        st.image("logo_aynibrava.png", use_container_width=True)
    except:
        st.markdown("<h1 style='text-align: center; font-size: 3em; margin: 0; color: #006080;'>👁️</h1>", unsafe_allow_html=True)
with col_title:
    st.markdown("<h1 style='margin-bottom: 0; font-family: Arial, sans-serif; font-size: 2.2em;'>Panel de Control de Inversión Pública (Visor MEF 360)</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #555; font-size: 16px; margin-top: 0;'><b>Plataforma de Auditoría Ciudadana con Sustento Técnico del SIAF-MEF</b></p>", unsafe_allow_html=True)

# ----------------- SIDEBAR: FILTROS (EXCEL STYLE) -----------------
st.sidebar.markdown("<h3 style='color: #006080; margin-bottom: 0;'>⚙️ Panel de Filtros</h3>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='font-size: 12px; color: gray;'>Selecciona la entidad a fiscalizar. Los gráficos se actualizarán en tiempo real.</p>", unsafe_allow_html=True)

where_clauses = []

anios_disponibles = processor.get_anios_disponibles()
anio_seleccionado = st.sidebar.selectbox("📅 Año Fiscal", anios_disponibles, index=0)
if anio_seleccionado:
    where_clauses.append(f"ANO_EJE = {anio_seleccionado}")

niveles = processor.get_filter_options("NIVEL_GOBIERNO_NOMBRE", " AND ".join(where_clauses) if where_clauses else "")
sel_gobierno = st.sidebar.selectbox("🏛️ Nivel de Gobierno", ["Todos"] + niveles, index=0)
if sel_gobierno != "Todos":
    where_clauses.append(f"NIVEL_GOBIERNO_NOMBRE = '{sel_gobierno}'")

sectores = processor.get_filter_options("SECTOR_NOMBRE", " AND ".join(where_clauses) if where_clauses else "")
sel_sector = st.sidebar.selectbox("🏢 Sector", ["Todos"] + sectores, index=0)
if sel_sector != "Todos":
    where_clauses.append(f"SECTOR_NOMBRE = '{sel_sector}'")

pliegos = processor.get_filter_options("PLIEGO_NOMBRE", " AND ".join(where_clauses) if where_clauses else "")
sel_pliego = st.sidebar.selectbox("📍 Pliego / Entidad", ["Todos"] + pliegos, index=0)
if sel_pliego != "Todos":
    where_clauses.append(f"PLIEGO_NOMBRE = '{sel_pliego}'")

current_where = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
ejecs = processor.get_ejecutoras(current_where)
sel_ejecutora_str = st.sidebar.selectbox("🎯 Unidad Ejecutora (SEC_EJEC)", ["Todos"] + ejecs, index=0)
sel_ejecutora = None
if sel_ejecutora_str != "Todos":
    sec_ejec = sel_ejecutora_str.split(' - ')[0]
    where_clauses.append(f"SEC_EJEC = '{sec_ejec}'")
    sel_ejecutora = sel_ejecutora_str.split(' - ')[1]

# Construct final WHERE clauses
final_where = "WHERE " + " AND ".join(where_clauses) if where_clauses else "WHERE 1=1"
where_sin_anio = [c for c in where_clauses if not c.startswith("ANO_EJE")]
final_where_sin_anio = "WHERE " + " AND ".join(where_sin_anio) if where_sin_anio else "WHERE 1=1"

# Sidebar Footer
st.sidebar.markdown("<hr>", unsafe_allow_html=True)
with st.sidebar.expander("💖 Apoya el Proyecto (Yape)"):
    st.markdown("<p style='font-size:13px; text-align:center;'>Mantenemos los servidores encendidos gracias a ti.</p>", unsafe_allow_html=True)
    try:
        st.image("yape.png", use_container_width=True)
    except:
        st.info("Sube tu archivo yape.png")

st.sidebar.markdown("<div style='text-align:center; font-size:11px;'>Desarrollado en <b>Chumbivilcas</b> por <b>AyniBrava</b></div>", unsafe_allow_html=True)

# ----------------- MAIN CONTENT: TABS -----------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 1. Visión General (Macro)", 
    "🏗️ 2. Fiscalización de Obras", 
    "🕵️ 3. Auditoría Técnica (KPIs)", 
    "📑 4. Expediente (SSI)"
])

# Determinar nombre de entidad
if 'sel_ejecutora' in locals() and sel_ejecutora and sel_ejecutora != "Todos":
    entidad_mostrar = sel_ejecutora
elif sel_pliego != "Todos":
    entidad_mostrar = sel_pliego
elif sel_sector != "Todos":
    entidad_mostrar = sel_sector
elif sel_gobierno != "Todos":
    entidad_mostrar = sel_gobierno
else:
    entidad_mostrar = "Nivel Nacional"

# TAB 1: VISION GENERAL
with tab1:
    st.markdown("""
    <div class='tech-box'>
        <b>Sustento Técnico:</b> Los datos mostrados en este panel provienen directamente del portal oficial de <i>Consulta Amigable (Gasto Diario)</i> del Ministerio de Economía y Finanzas (MEF) del Perú. 
        Representan la "Billetera Grande" de la entidad, incluyendo absolutamente todos los gastos (planillas, bienes, servicios y obras).<br><br>
        <b>¿Cómo leer esto?</b> Revisa primero el <i>PIM</i> (Dinero disponible total), luego el <i>Devengado</i> (Dinero que ya se gastó de manera comprobada) y el <i>Porcentaje de Ejecución</i>.
    </div>
    """, unsafe_allow_html=True)
    
    resumen = processor.get_kpis_resumen(final_where)
    pim_total = resumen['PIM']
    dev_total = resumen['Devengado']
    pct_ejec = (dev_total / pim_total * 100) if pim_total > 0 else 0
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Entidad Fiscalizada</div><div class='kpi-value' style='font-size: 1.2rem; margin-top: 15px;'>{entidad_mostrar}</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='kpi-card'><div class='kpi-title'>PIM (Presupuesto Total)</div><div class='kpi-value'>S/ {pim_total/1000000:,.1f} M</div><div class='kpi-sub'>Límite legal de gasto</div></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Devengado (Gasto Real)</div><div class='kpi-value'>S/ {dev_total/1000000:,.1f} M</div><div class='kpi-sub'>Bienes/servicios recibidos</div></div>", unsafe_allow_html=True)
    with c4:
        color_pct = "#c62828" if pct_ejec < 50 else "#008B8B"
        st.markdown(f"<div class='kpi-card' style='border-top-color: {color_pct};'><div class='kpi-title'>Avance Total</div><div class='kpi-value' style='color: {color_pct};'>{pct_ejec:.1f}%</div><div class='kpi-sub'>Devengado ÷ PIM</div></div>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    df_evo = processor.get_curva_evolucion(final_where)
    if not df_evo.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_evo['Mes'], y=df_evo['Devengado'], mode='lines+markers', name='Gasto Real (Devengado)', line=dict(color='#008B8B', width=4)))
        fig.add_trace(go.Scatter(x=df_evo['Mes'], y=df_evo['Compromiso_Anual'], mode='lines+markers', name='Contratos Firmados (Compromiso)', line=dict(color='#FF8C00', dash='dash')))
        fig.update_layout(title="Curva de Velocidad de Gasto Mensual", xaxis_title="Mes (1 = Ene, 12 = Dic)", yaxis_title="Monto (Soles)", template="plotly_white", margin=dict(t=50, l=0, r=0, b=0))
        st.plotly_chart(fig, use_container_width=True)

# TAB 2: FISCALIZACIÓN DE OBRAS (HISTORIAL COMPLETO)
with tab2:
    st.markdown("""
    <div class='tech-box'>
        <b>Auditoría Forense Avanzada: Historial Completo de Obras (Activas y Cerradas)</b><br>
        Esta tabla no solo muestra las obras de este año. La IA ha viajado en el tiempo a través de toda la base de datos para construir la <b>Línea de Vida</b> de cada código CUI en esta entidad.<br><br>
        <b>¿Cómo interpretar esto?</b><br>
        - 🟢 <b>Activa</b>: Sigue recibiendo presupuesto este año.<br>
        - 🔴 <b>Cerrada</b>: Ya no figura en el presupuesto de este año (obra terminada o abandonada en el pasado).<br>
        - <b>Sobrecosto Histórico</b> (Columna Roja): Es la diferencia entre con cuánto dinero nació la obra originalmente, y cuánto terminó costando. ¡Detecta adendas ocultas de gestiones pasadas!
    </div>
    """, unsafe_allow_html=True)
    
    df_proy = processor.get_auditoria_historica_proyectos(final_where_sin_anio)
    
    if not df_proy.empty:
        # Lógica de Estado
        if anio_seleccionado:
            df_proy['Estado'] = df_proy['anio_cierre'].apply(lambda x: '🟢 ACTIVA' if str(x) == str(anio_seleccionado) else '🔴 CERRADA')
        else:
            df_proy['Estado'] = df_proy['anio_cierre'].apply(lambda x: '🟢 ACTIVA' if str(x) == "2026" else '🔴 CERRADA')
            
        df_proy['Sobrecosto'] = df_proy['pim_cierre'] - df_proy['pia_nacimiento']
        df_proy['Ciclo_Vida'] = df_proy['anio_nacimiento'].astype(str) + " ➔ " + df_proy['anio_cierre'].astype(str)
        
        c1, c2, c3 = st.columns(3)
        total_activas = len(df_proy[df_proy['Estado'] == '🟢 ACTIVA'])
        total_cerradas = len(df_proy[df_proy['Estado'] == '🔴 CERRADA'])
        sobrecosto_total = df_proy['Sobrecosto'].sum()
        
        with c1: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Obras Activas Este Año</div><div class='kpi-value'>{total_activas}</div></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Obras Cerradas (Históricas)</div><div class='kpi-value'>{total_cerradas}</div></div>", unsafe_allow_html=True)
        with c3: st.markdown(f"<div class='kpi-card' style='border-top-color: #c62828;'><div class='kpi-title'>Sobrecosto Histórico Total</div><div class='kpi-value' style='color:#c62828;'>S/ {sobrecosto_total/1000000:,.1f} M</div></div>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        filtro_estado = st.radio("Filtro Rápido:", ["Mostrar Todas", "Solo 🟢 ACTIVAS", "Solo 🔴 CERRADAS"], horizontal=True)
        busqueda = st.text_input("🔍 Filtrar tabla por nombre del proyecto o código CUI:", "")
        
        df_filtro = df_proy.copy()
        if filtro_estado == "Solo 🟢 ACTIVAS": df_filtro = df_filtro[df_filtro['Estado'] == '🟢 ACTIVA']
        elif filtro_estado == "Solo 🔴 CERRADAS": df_filtro = df_filtro[df_filtro['Estado'] == '🔴 CERRADA']
        
        if busqueda:
            df_filtro = df_filtro[df_filtro['Proyecto'].str.contains(busqueda, case=False) | df_filtro['CUI'].astype(str).str.contains(busqueda)]
            
        df_mostrar = df_filtro[['Estado', 'CUI', 'Proyecto', 'Ciclo_Vida', 'pia_nacimiento', 'pim_cierre', 'Sobrecosto', 'devengado_total']].copy()
        df_mostrar.columns = ['Estado', 'CUI', 'Nombre de la Obra', 'Años de Vida', 'Costo Original (PIA Nace)', 'Costo Final (PIM Cierra)', 'Sobrecosto Histórico', 'Plata Pagada (Gasto Total)']
        
        st.dataframe(
            df_mostrar.style
            .background_gradient(subset=['Sobrecosto Histórico'], cmap='Reds', vmin=0)
            .format({
                'Costo Original (PIA Nace)': 'S/ {:,.0f}',
                'Costo Final (PIM Cierra)': 'S/ {:,.0f}',
                'Sobrecosto Histórico': 'S/ {:,.0f}',
                'Plata Pagada (Gasto Total)': 'S/ {:,.0f}'
            }),
            use_container_width=True, height=600, hide_index=True
        )
    else:
        st.warning("No se encontraron proyectos de inversión para esta entidad en la base de datos histórica.")

# TAB 3: AUDITORÍA TÉCNICA
with tab3:
    st.markdown("""
    <div class='tech-box'>
        <b>Metodología Oficial de Auditoría del Gasto:</b><br>
        Para juzgar si un alcalde o gobernador es eficiente, la Contraloría y el MEF analizan fórmulas clave. Léelas en este orden lógico:<br><br>
        <b>1️⃣ Paso 1 (IEG):</b> <i>¿Se gastó la plata?</i> Mide el Avance General. Acercarse a 100% es óptimo.<br>
        <b>2️⃣ Paso 2 (ICED):</b> <i>¿Se gastó de forma planificada o a última hora?</i> Mide el "Síndrome de Diciembre". Si es mayor a 20%, el alcalde gastó la plata apurado a fin de año para inflar sus cifras, lo cual suele resultar en obras mal hechas.<br>
        <b>3️⃣ Paso 3 (IOPR):</b> <i>¿En qué se gastó?</i> Mide la prioridad de Gasto Social (Salud, Educación, Saneamiento, etc.). Un porcentaje alto indica que se priorizó al ciudadano y no los gastos de escritorio (burocracia).
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    kpi_ieg = processor.get_kpi_1_ieg(final_where)
    kpi_iced = processor.get_kpi_5_iced(final_where)
    kpi_iopr = processor.get_kpi_3_iopr(final_where)
    with col1: 
        st.markdown(f"<div class='kpi-card'><div class='kpi-title'>1️⃣ Avance General (IEG)</div><div class='kpi-value'>{kpi_ieg:.1f}%</div><div class='kpi-sub'>Devengado Total ÷ PIM Total</div></div>", unsafe_allow_html=True)
    with col2: 
        st.markdown(f"<div class='kpi-card'><div class='kpi-title'>2️⃣ Síndrome Diciembre (ICED)</div><div class='kpi-value'>{kpi_iced:.1f}%</div><div class='kpi-sub'>Gasto Diciembre ÷ Gasto Anual</div></div>", unsafe_allow_html=True)
    with col3: 
        st.markdown(f"<div class='kpi-card'><div class='kpi-title'>3️⃣ Gasto Social (IOPR)</div><div class='kpi-value'>{kpi_iopr:.1f}%</div><div class='kpi-sub'>Inversión Social ÷ Gasto Total</div></div>", unsafe_allow_html=True)

    st.markdown("<br>### 📊 Origen y Destino de los Fondos", unsafe_allow_html=True)
    df_tree = processor.get_distribucion_rubro_funcion(final_where)
    if not df_tree.empty:
        df_rubro = df_tree.groupby('Rubro', as_index=False).agg({'PIM': 'sum', 'Devengado': 'sum'})
        df_rubro['% Avance'] = (df_rubro['Devengado'] / df_rubro['PIM'] * 100).fillna(0)
        df_rubro = df_rubro.sort_values('PIM', ascending=True).tail(5)
        
        df_funcion = df_tree.groupby('Funcion', as_index=False).agg({'PIM': 'sum', 'Devengado': 'sum'})
        df_funcion['% Avance'] = (df_funcion['Devengado'] / df_funcion['PIM'] * 100).fillna(0)
        df_funcion = df_funcion.sort_values('PIM', ascending=True).tail(5)
        
        colTree1, colTree2 = st.columns(2)
        with colTree1:
            fig3 = px.bar(df_rubro, x='PIM', y='Rubro', orientation='h', color='% Avance', color_continuous_scale='RdYlGn', range_color=[0, 100], title="Origen del Dinero (Rubros de Financiamiento)", text_auto='.2s')
            fig3.update_layout(template="plotly_white", margin=dict(t=40, l=0, r=0, b=0))
            st.plotly_chart(fig3, use_container_width=True)
        with colTree2:
            fig4 = px.bar(df_funcion, x='PIM', y='Funcion', orientation='h', color='% Avance', color_continuous_scale='RdYlGn', range_color=[0, 100], title="¿En qué se gasta? (Funciones del Estado)", text_auto='.2s')
            fig4.update_layout(template="plotly_white", margin=dict(t=40, l=0, r=0, b=0))
            st.plotly_chart(fig4, use_container_width=True)

    st.markdown("### 🚨 Dinero en Riesgo de Perderse (Alertas de Spillover)")
    st.info("Esta tabla muestra proyectos que **tienen presupuesto (PIM) pero no han firmado contratos (Compromiso Bajo)**. Si no gastan esto antes del 31 de Diciembre, el dinero regresa al Gobierno Central y la municipalidad lo pierde.")
    df_spill = processor.get_spillover_alerts(final_where)
    if not df_spill.empty:
        def evaluar_riesgo(row):
            if row['PIM'] == 0: return "Sin PIM"
            comp_pct = (row['Compromiso'] / row['PIM']) * 100
            if row['Certificado'] == 0: return "🔴 RIESGO EXTREMO (0% Certificado)"
            elif comp_pct < 40: return "🟠 RIESGO MEDIO (Compromiso Bajo)"
            else: return "🟢 SEGURO"
        df_spill['Nivel de Riesgo'] = df_spill.apply(evaluar_riesgo, axis=1)
        st.dataframe(df_spill[['Proyecto', 'PIM', 'Certificado', 'Compromiso', 'Nivel de Riesgo']].style.format({'PIM': "S/ {:,.0f}", 'Certificado': "S/ {:,.0f}", 'Compromiso': "S/ {:,.0f}"}), use_container_width=True, hide_index=True)

# TAB 4: FICHA SSI
with tab4:
    st.markdown("""
    <div class='tech-box'>
        <b>Auditoría Forense de un Proyecto:</b> Aquí usamos el <i>Código Único de Inversión (CUI)</i>, equivalente al antiguo SNIP, para extraer la radiografía histórica del proyecto desde que nació hasta hoy. 
        Podrás evaluar si el presupuesto ha sido inflado sistemáticamente año tras año.
    </div>
    """, unsafe_allow_html=True)
    
    proyectos_dict = processor.get_proyectos_dict(final_where_sin_anio)
    if not proyectos_dict:
        st.warning("No hay proyectos disponibles en la base de datos para buscar.")
    else:
        opciones = list(proyectos_dict.keys())
        format_func = lambda x: proyectos_dict[x]
        
        cui_seleccionado = st.selectbox("🔍 Escribe o selecciona el Código Único de Inversión (CUI) o Nombre del Proyecto:", options=opciones, format_func=format_func)
        
        if cui_seleccionado:
            ficha = processor.get_ficha_ssi(cui_seleccionado, final_where_sin_anio)
            if ficha:
                st.markdown(f"""
                <div style='background: #006080; color: white; padding: 15px; border-radius: 5px 5px 0 0;'>
                    <h4 style='margin:0; color: white;'>I. DATOS TÉCNICOS (CUI: {ficha['CUI']})</h4>
                </div>
                <div style='border: 1px solid #ddd; padding: 15px; border-radius: 0 0 5px 5px; margin-bottom: 20px;'>
                    <b>NOMBRE DEL PROYECTO:</b> {ficha['Nombre_Inversion']}<br>
                    <b>MUNICIPALIDAD / ENTIDAD A CARGO:</b> {ficha['OPMI_UEI']}
                </div>
                """, unsafe_allow_html=True)
                
                pct_avance = (ficha['Devengado'] / ficha['PIM'] * 100) if ficha['PIM'] > 0 else 0
                
                c1, c2, c3 = st.columns(3)
                with c1: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Costo Actualizado (PIM Total Histórico)</div><div class='kpi-value'>S/ {ficha['PIM']:,.0f}</div></div>", unsafe_allow_html=True)
                with c2: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Plata Pagada (Devengado Total Histórico)</div><div class='kpi-value'>S/ {ficha['Devengado']:,.0f}</div></div>", unsafe_allow_html=True)
                with c3: 
                    col_av = "#c62828" if pct_avance < 30 else "#008B8B"
                    st.markdown(f"<div class='kpi-card' style='border-top-color: {col_av};'><div class='kpi-title'>Avance Financiero Total</div><div class='kpi-value' style='color:{col_av};'>{pct_avance:.1f}%</div></div>", unsafe_allow_html=True)
                
                if ficha['PIM'] > 0 and pct_avance < 15.0:
                    st.error("🚨 **ALERTA CIUDADANA:** Esta obra tiene un avance crítico (menor a 15%). Altísima probabilidad de paralización o abandono. Verifica abajo si han inflado su costo recientemente.")
                
                st.markdown("<br><h4 style='color: #006080;'>III. HISTORIA DE LA BILLETERA (Gasto año por año)</h4>", unsafe_allow_html=True)
                st.info("Revisa la tabla inferior: Si el 'Presupuesto Inflado (PIM)' crece cada año, es una señal de que el proyecto está sufriendo adendas o sobrecostos crónicos.")
                
                df_hist = processor.get_historico_ssi(cui_seleccionado, final_where_sin_anio)
                if df_hist is not None and not df_hist.empty:
                    df_hist['% Avance del Año'] = (df_hist['Devengado'] / df_hist['PIM'] * 100).fillna(0)
                    df_mostrar_hist = df_hist[['Año', 'PIA', 'PIM', 'Devengado', '% Avance del Año']].copy()
                    df_mostrar_hist.columns = ['Año', 'Presupuesto Inicio Año (PIA)', 'Presupuesto Inflado (PIM)', 'Pagado en el Año', '% Avance del Año']
                    
                    st.dataframe(
                        df_mostrar_hist.style
                        .background_gradient(subset=['% Avance del Año'], cmap='RdYlGn', vmin=0, vmax=100)
                        .format({
                            'Presupuesto Inicio Año (PIA)': 'S/ {:,.0f}',
                            'Presupuesto Inflado (PIM)': 'S/ {:,.0f}',
                            'Pagado en el Año': 'S/ {:,.0f}',
                            '% Avance del Año': '{:.1f}%'
                        }),
                        use_container_width=True, hide_index=True
                    )
