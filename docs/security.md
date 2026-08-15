# Seguridad y Privacidad de Datos

**Estado:** varias secciones marcadas `[PENDIENTE]` porque dependen de
decisiones de negocio/infraestructura que Jorge aún no ha tomado (valores
concretos de IAM, GCP y retención). No se rellenan con supuestos.

## 1. Controles de seguridad de infraestructura (sección 20 de `docs/architecture.md`)

Requisitos ya definidos explícitamente: Secret Manager, variables de
entorno, mínimo privilegio, IAM, separación DEV/TEST/PROD, autenticación
Pub/Sub → Cloud Run, service accounts, auditoría, rotación de secretos,
permisos mínimos en Odoo y en Gmail. Prohibido explícitamente: hardcodear
credenciales, guardar API keys en Git, usar administrador general, enviar
información a servicios no aprobados.

`[PENDIENTE]` Lo que falta no es la lista de controles (ya está completa en
`docs/architecture.md` §20), sino su **especificación concreta**: nombres
reales de proyectos GCP por entorno, roles IAM específicos por service
account, y cadencia de rotación de secretos. Eso depende de que exista un
proyecto GCP real (ver `docs/open_questions.md` A.4).

## 2. Retención de datos (LOPDP Ecuador)

- **Pregunta bloqueante:** ¿cuánto tiempo se conservan correos, adjuntos y
  datos de cliente? Debe alinearse a la Ley Orgánica de Protección de Datos
  Personales (LOPDP) de Ecuador. Ver `docs/open_questions.md` A.5.
- **Responsable/encargado del tratamiento de datos:** `[PENDIENTE]` — debe
  documentarse aquí explícitamente una vez Jorge lo confirme.
- Variable de configuración: `DATA_RETENTION_DAYS` (sin valor hasta
  confirmación) — ver `.env.example`.

## 3. Minimización de datos

Regla obligatoria (sección 20 de `docs/architecture.md`): **no extraer ni almacenar más campos de
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

## 5. Reglas de arquitectura de seguridad no negociables (heredadas de la sección 3 de `docs/architecture.md`)

- Regla 19: no conectar credenciales ni permisos de escritura reales (Gmail,
  Odoo) sin aprobación explícita de Jorge — GATE 1.
- Regla 21: todo dato personal/comercial de cliente tiene regla de retención
  documentada antes de almacenarse de forma persistente (ver §2 arriba).

## 6. Fixtures y datos de prueba

Regla de la sección 24 de `docs/architecture.md`: **datos anonimizados, nunca datos
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
- [ ] Definir valores concretos de IAM/Secret Manager/rotación de secretos
      (roles, nombres de service accounts, cadencia) sobre el proyecto GCP
      real, una vez exista (ver `docs/open_questions.md` A.4).
- [ ] Confirmar separación de entornos (proyectos GCP distintos por
      DEV/TEST/PROD) — `[PENDIENTE]`.
