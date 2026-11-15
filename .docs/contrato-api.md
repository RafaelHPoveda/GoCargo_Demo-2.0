# DTO, mapeo y contrato uniforme de API

## Convención de DTO

Se sigue el patrón observado en los records del proyecto .NET:

| Necesidad | Nombre |
| --- | --- |
| Representación general de sucursal | BranchDto |
| Crear sucursal | BranchDtoCreate |
| Actualizar sucursal | BranchDtoUpdate |
| Información interna de sucursal | BranchDtoInfo |
| Representación general de envío | ShipmentDto |
| Crear envío | ShipmentDtoCreate |
| País externo traducido | CountryDto |

Si se necesita una representación adicional: ModeloDtoSufijo. No se crea ShipmentDtoUpdate porque el alcance actual no admite modificar envíos. Cada consumidor conserva su DTO interno de sucursal; el adaptador usa un alias para distinguir clases homónimas de módulos diferentes.

Los DTO de aplicación son dataclasses inmutables con tipos de Python; no importan Django ni DRF. Los campos de negocio conservan snake_case. Las propiedades camelCase corresponden a la envoltura solicitada, no a una transformación global de nombres.

## Mapeo similar a AutoMapper

Sí existen bibliotecas de mapeo por convención. Se evaluaron fuentes primarias y se eligieron dos herramientas para responsabilidades diferentes:

| Herramienta | Uso en este proyecto |
| --- | --- |
| py-automapper 2.2.0 | Entidad ↔ ORM y entidad → DTO; coincidencia por nombres y campos sobrescritos |
| djangorestframework-dataclasses 1.4.0 | DTO ↔ validación/serialización JSON de DRF |
| Adaptix | Alternativa evaluada: conversión entre dataclasses y otros modelos; Django no figura entre sus modelos soportados de fábrica |

py-automapper no incluye integración Django de fábrica. core/orm_mapping.py registra una especificación pequeña que descubre los campos concretos del ORM. core/mapping.py configura una instancia independiente para dataclasses sin dependencia de Django. No se modifica el mapper global de la biblioteca.

No se requieren clases BranchMapper/ShipmentMapper ni archivos mappers.py de persistencia. BaseRepository construye el AutoModelMapper genérico con los tipos recibidos. Solo las diferencias se configuran en model_fields/domain_fields de cada repositorio. Internamente la biblioteca ejecuta una conversión como:

```python
return orm_mapper.to(ShipmentModel).map(
    entity, fields_mapping={"weight_kg": entity.weight.kg}
)
```

La vuelta al dominio reconstruye PackageWeight. La biblioteca llama al constructor de la entidad, por lo que sus invariantes se mantienen. El mapeo no hace SQL ni concede permisos ni valida la semántica de la API institucional.

El mapper de Countries conserva comprobaciones explícitas porque datos incompletos o de otro país deben distinguirse de ausencia confirmada. Automatizar asignaciones no sustituye esas reglas del adaptador externo.

Fuentes: [py-automapper](https://github.com/anikolaienko/py-automapper), [dataclass serializers](https://github.com/oxan/djangorestframework-dataclasses), [modelos admitidos por Adaptix](https://adaptix.readthedocs.io/en/latest/reference/integrations.html).

## Contrato de respuesta

ApiResponseDto representa el contrato y ApiResponse lo integra con DRF. Viven en core/presentation/responses.py porque expresan transporte, no reglas del negocio. El código HTTP del cuerpo siempre se obtiene del mismo valor que el estado HTTP real.

```json
{
  "isSuccess": true,
  "errorMessages": [],
  "successMessages": ["Registro creado correctamente."],
  "httpCode": 201,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Managua",
    "city": "Managua",
    "max_weight_kg": "25.00",
    "is_active": true
  },
  "meta": {}
}
```

| Campo | Tipo y semántica |
| --- | --- |
| isSuccess | Booleano derivado del código HTTP 2xx |
| errorMessages | Lista de mensajes de error; vacía en resultados correctos |
| successMessages | Lista de mensajes de éxito; vacía cuando falla |
| httpCode | Entero idéntico al estado HTTP real |
| data | DTO serializado, lista de DTO o null al fallar |
| meta | Objeto extensible para información adicional |

No se responde HTTP 200 para esconder errores. Listados correctos sin elementos llevan data=[]; fallos llevan data=null.

Ejemplo de validación:

```json
{
  "isSuccess": false,
  "errorMessages": ["Solicitud invalida."],
  "successMessages": [],
  "httpCode": 400,
  "data": null,
  "meta": {
    "errorCode": "invalid_request",
    "validationErrors": {"city": ["Este campo es requerido."]}
  }
}
```

meta admite claves adicionales como page/total cuando exista paginación. Actualmente no se implementa paginación. Los campos adicionales van en meta para no sobrescribir las propiedades estables del contrato.

## Flujo y errores

DataclassSerializer valida entrada y devuelve directamente BranchDtoCreate, BranchDtoUpdate o ShipmentDtoCreate. La vista llama al servicio y envuelve el DTO serializado en ApiResponse. Los servicios no conocen httpCode ni la envoltura REST.

El manejador global normaliza errores de dominio, persistencia, DRF y excepciones inesperadas. Estas últimas devuelven un 500 genérico; se registra solo el tipo sin exponer datos privados. Se conservan cabeceras como Retry-After y Allow.

Un middleware normaliza errores de rutas bajo /api/ que no alcanzan DRF, por ejemplo UUID mal formado. Mantiene el contrato JSON con DEBUG activo o inactivo. /api/docs/ y /api/schema/ conservan HTML y OpenAPI estándar; no se envuelven esos recursos. HEAD y las respuestas sin cuerpo siguen las reglas de HTTP.

OpenAPI documenta data con el DTO concreto y distingue listas de elementos. Este cambio modifica el formato JSON anterior: el consumidor debe leer response.data para los datos, no el objeto raíz. Los ejemplos PowerShell de los manuales ya usan branch.data.id y shipment.data.id.

En .NET se observaron DTO generales/create/update y respuestas directas junto a ProblemDetails; la envoltura descrita aquí es la nueva decisión solicitada y no se atribuye a una clase que ya existiera en aquel proyecto.
