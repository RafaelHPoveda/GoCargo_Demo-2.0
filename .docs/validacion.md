# Validación de la organización del proyecto

Fecha UTC: 2026-11-15T03:18:59+00:00.

## Resultado

| Comprobación | Evidencia |
| --- | --- |
| Django system check | Correcto |
| Migraciones pendientes | Ninguna; los cambios de carpetas no alteraron el esquema |
| Suite automatizada | 94 pruebas correctas |
| OpenAPI | Generado y validado sin advertencias |
| Ruff | Imports, lint y formato correctos |
| Dependencias | pip check sin incompatibilidades declaradas |
| Copia aislada del proyecto | Configuración desde variables nuevas, base nueva y migraciones correctas |
| API en copia aislada | Crear sucursal/envío y consultar listado correctos |
| Documentación en copia aislada | Scalar y esquema responden correctamente |
| .gitignore | Excluye secretos, datos, entornos, cachés y AGENTS.md |
| Archivos versionables | Incluye código, migraciones, .env.example y manuales internos |
| Enlaces Markdown internos | Comprobados después de escribir este informe |

## Independencia comprobada

Se copió únicamente GoCargoDemo_Structure a una ubicación temporal, sin cachés, secretos ni base de datos. Se eliminaron GOCARGO_ENV_FILE y PYTHONPATH del entorno de esa comprobación y se proporcionaron variables nuevas. Se aplicaron migraciones y se probaron endpoints usando un doble del proveedor GraphQL. Se comprobó que settings se importaba de la copia.

El intérprete y los paquetes instalados se reutilizaron como runtime; no se volvió a descargar el entorno. Esto comprueba independencia del código/configuración exterior, no una segunda instalación completa de dependencias. requirements-lock.txt conserva las versiones verificadas.

El .gitignore se verificó con Git en la copia desechable. No se inicializó Git en el proyecto del usuario, ni se crearon commits ni se publicaron archivos. La copia temporal se eliminó al terminar.

## Archivos y ubicación

El código, las pruebas, las migraciones, las plantillas, los archivos de dependencias y la documentación propia residen dentro de GoCargoDemo_Structure. Fuera quedan las referencias académicas, el protocolo PDF, .venv, .env, SQLite y AGENTS.md. Las instrucciones de instalación permiten recrear configuración y base sin esos archivos actuales.

La carga de .env externo es optativa mediante GOCARGO_ENV_FILE. No existe búsqueda automática en la carpeta padre ni imports de archivos externos. El ejemplo usa DB_NAME=../db.sqlite3 para mantener los datos locales fuera.

## Límites

Esta reorganización mantiene el alcance y contrato de la demo. La verificación aislada utilizó un proveedor simulado; no repitió el acceso GraphQL real ya verificado en la revisión anterior. No se consumió PIAR ni se ejecutaron PostgreSQL o SQL Server.

Autenticación, autorización institucional y presentación GraphQL futura siguen documentadas, sin implementar. Los listados no son paginados y no se añade garantía de consistencia frente a cambios concurrentes de capacidad/inactivación de sucursal. SQLite no certifica el comportamiento del motor final.


## Ampliación del repositorio base

Se completaron create, get_all, get_by_id, update, delete e is_exist, sin alias duplicados. Los repositorios de sucursales/envíos heredan las operaciones y el orden de los listados se conserva.

Las 14 pruebas nuevas verifican ambos modelos, ID duplicado sin sobrescritura, actualización con/sin cambios, actualización inexistente sin inserción, borrado por ID sin afectar otros registros, existencia con una consulta sin mapeo, rollback de actualización/eliminación, traducción de errores y recuperación tras una restricción fallida. La suite total de 94 pruebas pasó junto a Django check, migraciones pendientes, OpenAPI sin advertencias y Ruff. No se añadieron rutas REST ni migraciones.


## DTO, mapeo por convención y contrato JSON

Se revisó la nomenclatura de DTO y el manejo de respuestas del proyecto .NET. Se adoptaron ModeloDto, ModeloDtoCreate, ModeloDtoUpdate y ModeloDtoSufijo. py-automapper 2.2.0 automatiza campos coincidentes con especificaciones propias para dataclasses y Django; djangorestframework-dataclasses 1.4.0 convierte JSON a DTO y DTO a JSON. Las conversiones de peso y la semántica de errores externos permanecen explícitas.

La suite actual suma 94 pruebas. Las nuevas comprobaciones cubren los seis campos de la respuesta, igualdad de httpCode con el estado real, listas vacías, datos tipados en OpenAPI, validación por campos, errores 404/405/500, rutas inválidas con DEBUG activo/inactivo, cabeceras de reintento, independencia de datos mutables y mapeos que conservan invariantes/Decimal/UUID.

OpenAPI se validó sin advertencias, Ruff y formato pasan, pip check no reporta incompatibilidades y no hay migraciones pendientes. Se repitió una copia aislada con nuevas variables y SQLite nuevo: creación de sucursal/envío, listado envuelto, error de ruta JSON y esquema OpenAPI estándar correctos. Se reutilizó el runtime instalado y se simuló GraphQL; no se certificó acceso institucional ni otros motores.

El formato JSON cambió deliberadamente: los datos ahora están en data y los detalles adicionales en meta. Los recursos /api/docs/ y /api/schema/ conservan sus formatos estándar. Los manuales y ejemplos fueron actualizados.


## Abstracción del mapeo de persistencia

Se eliminaron BranchMapper y ShipmentMapper y sus archivos mappers.py de persistencia. BaseRepository recibe modelo y entidad y crea un AutoModelMapper genérico sobre py-automapper. Sucursales usa convenciones; envíos declara únicamente las conversiones de peso en model_fields/domain_fields. Las pruebas de mapeo usan la misma configuración real del repositorio y verifican round-trip, precisión, DTO e invariantes sin ejecutar consultas.
