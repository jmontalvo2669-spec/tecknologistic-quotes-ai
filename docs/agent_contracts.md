# Contratos de Entrada/Salida por Agente

Cada agente consume exactamente los campos listados en "Input" y produce exactamente los campos listados en "Output". Ningún agente debe leer campos fuera de su contrato ni producir campos no declarados aquí — si necesita un dato adicional, el contrato debe actualizarse explícitamente (con versión nueva), no debe "improvisar" un campo extra en producción.

---

## 1. Gmail Ingest

**Consume evento:** `EMAIL_RECEIVED` (push notification de Gmail vía Pub/Sub)

**Input:**
```json
{ "gmail_message_id": "string", "gmail_history_id": "string" }
```

**Output → produce evento `EMAIL_INGESTED`:**
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

**Validación de idempotencia:** antes de producir el evento, verificar `message_hash` contra la tabla de mensajes ya ingeridos. Si existe, no reprocesar ni volver a publicar.

---

## 2. Clasificador

**Consume evento:** `EMAIL_INGESTED`

**Input (subconjunto):** `subject`, `body_text`, `from`, lista de nombres/tipos de `attachments`, `thread_context` (resumen de hasta 3 mensajes previos del mismo `gmail_thread_id`, si existen).

**Output → produce evento `EMAIL_CLASSIFIED`:** ver esquema JSON completo en `prompts/classifier_v1.txt`. Campos: `classification`, `confidence`, `signals`, `requires_human_review`, `ambiguous_alternative`.

**No consume ni produce:** nada relacionado a líneas, cotizador, ni estado de Odoo.

---

## 3. Extractor

**Consume evento:** `EMAIL_CLASSIFIED` con `classification="RFQ_NUEVA"` (o `"PO_CLIENTE"` cuando aplica extracción de líneas de la PO)

**Input:** `attachments` (contenido ya descargado), `document_type` determinado por código (extensión + inspección), `body_text` como contexto.

**Output → produce evento `DOCUMENT_EXTRACTED`:** ver esquema en `prompts/extractor_v1.txt`. Campos: `lines[]`, `line_count_confidence`, `ambiguous_groupings`, `requires_human_review`.

**Regla de contrato:** si la extracción fue 100% por código (Excel estructurado), el output debe tener el mismo esquema — el código debe producir el mismo JSON que produciría el prompt, para que el resto del sistema no distinga el origen.

---

## 4. Case Resolver

**Consume evento:** `DOCUMENT_EXTRACTED` (o cualquier evento que requiera asociar mensaje a expediente cuando las reglas deterministas no bastan)

**Input:** `mensaje_actual` (subject, body, from, date), `candidatos[]` (case_id, cliente, resumen, última_actividad, señales).

**Output → produce evento `CASE_RESOLVED`:** ver esquema en `prompts/case_resolver_v1.txt`. Campos: `resolution`, `confidence`, `evidence`, `discarded_candidates`, `requires_human_review`.

**Regla de contrato:** este agente nunca recibe ni produce datos de líneas o de cotizador — solo resuelve identidad de expediente.

---

## 5. Balanceador

**Consume evento:** `CASE_RESOLVED` (cuando el expediente llega a `LISTA_PARA_ASIGNAR`)

**Input:**
```json
{
  "case_id": "string",
  "line_count": "int",
  "cliente": "string",
  "flags": {"cliente_reservado": "bool", "producto_especializado": "bool", "certificacion_requerida": "bool", "urgente_vip": "bool"},
  "roster": [{"cotizador_id": "string", "activo": "bool", "carga_actual_lineas": "int"}]
}
```

**Output → produce evento `RFQ_ASSIGNED`:**
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

**Regla de contrato:** si ningún cotizador es elegible (todos excluidos por `flags` o roster vacío), `cotizador_id=null` y `requires_human_review=true` — nunca asignar por defecto al primero disponible ignorando exclusiones.

---

## 6. Orquestador (agente decisor — ver `orchestrator_decision_logic.md`)

**Consume:** todos los eventos del sistema.

**Input:** evento entrante + estado actual del expediente (leído de PostgreSQL) + tabla de transiciones (`state_machine.md`).

**Output:** nueva transición de estado aplicada (o rechazo de transición inválida), evento de auditoría, y — cuando corresponde según `orchestrator_decision_logic.md` — una decisión de escalamiento, reintento o solicitud de aclaración.

---

## 7. Odoo Connector

**Consume evento:** `QUOTE_APPROVED`, `SUPPLIER_PO_EMITTED` (o cualquier evento que requiera escritura en Odoo)

**Input:** `case_id`, datos ya validados y aprobados por humano (nunca escribe algo no aprobado).

**Output → produce evento con resultado de escritura:**
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

**Regla de contrato:** sigue estrictamente READ → DECIDE → VALIDATE → WRITE → VERIFY → AUDIT (sección 16 del prompt maestro). Nunca recibe instrucciones directas de Claude — solo del Orquestador tras aprobación humana.

---

## 8. SLA / Seguimiento

**Consume:** lectura periódica (Cloud Scheduler) del estado de expedientes activos.

**Output → produce evento `EXCEPTION_CREATED` (por SLA vencido) o notificación:**
```json
{ "case_id": "string", "sla_type": "string", "tiempo_transcurrido_horas": "float", "umbral_horas": "float", "accion": "alerta|excepcion" }
```

---

## 9. Trazabilidad

**Consume:** lectura periódica cruzando Gmail ↔ Expediente ↔ Odoo.

**Output:**
```json
{ "case_id": "string", "completeness_score": "float 0.0-1.0", "gaps": ["string"] }
```

---

## 10. Auditoría / KPI

**Consume:** todos los eventos de auditoría generados por los demás agentes (append-only).

**Output:** agregaciones para dashboard (sección 27 del prompt maestro) — no produce eventos de workflow, solo lectura/reportería.
