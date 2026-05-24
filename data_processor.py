import duckdb
import os
import pandas as pd
import streamlit as st

class MEFDataProcessor:
    def __init__(self, csv_path, parquet_path):
        self.csv_path = csv_path
        self.parquet_path = parquet_path
        
        # Detector Automático de Entorno Nube (Streamlit Cloud)
        # Si la ruta de Windows (C:\) no existe, sabemos con 100% de seguridad que estamos en el servidor Linux de Streamlit.
        self.is_cloud = not os.path.exists(self.csv_path) and not os.path.exists(self.parquet_path)
        
        # Enlaces de la Nube (Hugging Face Datasets) - ¡AQUÍ ACTUALIZAS LOS AÑOS!
        self.cloud_urls_raw = [
            "https://huggingface.co/datasets/marxvilam/mef-datos/resolve/main/2026-Gasto-Diario.parquet",
            "https://huggingface.co/datasets/marxvilam/mef-datos/resolve/main/2025-Gasto-Diario.parquet",
            "https://huggingface.co/datasets/marxvilam/mef-datos/resolve/main/2024-Gasto-Diario.parquet"
        ]
        self.cloud_urls = []

        if self.is_cloud:
            self._ensure_cloud_data()
        else:
            self._ensure_parquet()

    def _ensure_cloud_data(self):
        import urllib.request
        for url in self.cloud_urls_raw:
            filename = url.split('/')[-1]
            # Usar el directorio de trabajo temporal /tmp en Linux
            local_path = os.path.join('/tmp', filename)
            self.cloud_urls.append(local_path)
            
            if not os.path.exists(local_path):
                with st.spinner(f"Descargando datos desde la nube: {filename} ... (Esto solo ocurre la primera vez que enciendes el servidor)"):
                    try:
                        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(req) as response, open(local_path, 'wb') as out_file:
                            out_file.write(response.read())
                    except Exception as e:
                        st.error(f"Error descargando {filename}: {e}")

    def _ensure_parquet(self):
        """Converts the CSV to a Parquet file if it doesn't exist for massive speedup."""
        import glob
        if not glob.glob(self.parquet_path):
            st.warning("Convirtiendo archivo CSV (4.4GB) a formato Parquet para máxima velocidad. Esto tomará un par de minutos, por favor espera...", icon="⏳")
            conn = duckdb.connect()
            # We ignore errors to skip corrupted lines if any
            query = f"""
            COPY (
                SELECT * FROM read_csv_auto('{self.csv_path}', ignore_errors=true)
            ) TO '{self.parquet_path}' (FORMAT PARQUET);
            """
            conn.execute(query)
            conn.close()
            st.success("¡Conversión a Parquet completada! El dashboard ahora será ultra rápido.", icon="🚀")

    def _execute_query(self, query):
        conn = duckdb.connect()
        try:
            if self.is_cloud:
                # Ya no necesitamos httpfs, leemos de los archivos descargados en /tmp
                urls_str = ", ".join([f"'{url}'" for url in self.cloud_urls])
                data_source = f"read_parquet([{urls_str}])"
            else:
                data_source = f"'{self.parquet_path}'"

            cte = f"""
            WITH mef_data AS (
                SELECT 
                    * REPLACE (
                        TRY_CAST(MONTO_PIA AS DOUBLE) AS MONTO_PIA,
                        TRY_CAST(MONTO_PIM AS DOUBLE) AS MONTO_PIM,
                        TRY_CAST(MONTO_CERTIFICADO AS DOUBLE) AS MONTO_CERTIFICADO,
                        TRY_CAST(MONTO_COMPROMETIDO_ANUAL AS DOUBLE) AS MONTO_COMPROMETIDO_ANUAL,
                        TRY_CAST(MONTO_COMPROMETIDO AS DOUBLE) AS MONTO_COMPROMETIDO,
                        TRY_CAST(MONTO_DEVENGADO AS DOUBLE) AS MONTO_DEVENGADO,
                        TRY_CAST(MONTO_GIRADO AS DOUBLE) AS MONTO_GIRADO,
                        TRY_CAST(CATEGORIA_GASTO AS INTEGER) AS CATEGORIA_GASTO,
                        TRY_CAST(MES_EJE AS INTEGER) AS MES_EJE
                    )
                FROM {data_source}
            )
            """
            safe_query = cte + query.replace(f"'{self.parquet_path}'", "mef_data")
            return conn.execute(safe_query).df()
        finally:
            conn.close()

    def get_filter_options(self, column_name, filter_conditions=""):
        """Gets unique values for a column to populate dropdowns."""
        where_clause = f"WHERE {filter_conditions} AND" if filter_conditions else "WHERE"
        query = f"""
        SELECT DISTINCT {column_name}
        FROM '{self.parquet_path}'
        {where_clause} {column_name} IS NOT NULL
        ORDER BY {column_name}
        """
        df = self._execute_query(query)
        return df[column_name].tolist()
    
    def get_kpis_resumen(self, where_clause):
        """Calculates global KPIs based on filters."""
        query = f"""
        SELECT 
            SUM(MONTO_PIA) as PIA,
            SUM(MONTO_PIM) as PIM,
            SUM(MONTO_CERTIFICADO) as Certificado,
            SUM(MONTO_COMPROMETIDO_ANUAL) as Compromiso_Anual,
            SUM(MONTO_COMPROMETIDO) as Compromiso_Mensual,
            SUM(MONTO_DEVENGADO) as Devengado,
            SUM(MONTO_GIRADO) as Girado
        FROM '{self.parquet_path}'
        {where_clause}
        """
        return self._execute_query(query).iloc[0]

    def get_kpi_1_ieg(self, where_clause):
        """KPI 1: Indicador General de Eficacia de la Ejecución del Gasto (IEG) = DEVENGADO / PIM"""
        query = f"""
        SELECT 
            SUM(MONTO_DEVENGADO) as Devengado,
            SUM(MONTO_PIM) as PIM
        FROM '{self.parquet_path}'
        {where_clause}
        """
        res = self._execute_query(query).iloc[0]
        return (res['Devengado'] / res['PIM'] * 100) if res['PIM'] > 0 else 0

    def get_kpi_2_ieg_cap(self, where_clause):
        """KPI 2: Eficacia Sectorizada de Formación de Capital (Inversiones)"""
        # Filtro: CATEGORIA_GASTO = 6
        base_where = where_clause if where_clause.strip() != "" else "WHERE 1=1"
        query = f"""
        SELECT 
            SUM(MONTO_DEVENGADO) as Devengado_Cap,
            SUM(MONTO_PIM) as PIM_Cap
        FROM '{self.parquet_path}'
        {base_where} AND CATEGORIA_GASTO = 6
        """
        res = self._execute_query(query).iloc[0]
        return (res['Devengado_Cap'] / res['PIM_Cap'] * 100) if res['PIM_Cap'] > 0 else 0

    def get_kpi_3_iopr(self, where_clause):
        """KPI 3: Indicador de Orientación Presupuestal a Resultados (IOPR)"""
        # Excluyendo programas 9001 (Acciones Centrales) y 9002 (APNOP)
        base_where = where_clause if where_clause.strip() != "" else "WHERE 1=1"
        query = f"""
        SELECT 
            SUM(CASE WHEN CAST(PROGRAMA_PPTO AS VARCHAR) NOT IN ('9001', '9002') THEN MONTO_DEVENGADO ELSE 0 END) as Devengado_PpR,
            SUM(MONTO_DEVENGADO) as Devengado_Total
        FROM '{self.parquet_path}'
        {base_where}
        """
        res = self._execute_query(query).iloc[0]
        return (res['Devengado_PpR'] / res['Devengado_Total'] * 100) if res['Devengado_Total'] > 0 else 0

    def get_kpi_4_idg(self, where_clause):
        """KPI 4: Índice de Dinamismo y Fluidez del Gasto (Brechas)"""
        query = f"""
        SELECT 
            SUM(MONTO_CERTIFICADO) as Certificado,
            SUM(MONTO_COMPROMETIDO_ANUAL) as Compromiso_Anual,
            SUM(MONTO_DEVENGADO) as Devengado
        FROM '{self.parquet_path}'
        {where_clause}
        """
        res = self._execute_query(query).iloc[0]
        logistico = (res['Compromiso_Anual'] / res['Certificado'] * 100) if res['Certificado'] > 0 else 0
        ejecutivo = (res['Devengado'] / res['Compromiso_Anual'] * 100) if res['Compromiso_Anual'] > 0 else 0
        return logistico, ejecutivo

    def get_kpi_5_iced(self, where_clause):
        """KPI 5: Índice de Concentración Estacional (ICED) - Síndrome de Diciembre"""
        base_where = where_clause if where_clause.strip() != "" else "WHERE 1=1"
        query = f"""
        SELECT 
            SUM(CASE WHEN MES_EJE = 12 THEN MONTO_DEVENGADO ELSE 0 END) as Devengado_Dic,
            SUM(MONTO_DEVENGADO) as Devengado_Total
        FROM '{self.parquet_path}'
        {base_where}
        """
        res = self._execute_query(query).iloc[0]
        return (res['Devengado_Dic'] / res['Devengado_Total'] * 100) if res['Devengado_Total'] > 0 else 0

    def get_kpi_6_iv_pim(self, where_clause):
        """KPI 6: Variación Porcentual de Previsión (Estabilidad PIM)"""
        # Solo para inversiones (Categoria 6)
        base_where = where_clause if where_clause.strip() != "" else "WHERE 1=1"
        query = f"""
        SELECT 
            SUM(MONTO_PIA) as PIA_Cap,
            SUM(MONTO_PIM) as PIM_Cap
        FROM '{self.parquet_path}'
        {base_where} AND CATEGORIA_GASTO = 6
        """
        res = self._execute_query(query).iloc[0]
        return ((res['PIM_Cap'] - res['PIA_Cap']) / res['PIA_Cap'] * 100) if res['PIA_Cap'] > 0 else 0

    def get_kpi_7_autonomia(self, where_clause):
        """KPI 7: Ratio de Autonomía (RDR / Total)"""
        # Asumimos que RUBRO_NOMBRE conteniendo 'DIRECTAMENTE RECAUDADOS' es RDR (Rubro 09)
        base_where = where_clause if where_clause.strip() != "" else "WHERE 1=1"
        query = f"""
        SELECT 
            SUM(CASE WHEN RUBRO = '09' THEN MONTO_DEVENGADO ELSE 0 END) as Devengado_RDR,
            SUM(MONTO_DEVENGADO) as Devengado_Total
        FROM '{self.parquet_path}'
        {base_where}
        """
        res = self._execute_query(query).iloc[0]
        return (res['Devengado_RDR'] / res['Devengado_Total'] * 100) if res['Devengado_Total'] > 0 else 0

    def get_dictamen_data(self, where_clause):
        """Devuelve los componentes brutos para explicar las fórmulas de Evaluación de Gestión."""
        base_where = where_clause if where_clause.strip() != "" else "WHERE 1=1"
        query = f"""
        SELECT 
            SUM(CASE WHEN CATEGORIA_GASTO = 6 THEN MONTO_PIM ELSE 0 END) as PIM_Cap,
            SUM(CASE WHEN CATEGORIA_GASTO = 6 THEN MONTO_DEVENGADO ELSE 0 END) as Dev_Cap,
            SUM(MONTO_DEVENGADO) as Dev_Total,
            SUM(CASE WHEN MES_EJE = 12 THEN MONTO_DEVENGADO ELSE 0 END) as Dev_Dic,
            SUM(CASE WHEN CAST(PROGRAMA_PPTO AS VARCHAR) NOT IN ('9001', '9002') THEN MONTO_DEVENGADO ELSE 0 END) as Dev_PpR
        FROM '{self.parquet_path}'
        {base_where}
        """
        return self._execute_query(query).iloc[0]

    def get_kpi_breakdown(self, where_clause, kpi_type):
        """Devuelve el detalle del KPI agrupado por Unidad Ejecutora para disgregar los datos."""
        base_where = where_clause if where_clause.strip() != "" else "WHERE 1=1"
        
        if kpi_type == 'ieg':
            query = f"""
            SELECT 
                EJECUTORA_NOMBRE as Unidad_Ejecutora,
                SUM(MONTO_PIM) as PIM,
                SUM(MONTO_DEVENGADO) as Devengado,
                (SUM(MONTO_DEVENGADO) / NULLIF(SUM(MONTO_PIM), 0)) * 100 as KPI_Pct
            FROM '{self.parquet_path}'
            {base_where}
            GROUP BY EJECUTORA_NOMBRE
            HAVING SUM(MONTO_PIM) > 0
            ORDER BY KPI_Pct DESC
            """
        elif kpi_type == 'ieg_cap':
            query = f"""
            SELECT 
                EJECUTORA_NOMBRE as Unidad_Ejecutora,
                SUM(MONTO_PIM) as PIM_Inversiones,
                SUM(MONTO_DEVENGADO) as Devengado_Inversiones,
                (SUM(MONTO_DEVENGADO) / NULLIF(SUM(MONTO_PIM), 0)) * 100 as KPI_Pct
            FROM '{self.parquet_path}'
            {base_where} AND CATEGORIA_GASTO = 6
            GROUP BY EJECUTORA_NOMBRE
            HAVING SUM(MONTO_PIM) > 0
            ORDER BY KPI_Pct DESC
            """
        elif kpi_type == 'iopr':
            query = f"""
            SELECT 
                EJECUTORA_NOMBRE as Unidad_Ejecutora,
                SUM(MONTO_DEVENGADO) as Gasto_Total,
                SUM(CASE WHEN CAST(PROGRAMA_PPTO AS VARCHAR) NOT IN ('9001', '9002') THEN MONTO_DEVENGADO ELSE 0 END) as Gasto_Resultados,
                (SUM(CASE WHEN CAST(PROGRAMA_PPTO AS VARCHAR) NOT IN ('9001', '9002') THEN MONTO_DEVENGADO ELSE 0 END) / NULLIF(SUM(MONTO_DEVENGADO), 0)) * 100 as KPI_Pct
            FROM '{self.parquet_path}'
            {base_where}
            GROUP BY EJECUTORA_NOMBRE
            HAVING SUM(MONTO_DEVENGADO) > 0
            ORDER BY KPI_Pct DESC
            """
        elif kpi_type == 'logistica':
            query = f"""
            SELECT 
                EJECUTORA_NOMBRE as Unidad_Ejecutora,
                SUM(MONTO_CERTIFICADO) as Certificado,
                SUM(MONTO_COMPROMETIDO_ANUAL) as Compromiso,
                (SUM(MONTO_COMPROMETIDO_ANUAL) / NULLIF(SUM(MONTO_CERTIFICADO), 0)) * 100 as KPI_Pct
            FROM '{self.parquet_path}'
            {base_where}
            GROUP BY EJECUTORA_NOMBRE
            HAVING SUM(MONTO_CERTIFICADO) > 0
            ORDER BY KPI_Pct DESC
            """
        elif kpi_type == 'ejecutiva':
            query = f"""
            SELECT 
                EJECUTORA_NOMBRE as Unidad_Ejecutora,
                SUM(MONTO_COMPROMETIDO_ANUAL) as Compromiso,
                SUM(MONTO_DEVENGADO) as Devengado,
                (SUM(MONTO_DEVENGADO) / NULLIF(SUM(MONTO_COMPROMETIDO_ANUAL), 0)) * 100 as KPI_Pct
            FROM '{self.parquet_path}'
            {base_where}
            GROUP BY EJECUTORA_NOMBRE
            HAVING SUM(MONTO_COMPROMETIDO_ANUAL) > 0
            ORDER BY KPI_Pct DESC
            """
        else:
            return pd.DataFrame()
            
        return self._execute_query(query)
            
    def get_anios_disponibles(self):
        """Devuelve una lista con los años fiscales disponibles en la base de datos combinada."""
        try:
            query = f"SELECT DISTINCT ANO_EJE FROM '{self.parquet_path}' WHERE ANO_EJE IS NOT NULL ORDER BY ANO_EJE DESC"
            df = self._execute_query(query)
            return df['ANO_EJE'].dropna().astype(int).tolist()
        except Exception as e:
            import traceback
            st.error(f"Error cargando años: {e}")
            st.error(traceback.format_exc())
            return [2026] # Fallback if file not ready yet

    def get_proyectos_dict(self, where_clause):
        """Devuelve un diccionario de CUI -> 'CUI - Nombre' para el buscador SSI."""
        base_where = where_clause if where_clause.strip() != "" else "WHERE 1=1"
        query = f"""
        SELECT DISTINCT 
            PRODUCTO_PROYECTO as CUI, 
            CONCAT(CAST(PRODUCTO_PROYECTO AS VARCHAR), ' - ', PRODUCTO_PROYECTO_NOMBRE) as Proy_Name
        FROM '{self.parquet_path}'
        {base_where} AND CATEGORIA_GASTO = 6
        ORDER BY Proy_Name
        """
        df = self._execute_query(query)
        return dict(zip(df['CUI'].astype(str), df['Proy_Name']))

    def get_ficha_ssi(self, cui, where_clause):
        """Extrae la información detallada institucional y financiera de un proyecto para la Ficha SSI."""
        # Se requiere filtrar por CUI, pero sin perder el where_clause global si aplica
        base_where = where_clause if where_clause.strip() != "" else "WHERE 1=1"
        query = f"""
        SELECT 
            CAST(PRODUCTO_PROYECTO AS VARCHAR) as CUI,
            MAX(PRODUCTO_PROYECTO_NOMBRE) as Nombre_Inversion,
            MAX(EJECUTORA_NOMBRE) as OPMI_UEI,
            MAX(FUNCION_NOMBRE) as Funcion,
            SUM(MONTO_PIA) as PIA,
            SUM(MONTO_PIM) as PIM,
            SUM(MONTO_CERTIFICADO) as Certificado,
            SUM(MONTO_COMPROMETIDO_ANUAL) as Compromiso,
            SUM(MONTO_DEVENGADO) as Devengado
        FROM '{self.parquet_path}'
        {base_where} AND CATEGORIA_GASTO = 6 AND PRODUCTO_PROYECTO = '{cui}'
        GROUP BY PRODUCTO_PROYECTO
        """
        df = self._execute_query(query)
        if df.empty:
            return None
        return df.iloc[0].to_dict()

    def get_historico_ssi(self, cui, where_clause):
        """Extrae la tabla histórica agrupada por Año Fiscal para la Ficha SSI."""
        base_where = where_clause if where_clause.strip() != "" else "WHERE 1=1"
        query = f"""
        SELECT 
            ANO_EJE as Año,
            SUM(MONTO_PIA) as PIA,
            SUM(MONTO_PIM) as PIM,
            SUM(MONTO_CERTIFICADO) as Certificación,
            SUM(MONTO_COMPROMETIDO_ANUAL) as Compromiso_Anual,
            SUM(MONTO_DEVENGADO) as Devengado
        FROM '{self.parquet_path}'
        {base_where} AND CATEGORIA_GASTO = 6 AND PRODUCTO_PROYECTO = '{cui}'
        GROUP BY ANO_EJE
        ORDER BY ANO_EJE ASC
        """
        return self._execute_query(query)

    def get_ranking_riesgo_ssi(self, where_clause):
        """Genera una lista de proyectos ordenados por mayor riesgo financiero (menor % de avance)."""
        base_where = where_clause if where_clause.strip() != "" else "WHERE 1=1"
        query = f"""
        SELECT 
            CAST(PRODUCTO_PROYECTO AS VARCHAR) as CUI,
            PRODUCTO_PROYECTO_NOMBRE as Proyecto,
            MAX(EJECUTORA_NOMBRE) as Ejecutora,
            SUM(MONTO_PIM) as PIM,
            SUM(MONTO_DEVENGADO) as Devengado,
            (SUM(MONTO_DEVENGADO) / NULLIF(SUM(MONTO_PIM), 0)) * 100 as Pct_Avance
        FROM '{self.parquet_path}'
        {base_where} AND CATEGORIA_GASTO = 6
        GROUP BY PRODUCTO_PROYECTO, PRODUCTO_PROYECTO_NOMBRE
        HAVING SUM(MONTO_PIM) > 0
        ORDER BY Pct_Avance ASC
        LIMIT 50
        """
        return self._execute_query(query)

    def get_avance_proyectos(self, where_clause):
        """Data para Pestaña 2: Avance Presupuestal por Proyecto"""
        base_where = where_clause if where_clause.strip() != "" else "WHERE 1=1"
        query = f"""
        SELECT 
            CAST(PRODUCTO_PROYECTO AS VARCHAR) as CUI,
            PRODUCTO_PROYECTO_NOMBRE as Proyecto,
            SUM(MONTO_PIA) as PIA,
            SUM(MONTO_PIM) as PIM,
            SUM(MONTO_CERTIFICADO) as Certificado,
            SUM(MONTO_COMPROMETIDO_ANUAL) as Compromiso_Anual,
            SUM(MONTO_DEVENGADO) as Devengado
        FROM '{self.parquet_path}'
        {base_where} AND CATEGORIA_GASTO = 6
        GROUP BY PRODUCTO_PROYECTO, PRODUCTO_PROYECTO_NOMBRE
        HAVING SUM(MONTO_PIM) > 0
        ORDER BY Devengado DESC
        """
        return self._execute_query(query)

    def get_lista_proyectos(self, where_clause):
        """Devuelve la lista de proyectos para el filtro desplegable."""
        base_where = where_clause if where_clause.strip() != "" else "WHERE 1=1"
        query = f"""
        SELECT DISTINCT CONCAT(CAST(PRODUCTO_PROYECTO AS VARCHAR), ' - ', PRODUCTO_PROYECTO_NOMBRE) as Proy_Name
        FROM '{self.parquet_path}'
        {base_where} AND CATEGORIA_GASTO = 6
        ORDER BY Proy_Name
        """
        return self._execute_query(query)['Proy_Name'].tolist()

    def get_ejecutoras(self, where_clause):
        """Devuelve la lista de Unidades Ejecutoras."""
        base_where = where_clause if where_clause.strip() != "" else "WHERE 1=1"
        query = f"""
        SELECT DISTINCT CONCAT(CAST(SEC_EJEC AS VARCHAR), ' - ', EJECUTORA_NOMBRE) as Ejec_Name
        FROM '{self.parquet_path}'
        {base_where}
        ORDER BY Ejec_Name
        """
        return self._execute_query(query)['Ejec_Name'].tolist()

    def get_metas(self, where_clause):
        """Devuelve la lista de Metas Presupuestales (SEC_FUNC)."""
        base_where = where_clause if where_clause.strip() != "" else "WHERE 1=1"
        query = f"""
        SELECT DISTINCT CONCAT(CAST(SEC_FUNC AS VARCHAR), ' - ', META_NOMBRE) as Meta_Name
        FROM '{self.parquet_path}'
        {base_where}
        ORDER BY Meta_Name
        """
        return self._execute_query(query)['Meta_Name'].tolist()

    def get_curva_evolucion(self, where_clause):
        """Data para Pestaña 3: Curvas de Evolución (Mensual)"""
        base_where = where_clause if where_clause.strip() != "" else "WHERE 1=1"
        query = f"""
        SELECT 
            MES_EJE as Mes,
            SUM(MONTO_CERTIFICADO) as Certificado,
            SUM(MONTO_COMPROMETIDO_ANUAL) as Compromiso_Anual,
            SUM(MONTO_DEVENGADO) as Devengado,
            SUM(MONTO_GIRADO) as Girado
        FROM '{self.parquet_path}'
        {base_where}
        GROUP BY MES_EJE
        ORDER BY MES_EJE
        """
        return self._execute_query(query)

    def get_evolucion_acumulada(self, where_clause, total_pim):
        """Devuelve datos acumulados mes a mes para los gráficos ejecutivos."""
        base_where = where_clause if where_clause.strip() != "" else "WHERE 1=1"
        query = f"""
        SELECT 
            MES_EJE as Mes,
            SUM(MONTO_COMPROMETIDO) as Compromiso_Mensual,
            SUM(MONTO_DEVENGADO) as Devengado
        FROM '{self.parquet_path}'
        {base_where}
        GROUP BY MES_EJE
        ORDER BY MES_EJE
        """
        df = self._execute_query(query)
        if not df.empty:
            df['Comp_Acumulado'] = df['Compromiso_Mensual'].cumsum()
            df['Dev_Acumulado'] = df['Devengado'].cumsum()
            df['pct_Comp_Acumulado'] = (df['Comp_Acumulado'] / total_pim * 100) if total_pim > 0 else 0
            df['pct_Dev_Acumulado'] = (df['Dev_Acumulado'] / total_pim * 100) if total_pim > 0 else 0
            
            meses = {1:'Enero', 2:'Febrero', 3:'Marzo', 4:'Abril', 5:'Mayo', 6:'Junio', 
                     7:'Julio', 8:'Agosto', 9:'Setiembre', 10:'Octubre', 11:'Noviembre', 12:'Diciembre'}
            df['Mes_Nombre'] = df['Mes'].map(meses)
        return df

    def get_proyecciones(self, where_clause):
        """Data para Pestaña 4: Proyecciones de Gasto (Run Rate por Categoría)"""
        base_where = where_clause if where_clause.strip() != "" else "WHERE 1=1"
        query = f"""
        SELECT 
            CATEGORIA_GASTO_NOMBRE as Categoria,
            SUM(MONTO_PIM) as PIM,
            SUM(MONTO_DEVENGADO) as Devengado_Actual,
            MAX(MES_EJE) as Mes_Actual
        FROM '{self.parquet_path}'
        {base_where}
        GROUP BY CATEGORIA_GASTO_NOMBRE
        """
        df = self._execute_query(query)
        # Calculate Run Rate and Proyections
        df['RGM (Run Rate)'] = df['Devengado_Actual'] / df['Mes_Actual']
        df['Proyección_Cierre'] = df['RGM (Run Rate)'] * 12
        df['%_Proyectado_Cierre'] = (df['Proyección_Cierre'] / df['PIM']) * 100
        return df
        
    def get_spillover_alerts(self, where_clause):
        """Data para Pestaña 5: Alertas de Derrame (Spillovers)"""
        base_where = where_clause if where_clause.strip() != "" else "WHERE 1=1"
        query = f"""
        SELECT 
            PRODUCTO_PROYECTO_NOMBRE as Proyecto,
            SUM(MONTO_PIM) as PIM,
            SUM(MONTO_CERTIFICADO) as Certificado,
            SUM(MONTO_COMPROMETIDO_ANUAL) as Compromiso,
            SUM(MONTO_DEVENGADO) as Devengado,
            MAX(MES_EJE) as Mes_Eje
        FROM '{self.parquet_path}'
        {base_where} AND CATEGORIA_GASTO = 6
        GROUP BY PRODUCTO_PROYECTO_NOMBRE
        HAVING SUM(MONTO_PIM) > 0
        """
        df = self._execute_query(query)
        return df

    def get_ranking_ejecutora(self, where_clause):
        """Data para Pestaña 7: Ranking de Ejecución por Entidad/Ejecutora"""
        base_where = where_clause if where_clause.strip() != "" else "WHERE 1=1"
        query = f"""
        SELECT 
            EJECUTORA_NOMBRE as Entidad,
            SUM(MONTO_PIA) as PIA,
            SUM(MONTO_PIM) as PIM,
            SUM(MONTO_CERTIFICADO) as Cert,
            SUM(MONTO_COMPROMETIDO_ANUAL) as Comp,
            SUM(MONTO_DEVENGADO) as Dev
        FROM '{self.parquet_path}'
        {base_where}
        GROUP BY EJECUTORA_NOMBRE
        HAVING SUM(MONTO_PIM) > 0
        ORDER BY Dev DESC
        """
        df = self._execute_query(query)
        return df
        
    def get_distribucion_rubro_funcion(self, where_clause):
        """Data para Pestaña 7: Treemaps (Rubro y Función)"""
        base_where = where_clause if where_clause.strip() != "" else "WHERE 1=1"
        query = f"""
        SELECT 
            RUBRO_NOMBRE as Rubro,
            FUNCION_NOMBRE as Funcion,
            SUM(MONTO_PIM) as PIM,
            SUM(MONTO_DEVENGADO) as Devengado
        FROM '{self.parquet_path}'
        {base_where}
        GROUP BY RUBRO_NOMBRE, FUNCION_NOMBRE
        """
        return self._execute_query(query)
