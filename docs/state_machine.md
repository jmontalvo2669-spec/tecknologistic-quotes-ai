# Máquina de Estados del Expediente (TQL) — Tabla de Transiciones Ejecutable

Este documento es la fuente de verdad para implementar la state machine en código (p.ej. como tabla `TRANSITIONS` en `services/workflow/`). Cada fila es una transición válida. Cualquier transición no listada aquí debe ser rechazada por el orquestador y registrada como error, nunca ejecutada implícitamente.

Columnas: **Estado origen → Estado destino | Evento disparador | Condición | Agente/actor que ejecuta | Validación previa obligatoria**

| # | Origen | Destino | Evento disparador | Condición | Agente/actor | Validación previa |
|---|---|---|---|---|---|---|
| 1 | (ninguno) | RECIBIDA | `EMAIL_INGESTED` | mensaje nuevo, hash no duplicado | Gmail Ingest | verificar `message_hash` no existe |
| 2 | RECIBIDA | CLASIFICADA | `EMAIL_CLASSIFIED` | clasificación con `requires_human_review=false` | Clasificador | JSON de clasificación válido |
| 3 | RECIBIDA | EXCEPCIÓN | `EMAIL_CLASSIFIED` | `requires_human_review=true` o `classification="EXCEPCION"` | Clasificador | ninguna adicional |
| 4 | CLASIFICADA | EXTRAÍDA | `DOCUMENT_EXTRACTED` | extracción con `requires_human_review=false` | Extractor | JSON de extracción válido |
| 5 | CLASIFICADA | VALIDACIÓN_REQUERIDA | `DOCUMENT_EXTRACTED` | `line_count_confidence < LINE_COUNT_CONFIDENCE_THRESHOLD` | Extractor | ninguna adicional |
| 6 | CLASIFICADA | EXCEPCIÓN | `DOCUMENT_EXTRACTED` | extracción falló (documento ilegible, `lines=[]`) | Extractor | ninguna adicional |
| 7 | EXTRAÍDA | LISTA_PARA_ASIGNAR | `CASE_RESOLVED` | expediente único confirmado (regla determinista o `case_resolver_v1` con `resolution != EXCEPCION`) | Case Resolver / reglas deterministas | evidencia registrada |
| 8 | EXTRAÍDA | EXCEPCIÓN | `CASE_RESOLVED` | `resolution="EXCEPCION"` (dos candidatos con evidencia comparable) | Case Resolver | ninguna adicional |
| 9 | VALIDACIÓN_REQUERIDA | LISTA_PARA_ASIGNAR | `RFQ_VALIDATED` | humano confirma conteo de líneas manualmente | Humano (cotizador líder / supervisor) | registro de quién validó y cuándo |
| 10 | VALIDACIÓN_REQUERIDA | EXCEPCIÓN | `RFQ_VALIDATED` | humano determina que el documento no es procesable | Humano | motivo documentado |
| 11 | LISTA_PARA_ASIGNAR | ASIGNADA | `RFQ_ASSIGNED` | balanceador encontró cotizador elegible sin exclusiones activas | Balanceador | roster de cotizadores vigente (sección 42 del prompt maestro) |
| 12 | LISTA_PARA_ASIGNAR | EXCEPCIÓN | `RFQ_ASSIGNED` | ninguna exclusión resuelta (todos los cotizadores excluidos, o cliente reservado sin cotizador designado) | Balanceador | ninguna adicional |
| 13 | ASIGNADA | EN_COTIZACIÓN | (acción manual del cotizador en su herramienta) | cotizador marca inicio de trabajo | Humano (cotizador) | ninguna adicional |
| 14 | EN_COTIZACIÓN | COTIZACIÓN_EN_REVISIÓN | `QUOTE_APPROVAL_REQUIRED` | cotizador envía borrador a aprobación | Humano (cotizador) → sistema | borrador adjunto y registrado |
| 15 | COTIZACIÓN_EN_REVISIÓN | COTIZADA | `QUOTE_APPROVED` | aprobador humano aprueba y cotización se envía al cliente | Humano (aprobador, ver RACI) | aprobación registrada con identidad y timestamp |
| 16 | COTIZACIÓN_EN_REVISIÓN | EN_COTIZACIÓN | (rechazo de aprobación) | aprobador solicita cambios | Humano (aprobador) | motivo de rechazo documentado |
| 17 | COTIZADA | EN_NEGOCIACIÓN | `EMAIL_CLASSIFIED` con `classification="ACLARACION"` sobre el mismo case_id | cliente responde pidiendo ajustes | Clasificador + Case Resolver | asociación de expediente confirmada |
| 18 | EN_NEGOCIACIÓN | COTIZADA | (nueva versión de cotización aprobada) | se repite transición 14→15 con nueva versión | Humano | versión de cotización incrementada |
| 19 | COTIZADA | OC_CLIENTE_RECIBIDA | `CUSTOMER_PO_RECEIVED` | clasificador detecta `PO_CLIENTE` asociado al expediente | Clasificador + Case Resolver | PO adjunta y legible |
| 20 | EN_NEGOCIACIÓN | OC_CLIENTE_RECIBIDA | `CUSTOMER_PO_RECEIVED` | cliente acepta directamente durante negociación | Clasificador + Case Resolver | PO adjunta y legible |
| 21 | OC_CLIENTE_RECIBIDA | COMPRA_PROVEEDOR_EN_REVISIÓN | `SUPPLIER_PO_APPROVAL_REQUIRED` | sistema/humano prepara orden a proveedor | Humano (comprador) | línea a línea contra PO cliente |
| 22 | COMPRA_PROVEEDOR_EN_REVISIÓN | COMPRA_PROVEEDOR_EMITIDA | `SUPPLIER_PO_EMITTED` | aprobador humano aprueba la compra al proveedor | Humano (aprobador, ver RACI) | aprobación registrada |
| 23 | COMPRA_PROVEEDOR_EMITIDA | CERRADA | `CASE_CLOSED` | proveedor confirma entrega y no hay pendientes | Humano / Odoo Connector (lectura de estado) | verificación de recepción |
| 24 | EXCEPCIÓN | (cualquier estado anterior aplicable) | `EXCEPTION_RESOLVED` | humano resuelve la excepción y determina el estado correcto de reingreso | Humano (supervisor) | motivo de resolución documentado, no hay reingreso automático |
| 25 | (cualquier estado activo) | EXCEPCIÓN | `EXCEPTION_CREATED` | error técnico no recuperable, timeout de reintentos agotado, SLA vencido sin resolución | Orquestador | registrar estado de origen para poder reingresar tras resolución |

