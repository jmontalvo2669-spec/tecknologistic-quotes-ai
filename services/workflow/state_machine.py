"""Traducción literal de docs/state_machine.md a una tabla ejecutable.

Cada entrada de TRANSITIONS corresponde exactamente a una fila de esa tabla
(mismo número de fila, mismo origen/destino/evento/actor). Si el código
permite algo que docs/state_machine.md no lista, es un bug, no una
funcionalidad (regla general #5 de ese documento).

`condition_tag` es la representación en código de la columna "Condición":
como esa columna describe un predicado de negocio ya evaluado por el agente
upstream (p. ej. `requires_human_review`), el llamador debe pasar el tag que
corresponde a la condición que ya verificó — la máquina de estados no
reevalúa esos flags, solo obedece (docs/orchestrator_decision_logic.md D2:
"el Orquestador NO decide si el contenido está bien o mal").
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class EstadoExpediente(StrEnum):
    RECIBIDA = "RECIBIDA"
    CLASIFICADA = "CLASIFICADA"
    EXTRAIDA = "EXTRAÍDA"
    VALIDACION_REQUERIDA = "VALIDACIÓN_REQUERIDA"
    LISTA_PARA_ASIGNAR = "LISTA_PARA_ASIGNAR"
    ASIGNADA = "ASIGNADA"
    EN_COTIZACION = "EN_COTIZACIÓN"
    COTIZACION_EN_REVISION = "COTIZACIÓN_EN_REVISIÓN"
    COTIZADA = "COTIZADA"
    EN_NEGOCIACION = "EN_NEGOCIACIÓN"
    OC_CLIENTE_RECIBIDA = "OC_CLIENTE_RECIBIDA"
    COMPRA_PROVEEDOR_EN_REVISION = "COMPRA_PROVEEDOR_EN_REVISIÓN"
    COMPRA_PROVEEDOR_EMITIDA = "COMPRA_PROVEEDOR_EMITIDA"
    CERRADA = "CERRADA"
    EXCEPCION = "EXCEPCIÓN"


class _Ninguno:
    """Sentinel para la fila 1: el expediente todavía no existe."""

    def __repr__(self) -> str:
        return "(ninguno)"


class _CualquierEstadoActivo:
    """Sentinel para la fila 25: cualquier estado activo (no CERRADA, no EXCEPCIÓN)."""

    def __repr__(self) -> str:
        return "(cualquier estado activo)"


class _DestinoDinamico:
    """Sentinel para el destino de la fila 24: docs/state_machine.md dice
    literalmente "(cualquier estado anterior aplicable)" — el humano que
    resuelve la excepción decide el destino real, nunca es un valor fijo de
    tabla (regla general #4 de ese documento). Usar resolve_exception(),
    nunca leer `.destino` de esta fila directamente ni pasarla a
    find_transition()."""

    def __repr__(self) -> str:
        return "(cualquier estado anterior aplicable, decidido por el humano)"


NINGUNO = _Ninguno()
CUALQUIER_ESTADO_ACTIVO = _CualquierEstadoActivo()
DESTINO_DINAMICO = _DestinoDinamico()

ESTADOS_TERMINALES_O_ESTACIONAMIENTO = frozenset(
    {EstadoExpediente.CERRADA, EstadoExpediente.EXCEPCION}
)
"""'Estado activo' (fila 25) excluye CERRADA (terminal) y EXCEPCIÓN (ya es el
estacionamiento) — no es una condición literal del texto de
docs/state_machine.md, es la interpretación operativa de "activo" que
aplica esta implementación."""


@dataclass(frozen=True)
class Transition:
    row: int
    origen: EstadoExpediente | _Ninguno | _CualquierEstadoActivo
    destino: EstadoExpediente | _DestinoDinamico
    evento: str
    condition_tag: str
    condicion_texto: str
    actor: str


# Las filas 13, 16 y 18 de docs/state_machine.md no traen un nombre de
# evento fijo (usan una descripción entre paréntesis: "acción manual del
# cotizador", "rechazo de aprobación", "nueva versión de cotización
# aprobada"), y ninguno de esos tres aparece en la lista canónica de
# eventos de docs/event_contracts.md / docs/architecture.md §22. Los
# nombres COTIZADOR_INICIA_TRABAJO y QUOTE_REJECTED de abajo son
# identificadores de código que este módulo necesita para poder buscar en
# la tabla — no son nombres de evento confirmados por ninguna fuente.
# Jorge debe confirmarlos (o el sistema real que dispara la fila 13/16)
# antes de tratarlos como parte del contrato de eventos.
TRANSITIONS: tuple[Transition, ...] = (
    Transition(1, NINGUNO, EstadoExpediente.RECIBIDA, "EMAIL_INGESTED",
               "new_message_not_duplicate", "mensaje nuevo, hash no duplicado", "Gmail Ingest"),
    Transition(2, EstadoExpediente.RECIBIDA, EstadoExpediente.CLASIFICADA, "EMAIL_CLASSIFIED",
               "ok", "clasificación con requires_human_review=false", "Clasificador"),
    Transition(3, EstadoExpediente.RECIBIDA, EstadoExpediente.EXCEPCION, "EMAIL_CLASSIFIED",
               "requires_human_review", "requires_human_review=true o classification=EXCEPCION", "Clasificador"),
    Transition(4, EstadoExpediente.CLASIFICADA, EstadoExpediente.EXTRAIDA, "DOCUMENT_EXTRACTED",
               "ok", "extracción con requires_human_review=false", "Extractor"),
    Transition(5, EstadoExpediente.CLASIFICADA, EstadoExpediente.VALIDACION_REQUERIDA, "DOCUMENT_EXTRACTED",
               "low_line_count_confidence", "line_count_confidence < LINE_COUNT_CONFIDENCE_THRESHOLD", "Extractor"),
    Transition(6, EstadoExpediente.CLASIFICADA, EstadoExpediente.EXCEPCION, "DOCUMENT_EXTRACTED",
               "extraction_failed", "extracción falló (documento ilegible, lines=[])", "Extractor"),
    Transition(7, EstadoExpediente.EXTRAIDA, EstadoExpediente.LISTA_PARA_ASIGNAR, "CASE_RESOLVED",
               "case_unique_confirmed",
               "expediente único confirmado (regla determinista o case_resolver_v1 con resolution != EXCEPCION)",
               "Case Resolver / reglas deterministas"),
    Transition(8, EstadoExpediente.EXTRAIDA, EstadoExpediente.EXCEPCION, "CASE_RESOLVED",
               "case_ambiguous", "resolution=EXCEPCION (dos candidatos con evidencia comparable)", "Case Resolver"),
    Transition(9, EstadoExpediente.VALIDACION_REQUERIDA, EstadoExpediente.LISTA_PARA_ASIGNAR, "RFQ_VALIDATED",
               "human_confirmed_count", "humano confirma conteo de líneas manualmente",
               "Humano (cotizador líder / supervisor)"),
    Transition(10, EstadoExpediente.VALIDACION_REQUERIDA, EstadoExpediente.EXCEPCION, "RFQ_VALIDATED",
               "human_rejected_document", "humano determina que el documento no es procesable", "Humano"),
    Transition(11, EstadoExpediente.LISTA_PARA_ASIGNAR, EstadoExpediente.ASIGNADA, "RFQ_ASSIGNED",
               "cotizador_found", "balanceador encontró cotizador elegible sin exclusiones activas", "Balanceador"),
    Transition(12, EstadoExpediente.LISTA_PARA_ASIGNAR, EstadoExpediente.EXCEPCION, "RFQ_ASSIGNED",
               "no_cotizador_eligible",
               "ninguna exclusión resuelta (todos los cotizadores excluidos, o cliente reservado sin cotizador designado)",
               "Balanceador"),
    Transition(13, EstadoExpediente.ASIGNADA, EstadoExpediente.EN_COTIZACION, "COTIZADOR_INICIA_TRABAJO",
               "cotizador_starts_work", "cotizador marca inicio de trabajo (acción manual)", "Humano (cotizador)"),
    Transition(14, EstadoExpediente.EN_COTIZACION, EstadoExpediente.COTIZACION_EN_REVISION,
               "QUOTE_APPROVAL_REQUIRED", "draft_submitted", "cotizador envía borrador a aprobación",
               "Humano (cotizador) → sistema"),
    Transition(15, EstadoExpediente.COTIZACION_EN_REVISION, EstadoExpediente.COTIZADA, "QUOTE_APPROVED",
               "approved", "aprobador humano aprueba y cotización se envía al cliente",
               "Humano (aprobador, ver RACI)"),
    Transition(16, EstadoExpediente.COTIZACION_EN_REVISION, EstadoExpediente.EN_COTIZACION, "QUOTE_REJECTED",
               "rejected", "aprobador solicita cambios (rechazo de aprobación)", "Humano (aprobador)"),
    Transition(17, EstadoExpediente.COTIZADA, EstadoExpediente.EN_NEGOCIACION, "EMAIL_CLASSIFIED",
               "client_requests_clarification",
               "classification=ACLARACION sobre el mismo case_id — cliente responde pidiendo ajustes",
               "Clasificador + Case Resolver"),
    Transition(18, EstadoExpediente.EN_NEGOCIACION, EstadoExpediente.COTIZADA, "QUOTE_APPROVED",
               "new_version_approved", "se repite la transición 14→15 con nueva versión de cotización", "Humano"),
    Transition(19, EstadoExpediente.COTIZADA, EstadoExpediente.OC_CLIENTE_RECIBIDA, "CUSTOMER_PO_RECEIVED",
               "po_detected", "clasificador detecta PO_CLIENTE asociado al expediente",
               "Clasificador + Case Resolver"),
    Transition(20, EstadoExpediente.EN_NEGOCIACION, EstadoExpediente.OC_CLIENTE_RECIBIDA, "CUSTOMER_PO_RECEIVED",
               "client_accepts_during_negotiation", "cliente acepta directamente durante negociación",
               "Clasificador + Case Resolver"),
    Transition(21, EstadoExpediente.OC_CLIENTE_RECIBIDA, EstadoExpediente.COMPRA_PROVEEDOR_EN_REVISION,
               "SUPPLIER_PO_APPROVAL_REQUIRED", "supplier_po_prepared", "sistema/humano prepara orden a proveedor",
               "Humano (comprador)"),
    Transition(22, EstadoExpediente.COMPRA_PROVEEDOR_EN_REVISION, EstadoExpediente.COMPRA_PROVEEDOR_EMITIDA,
               "SUPPLIER_PO_EMITTED", "supplier_po_approved", "aprobador humano aprueba la compra al proveedor",
               "Humano (aprobador, ver RACI)"),
    Transition(23, EstadoExpediente.COMPRA_PROVEEDOR_EMITIDA, EstadoExpediente.CERRADA, "CASE_CLOSED",
               "supplier_delivery_confirmed", "proveedor confirma entrega y no hay pendientes",
               "Humano / Odoo Connector (lectura de estado)"),
    Transition(24, EstadoExpediente.EXCEPCION, DESTINO_DINAMICO, "EXCEPTION_RESOLVED",
               "exception_resolved_by_human",
               "humano resuelve la excepción y determina el estado correcto de reingreso"
               " (destino real = el que el humano indique explícitamente, ver resolve_exception())",
               "Humano (supervisor)"),
    Transition(25, CUALQUIER_ESTADO_ACTIVO, EstadoExpediente.EXCEPCION, "EXCEPTION_CREATED",
               "unrecoverable_error_or_sla_breach",
               "error técnico no recuperable, timeout de reintentos agotado, SLA vencido sin resolución",
               "Orquestador"),
)


class TransitionRejected(Exception):
    """Se lanza cuando (estado_actual, evento, condition_tag) no coincide con
    ninguna fila de TRANSITIONS. El llamador debe generar EXCEPTION_CREATED
    (fila 25) en vez de aplicar el cambio de estado "por si acaso"
    (regla general #1 de docs/state_machine.md)."""


def _origen_coincide(transition: Transition, estado_actual: EstadoExpediente | None) -> bool:
    if transition.origen is NINGUNO:
        return estado_actual is None
    if transition.origen is CUALQUIER_ESTADO_ACTIVO:
        return (
            estado_actual is not None
            and estado_actual not in ESTADOS_TERMINALES_O_ESTACIONAMIENTO
        )
    return transition.origen == estado_actual


def find_transition(
    estado_actual: EstadoExpediente | None,
    evento: str,
    condition_tag: str,
) -> Transition:
    """Busca la única fila de TRANSITIONS aplicable. Lanza TransitionRejected
    si no hay ninguna (o hay más de una, lo que sería un bug en la tabla)."""

    candidatas = [
        t
        for t in TRANSITIONS
        if t.evento == evento
        and t.condition_tag == condition_tag
        and _origen_coincide(t, estado_actual)
    ]
    if len(candidatas) != 1:
        raise TransitionRejected(
            f"No hay transición única para estado_actual={estado_actual!r}, "
            f"evento={evento!r}, condition_tag={condition_tag!r} "
            f"({len(candidatas)} candidatas)"
        )
    encontrada = candidatas[0]
    if encontrada.destino is DESTINO_DINAMICO:
        raise TransitionRejected(
            f"La fila {encontrada.row} tiene destino dinámico (lo decide el humano) — "
            "usa resolve_exception(destino), nunca find_transition() para esta fila."
        )
    return encontrada


def resolve_exception(
    destino: EstadoExpediente,
) -> Transition:
    """Fila 24 — única salida válida de EXCEPCIÓN. El destino lo decide el
    humano explícitamente (docs/state_machine.md regla general #2 y #4);
    esta función solo valida que el destino no sea EXCEPCIÓN de nuevo."""

    if destino == EstadoExpediente.EXCEPCION:
        raise TransitionRejected("El destino de una resolución de excepción no puede ser EXCEPCIÓN de nuevo")
    fila_24 = next(t for t in TRANSITIONS if t.row == 24)
    return Transition(
        row=24,
        origen=EstadoExpediente.EXCEPCION,
        destino=destino,
        evento=fila_24.evento,
        condition_tag=fila_24.condition_tag,
        condicion_texto=fila_24.condicion_texto,
        actor=fila_24.actor,
    )
