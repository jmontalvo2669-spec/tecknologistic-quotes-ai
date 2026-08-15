# ADR 0001 — Quitar `producto_especializado` y `certificacion_requerida` del contrato del Balanceador

**Estado:** aceptada
**Contexto de la decisión:** confirmación explícita de Jorge Montalvo (sesión de revisión de código posterior a PASO 6).

## Contexto

El contrato original del Balanceador (`docs/agent_contracts.md` §5,
`schemas.balancer.RosterFlags`) incluía cuatro flags de exclusión:
`cliente_reservado`, `producto_especializado`, `certificacion_requerida` y
`urgente_vip`. La razón original para que **cualquiera** de estas cuatro
flags excluyera la asignación automática (en vez de intentar filtrar el
roster por esa capacidad) era que el contrato del roster
(`cotizador_id/activo/carga_actual_lineas`) no incluye qué cotizador
cumple esa condición especial — no había forma de saber, en código, a
quién asignar sin adivinar.

Jorge confirmó que **los 6 cotizadores activos pueden cotizar cualquier
producto** — no hay especialidades ni certificaciones que diferencien a
uno de otro en la práctica actual de Tecknologistic.

## Decisión

Se quitan `producto_especializado` y `certificacion_requerida` de
`RosterFlags` (y de todo el contrato del Balanceador). Ya no existe ningún
cotizador "más calificado" que otro para esas condiciones, así que excluir
la asignación automática dejaba de proteger algo real: no había una
decisión humana de "a quién asignar por su especialidad" que hacer en su
lugar, solo fricción innecesaria.

`cliente_reservado` y `urgente_vip` **se mantienen** — su razón de ser es
distinta y sigue vigente:
- `cliente_reservado` típicamente implica que ese cliente tiene un
  cotizador designado de antemano (una decisión comercial, no de
  capacidad técnica) — el roster tampoco expone quién es ese cotizador
  designado, así que sigue sin poder resolverse automáticamente.
- `urgente_vip` no es una cuestión de "quién puede" sino de priorización
  humana explícita (¿se prioriza sobre la cola normal? ¿se avisa a
  gerencia?) — una decisión de negocio, no de balanceo por carga.

## Consecuencias

- `schemas.balancer.RosterFlags` ya no tiene los campos
  `producto_especializado` ni `certificacion_requerida`.
- `docs/agent_contracts.md` §5 y `docs/architecture.md` §13 se actualizan
  para reflejar solo dos exclusiones de flags (antes cuatro).
- Si en el futuro Tecknologistic introduce especialización real entre
  cotizadores (p. ej. contrata a alguien que solo cotiza cierto tipo de
  producto), este contrato necesita una nueva versión — con un campo en
  el roster que indique qué cotizador cumple esa condición, no solo un
  flag genérico en el caso.
