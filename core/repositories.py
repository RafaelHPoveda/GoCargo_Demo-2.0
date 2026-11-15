from collections.abc import Callable
from typing import Any, Generic, TypeVar
from uuid import UUID

from django.db import DatabaseError, IntegrityError, models

from core.exceptions import RepositoryConflictError, RepositoryError
from core.orm_mapping import AutoModelMapper

T = TypeVar("T")
M = TypeVar("M", bound=models.Model)


class BaseRepository(Generic[T, M]):
    """CRUD compartido para modelos simples con identificador UUID."""

    def __init__(
        self,
        model: type[M],
        entity_type: type[T],
        db_alias: str = "default",
        *,
        model_fields: Callable[[T], dict[str, Any]] | None = None,
        domain_fields: Callable[[M], dict[str, Any]] | None = None,
    ) -> None:
        self._model = model
        self._mapper = AutoModelMapper(
            entity_type, model, model_fields=model_fields, domain_fields=domain_fields
        )
        self._db_alias = db_alias
        self._ordering = tuple(model._meta.ordering) or ("pk",)

    def create(self, entity: T) -> T:
        model_instance = self._mapper.to_model(entity)
        try:
            model_instance.save(using=self._db_alias, force_insert=True)
        except IntegrityError as exc:
            raise RepositoryConflictError(
                "La entidad no cumple las restricciones de persistencia."
            ) from exc
        except DatabaseError as exc:
            raise RepositoryError("No fue posible crear la entidad.") from exc
        return self._mapper.to_domain(model_instance)

    def get_all(self) -> list[T]:
        try:
            records = list(
                self._model._default_manager.using(self._db_alias).order_by(*self._ordering)
            )
        except DatabaseError as exc:
            raise RepositoryError("No fue posible listar las entidades.") from exc
        return [self._mapper.to_domain(record) for record in records]

    def get_by_id(self, entity_id: UUID) -> T | None:
        try:
            record = self._model._default_manager.using(self._db_alias).get(pk=entity_id)
        except self._model.DoesNotExist:
            return None
        except DatabaseError as exc:
            raise RepositoryError("No fue posible consultar la entidad.") from exc
        return self._mapper.to_domain(record)

    def update(self, entity: T) -> T | None:
        model_instance = self._mapper.to_model(entity)
        values = {
            field.attname: getattr(model_instance, field.attname)
            for field in self._model._meta.get_fields()
            if field.concrete
            and not field.many_to_many
            and not field.primary_key
            and not field.generated
        }
        try:
            affected = (
                self._model._default_manager.using(self._db_alias)
                .filter(pk=model_instance.pk)
                .update(**values)
            )
        except IntegrityError as exc:
            raise RepositoryConflictError(
                "La entidad no cumple las restricciones de persistencia."
            ) from exc
        except DatabaseError as exc:
            raise RepositoryError("No fue posible actualizar la entidad.") from exc
        return self._mapper.to_domain(model_instance) if affected else None

    def delete(self, entity_id: UUID) -> bool:
        try:
            deleted, _ = (
                self._model._default_manager.using(self._db_alias).filter(pk=entity_id).delete()
            )
        except IntegrityError as exc:
            raise RepositoryConflictError(
                "La entidad no puede eliminarse por sus restricciones de integridad."
            ) from exc
        except DatabaseError as exc:
            raise RepositoryError("No fue posible eliminar la entidad.") from exc
        return deleted > 0

    def is_exist(self, entity_id: UUID) -> bool:
        try:
            return self._model._default_manager.using(self._db_alias).filter(pk=entity_id).exists()
        except DatabaseError as exc:
            raise RepositoryError("No fue posible comprobar la existencia de la entidad.") from exc
