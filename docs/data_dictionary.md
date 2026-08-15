# Diccionario de Datos

**Fuente:** sección 7 de `docs/architecture.md` (modelo de expediente) +
`docs/agent_contracts.md` (esquemas de entrada/salida por agente).
Ningún campo aquí fue inventado; donde `docs/architecture.md` no da tipo/formato
concreto se marca `[PENDIENTE]`.

## 1. Expediente (TQL)

Identificador: `TQL-AAAA-NNNNNN` (año + secuencial de 6 dígitos). No depende
solo del `Subject` del correo.

| Campo | Tipo | Notas |
|---|---|---|
| `case_id` | string (`TQL-AAAA-NNNNNN`) | PK lógica del expediente |
| `cliente` | `[PENDIENTE — estructura de contacto/cliente sin definir]` | vínculo a datos de cliente, sujeto a minimización (sección 20 de `docs/architecture.md`) |
| `contacto` | `[PENDIENTE]` | persona de contacto del cliente |
| `mensajes` | array de referencias a mensajes Gmail | ver `gmail_message_id`/`gmail_thread_id` |
| `gmail_message_id` | string | id de mensaje Gmail |
| `gmail_thread_id` | string | id de hilo Gmail |
| `archivos` | array de adjuntos | ver esquema de `attachments` en Gmail Ingest (§2.1) |
| `versiones` | `[PENDIENTE — versionado de cotización mencionado en fila 18 de state_machine.md, sin esquema de campos]` | |
| `rfq` | referencia a líneas extraídas | ver Extractor (§2.3) |
| `lineas` | array de líneas cotizables | ver esquema `lines[]` (§2.3) |
| `cotizador_asignado` | string (`cotizador_id`) | asignado por Balanceador |
| `carga_antes` / `carga_despues` | int | líneas abiertas del cotizador antes/después de la asignación |
| `cotizacion` | `[PENDIENTE — esquema de cotización no definido en las fuentes]` | |
| `oc_cliente` | `[PENDIENTE]` | orden de compra del cliente |
| `compras_proveedor` | `[PENDIENTE]` | compras al proveedor |
| `odoo_ids` | `{modelo: string, id: int}[]` | ver esquema de resultado del Odoo Connector (§2.7) |
| `aprobaciones` | `[PENDIENTE — estructura no definida; se sabe que registra identidad + timestamp, sección state_machine.md fila 15]` | |
| `excepciones` | referencia a eventos `EXCEPTION_CREATED`/`EXCEPTION_RESOLVED` | ver `docs/event_contracts.md` |
| `sla` | `{tipo, tiempo_transcurrido_horas, umbral_horas}` | ver esquema del agente SLA (§2.8) |
| `auditoria` | append-only, todos los eventos | consumido por Auditoría/KPI (§2.10) |
| `confianza_ia` | float 0.0–1.0, por decisión de IA | cada decisión de IA registra su propia confianza — no hay un único campo agregado definido |
| `estado_actual` | uno de los 15 estados de `docs/state_machine.md` | validado contra tabla `TRANSITIONS` |
| `timestamps` | creación, última transición, etc. | cada transición registra su propio timestamp (regla general #3 de `state_machine.md`) |

## 2. Esquemas de agentes (campo a campo, tomados literalmente de `docs/agent_contracts.md`)

### 2.1 Gmail Ingest — Output (`EMAIL_INGESTED`)
```json
{
  "case_hint_id": "string|null",
  "gmail_message_id": "string",
  "gmail_thread_id": "string",
  "message_id_header": "string",
  "in_reply_to": "string|null",
  "references": ["string"],
  "from": "string",
  "to": ["string"],
  "cc": ["string"],
  "subject": "string",
  "date": "ISO8601",
  "body_text": "string",
  "attachments": [{"filename": "string", "mime_type": "string", "storage_path": "string", "sha256": "string"}],
  "message_hash": "string"
}
```
Idempotencia: `message_hash` se verifica contra mensajes ya ingeridos antes de
producir el evento.

### 2.2 Clasificador — Output (`EMAIL_CLASSIFIED`)
Ver `prompts/classifier_v1.txt` para el esquema completo:
`classification` (enum cerrado de 7 valores), `confidence` (float 0-1),
`signals` (array de strings), `requires_human_review` (bool),
`ambiguous_alternative` (string enum o null).

### 2.3 Extractor — Output (`DOCUMENT_EXTRACTED`)
Ver `prompts/extractor_v1.txt`. Por línea: `line_id`, `description`,
`quantity`, `unit`, `manufacturer`, `part_number`, `standard`,
`specification`, `observations` (todos nullable salvo `line_id`). A nivel de
documento: `line_count_confidence` (float 0-1), `ambiguous_groupings`
(array), `requires_human_review` (bool). Regla de contrato: extracción por
código (Excel estructurado) debe producir el **mismo esquema** que el
prompt, sin distinguir origen para el resto del sistema.

### 2.4 Case Resolver — Output (`CASE_RESOLVED`)
Ver `prompts/case_resolver_v1.txt`: `resolution` (`case_id` o
`"EXCEPCION"`), `confidence`, `evidence[]`, `discarded_candidates[]`
(`{case_id, reason}`), `requires_human_review`.

### 2.5 Balanceador — Input / Output (`RFQ_ASSIGNED`)
Input:
```json
{
  "case_id": "string",
  "line_count": "int",
  "cliente": "string",
  "flags": {"cliente_reservado": "bool", "urgente_vip": "bool"},
  "roster": [{"cotizador_id": "string", "activo": "bool", "carga_actual_lineas": "int"}]
}
```
Output:
```json
{
  "case_id": "string",
  "cotizador_id": "string|null",
  "carga_antes": "int",
  "lineas_nuevas": "int",
  "carga_despues": "int",
  "regla_utilizada": "string",
  "motivo": "string",
  "requires_human_review": "bool"
}
```
Fuente del `roster`: **`[PENDIENTE]`** — ver `docs/open_questions.md` A.2.

`producto_especializado` y `certificacion_requerida` se quitaron de `flags`
(ver `docs/decisions/0001-balancer-flags-especializacion.md`): Jorge
confirmó que los 6 cotizadores pueden cotizar cualquier producto, sin
diferenciación de especialidad ni certificación.

### 2.6 Orquestador
No produce un esquema JSON fijo propio: aplica transiciones de
`docs/state_machine.md` y decisiones de `docs/orchestrator_decision_logic.md`
(D1-D5), generando siempre un evento de auditoría con estado origen/destino,
evento, agente/actor, timestamp, motivo, `correlation_id`.

### 2.7 Odoo Connector — Output
```json
{
  "case_id": "string",
  "odoo_model": "string",
  "odoo_id": "int|null",
  "operation": "create|update",
  "idempotency_key": "string",
  "verified": "bool",
  "error": "string|null"
}
```

### 2.8 SLA / Seguimiento — Output
```json
{ "case_id": "string", "sla_type": "string", "tiempo_transcurrido_horas": "float", "umbral_horas": "float", "accion": "alerta|excepcion" }
```

### 2.9 Trazabilidad — Output
```json
{ "case_id": "string", "completeness_score": "float 0.0-1.0", "gaps": ["string"] }
```

### 2.10 Auditoría / KPI
Consume todos los eventos de auditoría (append-only); no produce eventos de
workflow, solo agregaciones de dashboard. No tiene esquema JSON de evento
propio, pero sección 18 de `docs/architecture.md` (AGENTE 10) sí detalla qué
registra (RFQs, líneas, asignaciones, tiempos, conversiones, backlog,
errores, excepciones, reasignaciones, SLA, costo IA, versión de
modelo/prompt, decisiones relevantes) y los KPIs mínimos esperados — ver
también sección 26 de `docs/architecture.md` (DASHBOARD) para las tres
vistas (bandeja general, por cotizador, gerencia).

## 3. Umbrales de confianza (todas ya cuantificadas en las fuentes)

| Constante | Default | Efecto |
|---|---|---|
| `CLASSIFIER_ESCALATION_THRESHOLD` | 0.80 | escala de `CLAUDE_MODEL_FAST` a `CLAUDE_MODEL_REASONING` |
| `CLASSIFIER_MIN_THRESHOLD` | 0.60 | por debajo, incluso tras escalar → `EXCEPCIÓN` |
| `LINE_COUNT_CONFIDENCE_THRESHOLD` | 0.90 | por debajo → `VALIDACIÓN_REQUERIDA` |
| Case Resolver — revisión humana | confidence < 0.75 (aunque resuelva) | ver `prompts/case_resolver_v1.txt` |
| Technical Normalizer — revisión humana | `equivalence_confidence` < 0.85 | ver `prompts/technical_normalizer_v1.txt` |
| `MAX_RETRIES` | 3 | D1, `docs/orchestrator_decision_logic.md` |
| `CLARIFICATION_WAIT_HOURS` | 24 | D3, ídem |
