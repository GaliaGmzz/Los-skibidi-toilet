from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from difflib import get_close_matches
import statistics
import time
from random import uniform

# ----------------------------
# Configuración (modifica)
# ----------------------------
endpoint = "https://skibiditoilet1.cognitiveservices.azure.com/"
key = "ADSyzGDfYC8YEVMNICHUcAMHMtwpXBywwchJgAhJECToBff1TwPZJQQJ99CCACYeBjFXJ3w3AAALACOGr0Y2"
client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))

ROW_TOL = 0.010        # tolerancia para agrupar por Y (si hay bounding boxes)
FUZZY_CUTOFF = 0.82    # umbral fuzzy matching
DEBUG = False           # True para imprimir info de depuración

# Poller / retries
MAX_ANALYZE_ATTEMPTS = 3
ANALYZE_TIMEOUT = 120  # segundos por intento
POLL_INTERVAL = 1.5     # segundos entre checks

# ----------------------------
# Diccionarios y utilidades
# ----------------------------
mapa_numeros = {
    "cero": 0, "uno": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
    "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10,
    "once": 11, "doce": 12, "trece": 13, "catorce": 14, "quince": 15,
    "dieciseis": 16, "dieciséis": 16, "diecisiete": 17, "dieciocho": 18,
    "diecinueve": 19, "veinte": 20, "treinta": 30, "cuarenta": 40,
    "cincuenta": 50, "cien": 100, "ciento": 100, "doscientos": 200,
    "trescientos": 300, "trescientos sesenta y siete": 367,
    "ciento ochenta y tres": 183, "ciento veinticuatro": 124
}
def palabra_a_numero(texto):
    if not texto:
        return None
    t = texto.lower().strip()
    if t in mapa_numeros:
        return mapa_numeros[t]
    t2 = t.replace("-", " ").replace(" y ", " ").replace(",", " ")
    total = 0
    found = False
    for token in t2.split():
        if token in mapa_numeros:
            total += mapa_numeros[token]
            found = True
    return total if found else None

normalizar = {
    "pan": "PAN", "pri": "PRI", "prd": "PRD", "verde": "PVEM", "pvem": "PVEM",
    "pt": "PT", "mc": "Movimiento Ciudadano", "movimiento ciudadano": "Movimiento Ciudadano",
    "movimiento": "Movimiento Ciudadano", "ciudadano": "Movimiento Ciudadano",
    "morena": "Morena", "nueva alianza": "Nueva Alianza", "alianza": "Nueva Alianza",
    "abasano": "Movimiento Ciudadano",  # mapeo de OCR frecuente
    "verde pt": "PVEM–PT", "pvem-pt": "PVEM–PT",
    "pt morena": "Morena–PT", "morena-pt": "Morena–PT", "verde pt morena": "PVEM–PT–Morena",
    "pvem-pt-morena": "PVEM–PT–Morena", "verde morena": "PVEM–Morena",
    "coalición morena verde": "PVEM–Morena",
    "candidatos/as no registrados/as": "Candidatos/as no registrados/as",
    "candidatos/as no registrados": "Candidatos/as no registrados/as",
    "votos nulos": "Votos nulos", "total": "TOTAL"
}
valores_esperados = list(set(normalizar.values()))

COALITION_TOKEN_MAP = {
    "pan": "PAN", "pri": "PRI", "prd": "PRD", "verde": "PVEM", "pvem": "PVEM",
    "pt": "PT", "mc": "Movimiento Ciudadano", "movimiento": "Movimiento Ciudadano",
    "ciudadano": "Movimiento Ciudadano", "morena": "Morena",
    "nueva": "Nueva Alianza", "alianza": "Nueva Alianza",
    "abasano": "Movimiento Ciudadano"
}

orden_partidos = [
    "PAN","PRI","PRD","PVEM","PT","Movimiento Ciudadano","Morena",
    "Nueva Alianza","PVEM–PT","PVEM–PT–Morena","PVEM–Morena","Morena–PT",
    "PVEM–PT–Morena","Candidatos/as no registrados/as","Votos nulos","TOTAL"
]

