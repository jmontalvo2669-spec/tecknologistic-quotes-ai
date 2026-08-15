# ADR 0002 — Case Resolver siempre verifica con Claude, incluso con un único candidato

**Estado:** aceptada
**Contexto de la decisión:** confirmación explícita de Jorge Montalvo (sesión de revisión de código posterior a PASO 6).

## Contexto

La implementación original de `services/case_resolver/service.py` tenía
una rama que resolvía automáticamente, sin llamar a Claude, cuando la
lista de candidatos tenía exactamente un elemento y ninguna regla
determinista (hilo ya vinculado, número de expediente mencionado
explícitamente) había resuelto antes. El razonamiento era: si solo hay un
candidato, no hay ambigüedad entre dos que resolver.

Ese razonamiento no es del todo correcto: que solo exista un candidato en
la lista no significa que el mensaje realmente pertenezca a ese
expediente — solo significa que las reglas de búsqueda de candidatos no
encontraron un segundo. Podría ser un mensaje que no pertenece a ningún
expediente existente, o pertenece a uno que las reglas de búsqueda no
trajeron como candidato.

## Decisión

Se elimina la rama de "único candidato = automático". Ahora, **cualquier**
candidato — uno o más — sin evidencia determinista pasa por
`prompts/case_resolver_v1.txt` antes de resolverse. Solo las dos reglas
genuinamente deterministas (hilo de Gmail ya vinculado a un expediente;
número de expediente TQL mencionado explícitamente en el texto y que
coincide con un candidato) siguen resolviendo sin Claude.

Con el volumen actual confirmado (~3 RFQ/día, ~20/semana —
`docs/open_questions.md` A.1), el costo adicional de esta verificación es
mínimo. Jorge prefiere esta capa de seguridad adicional sobre el ahorro de
una llamada a Claude por caso.

## Consecuencias

- `services/case_resolver/service.py::resolve()` ya no acepta
  `client=None` cuando hay candidatos sin evidencia determinista (antes
  solo lo exigía con 2+ candidatos) — ahora lo exige con 1 o más.
- El costo de IA por expediente sube ligeramente (una llamada más de
  Case Resolver en el caso, antes evitable, de un único candidato). Se
  mide junto con el resto del costo real en GATE 2
  (`AI_COST_BUDGET_PER_CASE_USD`, todavía sin techo fijado —
  `docs/open_questions.md` A.7).
- Si el volumen de RFQ crece significativamente y este costo deja de ser
  marginal, esta decisión debe revisarse — está documentada aquí
  precisamente para que sea fácil de reabrir con el contexto completo.
