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

## C. Gaps encontrados en FASE 0 — no vienen en la sección 42 original

Estos gaps existen porque el documento **"Tecknologistic — Arquitectura IA
Cotizaciones — Uso interno — Versión 1.0"**, referenciado repetidamente en el
prompt maestro v1.1 como "(igual que v1.0)", **no está presente en este
repositorio**. No se inventó contenido para rellenar estos vacíos — se listan
aquí como bloqueantes reales.

| # | Gap | Impacto | Acción requerida |
|---|---|---|---|
| 9 | El documento v1.0 completo no está en el repo. Todo lo marcado "(igual que v1.0)" en el prompt maestro (estados 8, agentes 9-19 comportamiento base, stack sección 4, RACI base sección 22, pruebas sección 24, fixtures 25, observabilidad 26, dashboard 27, IaC 28, errores 32, producción 33, DoD 34) solo tiene el detalle que el propio v1.1 agrega explícitamente. | Alto — no se puede construir `docs/test_strategy.md` con los "20 casos mínimos" porque su contenido nunca llegó a este repo. | **Jorge debe compartir el documento v1.0 completo**, o confirmar que se reconstruye desde cero. |
| 10 | El stack tecnológico completo (sección 4) no tiene ningún detalle concreto salvo la nota de renovación del watch de Gmail. No hay versión de lenguaje/framework, ORM, cola de mensajes concreta más allá de "Pub/Sub", etc. | Medio — bloquea `docs/architecture.md` §Stack en detalle | Confirmar stack real o aceptar propuesta de referencia (ver `docs/architecture.md`, marcada como propuesta, no como decisión). |
| 11 | Los "20 casos de prueba" de la sección 24 (requeridos para GATE 2) no existen en ningún archivo del repo. | Alto — GATE 2 no se puede alcanzar sin ellos | Compartir el documento v1.0 o co-diseñar los 20 casos desde cero con Jorge. |
| 12 | El roster de cotizadores (sección 9.3) no tiene fuente confirmada: ¿Odoo RRHH, tabla propia, hoja de configuración? | Alto — bloquea implementación real del Balanceador | Ver pregunta A.2. |
| 13 | Canal de escalamiento del agente SLA (sección 9.4) sin definir. | Medio — bloquea implementación real de SLA | Ver pregunta A.6. |
| 14 | `docs/decisions/` (ADRs) está creado vacío — ninguna decisión no trivial se ha tomado aún porque no hay aprobación de negocio. | Bajo | Se irán agregando ADRs a medida que se resuelvan estas preguntas. |

---

## Cómo se usa este documento

- Cada vez que Jorge responda una pregunta, se actualiza la columna
  "Respuesta" con el valor confirmado (o "usar default: <valor>") y se agrega
  un ADR en `docs/decisions/` si la respuesta implica una decisión de
  arquitectura.
- Este archivo se revisa en cada GATE (1 y 2) — no se cierra, se mantiene vivo
  durante todo el proyecto.
