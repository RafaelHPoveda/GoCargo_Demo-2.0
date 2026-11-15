import logging

from django.db import DatabaseError
from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler

from apps.branches.application.exceptions import BranchNotFoundError as LocalBranchNotFound
from apps.branches.domain.exceptions import BranchValidationError
from apps.shipments.application.exceptions import (
    BranchCapacityExceededError,
    BranchInactiveError,
    BranchNotFoundError,
    CountryCatalogUnavailableError,
    CountryNotFoundError,
    ShipmentNotFoundError,
)
from apps.shipments.domain.exceptions import ShipmentValidationError
from core.exceptions import RepositoryConflictError, RepositoryError
from core.presentation.responses import ApiResponse

logger = logging.getLogger(__name__)


def api_exception_handler(exc, context):
    mappings = (
        (LocalBranchNotFound, "branch_not_found", 404),
        (BranchNotFoundError, "branch_not_found", 404),
        (BranchValidationError, "invalid_branch", 422),
        (ShipmentValidationError, "invalid_shipment", 422),
        (ShipmentNotFoundError, "shipment_not_found", 404),
        (BranchInactiveError, "branch_inactive", 422),
        (BranchCapacityExceededError, "branch_capacity_exceeded", 422),
        (CountryNotFoundError, "country_not_found", 404),
        (CountryCatalogUnavailableError, "country_catalog_unavailable", 503),
    )
    for error, code, status in mappings:
        if isinstance(exc, error):
            return ApiResponse(
                http_code=status, error_messages=[str(exc)], meta={"errorCode": code}
            )
    if isinstance(exc, RepositoryConflictError):
        return ApiResponse(
            http_code=409,
            error_messages=["Conflicto al guardar datos."],
            meta={"errorCode": "persistence_conflict"},
        )
    # Incluye errores al confirmar atomic(), que ocurren despues de salir del repositorio.
    if isinstance(exc, (RepositoryError, DatabaseError)):
        return ApiResponse(
            http_code=503,
            error_messages=["Persistencia no disponible."],
            meta={"errorCode": "persistence_unavailable"},
        )
    response = exception_handler(exc, context)
    if response is not None:
        return ApiResponse(
            http_code=response.status_code,
            error_messages=[
                "Solicitud invalida."
                if isinstance(exc, ValidationError)
                else str(response.data.get("detail", "Error HTTP."))
                if isinstance(response.data, dict)
                else "Error HTTP."
            ],
            meta={
                "errorCode": "invalid_request"
                if isinstance(exc, ValidationError)
                else "http_error",
                "validationErrors": response.data,
            },
            headers=dict(response.headers),
        )
    # Mantener un contrato JSON uniforme sin exponer excepciones inesperadas.
    logger.error("Error no controlado en API: %s", type(exc).__name__)
    return ApiResponse(
        http_code=500,
        error_messages=["Ocurrio un error interno del servidor."],
        meta={"errorCode": "internal_error"},
    )
