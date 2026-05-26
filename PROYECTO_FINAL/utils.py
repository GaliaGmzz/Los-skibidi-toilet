from difflib import get_close_matches
from diccionarios import mapa_numeros, normalizar, valores_esperados

def palabra_a_numero(texto):
    """
    Convierte un texto con número escrito en palabras a su valor numérico.
    Usa directamente el diccionario mapa_numeros.
    """
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

def cell_center(cell):
    if hasattr(cell, "bounding_box") and cell.bounding_box:
        pts = cell.bounding_box
        xs = [p.x for p in pts]
        ys = [p.y for p in pts]
        return (sum(xs)/len(xs), sum(ys)/len(ys))
    return None

def fuzzy_normalize(name_raw, cutoff=0.82):
    if not name_raw:
        return None
    key = name_raw.strip().lower().replace(".", "").replace(",", "").replace("–", "-")
    if key in normalizar:
        return normalizar[key]
    tokens = key.split()
    for t in tokens:
        if t in normalizar:
            return normalizar[t]
    matches = get_close_matches(key, list(normalizar.keys()), n=1, cutoff=cutoff)
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

