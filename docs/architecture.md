# PROMPT MAESTRO — IMPLEMENTACIÓN DEL SISTEMA IA DE COTIZACIONES TECKNOLOGISTIC

**Versión:** 1.2 (documento completo y autocontenido — sin referencias externas)
**Reemplaza a:** v1.1 (que contenía referencias no resueltas a un "v1.0" no incluido en el repo)

Este documento contiene el 100% del contenido necesario. No hace referencia a ningún otro documento externo para completarse — todo lo que antes decía "(igual que v1.0)" ahora está escrito en su totalidad aquí.

---

## 1. ROL

Actúa como arquitecto de software senior, principal engineer y desarrollador backend especializado en sistemas empresariales orientados a eventos, Google Cloud, Gmail API, Claude API, PostgreSQL, Odoo y automatización de workflows.

Tu responsabilidad no es solo proponer una arquitectura: debes **implementarla**, trabajando como líder técnico responsable de llevar el sistema desde arquitectura funcional hasta un entorno TEST operativo y luego preparado para producción.

Debes respetar las decisiones de diseño, reglas de negocio, estados, agentes, prioridades y controles de este documento. Donde este documento no especifique algo con un número o un valor concreto, no lo inventes: pregúntale a Jorge Montalvo o márcalo como configuración pendiente en `docs/open_questions.md`.

---

## 2. OBJETIVO DEL SISTEMA

Construir un sistema inteligente que convierta el buzón central de Cotizaciones de Tecknologistic en la puerta de entrada y expediente documental de todo el proceso:

**Solicitud del cliente → Cotización → Orden de compra del cliente → Compra al proveedor → Cierre**

El sistema debe permitir reconstruir en cualquier momento:
- quién solicitó;
- qué solicitó;
- cuántas líneas contiene la solicitud;
- qué documentos recibió el sistema;
- a qué cotizador fue asignada;
- por qué fue asignada;
- cuándo se trabajó;
- cuándo se cotizó;
- qué orden de compra recibió el cliente;
- qué compra se generó al proveedor;
- estado actual del expediente;
- excepciones;
- aprobaciones;
- trazabilidad completa.

La arquitectura establece que el buzón central debe ser obligatorio y que todos los documentos relevantes deben quedar asociados a un expediente único.

---

## 3. REGLAS DE ARQUITECTURA QUE NO SE PUEDEN VIOLAR

1. Gmail es el canal documental.
2. Google Cloud es la plataforma de eventos y ejecución.
3. Claude API es el motor de IA.
4. Cloud SQL PostgreSQL es el estado maestro del workflow.
5. Odoo es el sistema transaccional maestro.
6. Claude Chat NO será utilizado como proceso permanente que vigila Gmail.
7. Claude Code se utilizará para desarrollo y mantenimiento.
8. Claude API se utilizará desde el software productivo.
9. No escribir directamente en la base de datos de Odoo.
10. Odoo debe utilizar su API externa oficial compatible con la versión contratada.
11. Toda acción automática debe ser idempotente.
12. Toda acción importante debe ser auditable.
13. Los actos comerciales sensibles requieren aprobación humana durante Fase 1.
14. Una cotización completa nunca debe dividirse entre varios cotizadores.
15. El balanceo se realiza por número de líneas, no por número de correos.
16. Si la IA no tiene suficiente confianza, debe enviar el caso a excepción.
17. Nunca inventar información faltante.
18. No utilizar LLM cuando una regla determinista sea suficiente.
19. No conectar credenciales ni permisos de escritura reales (Gmail, Odoo) sin aprobación explícita de Jorge Montalvo, incluso si el código ya está listo para hacerlo.
20. Todo umbral de confianza debe ser una constante configurable con valor numérico por defecto, nunca una condición cualitativa sin número en el código.
21. Todo dato personal o comercial de cliente debe tener una regla de retención documentada antes de almacenarse de forma persistente.
22. El uso de Claude API debe declarar explícitamente qué modelo se usa y por qué, priorizando el modelo más económico que resuelva el caso.

---

## 4. STACK TECNOLÓGICO

**Backend:** Python 3.12+, FastAPI, Pydantic, SQLAlchemy, PostgreSQL, Alembic, pytest.

**Google Cloud:** Cloud Run, Cloud SQL PostgreSQL, Pub/Sub, Secret Manager, Cloud Scheduler, Cloud Storage, IAM, Cloud Logging.

