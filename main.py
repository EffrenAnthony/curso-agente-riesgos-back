import json
import uuid
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

from app.prompt import SYSTEM_PROMPT
from app.pdf_generator import generate_pdf

load_dotenv()

app = FastAPI(title="Agente de Riesgos", version="1.0.0")

# ── CORS — permite que Lovable llame a esta API ──────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # en producción pon la URL de Lovable
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Almacén de sesiones en memoria
# En producción: usar Redis o una base de datos
sessions: dict[str, list] = {}


# ── MODELOS ───────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    session_id: str
    message: str


class IniciarResponse(BaseModel):
    session_id: str
    mensaje: str


# ── ENDPOINTS ─────────────────────────────────────────────────────

@app.post("/iniciar", response_model=IniciarResponse)
async def iniciar():
    """Crea una sesión nueva y devuelve el session_id."""
    sid = str(uuid.uuid4())
    sessions[sid] = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]
    return {
        "session_id": sid,
        "mensaje": "Sesión iniciada. El agente está listo."
    }


@app.post("/chat")
async def chat(body: ChatRequest):
    """
    Recibe el mensaje del usuario, llama al LLM con el historial
    completo y devuelve la respuesta.

    Cuando el agente termina las preguntas devuelve:
      - analysis_ready: True
      - risks_json: el JSON de riesgos parseado (para que Lovable
                    pueda renderizar la tabla con colores)
    """
    sid = body.session_id

    if sid not in sessions:
        raise HTTPException(status_code=404, detail="Sesión no encontrada. Llama a /iniciar primero.")

    # Agregar mensaje del usuario al historial
    sessions[sid].append({
        "role": "user",
        "content": body.message
    })

    # Llamar al LLM
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=sessions[sid],
        temperature=0.3,    # bajo = más consistente para análisis técnico
        max_tokens=2000,
    )

    reply = response.choices[0].message.content

    # Guardar respuesta en el historial
    sessions[sid].append({
        "role": "assistant",
        "content": reply
    })

    # ── Detectar si el agente terminó las preguntas ──
    analysis_ready = "ANÁLISIS_LISTO" in reply
    risks_json = None

    if analysis_ready:
        try:
            # Extraer el JSON que viene después de "ANÁLISIS_LISTO"
            json_str = reply.split("ANÁLISIS_LISTO", 1)[1].strip()

            # Limpiar posibles bloques de código markdown ```json ... ```
            if json_str.startswith("```"):
                json_str = json_str.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]

            risks_json = json.loads(json_str.strip())

            # Guardar el JSON parseado en la sesión para usarlo en /reporte
            sessions[sid + "_data"] = risks_json

        except (json.JSONDecodeError, IndexError) as e:
            # Si falla el parseo, el frontend muestra el mensaje sin tabla
            analysis_ready = False
            print(f"Error parseando JSON: {e}")

    return {
        "message": "Análisis completado. Puedes descargar el reporte a continuación." if analysis_ready else reply,
        "analysis_ready": analysis_ready,
        "risks_json": risks_json,   # None si no terminó, dict si terminó
        "session_id": sid,
    }


@app.get("/reporte/{session_id}")
async def get_report(session_id: str):
    """
    Genera el PDF de riesgos a partir del JSON almacenado en la sesión
    y lo devuelve como archivo descargable.
    """
    data_key = session_id + "_data"

    if data_key not in sessions:
        raise HTTPException(
            status_code=404,
            detail="No hay análisis disponible para esta sesión. Completa la conversación primero."
        )

    data = sessions[data_key]

    try:
        pdf_bytes = generate_pdf(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando PDF: {str(e)}")

    nombre_proyecto = data.get("proyecto", {}).get("nombre", "proyecto").replace(" ", "_")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="Reporte_Riesgos_{nombre_proyecto}.pdf"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        }
    )


@app.get("/health")
async def health():
    """Endpoint de salud — Railway lo usa para verificar que el servidor está corriendo."""
    return {"status": "ok", "sesiones_activas": len([k for k in sessions if "_data" not in k])}