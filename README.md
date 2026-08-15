# Tecknologistic — Sistema IA de Cotizaciones

Convierte el buzón central de Cotizaciones en la puerta de entrada y
expediente documental de todo el proceso: Solicitud del cliente →
Cotización → Orden de compra del cliente → Compra al proveedor → Cierre.

**Estado actual:** FASE 0 (discovery) completa, PASO 6 (P0 con
mocks/fixtures) implementado. **GATE 1 vigente** — no hay ninguna
credencial real de Gmail, Odoo ni Claude API conectada todavía.

## Documentación

Empieza por `docs/architecture.md` (fuente de verdad autocontenida) y
`docs/open_questions.md` (qué sigue pendiente de negocio). El resto de
`docs/` detalla el modelo de datos, los contratos de eventos, seguridad,
estrategia de pruebas y el plan de implementación.

## Correr las pruebas

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/generate_fixtures.py   # genera tests/fixtures/*.xlsx si no existen
pytest -v
```

Todo el código bajo `services/`, `gmail/` y `odoo/` corre con clientes
falsos (`FakeGmailClient`, `FakeOdooClient`, `FakeClaudeClient`) — ninguna
prueba ni script de este repositorio conecta un sistema real.

## Estructura

Ver sección 5 de `docs/architecture.md` para la estructura completa del
repositorio, y sección 6 de `docs/implementation_plan.md` para el detalle
de qué está implementado y qué falta.
