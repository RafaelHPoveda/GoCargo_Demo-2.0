from django.conf import settings
from django.db import transaction

from apps.branches.application.services import BranchService
from apps.branches.infrastructure.persistence.repositories import DjangoBranchRepository
from apps.shipments.application.services import ShipmentService
from apps.shipments.infrastructure.integrations.branches import LocalBranchChecker
from apps.shipments.infrastructure.integrations.countries.catalog import GraphQLCountryCatalog
from apps.shipments.infrastructure.integrations.countries.client import CountryGraphQLClient
from apps.shipments.infrastructure.integrations.countries.mappers import CountryGraphQLMapper
from apps.shipments.infrastructure.persistence.repositories import DjangoShipmentRepository


def build_branch_service() -> BranchService:
    return BranchService(DjangoBranchRepository())


def build_country_catalog() -> GraphQLCountryCatalog:
    return GraphQLCountryCatalog(
        CountryGraphQLClient(
            settings.COUNTRIES_API_URL,
            (
                settings.COUNTRIES_CONNECT_TIMEOUT,
                settings.COUNTRIES_READ_TIMEOUT,
            ),
        ),
        CountryGraphQLMapper(),
    )


def build_shipment_service() -> ShipmentService:
    return ShipmentService(
        DjangoShipmentRepository(),
        LocalBranchChecker(build_branch_service()),
        build_country_catalog(),
        transaction.atomic(),
    )
