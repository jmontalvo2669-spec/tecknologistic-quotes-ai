# Preguntas Abiertas — Checklist Viva (bloqueante para Fase 1 real)

Este documento es el entregable #18 de la sección 38 de `docs/architecture.md`
y el insumo principal de GATE 1. Jorge ya respondió las 8 preguntas
originales (sección A) — ver el detalle de qué queda resuelto y qué sigue
abierto en las secciones D y E.

Estado: **PARCIALMENTE RESUELTO** — Jorge respondió las 8 preguntas
originales (ver tabla A). Algunas quedaron completamente resueltas, otras
parcialmente (un valor confirmado, un sub-punto todavía pendiente), y las
respuestas no cierran GATE 1 por sí solas — GATE 1 sigue exigiendo
aprobación explícita para conectar credenciales reales, independientemente
de que ya se sepa dónde viven esos datos.

---

## A. Preguntas originales del prompt maestro (sección 41 de `docs/architecture.md`)

| # | Pregunta | Por qué bloquea | Respuesta |
|---|---|---|---|
| 1 | ¿Cuántas RFQ/día y líneas/RFQ en promedio hoy? | Dimensiona balanceador y SLA | **RESUELTO** — ~3 RFQ/día, ~20/semana, 1 a 6+ líneas por RFQ (variable). |
| 2 | ¿Cuántos cotizadores activos hay y dónde vive su disponibilidad/ausencia? | Fuente del roster del Balanceador (sección 13 de `docs/architecture.md`) | **RESUELTO** — 6 cotizadores activos; disponibilidad/ausencias vive en Odoo (RRHH). |
| 3 | ¿Versión de Odoo instalada, plan contratado, existe sandbox/staging? | Bloquea diseño del Odoo Connector y GATE 2 | **PARCIAL** — versión 18 instalada. Plan contratado: sin dato. Sandbox: **no existe todavía** — pendiente de crear antes de GATE 2. |
| 4 | ¿El buzón central de cotizaciones ya existe como cuenta dedicada? ¿Quién administra el proyecto de Google Cloud? | Bloquea cualquier conexión real a Gmail | **PARCIAL** — el buzón ya existe: `cotizaciones.tecknologistic@tecknologistic.com`. Administrador: **por confirmar** entre la asistente actual y la coordinadora de ventas — no asumir ninguno de los dos. |
| 5 | ¿Existe política de retención de correspondencia comercial en Tecknologistic, o hay que definirla? | Bloquea `DATA_RETENTION_DAYS` y `docs/security.md` (LOPDP) | **PENDIENTE** — no existe política. El valor concreto (`DATA_RETENTION_DAYS`) se define más adelante; no se inventa un número. |
| 6 | ¿Las alertas de SLA/errores van por Gmail, Google Chat, ambos, u otro canal? | Bloquea diseño del agente SLA y observabilidad | **RESUELTO** — por correo (Gmail), canal oficial de Tecknologistic. |
| 7 | ¿Existe tope mensual/por expediente aceptable de gasto en Claude API? | Bloquea `AI_COST_BUDGET_PER_CASE_USD` | **PENDIENTE (por diseño)** — se define después de medir el costo real de IA en pruebas; no hay techo fijado todavía. |
| 8 | ¿Ya existen los 50–100 expedientes históricos anonimizados, o hay que construirlos? | Bloquea GATE 2 (pruebas de aceptación) | **PARCIAL** — las RFQ pasadas están disponibles en `cotizaciones.tecknologistic@tecknologistic.com`. Falta exportarlas y anonimizarlas para fixtures de prueba; **exportarlas requiere acceso real al buzón**, por lo que esa acción concreta sigue sujeta a GATE 1. |

## B. Tabla RACI incompleta (sección 21 de `docs/architecture.md`)

| Decisión | Responsable (R) | Aprueba (A) | Consultado (C) | Informado (I) |
|---|---|---|---|---|
| Envío de cotización al cliente | Cotizador asignado | **PENDIENTE** | — | Gerencia |
| Orden de compra a proveedor | **PENDIENTE** | **PENDIENTE** | — | — |
| Excepción sin resolver > SLA | Sistema (alerta) | **PENDIENTE** | — | — |

**Pregunta derivada:** ¿quién tiene autoridad de aprobación (columna A) para envío
de cotización y para orden de compra a proveedor? Sin esto, la máquina de
estados (transiciones 15 y 22 de `docs/state_machine.md`) no puede validar
identidad del aprobador en código.

## C. Gaps de documentación — RESUELTOS