# ----------------------------
# Utilidades espaciales y fuzzy
# ----------------------------
def cell_center(cell):
    if hasattr(cell, "bounding_box") and cell.bounding_box:
        pts = cell.bounding_box
        xs = [p.x for p in pts]
        ys = [p.y for p in pts]
        return (sum(xs)/len(xs), sum(ys)/len(ys))
    return None

def group_rows_by_y(cells, tol=ROW_TOL):
    centers = []
    for c in cells:
        ctr = cell_center(c)
        centers.append((c, ctr[1] if ctr else None))
    ys = [y for (_, y) in centers if y is not None]
    if not ys:
        rows = {}
        for c in cells:
            rows.setdefault(c.row_index, []).append(c)
        return [rows[k] for k in sorted(rows.keys())]
    sorted_centers = sorted(centers, key=lambda x: (x[1] is None, x[1]))
    groups = []
    current_group = []
    last_y = None
    for c, y in sorted_centers:
        if y is None:
            if current_group:
                groups.append(current_group)
                current_group = []
            groups.append([c])
            last_y = None
            continue
        if last_y is None:
            current_group = [c]
            last_y = y
            continue
        if abs(y - last_y) <= tol:
            current_group.append(c)
            last_y = (last_y + y) / 2.0
        else:
            groups.append(current_group)
            current_group = [c]
            last_y = y
    if current_group:
        groups.append(current_group)
    return groups

def fuzzy_normalize(name_raw, cutoff=FUZZY_CUTOFF):
    if not name_raw:
        return None
    key = name_raw.strip().lower().replace(".", "").replace(",", "").replace("–", "-")
    if key in normalizar:
        return normalizar[key]
    tokens = key.split()
    for t in tokens:
        if t in normalizar:
            return normalizar[t]
    claves = list(normalizar.keys())
    matches = get_close_matches(key, claves, n=1, cutoff=cutoff)
    if matches:
        return normalizar[matches[0]]
    matches2 = get_close_matches(key, valores_esperados, n=1, cutoff=cutoff)
    if matches2:
        return matches2[0]
    return None

def extraer_digitos(texto):
    if not texto:
        return None
    digits = "".join(ch for ch in texto if ch.isdigit())
    return int(digits) if digits else None

# ----------------------------
# Tokenizado y canonicalización de coaliciones
# ----------------------------
def parse_party_cell(text_raw):
    if not text_raw:
        return None, []
    header_variants = ["partido, coalición o candidato/a", "partido coalición o candidato/a", "partido, coalicion o candidato/a"]
    if text_raw.strip().lower() in header_variants:
        return None, []
    t = text_raw.lower().replace("\n", " ").replace(",", " ").replace(".", " ")
    tokens = [tok.strip() for tok in t.split() if tok.strip()]
    components = []
    for tok in tokens:
        if tok in ("coalición", "coalicion", "y", "con", "de", "la", "el"):
            continue
        mapped = COALITION_TOKEN_MAP.get(tok)
        if mapped and mapped not in components:
            components.append(mapped)
        else:
            for k, v in COALITION_TOKEN_MAP.items():
                if k in tok and v not in components:
                    components.append(v)
                    break
    if not components:
        norm = fuzzy_normalize(text_raw)
        if norm:
            components = [norm]
    order = ["PAN","PRI","PRD","PVEM","PT","Movimiento Ciudadano","Morena","Nueva Alianza"]
    components_sorted = sorted(components, key=lambda x: order.index(x) if x in order else 999)
    if not components_sorted:
        return None, []
    canonical = components_sorted[0] if len(components_sorted) == 1 else "–".join(components_sorted)
    return canonical, components_sorted

