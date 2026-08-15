# Contratos de Eventos

Todos los eventos deben ser versionados y llevar `correlation_id`. Los
esquemas de payload provienen literalmente de `docs/agent_contracts.md` y
`docs/state_machine.md`; no se han inventado campos adicionales.

## Lista de eventos identificados en las fuentes disponibles

La sección 22 de `docs/architecture.md` (v1.2, autocontenida) ya da una lista
canónica de eventos: `EMAIL_RECEIVED`, `EMAIL_INGESTED`, `EMAIL_CLASSIFIED`,
`DOCUMENT_EXTRACTED`, `CASE_CREATED`, `CASE_RESOLVED`, `RFQ_VALIDATED`,
`RFQ_ASSIGNED`, `QUOTE_APPROVAL_REQUIRED`, `QUOTE_APPROVED`,
`CUSTOMER_PO_RECEIVED`, `SUPPLIER_PO_APPROVAL_REQUIRED`,
`SUPPLIER_PO_EMITTED`, `CASE_CLOSED`, `EXCEPTION_CREATED`.

**Discrepancia sin resolver, no se decide aquí:** esa lista canónica incluye
`CASE_CREATED` (que no aparece en `docs/agent_contracts.md` ni en
`docs/state_machine.md` como evento disparador de ninguna fila) y **no**
incluye `EXCEPTION_RESOLVED` (que sí es el evento disparador explícito de la
fila 24 de `docs/state_machine.md`, la única salida válida del estado
`EXCEPCIÓN`). La tabla de abajo mantiene `EXCEPTION_RESOLVED` porque
`docs/state_machine.md` lo exige literalmente, y agrega `CASE_CREATED` al
final marcado como pendiente de ubicar en el flujo — **Jorge debe confirmar**
si `CASE_CREATED` reemplaza/precede a `EMAIL_INGESTED→RECIBIDA` (creación del
expediente) o es un evento aparte, y si `EXCEPTION_RESOLVED` fue una omisión
en `docs/architecture.md` §22 o un cambio intencional.

| Evento | Productor | Consumidor(es) | Dispara transición (state_machine.md) |
|---|---|---|---|
| `EMAIL_RECEIVED` | Gmail Pub/Sub push | Gmail Ingest | — (entrada externa) |
| `EMAIL_INGESTED` | Gmail Ingest | Clasificador, Orquestador | fila 1 → RECIBIDA |
| `EMAIL_CLASSIFIED` | Clasificador | Extractor, Case Resolver, Orquestador | filas 2, 3, 17 |
| `DOCUMENT_EXTRACTED` | Extractor | Case Resolver, Orquestador | filas 4, 5, 6 |
| `CASE_RESOLVED` | Case Resolver / reglas deterministas | Balanceador, Orquestador | filas 7, 8 |
| `RFQ_VALIDATED` | Humano (validación manual de conteo) | Orquestador | filas 9, 10 |
| `RFQ_ASSIGNED` | Balanceador | Orquestador | filas 11, 12 |
| `QUOTE_APPROVAL_REQUIRED` | Humano (cotizador) → sistema | Orquestador | fila 14 |
| `QUOTE_APPROVED` | Humano (aprobador) | Odoo Connector, Orquestador | fila 15 |
| `CUSTOMER_PO_RECEIVED` | Clasificador + Case Resolver | Orquestador | filas 19, 20 |
| `SUPPLIER_PO_APPROVAL_REQUIRED` | Humano (comprador) | Orquestador | fila 21 |
| `SUPPLIER_PO_EMITTED` | Humano (aprobador) | Odoo Connector, Orquestador | fila 22 |
| `CASE_CLOSED` | Humano / Odoo Connector (lectura) | Orquestador, Auditoría/KPI | fila 23 |
| `EXCEPTION_CREATED` | Cualquier agente (vía Orquestador) o SLA | Orquestador, Auditoría/KPI | fila 25 |
| `EXCEPTION_RESOLVED` | Humano (supervisor) | Orquestador | fila 24 |
| `CASE_CREATED` | `[PENDIENTE — no está en `docs/agent_contracts.md` ni `docs/state_machine.md`; ver discrepancia arriba]` | — | ninguna fila lo dispara explícitamente |

## Esquemas de payload

Ver `docs/data_dictionary.md` §2 para el JSON exacto de cada evento que
tiene esquema explícito en las fuentes (`EMAIL_INGESTED`, `EMAIL_CLASSIFIED`,
`DOCUMENT_EXTRACTED`, `CASE_RESOLVED`, `RFQ_ASSIGNED`, resultado de Odoo
Connector, SLA, Trazabilidad). Los eventos puramente de transición manual
(`RFQ_VALIDATED`, `QUOTE_APPROVAL_REQUIRED`, `QUOTE_APPROVED`,
`CUSTOMER_PO_RECEIVED`, `SUPPLIER_PO_APPROVAL_REQUIRED`,
`SUPPLIER_PO_EMITTED`, `CASE_CLOSED`, `EXCEPTION_RESOLVED`, `CASE_CREATED`) no
tienen un esquema JSON de payload especificado en las fuentes — `[PENDIENTE]`,
se definirán como Pydantic models mínimos (case_id + actor + timestamp +
motivo) cuando se implemente.

## Reglas de contrato transversales (de `docs/agent_contracts.md`)

1. Cada agente consume exactamente los campos listados en su contrato y
   produce exactamente los declarados — nunca lee ni improvisa campos fuera
   de contrato. Un campo nuevo requiere una nueva versión de contrato, no un
   ajuste ad-hoc en producción.
2. Toda transición de estado registra: estado origen, estado destino,
   evento, agente/actor, timestamp, motivo, `correlation_id`.
3. Ninguna transición se ejecuta sin un evento disparador listado en
   `docs/state_machine.md` — un evento no mapeado para el estado actual
   genera `EXCEPTION_CREATED`, nunca se aplica "por si acaso".
4. Idempotencia: `event_id`, `message_hash`, `gmail_message_id`,
   `idempotency_key` deben consultarse antes de crear registros (sección 19
   de `docs/architecture.md`).