Estos tres gaps existían porque el documento "Tecknologistic — Arquitectura
IA Cotizaciones — Uso interno — Versión 1.0", referenciado repetidamente en
el prompt maestro v1.1 como "(igual que v1.0)", no estaba presente en este
repositorio. Jorge actualizó `docs/architecture.md` a la versión 1.2
(autocontenida, sin referencias externas no resueltas) y `docs/test_strategy.md`
con el detalle completo de cada caso — quedan cerrados:

- ~~El documento v1.0 no estaba en el repo~~ → `docs/architecture.md` v1.2 es
  ahora autocontenido: cada sección que decía "(igual que v1.0)" tiene su
  contenido completo (estados, los 10 agentes, RACI, fixtures,
  observabilidad, dashboard, IaC, manejo de errores, fase de producción,
  DoD, modo de trabajo, prioridades).
- ~~Stack tecnológico sin detalle concreto~~ → `docs/architecture.md` §4 lista
  el stack completo (Python 3.12+/FastAPI/Pydantic/SQLAlchemy/PostgreSQL/
  Alembic/pytest, Cloud Run/Cloud SQL/Pub/Sub/Secret Manager/Scheduler/
  Storage/IAM/Logging, Gmail API, Claude API, Odoo External API, Docker).
- ~~Los "20 casos de prueba" no existían en el repo~~ → `docs/architecture.md`
  §23 los lista por nombre y `docs/test_strategy.md` los detalla uno por uno
  (fixture, entrada, comportamiento esperado, agente responsable), más 2
  casos adicionales de infraestructura.

## D. Gaps de negocio — estado tras las respuestas de Jorge

Estos no son gaps de documentación: son decisiones de negocio. Se cierran o
se mantienen abiertos según la tabla A.

- ~~El roster de cotizadores (sección 13 de `docs/architecture.md`) no tenía
  fuente confirmada~~ → **RESUELTO** (ver A.2): vive en Odoo (RRHH). Falta
  únicamente el detalle técnico de qué modelo/endpoint de Odoo 18 expone esa
  disponibilidad — se confirma cuando exista el sandbox (A.3).
- ~~Canal de escalamiento del agente SLA sin definir~~ → **RESUELTO** (ver
  A.6): Gmail/correo.
- `docs/decisions/` (ADRs) sigue vacío — ninguna decisión no trivial se ha
  tomado aún porque no hay aprobación de negocio completa (ver E más abajo).
  Bajo impacto; se irán agregando ADRs a medida que se confirmen las
  decisiones de esta lista.

## E. Lo que sigue genuinamente pendiente (no se puede avanzar sin Jorge)

| # | Pendiente | Bloquea qué |
|---|---|---|
| 12 | Administrador del proyecto de Google Cloud / buzón (asistente vs. coordinadora de ventas) | Conexión real a Gmail (GATE 1); no bloquea trabajo con mocks |
| 13 | Sandbox/staging de Odoo (no existe todavía) | Cualquier prueba contra Odoo real; GATE 2 |
| 14 | `DATA_RETENTION_DAYS` (valor concreto de retención LOPDP) | Almacenamiento persistente real de datos de cliente; no bloquea mocks |
| 15 | `AI_COST_BUDGET_PER_CASE_USD` (techo de gasto Claude API) | Alertas de sobrecosto; se define tras medir costo real, no bloquea mocks |
| 16 | Exportar y anonimizar el set histórico de RFQ desde el buzón real | GATE 2 (pruebas de aceptación); la exportación en sí requiere acceso real a Gmail, sujeta a GATE 1 |
| 17 | Tabla RACI — quién aprueba envío de cotización y OC a proveedor (sección B) | Flujo de aprobación humana (P1); no bloquea P0 con mocks |
| 18 | Nombre real del evento que dispara las filas 13, 16 y 18 de `docs/state_machine.md` (acción manual del cotizador, rechazo de aprobación, nueva versión aprobada) — hoy son identificadores de código sin confirmar (`COTIZADOR_INICIA_TRABAJO`, `QUOTE_REJECTED`, reutilización de `QUOTE_APPROVED`), ver `docs/state_machine.md` regla general #6 | No bloquea P0 (esas filas son P1: cotización/aprobación); si se conecta una herramienta real de cotización, sus eventos deben mapear a estos nombres o renombrarlos |

---

## Cómo se usa este documento

- Cada vez que Jorge responda una pregunta, se actualiza la columna
  "Respuesta" con el valor confirmado (o "usar default: <valor>") y se agrega
  un ADR en `docs/decisions/` si la respuesta implica una decisión de
  arquitectura.
- Este archivo se revisa en cada GATE (1 y 2) — no se cierra, se mantiene vivo
  durante todo el proyecto.