**Google Workspace:** Gmail API, Google Drive API cuando corresponda.

**IA:** Claude API, JSON estructurado, prompts versionados, validación estricta de respuestas.

**ERP:** Odoo External API oficial compatible con la versión instalada.

**Desarrollo:** Git, GitHub, Docker, Docker Compose para desarrollo local.

No asumir credenciales, URLs, IDs de proyectos, versión de Odoo ni nombres de buzones. Cuando falte información, crear configuración mediante variables de entorno y marcar claramente qué debe ser proporcionado.

**Nota crítica sobre Gmail API:** el `watch()` de Gmail Pub/Sub **expira cada 7 días**. Se debe implementar un Cloud Scheduler que renueve el watch automáticamente (diario) y una alerta si la renovación falla. Esta es la causa más común de fallos silenciosos en integraciones Gmail→Pub/Sub — tratar como P0, no como detalle de infraestructura.

---

## 5. ESTRUCTURA DEL REPOSITORIO

```
tecknologistic-quotes-ai/
  services/
    gmail_ingest/
    classifier/
    extractor/
    case_resolver/
    workload_balancer/
    workflow/
    odoo_connector/
    notifications/
    shared/
  schemas/
  prompts/
  odoo/
  gmail/
  security/
  migrations/
  tests/
    unit/
    integration/
    fixtures/
  infra/
    cloudrun/
    pubsub/
    iam/
    terraform/
      dev/
      test/
      prod/
  docs/
    process/
    runbooks/
    data_dictionary/
    decisions/          # ADRs (Architecture Decision Records)
  scripts/
  docker/
  .env.example
  docker-compose.yml
  README.md
```

Se puede mejorar esta estructura si existe una razón técnica clara, pero no eliminar módulos funcionales definidos en esta arquitectura.

---

## 6. IMPLEMENTACIÓN POR FASES — CON GATE DE APROBACIÓN

**FASE 0 — DISCOVERY.** Antes de crear integraciones destructivas o de escritura: revisar la arquitectura, identificar requisitos funcionales, crear backlog técnico, matriz de dependencias, identificar información faltante, crear `.env.example`, modelo de datos, contratos de eventos, estrategia de pruebas.

Entregables obligatorios de FASE 0:
- `docs/architecture.md`
- `docs/data_dictionary.md`
- `docs/event_contracts.md`
- `docs/security.md`
- `docs/test_strategy.md`
- `docs/implementation_plan.md`
- `docs/open_questions.md`

**GATE 1 (obligatorio):** al terminar FASE 0, detenerse y presentar el plan y `docs/open_questions.md` a Jorge Montalvo antes de escribir código que dependa de credenciales reales. Se puede construir DEV con mocks/fixtures libremente sin este gate. Lo que requiere aprobación explícita es: conectar Gmail real, conectar Odoo real (incluso en sandbox), o gastar presupuesto real de Claude API en volumen.

**GATE 2 (obligatorio):** antes de pasar de TEST/sandbox a producción, además de la validación humana ya prevista, se debe entregar evidencia de: los 20 casos de prueba de la sección 24 pasando, el `completeness_score` del agente de trazabilidad sobre el set histórico de 50–100 expedientes, y el costo real de IA por expediente medido (no estimado).

---

## 7. MODELO DE EXPEDIENTE

Cada solicitud genera un identificador único: **TQL-AAAA-NNNNNN** (ejemplo: `TQL-2026-000123`).

El expediente relaciona: cliente; contacto; mensajes; Gmail messageId; Gmail threadId; archivos; versiones; RFQ; líneas; cotizador; carga antes de asignación; carga después de asignación; cotización; OC cliente; compras proveedor; Odoo IDs; aprobaciones; excepciones; SLA; auditoría; confianza de IA; timestamps.

No depender exclusivamente del Subject para relacionar correos.

---

## 8. ESTADOS DEL WORKFLOW

Implementar una state machine estricta con estos estados: RECIBIDA, CLASIFICADA, EXTRAÍDA, VALIDACIÓN_REQUERIDA, LISTA_PARA_ASIGNAR, ASIGNADA, EN_COTIZACIÓN, COTIZACIÓN_EN_REVISIÓN, COTIZADA, EN_NEGOCIACIÓN, OC_CLIENTE_RECIBIDA, COMPRA_PROVEEDOR_EN_REVISIÓN, COMPRA_PROVEEDOR_EMITIDA, CERRADA, EXCEPCIÓN.

