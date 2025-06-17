import os
import glob
import pdfplumber
from docx import Document
from odf.opendocument import load
from odf.text import P
import requests
import json
import shutil
import re

def extraer_texto_archivo(ruta_archivo):
    texto = ""
    ext = os.path.splitext(ruta_archivo)[1].lower()

    try:
        if ext == '.pdf':
            with pdfplumber.open(ruta_archivo) as pdf:
                texto = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
        elif ext == '.docx':
            doc = Document(ruta_archivo)
            texto = "\n".join([p.text for p in doc.paragraphs])
        elif ext == '.odt':
            odt_doc = load(ruta_archivo)
            textos = odt_doc.getElementsByType(P)
            texto = "\n".join([t.firstChild.data if t.firstChild else "" for t in textos])
        elif ext == '.txt':
            with open(ruta_archivo, "r", encoding="utf-8", errors="ignore") as f:
                texto = f.read()
    except Exception as e:
        print(f"\u274C Error leyendo {ruta_archivo}: {e}")
    return texto.strip()

def recorrer_carpeta_y_extraer_textos(carpeta):
    archivos = glob.glob(os.path.join(carpeta, '**'), recursive=True)
    resultados = []

    for archivo in archivos:
        if os.path.isfile(archivo) and archivo.lower().endswith(('.pdf', '.docx', '.odt', '.txt')):
            print(f"\U0001F4C4 Procesando: {archivo}")
            texto = extraer_texto_archivo(archivo)
            if texto:
                resultados.append({
                    "archivo": archivo,
                    "texto": texto
                })
    return resultados

def detectar_referencia(texto):
    coincidencias = re.findall(r"\b2[\dA-Z]{6,}\b", texto)
    if coincidencias:
        return coincidencias[0]
    return ""

def obtener_tags_desde_ollama(texto, modelo="deepseek-r1:8b"):
    """Enviar el texto al modelo local de Ollama y extraer tags en formato JSON."""
    prompt = (
        "Eres un asistente experto en seguros. Analiza el siguiente texto y genera los siguientes tags si puedes:\n"
        "- Compa\u00F1\u00EDa aseguradora\n"
        "- Tipo de p\u00F3liza o ramo\n"
        "- Tipo de da\u00F1o\n"
        "- Cobertura aplicable\n"
        "- Tipo de indemnizaci\u00F3n\n"
        "- Valoraci\u00F3n econ\u00F3mica del da\u00F1o (aproximada si aparece)\n"
        "- Modelo de p\u00F3liza (si se indica en el documento)\n\n"
        "Devu\u00E9lvelo en este formato JSON:\n"
        "{{\n"
        "  \"compa\u00F1\u00EDa\": \"...\",\n"
        "  \"ramo\": \"...\",\n"
        "  \"da\u00F1o\": \"...\",\n"
        "  \"cobertura\": \"...\",\n"
        "  \"indemnizaci\u00F3n\": \"...\",\n"
        "  \"valoraci\u00F3n\": \"...\",\n"
        "  \"modelo_poliza\": \"...\"\n"
        "}}\n\n"
        "Texto:\n"
        f'"""{texto[:3000]}"""'
    )

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": modelo,
                "prompt": prompt,
                "stream": False
            }
        )
        if response.ok:
            salida = response.json().get('response', '')
            print("\U0001F50E Respuesta RAW:")
            print(salida)

            inicio = salida.find('{')
            fin = salida.rfind('}') + 1
            bloque_json = salida[inicio:fin]

            try:
                tags = json.loads(bloque_json)
                return tags
            except Exception as e:
                print("\u26A0\uFE0F No se pudo interpretar el JSON:", e)
                print("Texto detectado como posible JSON:")
                print(bloque_json)
                return None
        else:
            print("\u274C Error en la llamada:", response.status_code)
            return None
    except Exception as e:
        print("\u274C Error al conectar con Ollama:", e)
        return None

def normalizar(texto):
    if not texto:
        return ""
    return texto.replace(" ", "").replace(",", "").replace(":", "").replace(";", "").replace("/", "_").lower()

# === EJECUCI\u00D3N PRINCIPAL ===

carpeta = r"C:\MEGA"
carpeta_destino = r"C:\MEGA3"
os.makedirs(carpeta_destino, exist_ok=True)

resultados = recorrer_carpeta_y_extraer_textos(carpeta)

print(f"\n\u2705 Se han extra\u00EDdo textos de {len(resultados)} archivos.\n")

for resultado in resultados:
    archivo = resultado["archivo"]
    texto = resultado["texto"]

    print(f"\n\u23F3 Etiquetando: {archivo}")
    referencia = detectar_referencia(texto)
    tags = obtener_tags_desde_ollama(texto)

    if not tags:
        tags = {}

    if referencia:
        tags["referencia"] = referencia

    resultado["tags"] = tags

    if not tags.get("referencia"):
        print(f"\u26A0\uFE0F Saltando {archivo}, no tiene referencia v\u00E1lida.")
        continue

    ref = tags.get("referencia", "SINREF")
    comp = normalizar(tags.get("compa\u00F1\u00EDa", ""))
    ramo = normalizar(tags.get("ramo", ""))
    dano = normalizar(tags.get("da\u00F1o", ""))
    cobertura = normalizar(tags.get("cobertura", ""))
    valoracion = normalizar(tags.get("valoraci\u00F3n", ""))
    modelo = normalizar(tags.get("modelo_poliza", ""))

    nombre_base = "_".join(filter(None, [ref, comp, ramo, dano, cobertura, valoracion, modelo]))
    extension = os.path.splitext(archivo)[1]
    nuevo_nombre = f"{nombre_base}{extension}"

    destino = os.path.join(carpeta_destino, nuevo_nombre)

    try:
        shutil.copy2(archivo, destino)
        print(f"\U0001F4C1 Copiado como: {destino}")
    except Exception as e:
        print(f"\u274C Error al copiar {archivo}: {e}")
