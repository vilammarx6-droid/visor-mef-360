import duckdb
import os
import time
import pandas as pd

folder = r"C:\Users\marx_\Downloads"
out_folder = r"C:\Users\marx_\.gemini\antigravity\scratch\chumbi seguidor de proyectos"

conn = duckdb.connect()

def convert_gasto():
    years = [
        ("2022-Gasto.csv", "2022-Gasto-Diario.parquet"),
        ("2023-Gasto.csv", "2023-Gasto-Diario.parquet"),
        ("2024-Gasto.csv", "2024-Gasto-Diario.parquet"),
        ("2025-Gasto-Diario.csv", "2025-Gasto-Diario.parquet"),
        ("2026-Gasto-Diario.csv", "2026-Gasto-Diario.parquet")
    ]
    for csv_file, parquet_file in years:
        in_path = os.path.join(folder, csv_file)
        out_path = os.path.join(out_folder, parquet_file)
        if os.path.exists(in_path):
            print(f"Convirtiendo {in_path} a Parquet...")
            start = time.time()
            # Se usa latin1 o se asume UTF8, read_csv_auto maneja la mayoria
            query = f"""
            COPY (
                SELECT * FROM read_csv_auto('{in_path}', all_varchar=true, ignore_errors=true)
            ) TO '{out_path}' (FORMAT PARQUET)
            """
            try:
                conn.execute(query)
                size_mb = os.path.getsize(out_path) / (1024 * 1024)
                print(f"OK: {parquet_file} ({size_mb:.2f} MB) en {time.time() - start:.2f}s")
            except Exception as e:
                print(f"Error con {csv_file}: {e}")

def convert_ssi():
    in_path = os.path.join(folder, "2026-Seguimiento-PI.csv")
    out_path = os.path.join(out_folder, "seguimiento_inversiones.parquet")
    if os.path.exists(in_path):
        print(f"Convirtiendo y fusionando {in_path} con el historial...")
        start = time.time()
        
        try:
            # 1. Cargar el nuevo CSV a una tabla temporal
            conn.execute(f"CREATE OR REPLACE TABLE ssi_nuevo AS SELECT * FROM read_csv_auto('{in_path}', all_varchar=true, ignore_errors=true)")
            
            # 2. Unir con el historial existente (si existe) y deduplicar
            if os.path.exists(out_path):
                print("   -> Detectado historial previo. Actualizando...")
                # Agregamos las columnas necesarias del nuevo, y del viejo
                conn.execute(f"""
                CREATE OR REPLACE TABLE ssi_combinado AS
                SELECT PRODUCTO_PROYECTO, MAX(PRODUCTO_PROYECTO_NOMBRE) as PRODUCTO_PROYECTO_NOMBRE,
                       MAX(COSTO_ACTUAL) as COSTO_ACTUAL, MAX(MONTO_EJECUCION_TOTAL) as MONTO_EJECUCION_TOTAL,
                       MAX(SEC_EJEC) as SEC_EJEC
                FROM (
                    SELECT CAST(PRODUCTO_PROYECTO AS VARCHAR) as PRODUCTO_PROYECTO, CAST(PRODUCTO_PROYECTO_NOMBRE AS VARCHAR) as PRODUCTO_PROYECTO_NOMBRE, CAST(COSTO_ACTUAL AS VARCHAR) as COSTO_ACTUAL, CAST(MONTO_EJECUCION_TOTAL AS VARCHAR) as MONTO_EJECUCION_TOTAL, CAST(SEC_EJEC AS VARCHAR) as SEC_EJEC FROM ssi_nuevo
                    UNION ALL
                    SELECT CAST(PRODUCTO_PROYECTO AS VARCHAR), CAST(PRODUCTO_PROYECTO_NOMBRE AS VARCHAR), CAST(COSTO_ACTUAL AS VARCHAR), CAST(MONTO_EJECUCION_TOTAL AS VARCHAR), CAST(SEC_EJEC AS VARCHAR) FROM '{out_path}'
                )
                GROUP BY PRODUCTO_PROYECTO
                """)
            else:
                conn.execute("CREATE OR REPLACE TABLE ssi_combinado AS SELECT PRODUCTO_PROYECTO, PRODUCTO_PROYECTO_NOMBRE, COSTO_ACTUAL, MONTO_EJECUCION_TOTAL, SEC_EJEC FROM ssi_nuevo")

            # 3. Inyectar fechas
            fechas_path = os.path.join(out_folder, "fechas_inicio_mef.parquet")
            if os.path.exists(fechas_path):
                print("   -> Integrando historial de Anio_Inicio_MEF...")
                conn.execute(f"""
                CREATE OR REPLACE TABLE ssi_temp AS
                SELECT s.*, f.Anio_Inicio_MEF
                FROM ssi_combinado s
                LEFT JOIN '{fechas_path}' f ON s.PRODUCTO_PROYECTO = f.CUI
                """)
            else:
                conn.execute("CREATE OR REPLACE TABLE ssi_temp AS SELECT * FROM ssi_combinado")
            
            # Guardar
            conn.execute(f"COPY ssi_temp TO '{out_path}' (FORMAT PARQUET)")
            conn.execute("DROP TABLE ssi_temp; DROP TABLE ssi_combinado; DROP TABLE ssi_nuevo;")
            
            size_mb = os.path.getsize(out_path) / (1024 * 1024)
            print(f"OK: seguimiento_inversiones.parquet histórico ({size_mb:.2f} MB) en {time.time() - start:.2f}s")
        except Exception as e:
            print(f"Error con SSI: {e}")

def convert_infobras():
    # Obras Publicas (Avance)
    pub_file = os.path.join(folder, "DataSet-Obras-Publicas 09-06-2026.xlsx")
    pub_out = os.path.join(out_folder, "infobras_avance.parquet")
    if os.path.exists(pub_file):
        print("Convirtiendo INFObras Avance...")
        df = pd.read_excel(pub_file, skiprows=3)
        # Limpiar columnas
        df.columns = df.columns.str.replace(r'[^a-zA-Z0-9_]', '_', regex=True)
        conn.execute(f"COPY (SELECT * FROM df) TO '{pub_out}' (FORMAT PARQUET)")
        print(f"OK: infobras_avance.parquet")

    # Obras Paralizadas
    par_file = os.path.join(folder, "DataSet-Obras-Paralizadas 12-03-2025.xlsx")
    par_out = os.path.join(out_folder, "infobras_paralizadas.parquet")
    if os.path.exists(par_file):
        print("Convirtiendo INFObras Paralizadas...")
        df = pd.read_excel(par_file, skiprows=3)
        df.columns = df.columns.str.replace(r'[^a-zA-Z0-9_]', '_', regex=True)
        conn.execute(f"COPY (SELECT * FROM df) TO '{par_out}' (FORMAT PARQUET)")
        print(f"OK: infobras_paralizadas.parquet")

print("INICIANDO PROCESAMIENTO MASIVO...")
convert_ssi()
convert_infobras()
convert_gasto()

conn.close()
print("PROCESAMIENTO TERMINADO")
