from typing import Protocol, TypeVar
from uuid import UUID

T = TypeVar("T")


class IBaseRepository(Protocol[T]):
    """CRUD de entidades propias, independiente del motor de persistencia."""

    def create(self, entity: T) -> T:
        """Inserta una entidad nueva; un ID duplicado es un conflicto."""
        ...

    def get_all(self) -> list[T]:
        """Devuelve todas las entidades en orden estable; lista vacia si no hay datos."""
        ...

    def get_by_id(self, entity_id: UUID) -> T | None:
        """Devuelve una entidad o None cuando no existe."""
        ...

    def update(self, entity: T) -> T | None:
        """Actualiza por ID sin insertar; devuelve None si ya no existe."""
        ...

    def delete(self, entity_id: UUID) -> bool:
        """Elimina por ID; True si elimino un registro, False si no existia."""
        ...

    def is_exist(self, entity_id: UUID) -> bool:
        """Comprueba existencia por ID sin reconstruir la entidad."""
        ...
