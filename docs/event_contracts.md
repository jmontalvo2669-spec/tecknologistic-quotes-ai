# Contratos de Eventos

Todos los eventos deben ser versionados y llevar `correlation_id`. Los
esquemas de payload provienen literalmente de `docs/agent_contracts.md` y
`docs/state_machine.md`; no se han inventado campos adicionales.

## Lista de eventos identificados en las fuentes disponibles

`[PENDIENTE]` La sección 23 del prompt maestro afirma que la lista completa
de eventos (`EMAIL_RECEIVED ... EXCEPTION_CREATED`) es "igual que v1.0", pero
ese documento no está en el repo. La lista de abajo es la que se puede
**derivar con evidencia** de `docs/agent_contracts.md` y
`docs/state_machine.md` — puede no ser exhaustiva.

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

## Esquemas de payload

Ver `docs/data_dictionary.md` §2 para el JSON exacto de cada evento que
tiene esquema explícito en las fuentes (`EMAIL_INGESTED`, `EMAIL_CLASSIFIED`,
`DOCUMENT_EXTRACTED`, `CASE_RESOLVED`, `RFQ_ASSIGNED`, resultado de Odoo
Connector, SLA, Trazabilidad). Los eventos puramente de transición manual
(`RFQ_VALIDATED`, `QUOTE_APPROVAL_REQUIRED`, `QUOTE_APPROVED`,
`CUSTOMER_PO_RECEIVED`, `SUPPLIER_PO_APPROVAL_REQUIRED`,
`SUPPLIER_PO_EMITTED`, `CASE_CLOSED`, `EXCEPTION_RESOLVED`) no tienen un
esquema JSON de payload especificado en las fuentes — `[PENDIENTE]`, se
definirán como Pydantic models mínimos (case_id + actor + timestamp + motivo)
cuando se implemente, salvo que Jorge aporte el documento v1.0 con el detalle
original.

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
   `idempotency_key` deben consultarse antes de crear registros (sección 20
   del prompt maestro).
