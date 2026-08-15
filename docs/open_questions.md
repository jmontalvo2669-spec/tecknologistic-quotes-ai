# Preguntas Abiertas — Checklist Viva (bloqueante para Fase 1 real)

Este documento es el entregable #18 de la sección 39 del prompt maestro y el
insumo principal de GATE 1. Nada de esta lista se ha respondido todavía —
FASE 0 es discovery puro, sin acceso al negocio. Cada pregunta debe
responderse o marcarse explícitamente "usar default" antes de conectar
Gmail/Odoo reales.

Estado: **BLOQUEANTE** — GATE 1 no se supera hasta que Jorge responda o
apruebe explícitamente los defaults propuestos.

---

## A. Preguntas originales del prompt maestro (sección 42)

| # | Pregunta | Por qué bloquea | Respuesta |
|---|---|---|---|
| 1 | ¿Cuántas RFQ/día y líneas/RFQ en promedio hoy? | Dimensiona balanceador y SLA (sección 43) | **PENDIENTE** |
| 2 | ¿Cuántos cotizadores activos hay y dónde vive su disponibilidad/ausencia? | Fuente del roster del Balanceador (sección 9.3) | **PENDIENTE** |
| 3 | ¿Versión de Odoo instalada, plan contratado, existe sandbox/staging? | Bloquea diseño del Odoo Connector y GATE 2 | **PENDIENTE** |
| 4 | ¿El buzón central de cotizaciones ya existe como cuenta dedicada? ¿Quién administra el proyecto de Google Cloud? | Bloquea cualquier conexión real a Gmail | **PENDIENTE** |
| 5 | ¿Existe política de retención de correspondencia comercial en Tecknologistic, o hay que definirla? | Bloquea `DATA_RETENTION_DAYS` y `docs/security.md` (LOPDP) | **PENDIENTE** |
| 6 | ¿Las alertas de SLA/errores van por Gmail, Google Chat, ambos, u otro canal? | Bloquea diseño del agente SLA y observabilidad | **PENDIENTE** |
| 7 | ¿Existe tope mensual/por expediente aceptable de gasto en Claude API? | Bloquea `AI_COST_BUDGET_PER_CASE_USD` | **PENDIENTE** |
| 8 | ¿Ya existen los 50–100 expedientes históricos anonimizados, o hay que construirlos? | Bloquea GATE 2 (pruebas de aceptación) | **PENDIENTE** |

## B. Tabla RACI incompleta (sección 22 del prompt maestro)

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

## D. Gaps que siguen pendientes — Jorge los responde directamente

Estos no son gaps de documentación: son decisiones de negocio que no se
inventan ni se asumen. Se mantienen aquí hasta que Jorge las responda
(ver también la sección A de este documento, que cubre las mismas preguntas
en su redacción original del prompt maestro).

| # | Gap | Impacto | Acción requerida |
|---|---|---|---|
| 9 | El roster de cotizadores (sección 13 de `docs/architecture.md`) no tiene fuente confirmada: ¿Odoo RRHH, tabla propia, hoja de configuración? | Alto — bloquea implementación real del Balanceador | Ver pregunta A.2. |
| 10 | Canal de escalamiento del agente SLA (sección 16 de `docs/architecture.md`) sin definir. | Medio — bloquea implementación real de SLA | Ver pregunta A.6. |
| 11 | `docs/decisions/` (ADRs) está creado vacío — ninguna decisión no trivial se ha tomado aún porque no hay aprobación de negocio. | Bajo | Se irán agregando ADRs a medida que se resuelvan estas preguntas. |

---

## Cómo se usa este documento

- Cada vez que Jorge responda una pregunta, se actualiza la columna
  "Respuesta" con el valor confirmado (o "usar default: <valor>") y se agrega
  un ADR en `docs/decisions/` si la respuesta implica una decisión de
  arquitectura.
- Este archivo se revisa en cada GATE (1 y 2) — no se cierra, se mantiene vivo
  durante todo el proyecto.