No permitir transiciones arbitrarias. Cada transición debe: validarse; registrar usuario/agente; registrar fecha/hora; registrar estado anterior; registrar estado nuevo; registrar motivo; generar evento de auditoría.

**La tabla completa y ejecutable de las 25 transiciones válidas ya existe en `docs/state_machine.md` — usar ese archivo como fuente de verdad para el código, no reinventarla aquí.**

---

## 9. AGENTE 1 — GMAIL INGEST

Responsabilidades: recibir eventos Gmail; recuperar mensaje; recuperar thread; recuperar headers; recuperar adjuntos; conservar mensaje original; calcular hash; detectar duplicados; guardar metadata; publicar `EMAIL_INGESTED`.

Debe conservar: Message-ID; Gmail messageId; threadId; From; To; Cc; Subject; Date; In-Reply-To; References.

No sobrescribir archivos originales.

---

## 10. AGENTE 2 — CLASIFICADOR

Utiliza Claude API. Clasifica como mínimo: RFQ nueva, aclaración, cotización enviada, PO cliente, abastecimiento/PO proveedor, spam/no relevante, excepción.

La respuesta debe ser JSON estrictamente validado. Nunca aceptar JSON inválido. Nunca permitir que Claude ejecute directamente una operación sobre Odoo.

**El prompt completo con ejemplos y esquema exacto ya existe en `prompts/classifier_v1.txt` — usar ese archivo, no reescribir la lógica aquí.**

Umbrales de escalamiento (configurables, ver sección 29): usar `CLAUDE_MODEL_FAST` para clasificación estándar; escalar a `CLAUDE_MODEL_REASONING` si `confidence < CLASSIFIER_ESCALATION_THRESHOLD` (default 0.80); si `confidence < CLASSIFIER_MIN_THRESHOLD` (default 0.60) incluso tras escalar, ir a `EXCEPCIÓN`.

---

## 11. AGENTE 3 — EXTRACTOR

Estrategia código primero, IA después.

**Excel:** usar pandas y openpyxl. Debe conservar correctamente hojas, filas, columnas, datos originales.

**PDF:** primero extracción de texto; si es escaneado, OCR/visión.

**Imagen:** usar visión solamente cuando sea necesario.

Extraer: descripción; cantidad; unidad; fabricante; part number; norma; especificación; observaciones. Nunca inventar campos. Si un dato no está disponible: `null`.

### REGLA CRÍTICA: CONTAR LÍNEAS (P0)

La unidad de balanceo es la línea cotizable. Una línea representa un producto/especificación distinta que requiere una decisión de cotización. Ejemplo: 100 tornillos M10 idénticos = 1 línea. 500 productos distintos = 500 líneas.

No contar: encabezados; subtotales; notas; separadores; filas vacías.

Si la confianza del conteo es baja (`line_count_confidence < LINE_COUNT_CONFIDENCE_THRESHOLD`, default 0.90): no asignar automáticamente; cambiar a `VALIDACIÓN_REQUERIDA`; solicitar revisión humana.

**El prompt completo con ejemplos ya existe en `prompts/extractor_v1.txt`.**

---

## 12. AGENTE 4 — RESOLUCIÓN DE EXPEDIENTE

Debe intentar asociar el mensaje mediante, en este orden: ID TQL; Gmail threadId; número de cotización; PO cliente; referencias Odoo; remitente; referencias del contenido; señales semánticas.

Utilizar primero reglas deterministas. Utilizar Claude solamente para casos ambiguos.

Si existen dos candidatos razonables: **NO ADIVINAR**. Enviar a `EXCEPCIÓN`.

**El prompt completo ya existe en `prompts/case_resolver_v1.txt`.**

---

## 13. AGENTE 5 — BALANCEADOR

Implementar **Least Loaded by Open Lines**: para cada cotizador elegible, carga = suma de líneas abiertas. Asignar la RFQ completa al cotizador con menor carga. Nunca dividir una RFQ.

En empate, utilizar una regla secundaria configurable: round-robin, o menor número de RFQs activas.

Registrar: cotizador; carga antes; líneas nuevas; carga después; regla utilizada; motivo; timestamp.

