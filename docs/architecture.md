# Arquitectura — Sistema IA de Cotizaciones Tecknologistic

**Fase:** 0 (Discovery) · **Estado:** pre-GATE 1 · **Fuente de verdad:** `docs/prompt_maestro_v1.1.md`,
`docs/agent_contracts.md`, `docs/state_machine.md`, `docs/orchestrator_decision_logic.md`, `prompts/*.txt`

> Nota de honestidad de fuentes: el documento "Tecknologistic — Arquitectura IA
> Cotizaciones — Uso interno — Versión 1.0", citado repetidamente en el prompt
> maestro v1.1 como "(igual que v1.0)", **no está presente en este
> repositorio**. Todo lo que aquí se describe proviene única y exclusivamente
> de los 5 archivos fuente listados arriba. Donde v1.1 dice "igual que v1.0"
> sin dar el detalle, se marca `[PENDIENTE — falta v1.0]` en vez de inventarse.
> Ver `docs/open_questions.md` gap #9.

---

## 1. Objetivo del sistema

Convertir el buzón central de Cotizaciones en la puerta de entrada y
expediente documental de todo el proceso:

```
Solicitud del cliente → Cotización → Orden de compra del cliente → Compra al proveedor → Cierre
```

El sistema debe permitir reconstruir en cualquier momento: quién solicitó, qué
solicitó, líneas, documentos recibidos, cotizador asignado y por qué, cuándo
se trabajó y cotizó, OC del cliente, compra al proveedor, estado del
expediente, excepciones, aprobaciones y trazabilidad completa.

## 2. Reglas de arquitectura no negociables

Las reglas 19-22 de la sección 3 del prompt maestro son las que gobiernan
esta fase:

1. **No conectar credenciales ni permisos de escritura reales (Gmail, Odoo)
   sin aprobación explícita de Jorge** — incluso si el código ya está listo.
2. Todo umbral de confianza es una **constante configurable con valor
   numérico por defecto**, nunca una condición cualitativa sin número.
3. Todo dato personal/comercial de cliente tiene una **regla de retención
   documentada** antes de almacenarse de forma persistente (ver
   `docs/security.md`).
4. Todo uso de Claude API **declara explícitamente el modelo usado y por
   qué**, priorizando el modelo más económico que resuelva el caso.

## 3. Stack tecnológico

`[PENDIENTE — falta v1.0]` El único detalle operativo concreto disponible en
las fuentes es:

