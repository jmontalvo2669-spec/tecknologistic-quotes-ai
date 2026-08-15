# Seguridad y Privacidad de Datos

**Estado:** varias secciones marcadas `[PENDIENTE]` porque dependen del
documento v1.0 (Secret Manager, IAM, separación DEV/TEST/PROD, service
accounts, rotación de secretos) que no está en este repositorio, o de
decisiones de negocio que Jorge aún no ha tomado. No se rellenan con
supuestos.

## 1. Controles heredados de v1.0 (mencionados pero sin detalle disponible)

`[PENDIENTE — falta v1.0]` Secret Manager, IAM, separación de entornos
DEV/TEST/PROD, service accounts dedicadas por entorno, rotación de secretos.
La sección 21 del prompt maestro confirma que estos controles existen en la
arquitectura base, pero su especificación concreta no llegó a este repo.

## 2. Retención de datos (LOPDP Ecuador) — nuevo en v1.1

- **Pregunta bloqueante:** ¿cuánto tiempo se conservan correos, adjuntos y
  datos de cliente? Debe alinearse a la Ley Orgánica de Protección de Datos
  Personales (LOPDP) de Ecuador. Ver `docs/open_questions.md` A.5.
- **Responsable/encargado del tratamiento de datos:** `[PENDIENTE]` — debe
  documentarse aquí explícitamente una vez Jorge lo confirme.
- Variable de configuración: `DATA_RETENTION_DAYS` (sin valor hasta
  confirmación) — ver `.env.example`.

## 3. Minimización de datos

Regla obligatoria (sección 21): **no extraer ni almacenar más campos de
contacto/cliente que los estrictamente necesarios** para el workflow. Esto
aplica directamente a los campos `[PENDIENTE]` de `docs/data_dictionary.md`
§1 (`cliente`, `contacto`) — cuando se definan, deben limitarse a lo que el
Balanceador, el Case Resolver y el Odoo Connector realmente consumen según
sus contratos (`docs/agent_contracts.md`), no a un perfil de cliente
completo.

## 4. Control de acceso a adjuntos

Regla obligatoria: los adjuntos originales deben tener **control de acceso
equivalente al del buzón de Gmail** — nunca más permisivo. Esto aplica al
campo `storage_path` del esquema de `attachments` en `EMAIL_INGESTED`
(`docs/data_dictionary.md` §2.1).

## 5. Reglas de arquitectura de seguridad no negociables (heredadas de la sección 3 del prompt maestro)

- Regla 19: no conectar credenciales ni permisos de escritura reales (Gmail,
  Odoo) sin aprobación explícita de Jorge — GATE 1.
- Regla 21: todo dato personal/comercial de cliente tiene regla de retención
  documentada antes de almacenarse de forma persistente (ver §2 arriba).

## 6. Fixtures y datos de prueba

Regla de la sección 25 del prompt maestro: **datos anonimizados, nunca datos
reales en Git.** Cualquier fixture usado para pruebas en `tests/` (a crear en
fase de implementación) debe anonimizarse antes de commitear.

## 7. Gobernanza de modelos de IA y exposición de datos a Claude API

- El uso de Claude API debe declarar explícitamente qué modelo se usa y por
  qué (regla 22, sección 3), priorizando el modelo más económico que
  resuelva el caso.
- Ningún prompt (`prompts/*.txt`) debe recibir más datos de cliente que los
  estrictamente necesarios para su tarea — verificado contra los contratos
  de `docs/agent_contracts.md` (p. ej. el Clasificador solo recibe
  `subject`, `body_text`, `from`, nombres/tipos de adjuntos y
  `thread_context` resumido — nunca contenido completo de adjuntos).

## 8. Bloqueos pendientes antes de GATE 1

Ninguno de los puntos de esta sección impide completar FASE 0 (documentación
únicamente), pero **sí bloquean** cualquier despliegue con credenciales
reales:

- [ ] Confirmar política de retención (LOPDP) y responsable de tratamiento.
- [ ] Obtener o reconstruir el detalle de IAM/Secret Manager/rotación de
      secretos del documento v1.0.
- [ ] Confirmar separación de entornos (proyectos GCP distintos por
      DEV/TEST/PROD) — `[PENDIENTE]`.
