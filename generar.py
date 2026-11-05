from pathlib import Path
import pandas as pd

# Directorio actual donde tienes tu proyecto
base = Path.cwd()
source = base / "EJercio codigo vsc luciano.txt"
catalog_path = base / "datos.csv"

print(f"Buscando el archivo de texto en: {source}")

if not source.exists():
    print(f"\n⚠️ ERROR: No se encuentra 'EJercio codigo vsc luciano.txt' en:\n{base}")
    print("Por favor, asegúrate de que el archivo esté en esta misma carpeta y tenga exactamente ese nombre.")
else:
    # Lee el archivo de texto separado por tabulaciones y limpia los datos
    df = pd.read_csv(source, sep="\t", dtype=str).fillna("")
    df.columns = [c.strip() for c in df.columns]
    
    if "Objetivo" in df.columns:
        df["Objetivo"] = df["Objetivo"].replace("", pd.NA).ffill().fillna("")
    if "Ejercicios" in df.columns:
        df["Ejercicios"] = df["Ejercicios"].str.strip()
    if "Ejecucion" in df.columns:
        df["Ejecucion"] = df["Ejecucion"].str.strip()
        
    df = df[(df["Ejercicios"] != "") & (df["Ejecucion"] != "")]
    
    # Guarda el resultado como datos.csv en la misma carpeta
    df.to_csv(catalog_path, index=False, encoding="utf-8-sig")
    print(f"\n✅ ¡Listo! Se ha creado con éxito el archivo 'datos.csv' con {len(df)} ejercicios.")
    print("Ya puedes volver a ejecutar tu aplicación con: streamlit run app.py")