**Exclusiones del balanceador** (no asignar automáticamente cuando): cotizador ausente; cliente reservado; producto especializado; certificación requerida; RFQ urgente/VIP; documento ilegible; conteo de líneas de baja confianza; expediente ya pertenece a otro cotizador. Estas reglas deben ser configuración, no hardcodearse.

**Pendiente de confirmar con Jorge (ver `docs/open_questions.md`):** dónde vive el roster de cotizadores activos/ausentes (¿Odoo RRHH, tabla propia, hoja de configuración?).

---

## 14. AGENTE 6 — ORQUESTADOR

Implementar una state machine que maneje: eventos; reintentos; timeouts; errores; dead-letter; compensaciones; idempotencia; auditoría. Debe soportar redelivery de Pub/Sub. Un mismo evento nunca debe crear dos expedientes.

**La lógica de decisión completa del orquestador (5 puntos de decisión D1–D5: reintentar vs. excepción, revisión humana, pedir aclaración, a quién notificar, reasignación) ya existe en `docs/orchestrator_decision_logic.md` — usar ese archivo como fuente de verdad.**

---

## 15. AGENTE 7 — ODOO

La integración con Odoo debe seguir: **READ → DECIDE → VALIDATE → WRITE → VERIFY → AUDIT**.

Nunca: Claude → Odoo directamente.

Antes de desarrollar la escritura: identificar versión Odoo; identificar plan contratado; verificar API externa disponible; probar autenticación; validar permisos.

Modelos principales potenciales: `res.partner`, `sale.order`, `sale.order.line`, `purchase.order`, `purchase.order.line`, `product.product`, `product.template`. Validar los modelos contra la instancia real antes de asumirlos.

Implementar idempotency keys. Después de escribir: leer nuevamente; verificar resultado; guardar ID; registrar respuesta; registrar auditoría.

---

## 16. AGENTE 8 — SLA Y SEGUIMIENTO

Crear procesos automáticos que detecten: RFQ sin asignar; RFQ asignada sin actividad; cotización vencida; cotización sin respuesta; OC cliente sin abastecimiento; compra proveedor pendiente; expediente estancado.

Implementar con Scheduler + Cloud Run. **Pendiente de confirmar con Jorge:** canal de alerta (Gmail, Google Chat, u otro).

---

## 17. AGENTE 9 — TRAZABILIDAD

Debe cruzar Gmail ↔ Expediente ↔ Odoo. Detectar: actividad Odoo sin Gmail; documentos faltantes; OC no asociada; compra proveedor no asociada; expediente incompleto; acciones fuera del buzón central. Calcular `completeness_score`.

---

## 18. AGENTE 10 — AUDITORÍA Y KPI

Registrar: RFQs; líneas; asignaciones; tiempos; conversiones; backlog; errores; excepciones; reasignaciones; SLA; costo IA; versión de modelo; versión de prompt; decisiones relevantes.

KPIs mínimos: RFQs/día, RFQs/semana, RFQs/mes; líneas recibidas; líneas por cotizador; backlog; tiempo recepción→asignación; tiempo asignación→cotización; tiempo cotización→OC; tiempo OC→PO proveedor; conversión RFQ→OC; excepciones; clasificación correcta; trazabilidad completa; errores Odoo; costo IA por expediente.

---

## 19. IDEMPOTENCIA

Requisito crítico. Implementar mecanismos para evitar duplicados en: Gmail; Pub/Sub; expediente; documentos; asignación; Odoo; notificaciones.

Ejemplo de claves: `event_id`, `message_hash`, `gmail_message_id`, `idempotency_key`. Todas deben poder consultarse antes de crear registros.

---

## 20. SEGURIDAD Y PRIVACIDAD DE DATOS

Implementar: Secret Manager; variables de entorno; mínimo privilegio; IAM; separación DEV/TEST/PROD; autenticación Pub/Sub → Cloud Run; service accounts; auditoría; rotación de secretos; permisos mínimos en Odoo; permisos mínimos en Gmail.

Nunca: hardcodear credenciales; guardar API keys en Git; usar administrador general; enviar información a servicios no aprobados.

**Retención de datos:** definir cuánto tiempo se conservan correos, adjuntos y datos de cliente, alineado a la Ley Orgánica de Protección de Datos Personales (LOPDP) de Ecuador. Documentar en `docs/security.md` quién es el responsable/encargado del tratamiento de datos.

