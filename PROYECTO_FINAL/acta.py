from config import client, DEBUG
from diccionarios import orden_partidos
from utils import cell_center, extraer_digitos, palabra_a_numero
from coaliciones import parse_party_cell
from reconciliacion import reconcile_desglose
import statistics

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
            if key_low.startswith("partido") or key_low.startswith("fila_"):
                continue
            print(f"  {partido}: {votos}")
        print("Validación:", "Correcta" if self.validar() else "Error en conteo")


def procesar_acta(ruta_archivo, id_casilla):
    with open(ruta_archivo, "rb") as f:
        poller = client.begin_analyze_document("prebuilt-document", document=f)
        result = poller.result()

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

    rows = {}
    filas_info = []
    for c in all_cells:
        r = c.row_index
        col = getattr(c, "column_index", None)
        rows.setdefault(r, {})[col] = (c.content or "").strip()

    sorted_row_indices = sorted(rows.keys())

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

    return Acta(id_casilla, total, desglose)