# ----------------------------
# Reconciliación automática
# ----------------------------
def reconcile_desglose(desglose, filas_info, total_objetivo):
    current_sum = sum(desglose.values())
    diff = total_objetivo - current_sum
    if diff == 0:
        return desglose
    candidates = [f for f in filas_info if not f.get("canonical")]
    for f in candidates:
        v = f.get("votos_detectados", 0)
        if v == 0:
            continue
        for neighbor_idx in (f["row_index"]-1, f["row_index"]+1):
            neigh = next((x for x in filas_info if x["row_index"]==neighbor_idx), None)
            if not neigh:
                continue
            neigh_key = neigh.get("canonical") or neigh.get("fallback")
            if not neigh_key:
                continue
            temp = dict(desglose)
            orig_key = f.get("canonical") or f.get("fallback") or f.get("raw") or f"Fila_{f['row_index']}"
            temp[orig_key] = temp.get(orig_key, 0) - v
            if temp[orig_key] <= 0:
                temp.pop(orig_key, None)
            temp[neigh_key] = temp.get(neigh_key, 0) + v
            if sum(temp.values()) == total_objetivo:
                return temp
    if abs(diff) <= 5:
        suspect = [f for f in filas_info if f.get("numero_raw") and (" " in f["numero_raw"] or "." in f["numero_raw"])]
        if suspect:
            target = suspect[0]
            key = target.get("canonical") or target.get("fallback") or f"Fila_{target['row_index']}"
            temp = dict(desglose)
            temp[key] = temp.get(key, 0) + diff
            if sum(temp.values()) == total_objetivo:
                return temp
    return desglose

# ----------------------------
# Poller robusto con reintentos
# ----------------------------
def analyze_with_retries(file_obj, max_attempts=MAX_ANALYZE_ATTEMPTS):
    attempt = 0
    while attempt < max_attempts:
        attempt += 1
        try:
            poller = client.begin_analyze_document("prebuilt-document", document=file_obj)
            start = time.time()
            while not poller.done():
                elapsed = time.time() - start
                if elapsed > ANALYZE_TIMEOUT:
                    try:
                        poller.cancel()
                    except Exception:
                        pass
                    raise TimeoutError(f"Análisis excedió {ANALYZE_TIMEOUT} s en intento {attempt}")
                if DEBUG:
                    try:
                        status = poller.status()
                    except Exception:
                        status = "unknown"
                    print(f"[DEBUG] Poller status: {status} attempt={attempt} elapsed={int(elapsed)}s")
                time.sleep(POLL_INTERVAL)
            result = poller.result()
            return result
        except KeyboardInterrupt:
            try:
                poller.cancel()
            except Exception:
                pass
            print("Interrumpido por el usuario. Poller cancelado.")
            raise
        except Exception as e:
            print(f"[WARN] Intento {attempt} falló: {e}")
            if attempt >= max_attempts:
                raise
            backoff = (2 ** attempt) + uniform(0, 1)
            print(f"[INFO] Reintentando en {backoff:.1f}s...")
            time.sleep(backoff)
    return None

# ----------------------------
# Clase Acta y procesamiento principal
# ----------------------------
class Acta:
    def __init__(self, id_casilla, total_votos, desglose_partidos):
        self.id_casilla = id_casilla
        self.total_votos = total_votos
        self.desglose_partidos = desglose_partidos

    def validar(self):
        return sum(self.desglose_partidos.values()) == self.total_votos

    def mostrar(self):
        print(f"Acta de casilla: {self.id_casilla}")
        print(f"Total de votos: {self.total_votos}")
        print("Desglose por partido:")
        for partido, votos in self.desglose_partidos.items():
            key_low = partido.strip().lower()
            if key_low.startswith("partido") or key_low.startswith("fila_") or partido.strip() == "":
                continue
            print(f"  {partido}: {votos}")
        print("Validación:", "Correcta" if self.validar() else "Error en conteo")

