# Plan de Implementación

## 1. Modo de trabajo aplicado (sección 34 de `docs/architecture.md`)

| Paso | Descripción | Estado |
|---|---|---|
| 1 | Analizar toda la arquitectura disponible | ✅ Hecho — ver `docs/architecture.md` |
| 2 | Inspeccionar el repositorio actual | ✅ Hecho — el repo solo contenía el prompt maestro, 3 docs de arquitectura y 4 prompts de agentes, sin ninguna estructura de `docs/`/`prompts/` previa |
| 3 | Identificar qué ya existe | ✅ Existían: prompt maestro v1.1, contratos de agentes, máquina de estados, lógica de decisión del orquestador, y los prompts `classifier_v1`, `extractor_v1`, `case_resolver_v1`, `technical_normalizer_v1`. No existía código, ni `docs/` como carpeta, ni `.env.example` |
| 4 | No sobrescribir código funcional sin analizarlo | ✅ No había código — solo se reorganizaron documentos existentes (`git mv`), sin editar su contenido original |
| 5 | Construir el backlog | ✅ Ver sección 3 abajo |
| 6 | Implementar P0 con mocks/fixtures | ✅ Hecho — ver sección 6 abajo |
| 7 | Ejecutar tests | ✅ 68 passed, 1 skipped (`pytest -v`) |
| 8 | Corregir errores | ✅ Sin fallas pendientes al cierre de esta sesión |
| 9 | Documentar | ✅ Este archivo + docstrings de cada módulo citando su sección fuente |
| 10 | **Detenerse en GATE 1** | 🛑 **Sigue vigente** — nada de lo construido en PASO 6 conecta Gmail/Odoo/Claude reales |
| 11 | Continuar tras aprobación | ⏸️ Pendiente de luz verde de Jorge para conectar credenciales reales |

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
- Se creó `.env.example` con las variables de la sección 28 de
  `docs/architecture.md`, sin valores ficticios.
- **No se tocó ningún sistema real** (Gmail, Odoo, Claude API en volumen).
  No se escribió código de servicios todavía.

## 3. Backlog técnico por prioridad (sección 35 de `docs/architecture.md`)

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
12. Dashboard de KPIs — vistas ya definidas en la sección 26 de
    `docs/architecture.md` (bandeja general, por cotizador, gerencia); se
    implementa cuando haya datos reales de volumen (`docs/open_questions.md`
    A.1).

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

**Definición (sección 6 de `docs/architecture.md`):** al terminar FASE 0, detenerse
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

## 6. PASO 6 — P0 implementado con mocks/fixtures

Todo lo de esta sección corre localmente con `pytest` (68 passed, 1
skipped), sin ninguna credencial ni conexión real. El entorno usado fue un
venv (`.venv/`, no versionado) con las dependencias de `requirements.txt`.

### 6.1 Estructura creada

```
services/
  gmail_ingest/service.py       # Agente 1
  classifier/service.py         # Agente 2 (+ escalamiento fast->reasoning)
  extractor/excel.py            # código primero (pandas/openpyxl)
  extractor/claude_fallback.py  # respaldo IA (prompts/extractor_v1.txt)
  extractor/service.py          # orquesta código vs. respaldo + umbral
  case_resolver/service.py      # Agente 4 (determinista + respaldo IA)
  workload_balancer/service.py  # Agente 5 (Least Loaded by Open Lines)
  workflow/state_machine.py     # TRANSITIONS (25 filas literales) + apply
  workflow/orchestrator.py      # Agente 6 — camino feliz P0 end-to-end
  odoo_connector/service.py     # Agente 7 (READ→DECIDE→VALIDATE→WRITE→VERIFY→AUDIT)
  traceability/service.py       # Agente 9 (completeness_score + gaps)
  shared/                       # settings, claude_client (fake), repos en
                                 # memoria, blob store en memoria, prompts.py
schemas/         # Pydantic — un archivo por evento/contrato de agente_contracts.md
gmail/           # client interface + FakeGmailClient + modelos crudos
odoo/            # client interface + FakeOdooClient
migrations/      # Alembic — esquema inicial (expedientes, ingested_messages,
                 # state_transitions), probado contra SQLite en CI
tests/unit/      # una suite por agente
tests/integration/  # migraciones + pipeline P0 completo
tests/fixtures/  # xlsx generados por scripts/generate_fixtures.py
```

### 6.2 Qué cubre y qué no

- **Cubre el primer objetivo de implementación** (sección 37 de
  `docs/architecture.md`): `services/workflow/orchestrator.py::run_p0_happy_path`
  encadena Gmail Ingest → Clasificador → Extractor → Case Resolver
  (determinista) → Balanceador, aplicando `docs/state_machine.md` fila por
  fila y registrando cada transición con `correlation_id`. Probado en
  `tests/integration/test_p0_pipeline.py`.
