# Lógica de Decisión del Orquestador (Agente, no solo Workflow)

Un workflow ejecuta pasos fijos. Un agente decide qué hacer ante una situación. El Orquestador de este sistema debe comportarse como agente en los siguientes puntos de decisión — el resto del tiempo, sigue la tabla fija de `state_machine.md`. Esta separación es intencional: **decisión determinista donde sea posible, decisión de agente solo donde el resultado del paso anterior lo exige.**

## Puntos de decisión del Orquestador

### D1 — ¿Reintentar o escalar a EXCEPCIÓN?
**Se activa cuando:** un agente (Clasificador, Extractor, Case Resolver, Odoo Connector) falla técnicamente (timeout, error de API, respuesta JSON inválida).

**Regla de decisión:**
- Si es el intento 1 o 2 de un máximo de `MAX_RETRIES` (default: 3) → reintentar con backoff exponencial.
- Si se agotan los reintentos → `EXCEPTION_CREATED`, registrando el estado de origen para reingreso posterior.
- Nunca reintentar indefinidamente ni "saltarse" el paso fallido para continuar el flujo.

### D2 — ¿El resultado de un agente requiere revisión humana?
**Se activa cuando:** cualquier agente devuelve `requires_human_review=true` en su output (ver `agent_contracts.md`).

**Regla de decisión:**
- El Orquestador NO decide si el contenido está bien o mal — solo obedece el flag que el agente ya calculó con sus propios umbrales.
- Transición al estado correspondiente según `state_machine.md` (normalmente EXCEPCIÓN o VALIDACIÓN_REQUERIDA).
- El Orquestador sí decide **a quién notificar** (ver D4).

### D3 — ¿Pedir aclaración al cliente o esperar?
**Se activa cuando:** el expediente está en EXCEPCIÓN por ambigüedad de clasificación o de resolución de expediente, y ha pasado más de `CLARIFICATION_WAIT_HOURS` (default: 24h) sin que un humano lo resuelva.

**Regla de decisión (determinista, no discrecional):**
- Si `CLARIFICATION_WAIT_HOURS` se cumple y la excepción es de tipo "ambigüedad de contenido" (no de fallo técnico) → generar notificación al supervisor humano recomendando el envío de una solicitud de aclaración al cliente. El Orquestador **redacta la recomendación, nunca envía el correo sin aprobación humana** (regla de HITL de la sección 22 del prompt maestro).
- Si la excepción es de tipo "fallo técnico" → no recomendar contacto con cliente, solo escalar internamente.

### D4 — ¿A quién notificar según el tipo de excepción?
**Regla de decisión (tabla, no libre albedrío):**

| Tipo de excepción | Notificar a |
|---|---|
| Clasificación ambigua / resolución de expediente ambigua | Supervisor de cotizaciones |
| Conteo de líneas de baja confianza | Cotizador líder designado |
| Fallo técnico (Gmail, Odoo, Claude API caído) | Equipo técnico (canal de alertas, sección 26 del prompt maestro) |
| SLA vencido | Cotizador asignado + supervisor (escalamiento a las 2x del SLA sin respuesta) |
| Cotización o compra a proveedor pendiente de aprobación | Aprobador correspondiente según tabla RACI |

### D5 — ¿Reasignar una RFQ ya asignada?
**Se activa cuando:** un cotizador queda inactivo/ausente después de que una RFQ ya le fue asignada.

**Regla de decisión:**
- El Orquestador NO reasigna automáticamente por su cuenta. Genera una recomendación de reasignación (usando la misma lógica del Balanceador: Least Loaded by Open Lines entre los cotizadores restantes) y la deja pendiente de confirmación humana — reasignar sin confirmación puede duplicar trabajo si el cotizador original ya había avanzado offline.

## Lo que el Orquestador NUNCA decide por sí mismo

- Nunca aprueba una cotización o una compra a proveedor (siempre humano, sección 22).
- Nunca escribe en Odoo directamente (siempre vía Odoo Connector, sección 16).
- Nunca cambia un umbral de confianza definido en configuración.
- Nunca genera contenido comercial (precios, condiciones) — solo mueve estado y notifica.

## Resumen de diseño

El Orquestador es un **agente de bajo riesgo con decisiones acotadas a una tabla explícita** (D1–D5 arriba), no un agente de razonamiento libre. Esto es intencional: en un sistema con dinero y compromisos comerciales de por medio, la autonomía del orquestador debe crecer solo después de que Fase 1 (todo con aprobación humana) demuestre ser confiable en producción — no antes.