## Reglas generales de la tabla

1. **Ninguna transición se ejecuta sin un evento disparador listado.** Si el código recibe un evento no mapeado a una fila de esta tabla para el estado actual del expediente, debe rechazar la transición y generar `EXCEPTION_CREATED`, nunca aplicar el cambio de estado "por si acaso".
2. **EXCEPCIÓN es un estado de estacionamiento, no un callejón sin salida.** La fila 24 es la única forma de salir de EXCEPCIÓN, y siempre es una acción humana explícita — nunca automática.
3. **Toda transición registra:** estado origen, estado destino, evento, agente/actor, timestamp, motivo (aunque sea "condición cumplida automáticamente"), y un `correlation_id` que amarra el evento a los logs técnicos.
4. **Reingreso tras EXCEPCIÓN (fila 24) no reprocesa automáticamente los pasos previos** — el humano que resuelve la excepción decide explícitamente a qué estado vuelve el expediente, y esa decisión queda auditada igual que cualquier otra transición.
5. Esta tabla es la que debe traducirse literalmente a la constante `TRANSITIONS` (o equivalente) en `services/workflow/state_machine.py`. Si el código permite algo que esta tabla no lista, es un bug, no una funcionalidad.
6. **Filas 13, 16 y 18 no traen un nombre de evento fijo** — la columna "Evento disparador" describe una acción entre paréntesis ("acción manual del cotizador en su herramienta", "rechazo de aprobación", "nueva versión de cotización aprobada") en vez de un identificador de evento como el resto de las filas. `services/workflow/state_machine.py` usa los identificadores de código `COTIZADOR_INICIA_TRABAJO` (fila 13) y `QUOTE_REJECTED` (fila 16), y reutiliza `QUOTE_APPROVED` para la fila 18 — son nombres de trabajo, no confirmados por ninguna fuente. Pendiente de que Jorge los confirme (o indique el evento real del sistema/herramienta que los dispara) — ver `docs/open_questions.md`.
