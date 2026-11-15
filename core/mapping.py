from dataclasses import fields, is_dataclass

from automapper import Mapper

# Instancia propia; sin extensiones globales ni dependencia de Django.
object_mapper = Mapper()
object_mapper.add_spec(
    is_dataclass, lambda target: [field.name for field in fields(target) if field.init]
)
