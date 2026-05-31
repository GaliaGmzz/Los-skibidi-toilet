mapa_numeros = {
    "cero": 0, "uno": 1, "dos": 2, "tres": 3, "cuatro": 4,
    "cinco": 5, "seis": 6, "siete": 7, "ocho": 8, "nueve": 9,
    "diez": 10, "once": 11, "doce": 12, "trece": 13,
    "catorce": 14, "quince": 15, "dieciseis": 16, "dieciséis": 16,
    "diecisiete": 17, "dieciocho": 18, "diecinueve": 19,
    "veinte": 20, "treinta": 30, "cuarenta": 40, "cincuenta": 50,
    "cien": 100, "ciento": 100, "doscientos": 200, "trescientos": 300
}

normalizar = {
    "pan": "PAN", "pri": "PRI", "prd": "PRD", "verde": "PVEM",
    "pvem": "PVEM", "pt": "PT", "mc": "Movimiento Ciudadano",
    "morena": "Morena", "nueva alianza": "Nueva Alianza",
    "abasano": "Movimiento Ciudadano",
    "votos nulos": "Votos nulos", "total": "TOTAL"
}

valores_esperados = list(set(normalizar.values()))

orden_partidos = [
    "PAN","PRI","PRD","PVEM","PT","Movimiento Ciudadano","Morena",
    "Nueva Alianza","PVEM–PT","PVEM–PT–Morena","PVEM–Morena","Morena–PT",
    "Candidatos/as no registrados/as","Votos nulos","TOTAL"
]