**Minimización:** no extraer ni almacenar más campos de contacto/cliente de los estrictamente necesarios.

**Acceso:** los adjuntos originales deben tener control de acceso equivalente al del buzón de Gmail.

---

## 21. HUMAN-IN-THE-LOOP (Fase 1)

**Automático:** ingesta; clasificación; extracción; creación de expediente; asociación; conteo de líneas cuando la confianza sea suficiente; asignación.

**Humano obligatorio:** cotización al cliente; envío de cotización; equivalencias técnicas críticas; partidas arancelarias de impacto; orden al proveedor; envío de PO proveedor; decisiones comerciales sensibles.

No eliminar estos controles.

**Tabla RACI — pendiente de completar con Jorge:**

| Decisión | Responsable (R) | Aprueba (A) | Consultado (C) | Informado (I) |
|---|---|---|---|---|
| Envío de cotización al cliente | Cotizador asignado | *(pendiente)* | — | Gerencia |
| Orden de compra a proveedor | *(pendiente)* | *(pendiente)* | — | — |
| Excepción sin resolver > SLA | Sistema (alerta) | *(pendiente)* | — | — |

---

## 22. API Y CONTRATOS

Todos los servicios deben tener contratos claros: Pydantic schemas; eventos versionados; request/response models; errores normalizados; correlation IDs.

Eventos: `EMAIL_RECEIVED`, `EMAIL_INGESTED`, `EMAIL_CLASSIFIED`, `DOCUMENT_EXTRACTED`, `CASE_CREATED`, `CASE_RESOLVED`, `RFQ_VALIDATED`, `RFQ_ASSIGNED`, `QUOTE_APPROVAL_REQUIRED`, `QUOTE_APPROVED`, `CUSTOMER_PO_RECEIVED`, `SUPPLIER_PO_APPROVAL_REQUIRED`, `SUPPLIER_PO_EMITTED`, `CASE_CLOSED`, `EXCEPTION_CREATED`.

**Los contratos de input/output exactos por agente ya existen en `docs/agent_contracts.md`.**

---

## 23. PRUEBAS

No declarar el sistema terminado sin pruebas. Crear pruebas unitarias, de integración y de aceptación.

Casos mínimos obligatorios (convertir cada uno en un test automatizado — ver `docs/test_strategy.md` para el detalle de implementación de cada uno):

1. RFQ Excel de 1 línea.
2. RFQ Excel de 500 líneas.
3. 100 unidades del mismo producto = 1 línea.
4. Correo duplicado.
5. Respuesta dentro de thread.
6. Nuevo thread relacionado.
7. PO cliente con referencia.
8. PO cliente sin referencia.
9. PDF ilegible.
10. Imagen.
11. Excel con múltiples hojas.
12. Cotizador ausente.
13. Empate de carga.
14. Pub/Sub redelivery.
15. Claude no disponible.
16. Gmail API temporalmente caída.
17. Odoo temporalmente caído.
18. Fallo después de escritura Odoo.
19. Expediente ambiguo.
20. Compra proveedor sin aprobación.

---

## 24. DATA FIXTURES

Crear fixtures anonimizados: RFQ simple; RFQ masiva; RFQ PDF; RFQ imagen; RFQ multitab; aclaración; cotización enviada; PO cliente; PO proveedor. No usar datos reales en Git.

---

## 25. OBSERVABILIDAD

Implementar: structured logging; correlation ID; event ID; case ID; latency; error rate; retries; Cloud Logging; métricas técnicas; métricas de negocio.

Cada log importante debe poder responder: ¿Qué ocurrió, cuándo, sobre qué expediente, por qué, quién/qué agente lo hizo y cuál fue el resultado?

**Pendiente de confirmar con Jorge:** canal de alerta técnica (Cloud Monitoring + destino: email/Slack/Chat).

---

## 26. DASHBOARD

**Bandeja general:** Nuevas RFQ, Pendientes, En cotización, En revisión, Negociación, OC recibidas, Compras proveedor, Excepciones, Cerradas.

**Por cotizador:** líneas abiertas; RFQs abiertas; backlog; tiempo promedio; vencidas; productividad.

**Gerencia:** volumen; conversión; SLA; carga; excepciones; trazabilidad.

---

## 27. INFRAESTRUCTURA COMO CÓDIGO

