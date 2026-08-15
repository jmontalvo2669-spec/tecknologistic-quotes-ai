# Estrategia de Pruebas — Sistema IA de Cotizaciones Tecknologistic

Este documento convierte los 20 casos mínimos exigidos en la arquitectura (sección 23) en pruebas concretas, con datos de entrada, comportamiento esperado y el agente/módulo responsable. Cada uno debe existir como test automatizado en `tests/` antes de considerar el sistema listo para GATE 2.

## Convenciones
- Todos los tests usan fixtures anonimizados de `tests/fixtures/`, nunca datos reales.
- Cada test verifica tanto el resultado (output correcto) como el efecto secundario (evento publicado, estado de expediente, registro de auditoría).

---

### 1. RFQ Excel de 1 línea
**Entrada:** fixture `rfq_simple_1_linea.xlsx` con un solo producto.
**Esperado:** Extractor produce `lines` con 1 elemento, `line_count_confidence >= 0.90`, expediente pasa a `LISTA_PARA_ASIGNAR` sin pasar por `VALIDACIÓN_REQUERIDA`.

### 2. RFQ Excel de 500 líneas
**Entrada:** fixture `rfq_masiva_500_lineas.xlsx`.
**Esperado:** las 500 líneas se extraen correctamente, sin timeout, sin truncar datos; el balanceador recibe `line_count=500` y lo asigna a un solo cotizador (nunca dividir).

### 3. 100 unidades del mismo producto = 1 línea
**Entrada:** fixture con una fila "100 tornillos M10 idénticos".
**Esperado:** `lines` contiene exactamente 1 elemento con `quantity=100`, no 100 elementos.

### 4. Correo duplicado
**Entrada:** el mismo `gmail_message_id` y `message_hash` enviado dos veces (simulando redelivery o reenvío accidental).
**Esperado:** el segundo evento se descarta en Gmail Ingest; no se crea un segundo expediente ni se reprocesa.

### 5. Respuesta dentro de thread
**Entrada:** mensaje con `in_reply_to` apuntando a un mensaje ya ingerido del mismo `gmail_thread_id`.
**Esperado:** Case Resolver asocia correctamente al expediente existente usando `threadId`, sin pasar por `case_resolver_v1` (regla determinista es suficiente).

### 6. Nuevo thread relacionado
**Entrada:** un correo en un thread nuevo, pero que menciona un número de expediente/cotización existente en el cuerpo.
**Esperado:** las reglas deterministas fallan (thread nuevo), `case_resolver_v1` se invoca y asocia correctamente usando la evidencia textual del número de expediente.

### 7. PO cliente con referencia
**Entrada:** correo con adjunto de orden de compra que referencia explícitamente el número de cotización enviado.
**Esperado:** clasificación `PO_CLIENTE`, asociación automática al expediente correcto, transición a `OC_CLIENTE_RECIBIDA`.

### 8. PO cliente sin referencia
**Entrada:** correo con adjunto de orden de compra sin ningún número de cotización ni referencia textual.
**Esperado:** Case Resolver no encuentra evidencia suficiente → `EXCEPCIÓN`, `requires_human_review=true`. Nunca asociar por defecto al expediente más reciente del mismo cliente.

### 9. PDF ilegible
**Entrada:** fixture de PDF escaneado de mala calidad donde el OCR devuelve texto sin sentido o vacío.
**Esperado:** Extractor devuelve `lines=[]`, `requires_human_review=true`; expediente pasa a `EXCEPCIÓN`, nunca se inventa una línea.

### 10. Imagen
**Entrada:** fixture de imagen de una RFQ escrita a mano o fotografiada.
**Esperado:** el extractor usa visión, produce líneas con los campos disponibles y `null` en los no legibles; nunca completa campos no visibles con suposiciones.

### 11. Excel con múltiples hojas
**Entrada:** fixture `rfq_multitab.xlsx` con 3 hojas, solo una de ellas con datos de producto (las otras son notas/portada).
**Esperado:** el extractor identifica la hoja relevante y no cuenta las hojas de notas como líneas adicionales.

### 12. Cotizador ausente
**Entrada:** roster donde el único cotizador con especialización en el producto está marcado como `activo=false`.
**Esperado:** Balanceador no asigna, `cotizador_id=null`, `requires_human_review=true`, expediente permanece en `LISTA_PARA_ASIGNAR` (no pasa a `EXCEPCIÓN`, ya que es una condición esperada, no un error).

