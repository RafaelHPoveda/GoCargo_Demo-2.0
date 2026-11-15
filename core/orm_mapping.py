from collections.abc import Callable
from dataclasses import fields, is_dataclass
from typing import Any, Generic, TypeVar

from automapper import Mapper
from django.db import models

# py-automapper no trae extension Django: registrar solo campos concretos del modelo.
orm_mapper = Mapper()
orm_mapper.add_spec(
    is_dataclass, lambda target: [field.name for field in fields(target) if field.init]
)
orm_mapper.add_spec(
    models.Model,
    lambda target: [
        field.attname
        for field in target._meta.get_fields()
        if field.concrete and not field.many_to_many and not field.generated
    ],
)


T = TypeVar("T")
M = TypeVar("M", bound=models.Model)


class AutoModelMapper(Generic[T, M]):
    """Un unico adaptador py-automapper reutilizable por todos los repositorios."""

    def __init__(
        self,
        entity_type: type[T],
        model_type: type[M],
        *,
        model_fields: Callable[[T], dict[str, Any]] | None = None,
        domain_fields: Callable[[M], dict[str, Any]] | None = None,
    ) -> None:
        self._entity_type = entity_type
        self._model_type = model_type
        self._model_fields = model_fields
        self._domain_fields = domain_fields

    def to_model(self, entity: T) -> M:
        overrides = self._model_fields(entity) if self._model_fields else None
        return orm_mapper.to(self._model_type).map(entity, fields_mapping=overrides)

    def to_domain(self, model: M) -> T:
        overrides = self._domain_fields(model) if self._domain_fields else None
        return orm_mapper.to(self._entity_type).map(model, fields_mapping=overrides)
