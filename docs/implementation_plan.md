# Plan de Implementación

## 1. Modo de trabajo aplicado (sección 35 del prompt maestro)

| Paso | Descripción | Estado |
|---|---|---|
| 1 | Analizar toda la arquitectura disponible | ✅ Hecho — ver `docs/architecture.md` |
| 2 | Inspeccionar el repositorio actual | ✅ Hecho — el repo solo contenía el prompt maestro, 3 docs de arquitectura y 4 prompts de agentes, sin ninguna estructura de `docs/`/`prompts/` previa |
| 3 | Identificar qué ya existe | ✅ Existían: prompt maestro v1.1, contratos de agentes, máquina de estados, lógica de decisión del orquestador, y los prompts `classifier_v1`, `extractor_v1`, `case_resolver_v1`, `technical_normalizer_v1`. No existía código, ni `docs/` como carpeta, ni `.env.example` |
| 4 | No sobrescribir código funcional sin analizarlo | ✅ No había código — solo se reorganizaron documentos existentes (`git mv`), sin editar su contenido original |
| 5 | Construir el backlog | ✅ Ver sección 3 abajo |
| 6 | Implementar P0 con mocks/fixtures | ⏸️ No iniciado — corresponde a la fase posterior a GATE 1 |
| 7-9 | Tests, corrección, documentación | ⏸️ No iniciado |
| 10 | **Detenerse en GATE 1** | 🛑 **Este es el punto actual** |
| 11 | Continuar tras aprobación | ⏸️ Pendiente de luz verde de Jorge |

## 2. Qué se hizo en esta sesión (FASE 0, discovery)

- Se leyeron las 5 fuentes de verdad disponibles: prompt maestro v1.1,
  `agent_contracts.md`, `state_machine.md`, `orchestrator_decision_logic.md`,
  y los 4 archivos de `prompts/`.
- Se reorganizó el repositorio a la estructura objetivo de la sección 5:
  `docs/` (con `decisions/` vacío) y `prompts/`. Los archivos existentes se
  movieron con `git mv` sin alterar su contenido.
- Se produjeron los 7 entregables de FASE 0 exigidos por la sección 6:
  `docs/architecture.md`, `docs/data_dictionary.md`,
  `docs/event_contracts.md`, `docs/security.md`, `docs/test_strategy.md`,
  `docs/implementation_plan.md` (este archivo), `docs/open_questions.md`.
- Se creó `.env.example` con las variables de la sección 29, sin valores
  ficticios.
- **No se tocó ningún sistema real** (Gmail, Odoo, Claude API en volumen).
  No se escribió código de servicios todavía.

## 3. Backlog técnico por prioridad (sección 36 del prompt maestro)

**P0 — no perder correos, evitar duplicados, contar líneas, expediente
único, resolución, balanceo, trazabilidad:**
1. `services/gmail_ingest/` — idempotencia por `message_hash`, manejo de
   `EMAIL_RECEIVED` → `EMAIL_INGESTED`.
2. Cloud Scheduler de renovación del `watch()` de Gmail (expira cada 7 días)
   + alerta si falla — **P0 explícito**, no infraestructura secundaria.
3. `services/classifier/` — wrapper de `prompts/classifier_v1.txt` +
   umbrales configurables (`CLASSIFIER_ESCALATION_THRESHOLD`,
   `CLASSIFIER_MIN_THRESHOLD`).
4. `services/extractor/` — extracción por código primero (pandas/openpyxl,
   texto de PDF), fallback a `prompts/extractor_v1.txt` solo si el código no
   resuelve; mismo esquema de salida en ambos caminos.
5. `services/case_resolver/` — reglas deterministas primero, fallback a
   `prompts/case_resolver_v1.txt`.
6. `services/workflow/state_machine.py` — traducción literal de la tabla de
   `docs/state_machine.md` a la constante `TRANSITIONS`.
7. `services/balancer/` — Least Loaded by Open Lines; roster **bloqueado**
   hasta resolver su fuente (`docs/open_questions.md` A.2).
8. `services/traceability/` — `completeness_score` + `gaps[]`.

**P1 — Odoo, OC, compra proveedor, aprobaciones, auditoría:**
9. `odoo/` — Odoo Connector con READ→DECIDE→VALIDATE→WRITE→VERIFY→AUDIT;
   validar modelos reales (`res.partner`, `sale.order`, etc.) contra la
   instancia real antes de asumir nombres — **bloqueado por GATE 1 y por
   `docs/open_questions.md` A.3** (versión/sandbox de Odoo).
10. Flujo de aprobación humana con RACI — **bloqueado** hasta completar la
    tabla RACI (`docs/open_questions.md` B).

**P2 — SLA, dashboard, optimización:**
11. `services/sla/` — canal de escalamiento **bloqueado**
    (`docs/open_questions.md` A.6).
12. Dashboard de KPIs (sección 27) — sin detalle adicional disponible más
    allá de "igual que v1.0"; se diseñará cuando haya datos reales de
    volumen (`docs/open_questions.md` A.1).

**P3 — búsqueda de proveedores, normalización técnica, aranceles, borradores:**
13. `services/technical_normalizer/` — wrapper de
    `prompts/technical_normalizer_v1.txt`, nunca fuerza equivalencias sin
    certeza.

## 4. Matriz de dependencias (alto nivel)

```
Gmail Ingest ──▶ Clasificador ──▶ Extractor ──▶ Case Resolver ──▶ Balanceador ──▶ (humano: cotización)
                                                                        │
                                                                        ▼
                                                                  Orquestador (todos los eventos, D1-D5)
                                                                        │
                                                                        ▼
                                                          Odoo Connector (solo tras aprobación humana)
                                                                        │
                                                                        ▼
                                                              SLA + Trazabilidad + Auditoría/KPI (transversales)
```

Ningún agente aguas abajo puede empezar a construirse con datos reales antes
de que el agente aguas arriba tenga su contrato validado con fixtures —
pero todos pueden construirse en paralelo con mocks (sección 6, "puedes
construir DEV con mocks/fixtures libremente sin este gate").

## 5. GATE 1 — punto de control actual

**Definición (sección 6 del prompt maestro):** al terminar FASE 0, detenerse
y presentar el plan y `docs/open_questions.md` antes de escribir código que
dependa de credenciales reales. Se puede construir DEV con mocks/fixtures
libremente sin este gate. Requiere aprobación explícita de Jorge: conectar
Gmail real, conectar Odoo real (incluso en sandbox), o gastar presupuesto
real de Claude API en volumen.

**Estado: 🛑 detenido en GATE 1**, tal como pidió Jorge explícitamente en
esta sesión. No se ha conectado ninguna credencial real. El siguiente paso
(PASO 6: implementar P0 con mocks/fixtures) requiere su confirmación para
continuar — no porque PASO 6 en sí toque sistemas reales, sino porque así lo
pidió explícitamente para esta sesión.

## 6. GATE 2 (futuro, no aplica todavía)

Antes de pasar de TEST/sandbox a producción: los 20 casos de prueba de la
sección 24 pasando (**bloqueado**, ver `docs/test_strategy.md`), el
`completeness_score` sobre 50-100 expedientes históricos (**bloqueado**,
set histórico no existe), y costo real de IA por expediente medido (no
estimado).
