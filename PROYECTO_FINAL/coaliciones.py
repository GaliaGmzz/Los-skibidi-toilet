from utils import fuzzy_normalize

COALITION_TOKEN_MAP = {
    "pan": "PAN", "pri": "PRI", "prd": "PRD", "verde": "PVEM", "pvem": "PVEM",
    "pt": "PT", "mc": "Movimiento Ciudadano", "movimiento": "Movimiento Ciudadano",
    "ciudadano": "Movimiento Ciudadano", "morena": "Morena",
    "nueva": "Nueva Alianza", "alianza": "Nueva Alianza",
    "abasano": "Movimiento Ciudadano"
}

def parse_party_cell(text_raw):
    """
    Recibe el texto crudo de una celda y devuelve:
    - canonical: nombre estandarizado (ej. 'Morena–PT')
    - components: lista de partidos detectados
    """
    if not text_raw:
        return None, []

    header_variants = [
        "partido, coalición o candidato/a",
        "partido coalición o candidato/a",
        "partido, coalicion o candidato/a"
    ]
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
            # Buscar coincidencias parciales
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