### 13. Empate de carga
**Entrada:** dos cotizadores elegibles con exactamente la misma carga de líneas abiertas.
**Esperado:** se aplica la regla secundaria configurada (round-robin o menor número de RFQs activas), se registra `regla_utilizada` en el evento `RFQ_ASSIGNED`.

### 14. Pub/Sub redelivery
**Entrada:** el mismo evento de Pub/Sub entregado dos veces (comportamiento normal de Pub/Sub "at-least-once").
**Esperado:** el orquestador detecta el `event_id` ya procesado y no repite la transición de estado ni genera un segundo efecto secundario (ej. no envía la misma notificación dos veces).

### 15. Claude no disponible
**Entrada:** simular timeout o error 5xx de la API de Claude durante clasificación o extracción.
**Esperado:** el orquestador aplica la regla D1 (reintento con backoff exponencial, máximo `MAX_RETRIES`); si se agotan los reintentos, pasa a `EXCEPCIÓN` con el estado de origen registrado para reingreso posterior.

### 16. Gmail API temporalmente caída
**Entrada:** simular error de conexión al intentar recuperar un mensaje o adjunto de Gmail.
**Esperado:** reintento con backoff; el evento no se pierde (permanece en cola/dead-letter hasta poder procesarse); se genera alerta técnica si se agotan los reintentos.

### 17. Odoo temporalmente caído
**Entrada:** simular error de conexión al intentar leer o escribir en Odoo.
**Esperado:** Odoo Connector no marca la operación como exitosa; reintento con backoff; si falla persistentemente, `EXCEPTION_CREATED` con detalle técnico, nunca se asume que la escritura sí ocurrió.

### 18. Fallo después de escritura Odoo
**Entrada:** simular que la escritura en Odoo se ejecuta pero la verificación posterior (paso VERIFY de READ→DECIDE→VALIDATE→WRITE→VERIFY→AUDIT) falla o no responde.
**Esperado:** el sistema no asume éxito silencioso; genera alerta específica de "escritura no verificada" para revisión manual — este es el caso más peligroso de duplicar compras/cotizaciones y debe tener su propio tipo de alerta, no genérico.

### 19. Expediente ambiguo
**Entrada:** mensaje que podría pertenecer a dos expedientes distintos con evidencia textual comparable (ver ejemplo 3 de `prompts/case_resolver_v1.txt`).
**Esperado:** `resolution="EXCEPCION"`, ambos candidatos quedan registrados en `discarded_candidates` con su razón, ninguno se elige automáticamente.

### 20. Compra proveedor sin aprobación
**Entrada:** intento de generar evento `SUPPLIER_PO_EMITTED` sin que exista un registro previo de aprobación humana para ese expediente.
**Esperado:** el Odoo Connector rechaza la operación; el orquestador no permite la transición 22 de `state_machine.md` (`COMPRA_PROVEEDOR_EN_REVISIÓN → COMPRA_PROVEEDOR_EMITIDA`) sin la aprobación registrada.

---

## Pruebas adicionales de infraestructura (no listadas en la sección 23 original, pero necesarias)

### 21. Renovación de Gmail watch
**Entrada:** simular que pasan 7 días sin renovación del `watch()`.
**Esperado:** Cloud Scheduler dispara la renovación antes de la expiración; si la renovación falla, se genera alerta técnica inmediata (este es el fallo silencioso más común en integraciones Gmail, ver sección 4 de `docs/architecture.md`).

### 22. Umbral de confianza en el límite exacto
**Entrada:** clasificación o extracción con `confidence` exactamente igual al umbral configurado (ej. 0.80 cuando `CLASSIFIER_ESCALATION_THRESHOLD=0.80`).
**Esperado:** el comportamiento en el límite debe estar definido explícitamente en el código (ej. `>=` vs `>`) y probado — evitar ambigüedad de "qué pasa exactamente en el borde".

---

## Cobertura mínima esperada por fase

- **FASE 0 (mocks):** los 22 casos anteriores deben poder ejecutarse contra fixtures y mocks, sin ningún sistema real conectado.
- **GATE 2 (antes de producción):** los 22 casos deben pasar contra el sandbox de Odoo y un buzón Gmail de prueba real, no solo mocks.
