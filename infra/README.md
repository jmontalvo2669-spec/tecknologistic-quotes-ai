# Infraestructura como código

Vacío por diseño hasta que exista un proyecto de Google Cloud real (ver
`docs/open_questions.md` E.12). Cuando se defina, aquí vive Terraform
(`terraform/dev`, `terraform/test`, `terraform/prod`) para Cloud Run,
Pub/Sub, Cloud SQL, Secret Manager, IAM, Cloud Storage y Cloud Scheduler
(sección 27 de `docs/architecture.md`), incluyendo el Cloud Scheduler de
renovación del `watch()` de Gmail (sección 4).

No conectar credenciales reales aquí sin aprobación explícita de Jorge
(GATE 1).