- **Traduce literalmente `docs/state_machine.md`**: las 25 filas están en
  `TRANSITIONS`, con pruebas que verifican cada una es alcanzable y que un
  evento no mapeado se rechaza (nunca se aplica "por si acaso").
- **Nunca llama a Gmail, Odoo ni Claude reales.** `FakeGmailClient`,
  `FakeOdooClient` y `FakeClaudeClient` son los únicos clientes usados;
  `UnconfiguredClaudeClient` falla ruidosamente si algo intenta usar Claude
  sin que se le inyecte explícitamente un cliente.
- **No incluye todavía** (deliberadamente fuera de alcance de PASO 6):
  - Capa HTTP (FastAPI) y despliegue en Cloud Run — no hay endpoint que
    reciba el push real de Pub/Sub.
  - Conexión real a Postgres (los servicios usan repositorios en memoria;
    `services/shared/db_models.py` + Alembic solo se probaron contra SQLite).
  - `services/notifications/` (canal Gmail para alertas SLA) y
    `services/sla/` en sí — quedan para P2, aunque el canal ya se confirmó
    (`docs/open_questions.md` A.6).
  - `services/technical_normalizer/` (P3).
  - Docker/Terraform reales (`docker-compose.yml` solo trae Postgres local,
    sin conectar la app todavía).
  - El roster real de cotizadores contra Odoo 18 — `BalancerInput.roster`
    se recibe ya armado; falta el código que lo lea de Odoo RRHH cuando
    exista el sandbox (`docs/open_questions.md` A.2/A.3).
  - **Pendiente explícito — camino de "correo de seguimiento con
    candidatos ambiguos":** `run_p0_happy_path` (en
    `services/workflow/orchestrator.py`) solo cubre una RFQ_NUEVA de un
    thread nuevo, sin candidatos — nunca invoca de verdad
    `services/case_resolver/service.py::resolve()`, asume directamente
    que es un expediente recién creado (regla determinista). Falta
    construir el camino del Orquestador para un mensaje entrante que
    referencia un thread/tema existente con **dos o más expedientes
    candidatos**: buscar candidatos (por remitente, tema, referencias),
    invocar `resolve()` (que ahora, tras
    `docs/decisions/0002-case-resolver-siempre-verifica-con-claude.md`,
    siempre pasa por Claude aunque haya un único candidato), y aplicar las
    filas 7/8 de `docs/state_machine.md` según el resultado
    (`case_unique_confirmed` → `LISTA_PARA_ASIGNAR`, `case_ambiguous` →
    `EXCEPCIÓN`). No se construye ahora — queda para cuando se implemente
    ese flujo explícitamente.
- **Discrepancias encontradas durante la implementación — corregidas
  (documentadas, no inventadas):**
  - Las filas 13, 16 y 18 de `docs/state_machine.md` no traen un nombre de
    evento fijo (usan una descripción entre paréntesis). El código usa los
    identificadores `COTIZADOR_INICIA_TRABAJO` y `QUOTE_REJECTED` (fila 18
    reutiliza `QUOTE_APPROVED`) — siguen siendo nombres de trabajo, no
    confirmados por ninguna fuente. Ahora está anotado explícitamente en
    `docs/state_machine.md` (regla general #6) y rastreado como pendiente
    en `docs/open_questions.md` E.18, además del comentario ya existente en
    `services/workflow/state_machine.py`.
  - `docs/test_strategy.md` citaba "ejemplo 3 de `prompts/case_resolver_v1.txt`"
    para el caso 19 (expediente ambiguo), pero ese archivo solo tiene un
    ejemplo (el de bridas), que además no es ambiguo. Se corrigió la cita:
    ahora apunta a la sección "REGLA CRÍTICA — NO ADIVINAR" de ese mismo
    prompt y aclara que el Ejemplo 3 ambiguo real vive en
    `prompts/classifier_v1.txt` (ambigüedad de clasificación, no de
    expediente). El test del caso 19 en `tests/unit/test_case_resolver.py`
    sigue usando un escenario sintético propio, que no depende de esta cita.

### 6.3 Cómo correrlo

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/generate_fixtures.py   # solo si tests/fixtures/ no existe
pytest -v
```

## 7. GATE 2 (futuro, no aplica todavía)

Antes de pasar de TEST/sandbox a producción: los 20 casos de prueba de la
sección 23 de `docs/architecture.md` pasando (**bloqueado**, ver
`docs/test_strategy.md`), el
`completeness_score` sobre 50-100 expedientes históricos (**bloqueado**,
set histórico no existe), y costo real de IA por expediente medido (no
estimado).