- **Gmail API / Pub/Sub:** el `watch()` de Gmail expira cada 7 días. Se
  requiere un Cloud Scheduler que lo renueve automáticamente (diario) y una
  alerta si la renovación falla (P0, no detalle de infraestructura —
  causa #1 de fallos silenciosos en integraciones Gmail→Pub/Sub).
- Base de datos: PostgreSQL (mencionado en sección 9 del prompt maestro como
  fuente de estado que lee el Orquestador).
- Motor de IA: Claude API, con al menos dos tiers configurables:
  `CLAUDE_MODEL_FAST` (clasificación estándar) y `CLAUDE_MODEL_REASONING`
  (escalamiento por baja confianza).
- Odoo como sistema de registro comercial (versión, plan y disponibilidad de
  sandbox: `[PENDIENTE]`, ver `docs/open_questions.md` A.3).

No se asumen credenciales, URLs, IDs de proyecto GCP, versión de Odoo ni
nombres de buzones — todo vive en variables de entorno (`.env.example`) y se
marca pendiente donde falte.

## 4. Estructura del repositorio (objetivo)

```
docs/
  architecture.md            # este archivo
  data_dictionary.md
  event_contracts.md
  security.md
  test_strategy.md
  implementation_plan.md
  open_questions.md
  state_machine.md
  agent_contracts.md
  orchestrator_decision_logic.md
  prompt_maestro_v1.1.md
  decisions/                 # ADRs — vacío hasta que existan decisiones no triviales
prompts/
  classifier_v1.txt
  extractor_v1.txt
  case_resolver_v1.txt
  technical_normalizer_v1.txt
services/       # [a crear en la fase de implementación, tras GATE 1]
schemas/        # [a crear en la fase de implementación, tras GATE 1]
odoo/           # [a crear en la fase de implementación, tras GATE 1]
gmail/          # [a crear en la fase de implementación, tras GATE 1]
security/       # [a crear en la fase de implementación, tras GATE 1]
migrations/     # [a crear en la fase de implementación, tras GATE 1]
tests/          # [a crear en la fase de implementación, tras GATE 1]
infra/          # [a crear en la fase de implementación, tras GATE 1]
scripts/        # [a crear en la fase de implementación, tras GATE 1]
docker/         # [a crear en la fase de implementación, tras GATE 1]
```

FASE 0 solo produce documentación — el código de `services/`, `schemas/`,
etc. se escribe en la fase de implementación (PASO 6 en adelante de la
sección 35), que empieza **después** de que Jorge revise este documento y
`docs/open_questions.md` en GATE 1. Incluso esa siguiente fase puede
construirse con mocks/fixtures sin tocar Gmail/Odoo reales — lo que requiere
aprobación explícita adicional es conectar credenciales reales o gastar
presupuesto real de Claude API en volumen (sección 6, GATE 1).

## 5. Modelo de expediente (TQL)

Identificador: `TQL-AAAA-NNNNNN`. Relaciona: cliente, contacto, mensajes,
`gmail_message_id`/`gmail_thread_id`, archivos, versiones, RFQ, líneas,
cotizador asignado, carga antes/después, cotización, OC cliente, compras a
proveedor, IDs de Odoo, aprobaciones, excepciones, SLA, auditoría, confianza
de IA, timestamps. No debe depender solo del `Subject` del correo (los
agentes de clasificación y resolución de expediente existen precisamente
para no depender de eso). Ver detalle campo a campo en
`docs/data_dictionary.md`.

## 6. Estados del workflow

15 estados, transiciones validadas por evento + condición + agente/actor,
con timestamp, estado anterior/nuevo, motivo y evento de auditoría. La tabla
ejecutable completa vive en `docs/state_machine.md` — es la fuente literal
para la constante `TRANSITIONS` de `services/workflow/state_machine.py`
cuando se implemente. Ninguna transición no listada allí debe ejecutarse.

## 7. Agentes del sistema

10 agentes, con contratos de entrada/salida estrictos documentados en
`docs/agent_contracts.md` (ningún agente lee ni produce campos fuera de su
contrato declarado):

| # | Agente | Consume | Produce | Umbral(es) clave |
|---|---|---|---|---|
| 1 | Gmail Ingest | `EMAIL_RECEIVED` | `EMAIL_INGESTED` | idempotencia por `message_hash` |
| 2 | Clasificador | `EMAIL_INGESTED` | `EMAIL_CLASSIFIED` | escalar si `confidence < 0.80`; excepción si `< 0.60` tras escalar |
| 3 | Extractor | `EMAIL_CLASSIFIED` (RFQ_NUEVA/PO_CLIENTE) | `DOCUMENT_EXTRACTED` | `VALIDACIÓN_REQUERIDA` si `line_count_confidence < 0.90` |
| 4 | Case Resolver | `DOCUMENT_EXTRACTED` (o disambiguación) | `CASE_RESOLVED` | excepción si evidencia comparable entre candidatos, o `confidence < 0.75` |
| 5 | Balanceador | `CASE_RESOLVED` (→ `LISTA_PARA_ASIGNAR`) | `RFQ_ASSIGNED` | Least Loaded by Open Lines; nunca divide una RFQ |
| 6 | Orquestador | todos los eventos | transición de estado + auditoría + decisión D1-D5 | ver `docs/orchestrator_decision_logic.md` |
| 7 | Odoo Connector | `QUOTE_APPROVED`, `SUPPLIER_PO_EMITTED` | evento de resultado de escritura | READ→DECIDE→VALIDATE→WRITE→VERIFY→AUDIT; nunca invocado directo por Claude |
| 8 | SLA / Seguimiento | lectura periódica (Cloud Scheduler) | `EXCEPTION_CREATED` o notificación | canal de escalamiento `[PENDIENTE]` |
| 9 | Trazabilidad | lectura periódica Gmail↔Expediente↔Odoo | `completeness_score` (0.0-1.0) + `gaps[]` | usado en GATE 2 |
| 10 | Auditoría / KPI | eventos de auditoría (append-only) | agregaciones de dashboard | solo lectura/reportería |

Los agentes 2, 3 y 4 tienen prompt versionado en `prompts/` (`classifier_v1`,
`extractor_v1`, `case_resolver_v1`). Existe además un quinto prompt,
`technical_normalizer_v1`, para normalización técnica de normas/equivalencias
— es P3 (fuera del primer sprint) y **nunca** decide equivalencias sin
certeza (ver `prompts/technical_normalizer_v1.txt`).

## 8. Orquestador como agente de decisión acotada

El Orquestador sigue la tabla fija de `docs/state_machine.md` salvo en 5
puntos de decisión explícitos (D1–D5, `docs/orchestrator_decision_logic.md`):
reintentar vs. escalar, obedecer `requires_human_review`, recomendar
aclaración al cliente tras `CLARIFICATION_WAIT_HOURS` (default 24h),
notificar según tabla D4, y recomendar (nunca ejecutar) reasignación de RFQ.
Nunca aprueba cotizaciones/compras, nunca escribe en Odoo directo, nunca
cambia un umbral de configuración, nunca genera contenido comercial.

## 9. Gobierno de costo de IA

Cada decisión de IA registra: modelo usado, `prompt_version`, `timestamp`,
`confidence`, resultado. Regla fundamental: reglas → datos del sistema →
documentos → API → Claude → humano, en ese orden de prioridad para
decisiones críticas. Presupuesto máximo por expediente:
`AI_COST_BUDGET_PER_CASE_USD` — valor `[PENDIENTE, ver open_questions.md A.7]`,
con alerta si se excede. El costo real (no estimado) se mide en GATE 2.

## 10. Fases e implementación

Ver `docs/implementation_plan.md` para el backlog priorizado (P0-P3),
matriz de dependencias, y el detalle de GATE 1 / GATE 2.

## 11. Estado de esta fase

FASE 0 completa a nivel de documentación con la información disponible en el
repositorio. **GATE 1 activo**: no se debe escribir código que dependa de
credenciales reales de Gmail/Odoo, ni gastar presupuesto real de Claude API en
volumen, hasta que Jorge revise este documento junto con
`docs/open_questions.md` y dé luz verde explícita.
