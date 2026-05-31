from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import tempfile
from acta import procesar_acta

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/procesar_acta/")
async def procesar(file: UploadFile = File(...)):
    # Guardar archivo temporalmente
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    acta = procesar_acta(tmp_path, "SIN_ID")

    # Filtrar filas basura
    desglose_filtrado = {
        partido: votos
        for partido, votos in acta.desglose_partidos.items()
        if not partido.lower().startswith("fila")
        and partido.lower() != "total"
    }

    return {
        "id_casilla": acta.id_casilla,
        "total_votos": acta.total_votos,
        "desglose_partidos": desglose_filtrado
    }

#cd "C:\Users\gomez\OneDrive\Documentos\Programación\Programacion 2\proyectox\Visual"
#uvicorn server:app --reload