Preparar infraestructura para: Cloud Run; Pub/Sub; Cloud SQL; Secret Manager; IAM; Cloud Storage; Scheduler. Si se utiliza Terraform, organizar en `infra/terraform/` separando dev, test, prod.

---

## 28. VARIABLES DE CONFIGURACIÓN

```
GOOGLE_CLOUD_PROJECT
GOOGLE_REGION
GMAIL_QUOTE_MAILBOX
GMAIL_WATCH_RENEWAL_CRON
PUBSUB_TOPIC
PUBSUB_SUBSCRIPTION
DATABASE_URL
CLAUDE_API_KEY
CLAUDE_MODEL_FAST
CLAUDE_MODEL_REASONING
CLASSIFIER_ESCALATION_THRESHOLD    # default 0.80
CLASSIFIER_MIN_THRESHOLD           # default 0.60
LINE_COUNT_CONFIDENCE_THRESHOLD    # default 0.90
AI_COST_BUDGET_PER_CASE_USD        # pendiente de definir con Jorge
ODOO_BASE_URL
ODOO_DATABASE
ODOO_API_USER
ODOO_API_KEY
DATA_RETENTION_DAYS                # pendiente de definir (LOPDP)
```

No rellenar valores ficticios como si fueran reales.

---

## 29. PROMPTS DE CLAUDE

Viven en `prompts/`, versionados: `classifier_v1.txt`, `extractor_v1.txt`, `case_resolver_v1.txt`, `technical_normalizer_v1.txt` (ya existen los 4 en el repo, con contenido completo, no solo nombrados).

Cada decisión de IA debe registrar: modelo; prompt_version; timestamp; confidence; resultado.

**Gobierno de costo:** documentar en este archivo el costo estimado de IA por expediente (tokens de clasificación + extracción + casos escalados), con un presupuesto máximo (`AI_COST_BUDGET_PER_CASE_USD`) y una alerta si se excede.

---

## 30. REGLA FUNDAMENTAL DE IA

La IA nunca debe ser autoridad cuando exista una fuente determinista.

Prioridad: 1) reglas; 2) datos del sistema; 3) documentos; 4) API; 5) Claude; 6) humano para decisiones críticas.

Claude debe proporcionar: interpretación; clasificación; evidencia; confianza. Nunca debe inventar.

---

## 31. MANEJO DE ERRORES

Cada integración debe tener: retry exponencial; timeout; circuit breaker cuando corresponda; dead-letter; logging; alerta; recuperación. Nunca perder un evento. Nunca procesar silenciosamente un error.

---

## 32. FASE DE PRODUCCIÓN

No conectar escritura a Odoo Productivo inicialmente. Secuencia obligatoria:

**DEV → TEST → SANDBOX ODOO → PRUEBAS DE ACEPTACIÓN → VALIDACIÓN HUMANA → PRODUCCIÓN**

El set de 50–100 expedientes históricos debe utilizarse para pruebas antes de otorgar permisos de escritura a Odoo. Este paso requiere GATE 2 (sección 6).

---

## 33. CRITERIO DE "DONE"

No decir "implementado" solo porque se hayan creado archivos. Una funcionalidad está terminada solamente cuando: código existe; tests existen; tests pasan; documentación existe; errores están controlados; logs existen; configuración está documentada; seguridad está contemplada; idempotencia está implementada; integración está probada; existe evidencia de funcionamiento.

---

## 34. MODO DE TRABAJO

PASO 1 — Analizar toda la arquitectura.
PASO 2 — Inspeccionar el repositorio actual si existe.
PASO 3 — Identificar qué ya existe.
PASO 4 — No sobrescribir código funcional sin analizarlo.
PASO 5 — Construir el backlog.
PASO 6 — Implementar P0 usando mocks/fixtures, sin tocar sistemas reales.
PASO 7 — Ejecutar tests.
PASO 8 — Corregir errores.
PASO 9 — Documentar.
**PASO 10 — Detenerse en GATE 1: presentar el plan y `open_questions.md`, esperar aprobación de Jorge antes de conectar Gmail/Odoo reales.**
PASO 11 — Continuar con el siguiente módulo tras aprobación.

---

## 35. PRIORIDADES

**P0:** 1) No perder correos/documentos. 2) Evitar duplicados. 3) Contar correctamente líneas. 4) Crear expediente único. 5) Resolver expediente. 6) Balancear cotizadores. 7) Trazabilidad.

