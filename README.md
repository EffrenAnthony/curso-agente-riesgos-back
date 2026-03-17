# Agente IA — Gestión de Riesgos en Construcción

API con FastAPI que identifica riesgos de proyectos de construcción
a través de una conversación guiada con un LLM y genera un reporte PDF.

## Estructura del proyecto

```
agente-riesgos/
├── main.py              # FastAPI — endpoints principales
├── app/
│   ├── prompt.py        # System prompt del agente
│   └── pdf_generator.py # Generación del PDF con ReportLab
├── requirements.txt
├── Procfile             # Para deploy en Railway
├── .env.example         # Variables de entorno de ejemplo
└── .gitignore
```

## Instalación local

```bash
# 1. Clonar y entrar al proyecto
git clone <tu-repo>
cd agente-riesgos

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar API key
cp .env.example .env
# Editar .env y agregar tu OPENAI_API_KEY

# 5. Correr el servidor
uvicorn main:app --reload
```

La API corre en: http://localhost:8000
Documentación Swagger: http://localhost:8000/docs

## Endpoints

| Método | Endpoint              | Descripción                              |
|--------|-----------------------|------------------------------------------|
| POST   | /iniciar              | Crea sesión nueva, devuelve session_id   |
| POST   | /chat                 | Envía mensaje, recibe respuesta del agente|
| GET    | /reporte/{session_id} | Descarga el PDF de riesgos               |
| GET    | /health               | Estado del servidor                      |

## Deploy en Railway

1. Subir el proyecto a GitHub
2. Crear proyecto en Railway → "Deploy from GitHub repo"
3. En Variables: agregar `OPENAI_API_KEY`
4. Railway detecta el `Procfile` y hace el deploy automáticamente

## Conectar con Lovable

En Lovable, la URL base de la API es la URL de Railway:
```
https://tu-app.railway.app
```

El frontend debe:
1. Llamar a `POST /iniciar` al cargar → guardar `session_id`
2. Enviar cada mensaje a `POST /chat` con el `session_id`
3. Si `analysis_ready = true` → renderizar `risks_json` como tabla
4. Botón de descarga → `window.open(API_URL + '/reporte/' + session_id)`