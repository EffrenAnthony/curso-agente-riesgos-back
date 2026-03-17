# Prompt para Lovable — Agente IA de Gestión de Riesgos

Crea una aplicación web de una sola página con estilo moderno y minimalista,
inspirada en Typeform. La app es un agente conversacional que identifica riesgos
en proyectos de construcción.

---

## STACK Y URL BASE

- React + Tailwind CSS
- API base URL: https://curso-agente-riesgos-back-production-9517.up.railway.app
- Endpoints:
  - POST /iniciar → devuelve { session_id, mensaje }
  - POST /chat    → body: { session_id, message } → devuelve { message, analysis_ready, risks_json, session_id }
  - GET  /reporte/{session_id} → descarga el PDF

---

## DISEÑO GENERAL

- Fondo: azul muy oscuro (#020d1f) en toda la página
- Fuente principal: Inter o similar sans-serif moderna
- Un solo elemento visible a la vez, centrado en pantalla (estilo Typeform)
- Animaciones suaves de entrada (fade + slide up) entre pantallas
- Sin navbar, sin sidebar, sin footer visible — pantalla completa limpia

---

## PANTALLA 1 — BIENVENIDA (pantalla inicial)

Mostrar centrado verticalmente:

- Badge superior: "Agente IA · ISO 31000" en texto pequeño con borde, color azul eléctrico (#38b6ff)
- Título grande (60-70px): "Identifica los riesgos de tu proyecto" en blanco, bold
- Subtítulo (18px): "Responde algunas preguntas. La IA analiza y genera tu reporte de riesgos en PDF." en gris claro
- Botón grande: "Comenzar análisis →" con fondo azul eléctrico (#38b6ff), texto oscuro, bordes redondeados, padding generoso
- Texto pequeño debajo del botón: "~5 minutos · Gratis · Sin registro"

Al hacer clic en el botón:
1. Llamar a POST /iniciar
2. Guardar el session_id en estado local (useState)
3. Llamar a POST /chat con { session_id, message: "Hola, quiero analizar los riesgos de mi proyecto" }
4. Transición animada a la PANTALLA 2 con la primera pregunta del agente

---

## PANTALLA 2 — CONVERSACIÓN (estilo Typeform)

Layout de pantalla completa con:

### Barra de progreso (top)
- Barra delgada (3px) en la parte superior
- Color azul eléctrico (#38b6ff)
- Progreso estimado: avanza de 0% a 90% durante las preguntas (incrementa ~7.5% por respuesta)
- A la derecha de la barra: contador "Pregunta X de ~12" en texto pequeño gris

### Zona central (el corazón de la UI)
Centrado vertical y horizontal, max-width 680px:

**Burbuja del agente** (aparece con animación fade-in):
- Pequeño avatar circular a la izquierda: fondo azul eléctrico, icono de robot o "IA" en blanco
- Texto de la pregunta en blanco, 22-24px, line-height amplio
- Aparece con efecto de "typing" (los 3 puntos animados por 0.8 segundos antes de mostrar el texto)

**Input de respuesta** (aparece 0.5s después del texto):
- Campo de texto grande, fondo semitransparente (#0a1628), borde sutil azul
- Placeholder: "Escribe tu respuesta aquí..."
- Sin label visible — el placeholder es suficiente
- Botón "Enviar →" o presionar Enter para enviar
- Al enviar: mostrar la respuesta del usuario como burbuja alineada a la derecha
  (fondo #1a4a7a, texto blanco, border-radius 16px 16px 4px 16px)

**Historial de conversación**:
- Mostrar las últimas 3-4 burbujas intercaladas (agente izquierda, usuario derecha)
- Las anteriores se desvanecen suavemente hacia arriba (opacity más baja)
- Auto-scroll al último mensaje

### Lógica de envío
```
const sendMessage = async (userMessage) => {
  // 1. Mostrar burbuja del usuario inmediatamente
  // 2. Mostrar typing indicator
  // 3. Llamar a POST /chat con { session_id, message: userMessage }
  // 4. Si analysis_ready === false → mostrar respuesta como nueva pregunta
  // 5. Si analysis_ready === true → transición a PANTALLA 3
}
```

---

## PANTALLA 3 — RESULTADOS

Cuando analysis_ready === true, transición con animación a esta pantalla.

### Header de resultados
- Ícono de check grande animado (círculo verde con checkmark, animación de dibujado)
- Título: "Análisis completado" en blanco, 40px
- Subtítulo: "Se identificaron X riesgos en tu proyecto" (X viene de risks_json.riesgos.length)

### Resumen de métricas (4 cards en fila)
Cards con fondo #0a2540, borde sutil, border-radius 12px:
- **Riesgos Altos**: número grande en rojo (#dc3545)
- **Riesgos Medios**: número grande en naranja (#fd7e14)
- **Riesgos Bajos**: número grande en verde (#22c55e)
- **Contingencia rec.**: número en azul eléctrico, formato "$XXXk"

Calcular conteos desde risks_json.riesgos filtrando por nivel.

### Tabla de riesgos
Tabla con fondo #081729, bordes sutiles entre filas:

Columnas: ID | Riesgo | Categoría | P | I | Score | Nivel | Acción

- Columna "Nivel" con badge de color:
  - Alto  → badge rojo   (bg #fde8ea, text #dc3545, border #dc3545)
  - Medio → badge naranja (bg #fff0e0, text #fd7e14, border #fd7e14)
  - Bajo  → badge verde  (bg #e8f5ee, text #22c55e, border #22c55e)
- Filas alternas con fondo ligeramente diferente
- Texto blanco / gris claro
- Scroll horizontal en móvil

### Botón de descarga (prominente, centrado)
```
<button onClick={() => window.open(`${API_URL}/reporte/${sessionId}`, '_blank')}>
  📄 Descargar Reporte PDF
</button>
```
- Tamaño grande, padding 16px 48px
- Fondo azul eléctrico (#38b6ff), texto oscuro (#020d1f), bold
- Borde redondeado (border-radius 8px)
- Hover: brighten + sutil shadow glow azul
- Texto debajo del botón (pequeño, gris): "PDF profesional · Matriz de calor · Monte Carlo"

### Botón secundario
- "Analizar otro proyecto" — ghost button, reinicia el estado y vuelve a PANTALLA 1

---

## MANEJO DE ERRORES

- Si la API tarda más de 3 segundos → mostrar skeleton/spinner
- Si hay error de red → mensaje "Error de conexión. Intenta de nuevo." con botón de reintentar
- El typing indicator (3 puntos animados) debe mostrarse siempre mientras espera respuesta

---

## ESTADO GLOBAL (useState / useRef)

```javascript
const [screen, setScreen] = useState('welcome')      // 'welcome' | 'chat' | 'results'
const [sessionId, setSessionId] = useState(null)
const [messages, setMessages] = useState([])          // { role: 'agent'|'user', text: string }
const [risksJson, setRisksJson] = useState(null)
const [loading, setLoading] = useState(false)
const [progress, setProgress] = useState(0)           // 0-100 para la barra
```

---

## DETALLES DE PULIDO

- Cursor personalizado o efecto hover en el botón principal
- Transición entre pantallas: fade out 200ms → fade in 300ms
- El input de texto se enfoca automáticamente después de cada respuesta del agente
- En móvil: el teclado no debe tapar el input (usar padding-bottom dinámico)
- Meta tag: <title>Agente de Riesgos · IA para Construcción</title>
- Favicon: emoji 🏗️

---

## NOTAS IMPORTANTES

1. CORS ya está habilitado en el backend — no necesitas proxy
2. El session_id es un UUID string — guardarlo en useState, no en localStorage
3. El endpoint /reporte devuelve el PDF directamente — window.open() es suficiente
4. No mostrar el JSON crudo nunca — solo renderizar la tabla formateada
5. La API puede tardar 3-8 segundos en responder (LLM) — el typing indicator es esencial