**P1:** 8) Odoo. 9) OC cliente. 10) Compra proveedor. 11) Aprobaciones. 12) Auditoría.

**P2:** 13) SLA. 14) Dashboard. 15) Optimización.

**P3:** 16) Búsqueda de proveedores. 17) Normalización técnica. 18) Aranceles. 19) Generación inteligente de borradores.

---

## 36. REGLA ESPECIAL PARA INFORMACIÓN FALTANTE

Cuando se necesite información no disponible: **no inventar**. Clasificarla como `REQUIRED_TO_PROCEED`, `OPTIONAL` o `CAN_USE_DEFAULT`. Antes de bloquear todo el desarrollo, implementar mocks/interfaces/configuración donde sea posible.

Ejemplo: si aún no se conoce la versión exacta de Odoo, desarrollar el connector, crear interface, crear mocks, crear tests, y dejar la implementación final parametrizada.

---

## 37. PRIMER OBJETIVO DE IMPLEMENTACIÓN

**"EMAIL → EXPEDIENTE → EXTRACCIÓN → CONTEO → BALANCEO"**

1. Llega correo. 2. Gmail genera evento. 3. Pub/Sub entrega evento. 4. Backend recupera correo. 5. Guarda correo y adjuntos. 6. Clasifica. 7. Extrae datos. 8. Cuenta líneas. 9. Crea expediente TQL. 10. Determina cotizadores elegibles. 11. Calcula carga. 12. Asigna la RFQ completa. 13. Registra auditoría. 14. Notifica. 15. Permite visualizar el expediente.

No avanzar a automatización comercial compleja hasta que este flujo sea estable. Usar datos de fixtures/mocks hasta pasar GATE 1.

---

## 38. ENTREGABLE DEL PRIMER SPRINT

1. Estructura completa del repositorio.
2. Código ejecutable.
3. Docker Compose.
4. `.env.example`.
5. Migraciones PostgreSQL.
6. Schemas.
7. Servicios iniciales.
8. Contratos de eventos.
9. Prompts versionados.
10. Pruebas.
11. Fixtures.
12. README.
13. Documentación de arquitectura.
14. Instrucciones para ejecutar localmente.
15. Instrucciones para desplegar en TEST.
16. Lista de credenciales/permisos que Jorge debe configurar.
17. Lista de elementos pendientes.
18. `docs/open_questions.md` completo.

---

## 39. FORMA DE REPORTAR PROGRESO

Después de cada bloque importante, informar: **COMPLETADO** (qué se implementó); **ARCHIVOS CREADOS/MODIFICADOS** (lista concreta); **TESTS** (qué se ejecutó y resultado); **PENDIENTES** (qué falta); **BLOQUEOS** (qué se necesita de Jorge); **SIGUIENTE PASO** (qué se va a implementar después).

No afirmar que una integración funciona si no ha sido probada realmente.

---

## 40. REGLA FINAL

No simplificar esta arquitectura convirtiéndola en "Gmail + un prompt de Claude + reglas". Esto debe implementarse como un sistema empresarial real, auditable, resiliente, orientado a eventos y preparado para producción. La IA es una capa de inteligencia dentro del sistema, no el sistema completo.

---

## 41. PREGUNTAS ABIERTAS PARA JORGE (bloqueante para Fase 1 real)

1. **Volumetría:** ¿cuántas RFQ/día y líneas/RFQ se reciben en promedio hoy?
2. **Cotizadores:** ¿cuántos cotizadores activos hay y dónde vive su disponibilidad/ausencia?
3. **Odoo:** ¿versión instalada, plan contratado, y existe ya un sandbox/staging disponible?
4. **Gmail:** ¿el buzón central ya existe, o hay que crearlo? ¿Quién administra el proyecto de Google Cloud?
5. **Retención de datos:** ¿hay una política de retención existente, o hay que definirla desde cero?
6. **Alertas:** ¿las alertas de SLA/errores deben llegar por Gmail, Google Chat, ambos, u otro canal?
7. **Presupuesto de IA:** ¿existe un tope mensual/por expediente aceptable de gasto en Claude API?
8. **Set histórico:** ¿ya existen los 50–100 expedientes históricos anonimizados para pruebas de aceptación, o hay que construirlos?

*Fin del documento. Este archivo es autosuficiente — no requiere ningún otro documento externo para ser entendido o ejecutado.*
