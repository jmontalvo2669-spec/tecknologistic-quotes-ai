# Estrategia de Pruebas

## Gap crítico — bloqueante para GATE 2

La sección 24 del prompt maestro afirma "igual que v1.0 — los 20 casos
mínimos se mantienen sin cambios, son sólidos", pero **el contenido de esos
20 casos no existe en ningún archivo de este repositorio**. No se han
inventado casos para rellenar el vacío — inventar aquí sería especialmente
peligroso porque GATE 2 exige explícitamente "los 20 casos de prueba de la
sección 24 pasando" como evidencia de aceptación (sección 6 del prompt
maestro).

**Acción requerida antes de poder cerrar este documento:** Jorge comparte el
documento v1.0 con los 20 casos, o se co-diseñan desde cero con él. Ver
`docs/open_questions.md` gap #11.

## Marco de pruebas que sí se puede derivar de las fuentes disponibles

Aunque los 20 casos concretos no están disponibles, los contratos y la
máquina de estados sí permiten definir la **estructura** de la suite de
pruebas, alineada a lo que cada documento exige explícitamente:

### 1. Pruebas de contrato por agente (`docs/agent_contracts.md`)
Para cada uno de los 10 agentes: validar que el output cumple exactamente el
esquema declarado (ni campos de más ni de menos), y que los umbrales de
`docs/data_dictionary.md` §3 se aplican correctamente:
- Clasificador: `confidence < 0.80` → escalamiento; `< 0.60` tras escalar →
  `EXCEPCIÓN`.
- Extractor: `line_count_confidence < 0.90` → `VALIDACIÓN_REQUERIDA`, nunca
  asignación automática.
- Case Resolver: dos candidatos con evidencia comparable → `EXCEPCION`,
  nunca "elegir el más probable".
- Balanceador: roster vacío o todos excluidos → `cotizador_id=null` +
  `requires_human_review=true`, nunca asignar al primero disponible.

### 2. Pruebas de máquina de estados (`docs/state_machine.md`)
- Cada una de las 25 filas de transición: dado el estado origen + evento +
  condición, verificar la transición esperada.
- Prueba negativa obligatoria (regla general #1): un evento no mapeado para
  el estado actual debe rechazarse y generar `EXCEPTION_CREATED`, nunca
  aplicar el cambio "por si acaso".
- Prueba de reingreso desde `EXCEPCIÓN` (fila 24): nunca automático, siempre
  requiere decisión humana explícita de a qué estado se reingresa.

### 3. Pruebas de decisión del Orquestador (`docs/orchestrator_decision_logic.md`)
- D1: reintento con backoff hasta `MAX_RETRIES=3`, luego `EXCEPTION_CREATED`
  con estado de origen registrado — nunca reintento indefinido ni "saltar"
  el paso fallido.
- D2: el Orquestador nunca reinterpreta `requires_human_review` — solo lo
  obedece.
- D3: recomendación de aclaración al cliente solo tras
  `CLARIFICATION_WAIT_HOURS=24` y solo si la excepción es de ambigüedad de
  contenido (no de fallo técnico) — y siempre como *recomendación*, nunca
  envío automático.
- D4: notificación según la tabla fija (supervisor, cotizador líder, equipo
  técnico, cotizador+supervisor a 2x SLA, aprobador RACI) — nunca "a
  discreción".
- D5: reasignación de RFQ siempre queda pendiente de confirmación humana,
  nunca automática.

### 4. Pruebas de idempotencia (sección 20 del prompt maestro)
- Reenvío del mismo `gmail_message_id`/`message_hash` no debe reprocesar ni
  duplicar el expediente.
- Reintento de escritura en Odoo con el mismo `idempotency_key` no debe
  crear un segundo registro.

### 5. Pruebas de agentes de contenido sensible
- `prompts/classifier_v1.txt`: correo con dos categorías con señales de
  fuerza similar → `EXCEPCION`, nunca elegir una por defecto; contenido
  legal/comercial sensible (montos, penalidades) → `requires_human_review`
  aunque la confianza de categoría sea alta.
- `prompts/extractor_v1.txt`: documento ilegible/OCR sin sentido →
  `lines: []` + `requires_human_review: true`, nunca inventar líneas.
- `prompts/technical_normalizer_v1.txt`: equivalencia de norma sin certeza
  razonable → `possible_equivalent_standards: []`, nunca forzar una
  equivalencia (regla crítica de seguridad/incumplimiento contractual).

## Pruebas de aceptación (GATE 2 — bloqueadas)

- Los 20 casos de la sección 24: **bloqueado**, ver gap arriba.
- `completeness_score` del agente de Trazabilidad sobre 50–100 expedientes
  históricos anonimizados: **bloqueado** — el set histórico no existe
  todavía (ver `docs/open_questions.md` A.8).
- Costo real de IA por expediente medido (no estimado): pendiente de tener
  volumen real de prueba.

## Datos de prueba

Regla de la sección 25: fixtures anonimizados, nunca datos reales en Git.
Los fixtures para las pruebas de contrato y de máquina de estados de arriba
sí pueden construirse ahora mismo con datos sintéticos, sin esperar
aprobación de GATE 1 (sección 6: "puedes construir DEV con mocks/fixtures
libremente sin este gate").
