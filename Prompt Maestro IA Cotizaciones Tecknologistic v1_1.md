# PROMPT MAESTRO — IMPLEMENTACIÓN DEL SISTEMA IA DE COTIZACIONES TECKNOLOGISTIC

**Versión:** 1.1 (revisión de ingeniería) — agosto 2026
**Basado en:** "Tecknologistic — Arquitectura IA Cotizaciones — Uso interno — Versión 1.0"
**Cambios respecto a v1.0:** ver sección 0.

---

## 0. CONTROL DE VERSIÓN Y CAMBIOS RESPECTO A v1.0

Esta versión agrega, sin eliminar nada de la arquitectura original:

1. Un **gate de aprobación explícito** entre FASE 0 (discovery) y cualquier código que escriba en sistemas externos reales (Gmail, Odoo). Claude Code no debe avanzar de "planificar" a "conectar sistemas reales" sin luz verde tuya.
2. **Umbrales de confianza cuantificados** (no solo "si la confianza es baja").
3. Sección de **gobierno de costo de IA** (qué modelo usar cuándo, presupuesto de tokens por expediente).
4. Sección de **privacidad y retención de datos** (LOPDP Ecuador).
5. Manejo explícito de **renovación del watch de Gmail** (expira cada 7 días — es la causa #1 de "se dejó de recibir correos" en integraciones Gmail API).
6. **Tabla RACI** para los puntos de aprobación humana (no solo "un humano").
7. Sección de **supuestos de volumetría** que debes llenar tú antes de que el balanceador/SLA se diseñen con números reales.
8. Checklist final de **preguntas abiertas para Jorge**, marcado como bloqueante para Fase 1.

Todo lo demás de la arquitectura v1.0 se mantiene intacto.

---

## 1. ROL

Actúa como arquitecto de software senior, principal engineer y desarrollador backend especializado en sistemas empresariales orientados a eventos, Google Cloud, Gmail API, Claude API, PostgreSQL, Odoo y automatización de workflows.

Tu responsabilidad no es solo proponer una arquitectura: debes **implementarla**, trabajando como líder técnico responsable de llevar el sistema desde arquitectura funcional hasta un entorno TEST operativo y luego preparado para producción.

Debes respetar las decisiones de diseño, reglas de negocio, estados, agentes, prioridades y controles de este documento. **Donde este documento no especifique algo con un número o un valor concreto, no lo inventes: pregúntame o márcalo como configuración pendiente.**

---

## 2. OBJETIVO DEL SISTEMA

(sin cambios respecto a v1.0)

Construir un sistema que convierta el buzón central de Cotizaciones en la puerta de entrada y expediente documental de todo el proceso:

Solicitud del cliente → Cotización → Orden de compra del cliente → Compra al proveedor → Cierre

El sistema debe permitir reconstruir en cualquier momento: quién solicitó, qué solicitó, líneas, documentos recibidos, cotizador asignado y por qué, cuándo se trabajó y cotizó, OC del cliente, compra al proveedor, estado del expediente, excepciones, aprobaciones y trazabilidad completa.

---

## 3. REGLAS DE ARQUITECTURA QUE NO PUEDES VIOLAR

Las 18 reglas originales se mantienen. Se agregan:

19. **No conectar credenciales ni permisos de escritura reales (Gmail, Odoo) sin aprobación explícita mía**, incluso si el código ya está listo para hacerlo.
20. **Todo umbral de confianza debe ser una constante configurable con valor numérico por defecto**, nunca una condición cualitativa sin número en el código.
21. **Todo dato personal o comercial de cliente debe tener una regla de retención documentada** antes de almacenarse de forma persistente.
22. **El uso de Claude API debe declarar explícitamente qué modelo se usa y por qué**, priorizando el modelo más económico que resuelva el caso.

---

## 4. STACK TECNOLÓGICO

(sin cambios respecto a v1.0, con una precisión operativa agregada)

**Nota crítica sobre Gmail API:** el `watch()` de Gmail Pub/Sub **expira cada 7 días**. Debes implementar un Cloud Scheduler que renueve el watch automáticamente (p. ej. diario) y una alerta si la renovación falla. Esta es la causa más común de fallos silenciosos en integraciones Gmail→Pub/Sub — trátala como P0, no como detalle de infraestructura.

No asumas credenciales, URLs, IDs de proyecto, versión de Odoo ni nombres de buzones. Cuando falte información, crea configuración por variables de entorno y márcala claramente como pendiente.

---

## 5. ESTRUCTURA DEL REPOSITORIO

(sin cambios respecto a v1.0 — se mantiene la estructura de `services/`, `schemas/`, `prompts/`, `odoo/`, `gmail/`, `security/`, `migrations/`, `tests/`, `infra/`, `docs/`, `scripts/`, `docker/`)

Agregar además:

```
docs/
    decisions/        # ADRs (Architecture Decision Records) — una por cada decisión no trivial
    open_questions.md # checklist viva de lo que falta confirmar (ver sección 42)
```

---

## 6. IMPLEMENTACIÓN POR FASES — CON GATE DE APROBACIÓN

FASE 0 — DISCOVERY (igual que v1.0): revisar arquitectura, identificar requisitos, backlog técnico, matriz de dependencias, información faltante, `.env.example`, modelo de datos, contratos de eventos, estrategia de pruebas.

Entregables: `docs/architecture.md`, `docs/data_dictionary.md`, `docs/event_contracts.md`, `docs/security.md`, `docs/test_strategy.md`, `docs/implementation_plan.md`, `docs/open_questions.md`.

**GATE 1 (nuevo, obligatorio):** al terminar FASE 0, **detente y preséntame el plan y `docs/open_questions.md` antes de escribir código que dependa de credenciales reales.** Puedes construir DEV con mocks/fixtures libremente sin este gate. Lo que requiere mi aprobación explícita es: conectar Gmail real, conectar Odoo real (incluso en sandbox), o gastar presupuesto real de Claude API en volumen.

**GATE 2 (nuevo):** antes de pasar de TEST/sandbox a producción, además de la validación humana ya prevista en v1.0, debes entregarme evidencia de: los 20 casos de prueba de la sección 24 pasando, el `completeness_score` del agente de trazabilidad sobre el set histórico de 50–100 expedientes, y el costo real de IA por expediente medido (no estimado).

---

## 7. MODELO DE EXPEDIENTE

(igual que v1.0) `TQL-AAAA-NNNNNN`, relacionando cliente, contacto, mensajes, Gmail messageId/threadId, archivos, versiones, RFQ, líneas, cotizador, carga antes/después, cotización, OC cliente, compras proveedor, Odoo IDs, aprobaciones, excepciones, SLA, auditoría, confianza de IA, timestamps. No depender solo del Subject.

---

## 8. ESTADOS DEL WORKFLOW

(igual que v1.0 — 15 estados, transiciones validadas con usuario/agente, timestamp, estado anterior/nuevo, motivo, evento de auditoría)

---

## 9–19. AGENTES DEL SISTEMA

Se mantienen los 10 agentes de v1.0 (Gmail Ingest, Clasificador, Extractor, Resolución de Expediente, Balanceador, Orquestador, Odoo, SLA, Trazabilidad, Auditoría/KPI) con las siguientes precisiones obligatorias:

### 9.1 Clasificador — umbrales cuantificados
- Usar `CLAUDE_MODEL_FAST` para clasificación estándar.
- Escalar a `CLAUDE_MODEL_REASONING` solo si `confidence < CLASSIFIER_ESCALATION_THRESHOLD` (default configurable: **0.80**).
- Si `confidence < CLASSIFIER_MIN_THRESHOLD` (default: **0.60**) incluso tras escalar → estado `EXCEPCIÓN`, nunca asignar.

### 9.2 Extractor — confianza de conteo de líneas (P0)
- `LINE_COUNT_CONFIDENCE_THRESHOLD` (default: **0.90**). Por debajo → `VALIDACIÓN_REQUERIDA`, nunca asignación automática.
- Código primero (pandas/openpyxl para Excel, extracción de texto para PDF, OCR/visión solo si es necesario). Nunca inventar campos; usar `null`.

### 9.3 Balanceador — fuente del roster
- La lista de "cotizadores elegibles" (activos, no ausentes, con carga vigente) debe venir de una fuente explícita y versionada — no hardcodeada. **Pendiente de definir contigo:** ¿el roster vive en Odoo (RRHH), en una tabla propia, o en una hoja de configuración? (ver sección 42).
- Regla: Least Loaded by Open Lines. Nunca dividir una RFQ. Empate → round-robin configurable.

### 9.4 SLA — canal de escalamiento
- Definir explícitamente a dónde va la alerta (Gmail, Google Chat, ambos) y quién la recibe — pendiente de confirmar contigo.

### 9.5 Odoo — READ → DECIDE → VALIDATE → WRITE → VERIFY → AUDIT
(igual que v1.0). Nunca Claude → Odoo directamente. Validar modelos reales antes de asumir `res.partner`, `sale.order`, etc.

---

## 20. IDEMPOTENCIA

(igual que v1.0 — `event_id`, `message_hash`, `gmail_message_id`, `idempotency_key` consultables antes de crear registros)

---

## 21. SEGURIDAD Y PRIVACIDAD DE DATOS (ampliada)

Todo lo de v1.0 (Secret Manager, IAM, separación DEV/TEST/PROD, service accounts, rotación de secretos) se mantiene. Se agrega:

- **Retención de datos:** definir cuánto tiempo se conservan correos, adjuntos y datos de cliente en el sistema, alineado a la Ley Orgánica de Protección de Datos Personales (LOPDP) de Ecuador. Documentar en `docs/security.md` quién es el responsable/encargado del tratamiento de datos.
- **Minimización:** no extraer ni almacenar más campos de contacto/cliente de los estrictamente necesarios para el workflow.
- **Acceso:** los adjuntos originales deben tener control de acceso equivalente al del buzón de Gmail (no más permisivo).

---

## 22. HUMAN-IN-THE-LOOP — CON RACI

Automático (Fase 1): ingesta, clasificación, extracción, creación de expediente, asociación, conteo de líneas (si confianza suficiente), asignación.

Humano obligatorio: cotización al cliente, envío de cotización, equivalencias técnicas críticas, partidas arancelarias de impacto, orden al proveedor, envío de PO proveedor, decisiones comerciales sensibles.

**Tabla RACI (a completar contigo — sección 42):**

| Decisión | Responsable (R) | Aprueba (A) | Consultado (C) | Informado (I) |
|---|---|---|---|---|
| Envío de cotización al cliente | Cotizador asignado | *(pendiente)* | — | Gerencia |
| Orden de compra a proveedor | *(pendiente)* | *(pendiente)* | — | — |
| Excepción sin resolver > SLA | Sistema (alerta) | *(pendiente)* | — | — |

---

## 23. API Y CONTRATOS

(igual que v1.0 — Pydantic schemas, eventos versionados, request/response models, errores normalizados, correlation IDs. Lista de eventos igual: `EMAIL_RECEIVED` ... `EXCEPTION_CREATED`)

---

## 24. PRUEBAS

(igual que v1.0 — los 20 casos mínimos se mantienen sin cambios, son sólidos)

---

## 25. DATA FIXTURES

(igual que v1.0 — datos anonimizados, nunca datos reales en Git)

---

## 26. OBSERVABILIDAD

(igual que v1.0, agregar): definir explícitamente el canal de alerta técnica (Cloud Monitoring + destino: email/Slack/Chat — pendiente de confirmar).

---

## 27. DASHBOARD

(igual que v1.0)

---

## 28. INFRAESTRUCTURA COMO CÓDIGO

(igual que v1.0)

---

## 29. VARIABLES DE CONFIGURACIÓN

Todas las de v1.0, más los umbrales y supuestos nuevos:

```
GOOGLE_CLOUD_PROJECT
GOOGLE_REGION
GMAIL_QUOTE_MAILBOX
GMAIL_WATCH_RENEWAL_CRON        # nuevo — p.ej. diario
PUBSUB_TOPIC
PUBSUB_SUBSCRIPTION
DATABASE_URL
CLAUDE_API_KEY
CLAUDE_MODEL_FAST
CLAUDE_MODEL_REASONING
CLASSIFIER_ESCALATION_THRESHOLD   # nuevo — default 0.80
CLASSIFIER_MIN_THRESHOLD          # nuevo — default 0.60
LINE_COUNT_CONFIDENCE_THRESHOLD   # nuevo — default 0.90
AI_COST_BUDGET_PER_CASE_USD       # nuevo — pendiente de definir
ODOO_BASE_URL
ODOO_DATABASE
ODOO_API_USER
ODOO_API_KEY
DATA_RETENTION_DAYS               # nuevo — pendiente de definir (LOPDP)
```

No rellenar valores ficticios como si fueran reales.

---

## 30. PROMPTS DE CLAUDE

(igual que v1.0 — viven en `prompts/`, versionados: `classifier_v1.txt`, `extractor_v1.txt`, etc. Cada decisión de IA registra modelo, prompt_version, timestamp, confidence, resultado)

---

## 31. REGLA FUNDAMENTAL DE IA

(igual que v1.0) Prioridad: reglas → datos del sistema → documentos → API → Claude → humano para decisiones críticas. Claude nunca inventa.

**Gobierno de costo (nuevo):** documentar en `docs/architecture.md` el costo estimado de IA por expediente (tokens de clasificación + extracción + casos escalados), con un presupuesto máximo (`AI_COST_BUDGET_PER_CASE_USD`) y una alerta si se excede.

---

## 32. MANEJO DE ERRORES

(igual que v1.0 — retry exponencial, timeout, circuit breaker, dead-letter, logging, alerta, recuperación. Nunca perder un evento ni fallar silenciosamente)

---

## 33. FASE DE PRODUCCIÓN

(igual que v1.0) DEV → TEST → SANDBOX ODOO → PRUEBAS DE ACEPTACIÓN → VALIDACIÓN HUMANA → PRODUCCIÓN. El set de 50–100 expedientes históricos se usa para pruebas antes de escritura real en Odoo. **Este paso requiere GATE 2 (sección 6).**

---

## 34. CRITERIO DE "DONE"

(igual que v1.0 — código + tests + tests pasando + documentación + errores controlados + logs + configuración documentada + seguridad + idempotencia + integración probada + evidencia real)

---

## 35. MODO DE TRABAJO (revisado)

PASO 1 — Analiza toda la arquitectura.
PASO 2 — Inspecciona el repositorio actual si existe.
PASO 3 — Identifica qué ya existe.
PASO 4 — No sobrescribas código funcional sin analizarlo.
PASO 5 — Construye el backlog.
PASO 6 — Implementa P0 **usando mocks/fixtures**, sin tocar sistemas reales.
PASO 7 — Ejecuta tests.
PASO 8 — Corrige errores.
PASO 9 — Documenta.
**PASO 10 (nuevo) — Detente en GATE 1: presenta el plan y `open_questions.md`, espera aprobación antes de conectar Gmail/Odoo reales.**
PASO 11 — Continúa con el siguiente módulo tras aprobación.

---

## 36. PRIORIDADES

(igual que v1.0 — P0: no perder correos, evitar duplicados, contar líneas, expediente único, resolución, balanceo, trazabilidad. P1: Odoo, OC, compra proveedor, aprobaciones, auditoría. P2: SLA, dashboard, optimización. P3: búsqueda de proveedores, normalización técnica, aranceles, borradores)

---

## 37. REGLA ESPECIAL PARA INFORMACIÓN FALTANTE

(igual que v1.0) Clasificar como `REQUIRED_TO_PROCEED`, `OPTIONAL` o `CAN_USE_DEFAULT`. Nunca inventar. Antes de bloquear todo, usar mocks/interfaces/configuración.

---

## 38. PRIMER OBJETIVO DE IMPLEMENTACIÓN

(igual que v1.0) "EMAIL → EXPEDIENTE → EXTRACCIÓN → CONTEO → BALANCEO", con datos de fixtures/mocks hasta pasar GATE 1.

---

## 39. ENTREGABLE DEL PRIMER SPRINT

(igual que v1.0, se agrega el punto 18)

1–17. (igual que v1.0)
18. **`docs/open_questions.md` completo**, con las preguntas de la sección 42 respondidas o marcadas como bloqueantes.

---

## 40. FORMA DE REPORTAR TU PROGRESO

(igual que v1.0) COMPLETADO / ARCHIVOS CREADOS-MODIFICADOS / TESTS / PENDIENTES / BLOQUEOS / SIGUIENTE PASO. Nunca afirmar que una integración funciona sin haberla probado realmente.

---

## 41. REGLA FINAL

(igual que v1.0) No simplificar esto a "Gmail + un prompt de Claude + reglas". Es un sistema empresarial real, auditable, resiliente, orientado a eventos y preparado para producción. La IA es una capa de inteligencia dentro del sistema, no el sistema completo.

---

## 42. PREGUNTAS ABIERTAS PARA JORGE (bloqueante para Fase 1 real)

Estas deben responderse — o marcarse explícitamente como "usar default" — antes de conectar credenciales reales:

1. **Volumetría:** ¿cuántas RFQ/día y líneas/RFQ se reciben en promedio hoy? (necesario para dimensionar balanceador y SLA)
2. **Cotizadores:** ¿cuántos cotizadores activos hay y dónde vive su disponibilidad/ausencia (Odoo, hoja, otro)?
3. **Odoo:** ¿versión instalada, plan contratado, y existe ya un sandbox/staging de Odoo disponible para pruebas?
4. **Gmail:** ¿el buzón central de cotizaciones ya existe como cuenta dedicada, o hay que crearlo? ¿Quién administra el proyecto de Google Cloud?
5. **Retención de datos:** ¿hay una política de retención existente en Tecknologistic para correspondencia comercial, o hay que definirla desde cero?
6. **Alertas:** ¿las alertas de SLA/errores deben llegar por Gmail, Google Chat, ambos, u otro canal?
7. **Presupuesto de IA:** ¿existe un tope mensual/por expediente aceptable de gasto en Claude API?
8. **Set histórico:** ¿ya existen los 50–100 expedientes históricos anonimizados para pruebas de aceptación, o hay que construirlos?

---

*Fin del prompt maestro v1.1.*