def procesar_acta(ruta_archivo, id_casilla):
    with open(ruta_archivo, "rb") as f:
        result = analyze_with_retries(f)
    if result is None:
        raise RuntimeError("No se pudo analizar el documento después de varios intentos.")

    # recolectar celdas
    all_cells = []
    bbox_count = 0
    for table in result.tables:
        for cell in table.cells:
            all_cells.append(cell)
            if cell_center(cell) is not None:
                bbox_count += 1

    total_cells = len(all_cells)
    bbox_ratio = (bbox_count / total_cells) if total_cells else 0.0
    if DEBUG:
        print(f"[DEBUG] Celdas totales detectadas: {total_cells}")
        print(f"[DEBUG] Celdas con bbox: {bbox_count} (ratio={bbox_ratio:.2f})")

    # construir mapa row_index -> {col_index: texto}
    rows = {}
    filas_info = []
    for c in all_cells:
        r = c.row_index
        col = getattr(c, "column_index", None)
        rows.setdefault(r, {})[col] = (c.content or "").strip()

    sorted_row_indices = sorted(rows.keys())

    # detectar matches directos para calcular offset
    matches = []
    for r in sorted_row_indices:
        col0 = rows[r].get(0, "").strip()
        if col0.strip().lower().startswith("partido"):
            if DEBUG:
                print(f"[DEBUG] Ignorando encabezado en row {r}: '{col0}'")
            col0 = ""
        canonical, components = parse_party_cell(col0)
        if canonical:
            try:
                expected_idx = orden_partidos.index(canonical)
            except ValueError:
                expected_idx = None
            if expected_idx is not None:
                matches.append((r, expected_idx))
                if DEBUG:
                    print(f"[DEBUG] Match detectado row {r} -> '{col0}' canonical='{canonical}' expected_idx={expected_idx}")

    offset = 0
    if matches:
        offsets = [detected - expected for (detected, expected) in matches]
        offset = int(statistics.median(offsets))
        if DEBUG:
            print(f"[DEBUG] Offsets detectados: {offsets} mediana offset={offset}")
    else:
        if DEBUG:
            print("[DEBUG] No se detectaron matches confiables; offset=0 (sin ajuste)")

    # parsear filas y construir filas_info
    for r in sorted_row_indices:
        cols = rows[r]
        partido_raw = cols.get(0, "").strip()
        if partido_raw.strip().lower().startswith("partido"):
            partido_raw = ""
        letra_raw = cols.get(1, "").strip()
        numero_raw = cols.get(2, "").strip()
        canonical, components = parse_party_cell(partido_raw)
        expected_idx = r - offset
        fallback = None
        if not canonical:
            if 0 <= expected_idx < len(orden_partidos):
                fallback = orden_partidos[expected_idx]
            else:
                fallback = (partido_raw or f"Fila_{r}").strip().capitalize()
        votos = extraer_digitos(numero_raw)
        if votos is None:
            votos = palabra_a_numero(letra_raw)
        if votos is None:
            votos = 0
        filas_info.append({
            "row_index": r,
            "raw": partido_raw,
            "numero_raw": numero_raw,
            "letra_raw": letra_raw,
            "canonical": canonical,
            "components": components,
            "fallback": fallback,
            "votos_detectados": votos
        })

    # construir desglose sumando por clave canonical o fallback
    desglose = {}
    total = 0
    for f in filas_info:
        key = f["canonical"] or f["fallback"]
        votos = f["votos_detectados"] or 0
        if key == "TOTAL":
            total = votos
        else:
            desglose[key] = desglose.get(key, 0) + votos

    if DEBUG:
        print(f"[DEBUG] Desglose antes de reconciliar: {desglose} total_detectado={total}")

    if total == 0:
        total = sum(desglose.values())
    desglose_reconciliado = reconcile_desglose(desglose, filas_info, total)
    if DEBUG and desglose_reconciliado != desglose:
        print(f"[DEBUG] Desglose reconciliado: {desglose_reconciliado}")
    desglose = desglose_reconciliado

    # eliminar claves vacías o encabezados del diccionario final
    keys_to_remove = [k for k in desglose.keys() if not k or k.strip().lower().startswith("partido") or k.strip().lower().startswith("fila_")]
    for k in keys_to_remove:
        desglose.pop(k, None)

    return Acta(id_casilla, total, desglose)

# ----------------------------
# Uso / pruebas
# ----------------------------
def main():
    archivos = [
        ("c:/Users/gomez/OneDrive/Documentos/Programación/Programacion 2/proyectox/Visual/Acta1.JPG", "MX-001"),
        ("c:/Users/gomez/OneDrive/Documentos/Programación/Programacion 2/proyectox/Visual/acta2.JPG", "MX-001"),
        ("c:/Users/gomez/OneDrive/Documentos/Programación/Programacion 2/proyectox/Visual/acta3.JPG", "MX-001")
    ]
    for ruta, id_casilla in archivos:
        try:
            acta = procesar_acta(ruta, id_casilla)
            acta.mostrar()
            print("-" * 40)
        except Exception as e:
            print(f"[ERROR] No se pudo procesar {ruta}: {e}")

if __name__ == "__main__":
    main()