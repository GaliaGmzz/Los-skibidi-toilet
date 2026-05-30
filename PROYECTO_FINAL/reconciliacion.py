def reconcile_desglose(desglose, filas_info, total_objetivo):
    """
    Ajusta el desglose de votos para que coincida con el total objetivo.
    - desglose: dict con votos por partido
    - filas_info: lista de filas con info cruda y normalizada
    - total_objetivo: total de votos esperado
    """
    current_sum = sum(desglose.values())
    diff = total_objetivo - current_sum

    # Caso ideal: ya coincide
    if diff == 0:
        return desglose

    # Intento 1: mover votos de filas sin canonical a vecinos
    candidates = [f for f in filas_info if not f.get("canonical")]
    for f in candidates:
        v = f.get("votos_detectados", 0)
        if v == 0:
            continue
        for neighbor_idx in (f["row_index"]-1, f["row_index"]+1):
            neigh = next((x for x in filas_info if x["row_index"] == neighbor_idx), None)
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

    # Intento 2: si la diferencia es pequeña, ajustar sospechosos
    if abs(diff) <= 5:
        suspect = [f for f in filas_info if f.get("numero_raw") and (" " in f["numero_raw"] or "." in f["numero_raw"])]
        if suspect:
            target = suspect[0]
            key = target.get("canonical") or target.get("fallback") or f"Fila_{target['row_index']}"
            temp = dict(desglose)
            temp[key] = temp.get(key, 0) + diff
            if sum(temp.values()) == total_objetivo:
                return temp

    # Si no se pudo reconciliar, devolver desglose original
    return desglose
