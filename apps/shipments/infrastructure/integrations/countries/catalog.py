from apps.shipments.application.dto import CountryDto
from apps.shipments.application.exceptions import CountryCatalogUnavailableError
from apps.shipments.infrastructure.integrations.countries.client import CountryGraphQLClient
from apps.shipments.infrastructure.integrations.countries.mappers import CountryGraphQLMapper
from apps.shipments.infrastructure.integrations.countries.queries import GET_COUNTRY_QUERY


class GraphQLCountryCatalog:
    def __init__(self, client: CountryGraphQLClient, mapper: CountryGraphQLMapper) -> None:
        self._client = client
        self._mapper = mapper

    def get_country(self, code: str) -> CountryDto | None:
        data = self._client.execute(GET_COUNTRY_QUERY, {"code": code})
        if "country" not in data:
            raise CountryCatalogUnavailableError("La respuesta no contiene el país solicitado.")
        if data["country"] is None:
            return None
        return self._mapper.to_dto(data["country"], expected_code=code)
