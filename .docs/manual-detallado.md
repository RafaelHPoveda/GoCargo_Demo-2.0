# Manual detallado de desarrollo y mantenimiento

## 1. Punto de entrada y convenciones

Ejecutar desde la raíz que contiene manage.py. config/settings.py obtiene BASE_DIR de su ubicación. El proyecto no importa código del directorio padre. GOCARGO_ENV_FILE selecciona expresamente una configuración externa; el entorno virtual se recrea al instalar y no se versiona.

manage.py carga config.settings. config.urls incluye las rutas de presentación. Las vistas reciben servicios de config.dependencies. Cada app descubre modelos mediante apps.py y su models.py raíz.

## 2. Dominio de sucursales

apps/branches/domain/entities.py contiene Branch, dataclass inmutable con UUID, name, city, max_weight_kg e is_active. El constructor normaliza nombre/ciudad y rechaza campos vacíos, longitudes inválidas y capacidad no finita/no positiva, fuera de rango o con precisión superior a dos decimales.

domain/exceptions.py define BranchValidationError y sus especializaciones. No importan Django ni guardan datos. Las actualizaciones usan dataclasses.replace en aplicación para conservar identidad y reejecutar las invariantes.

## 3. Dominio de envíos

apps/shipments/domain/value_objects.py contiene PackageWeight: Decimal finito, mayor que cero, máximo 50.00 kg y hasta dos decimales. Es inmutable y no conoce sucursales.

domain/entities.py contiene Shipment. Conserva UUID propio, referencia/nombre de sucursal, descripción, peso, código/nombre de país, moneda y estado CREATED. Comprueba descripción, código de dos letras, nombres, moneda, tipo de peso y estado.

La capacidad de una sucursal específica es una coordinación de aplicación; los límites intrínsecos del peso pertenecen al objeto de valor.

## 4. Aplicación: mensajes y contratos

application/dto.py agrupa entradas y salidas inmutables. DataclassSerializer convierte HTTP directamente al DTO tipado; el servicio recibe serializer.validated_data sin reconstruirlo manualmente. Las salidas no exponen modelos ORM.

Cada consumidor puede tener su DTO propio de sucursal para conservar independencia del contrato. No se importan modelos ORM de otra app.

application/ports.py contiene Protocol para persistencia e integraciones. Los adaptadores satisfacen estructuralmente esos contratos, sin herencia nominal obligatoria. Los repositorios específicos extienden IBaseRepository con CRUD y existencia; solo agregan consultas particulares cuando son necesarias.

application/exceptions.py expresa fallos del caso de uso: recurso inexistente, sucursal inactiva/capacidad excedida o catálogo indisponible. Los códigos HTTP se asignan fuera del núcleo.

## 5. Servicios y flujos

BranchService ofrece create, get_all, update y get_info. get_info publica la información interna mínima para validar una sucursal sin exponer su persistencia.

ShipmentService ofrece create, get_all y get_by_id. Creación:

1. Construir PackageWeight y normalizar/validar el código de país.
2. Consultar IBranchChecker y verificar existencia, actividad y capacidad.
3. Consultar ICountryCatalog y distinguir inexistencia de indisponibilidad.
4. Entrar al context manager transaccional recibido desde composición.
5. Construir Shipment con referencias y snapshots.
6. Guardar mediante IShipmentRepository y convertir el resultado a DTO.
7. Salir del contexto antes de devolver el resultado; Django confirma o revierte.

Algunas validaciones de Shipment se ejecutan al construir la entidad. No se garantiza que toda entrada inválida desde aplicación se rechace antes de consultar red; HTTP valida formato con serializers.

Los listados y detalles usan solo persistencia local y no revalidan snapshots contra el proveedor.

## 6. Persistencia separada

Cada app contiene infrastructure/persistence/ con:

- models.py: tablas, campos y restricciones ORM.
- repositories.py: consultas/escrituras según los puertos.

El models.py raíz de cada app reexporta el modelo para descubrimiento Django. No duplicar tablas ni añadir reglas de negocio ahí. migrations/ sigue en la raíz de la app.

core/repositories.py contiene BaseRepository, que configura el AutoModelMapper genérico de core/orm_mapping.py a partir del tipo de entidad y el modelo ORM. El CRUD completo se implementa una sola vez y ambos repositorios concretos lo heredan:

| Método | Resultado y comportamiento |
| --- | --- |
| create(entity) | Entidad insertada; ID duplicado produce RepositoryConflictError |
| get_all() | Lista de entidades, vacía si no hay datos |
| get_by_id(id) | Entidad o None |
| update(entity) | Entidad actualizada o None si falta; nunca inserta |
| delete(id) | True si eliminó, False si no existía |
| is_exist(id) | Booleano por ID, sin materializar la entidad |

get_all respeta Meta.ordering del modelo y usa la clave primaria cuando no hay orden configurado. Así se conserva el orden nombre/ID de sucursales y por ID de envíos. IntegrityError se traduce a conflicto; DatabaseError a RepositoryError.

update realiza una actualización completa de los campos concretos que entrega el mapper, excluyendo clave primaria, relaciones muchos-a-muchos y campos generados. No ejecuta Model.save, full_clean ni señales de guardado. Las entidades deben llegar validadas desde el caso de uso. Si un modelo futuro necesita hooks, auditoría automática, relaciones complejas o política de eliminación lógica, su adaptador debe implementar esa responsabilidad explícitamente.

delete aplica eliminación física y respeta las restricciones y cascadas del ORM. No comprueba is_exist antes de actualizar/eliminar: decide con el resultado de la operación, evitando una comprobación previa sujeta a cambios concurrentes. Los permisos y las reglas de negocio continúan siendo responsabilidad del caso de uso.

Estas capacidades de persistencia no habilitan endpoints nuevos ni acciones de negocio de modificación/eliminación de envíos. Los servicios utilizan create para insertar y get_all para consultar, sin cambiar el contrato REST. La atomicidad de varias operaciones se controla con el contexto transaccional inyectado, no con un commit individual del repositorio.

Referencia: [QuerySet de Django](https://docs.djangoproject.com/en/6.1/ref/models/querysets/).

La actualización de sucursal cambia únicamente campos permitidos tras validar la entidad. Escrituras masivas/directas desde otros caminos pueden saltarse invariantes; no habilitarlas como alternativa a los servicios.

## 7. Integración entre módulos

shipments/infrastructure/integrations/branches.py implementa LocalBranchChecker. Recibe un BranchReader estructural mínimo con get_info. Consulta el servicio de sucursales y convierte su respuesta al DTO del consumidor.

No consulta BranchModel ni hace joins al ORM de otra app. La composición proporciona el servicio real; las pruebas usan sustitutos.

## 8. Consumo GraphQL por responsabilidades

infrastructure/integrations/countries/queries.py declara GET_COUNTRY_QUERY parametrizada. No interpolar valores de usuario dentro del texto GraphQL.

client.py ejecuta requests con esperas de conexión/lectura. Comprueba HTTP, JSON objeto, ausencia de errors y data objeto. Las respuestas parciales con errors se rechazan para esta validación obligatoria.

mappers.py comprueba código esperado, nombre, moneda, tipos y longitudes. Devuelve CountryDto y mantiene la representación externa fuera del servicio.

catalog.py implementa get_country. country=null con respuesta válida significa inexistente; campo ausente o mal formado significa indisponibilidad. Recibe cliente y mapper por constructor.

No hay reintentos ni caché. Añadirlos requiere presupuesto de latencia y vigencia explícitos. Para PIAR serán necesarios contratos específicos del caso pedagógico, IDs opacos/Relay, paginación y permisos. No basta sustituir la URL de Countries por PIAR porque sus esquemas son diferentes.

## 9. REST y contrato OpenAPI

Los serializers se generan desde los DTO con djangorestframework-dataclasses y no escriben ORM. Las restricciones HTTP se configuran en Meta.extra_kwargs y se comparten entre los serializers de sucursales. PUT exige todos los campos editables; PATCH admite cambios parciales. La actualización rechaza campos desconocidos y cuerpo sin cambios.

Las vistas reciben el DTO desde serializer.validated_data y llaman servicios; crear responde 201 mediante ApiResponse. Las rutas no publican acciones adicionales por heredar un CRUD genérico.

config.exceptions traduce errores de ambos módulos y distingue con alias las dos BranchNotFoundError homónimas. También sanitiza DatabaseError que pueda surgir al confirmar la transacción fuera del repositorio.

drf-spectacular genera OpenAPI desde extend_schema_view y serializers. core/presentation/schema.py documenta la envoltura y los errores; config.api_docs renderiza Scalar, que consume /api/schema/.

Exportación opcional regenerable:

```powershell
New-Item -ItemType Directory -Force .docs/generated | Out-Null
..\.venv\Scripts\python.exe manage.py spectacular --validate --fail-on-warn --file .docs/generated/openapi.yaml
```

.docs/generated/ se ignora. Los manuales y la arquitectura sí se versionan.

## 10. Composición y atomicidad

config.dependencies construye BranchService con su repositorio y ShipmentService con repositorio, adaptador interno, catálogo y transaction.atomic(). Las fábricas se invocan por solicitud: no se comparte globalmente un servicio con estado transaccional.

Aplicación conoce AbstractContextManager de Python, no atomic ni settings. Los repositorios y la transacción deben usar la misma conexión para tener atomicidad local conjunta.

La consulta remota ocurre antes de abrir la transacción. Esta no protege cambios simultáneos de PIAR ni un cambio de capacidad/inactivación de sucursal entre validación y escritura. Si se exige esa garantía, diseñar relectura/bloqueos/restricciones y probarlos en el motor final.

## 11. Procedimiento de cambio

1. Distinguir invariante de dominio, coordinación de servicio o formato HTTP.
2. Cambiar la responsabilidad correspondiente.
3. Ajustar DTO/puerto solo si se requieren datos u operaciones nuevas.
4. Cambiar mapper/adaptador si cambia persistencia o contrato externo.
5. Actualizar serializer, vista y OpenAPI cuando cambie HTTP.
6. Generar migración si cambia el modelo y revisar datos existentes.
7. Ejecutar tests relacionados, suite completa, migraciones, esquema y Ruff.
8. Actualizar documentación de contratos/uso.

No crear interfaces, clases base, dependencias o carpetas vacías por anticipación. La estructura separa responsabilidades que ya existen. Los DTO y puertos relacionados permanecen agrupados.

## 12. Construir el módulo pedagógico

Acordar lenguaje, horarios, estados, agregados, cierre, evidencias y permisos con responsables institucionales. Crear una app con las cuatro responsabilidades y definir puertos según sus casos de uso; no replicar todo el esquema PIAR.

Autenticación local prevista: Django/Simple JWT. Resolver usuario y AUTH_USER_MODEL antes de las migraciones iniciales. Distinguir cuenta local, asesor y credencial PIAR. Aplicación deberá comprobar autorización por operación y objeto para reutilizarla desde distintos transportes.

La cuenta de servicio puede acceder a más información que un usuario local; el backend debe filtrar ese alcance. Mantener credenciales fuera de Git y excluir tokens/respuestas institucionales completas de los registros.

## 13. Cambiar de motor de base de datos

Configurar DB_ENGINE y credenciales. PostgreSQL necesita psycopg compatible; SQL Server necesita mssql-django compatible, pyodbc y ODBC del sistema. Validar compatibilidad con Python/Django antes de instalar.

Aplicar migraciones en base vacía y verificar UUID, Decimal, restricciones, longitudes, collation y transacciones. Ejecutar tests contra el servidor real. Si hay datos, planificar traslado/recuperación: cambiar ENGINE no los mueve. SQLite no certifica bloqueo o concurrencia del motor final.

## 14. GraphQL de entrada futuro

El REST propio puede consumir PIAR GraphQL sin cambiarlo. Si se aprueba otro transporte de entrada, añadir presentation/graphql/ con resolvers que invoquen servicios existentes y compartan reglas y autorización.

Incorporar el módulo dentro de PIAR requiere alinear versiones, settings, usuarios, permisos, app labels, migraciones y propiedad de datos. Esta demo conserva las versiones verificadas de GoCargo; no garantiza compatibilidad directa con Django 5.2.8 declarado por la copia de PIAR.

## 15. Pruebas y diagnóstico

Los tests de dominio cubren invariantes sin framework. Servicios usan sustitutos de puertos. Persistencia verifica round-trip y rollback. REST comprueba estados, contratos y ausencia de escritura al fallar el proveedor. config/tests comprueba errores, documentación y fronteras del núcleo recorriendo domain/ y application/.

| Síntoma | Revisión |
| --- | --- |
| Falta DJANGO_SECRET_KEY | Definir GOCARGO_ENV_FILE en esta terminal o exportar variables |
| No existe tabla | Ejecutar migrate con la misma configuración de base |
| 503 al crear envío | Revisar proveedor/timeouts; el historial local no depende de él |
| OpenAPI incompleto | Revisar serializers y extend_schema_view y regenerar |
| ImportError tras mover clases | Usar domain.entities/exceptions/value_objects e infrastructure.persistence/integrations |
| PyYAML intenta compilar C | Configurar PYYAML_FORCE_LIBYAML=0 en Python 3.15 Windows |
| Falla otro motor | Revisar compatibilidad y drivers; probar restricciones sin cambiar dominio para ocultarlas |

## 16. Preparar Git y una copia independiente

Inicializar Git desde esta carpeta, revisar el índice y conservar migraciones, tests y documentación. .gitignore no elimina archivos ya rastreados; si existe historial, revisar el índice. Este trabajo prepara archivos, sin hacer commits ni enviar código a un remoto.

Se recrean entorno, configuración y base desde archivos versionados. No se necesitan referencias académicas externas, AGENTS.md, el entorno original ni sus datos. La verificación de copia aislada se registra en [validación](validacion.md).


## 17. DTO y contrato de respuesta

Consultar [DTO, mapeo y contrato API](contrato-api.md). BaseRepository reutiliza AutoModelMapper con py-automapper; los serializers reutilizan DataclassSerializer. No existen BranchMapper ni ShipmentMapper por entidad. ApiResponseDto/ApiResponse están en core/presentation/responses.py, los esquemas en core/presentation/schema.py y la normalización de rutas fallidas en middleware.py. La convención es ModeloDto, ModeloDtoCreate, ModeloDtoUpdate y ModeloDtoSufijo para representaciones adicionales.


## 18. Configurar persistencia sin una clase mapper por entidad

Cuando entidad y modelo coinciden en sus campos, declarar solo ambos tipos:

```python
class DjangoBranchRepository(BaseRepository[Branch, BranchModel]):
    def __init__(self, db_alias="default"):
        super().__init__(BranchModel, Branch, db_alias)
```

La base construye AutoModelMapper y todas sus operaciones usan la misma conversión. No crear BranchMapper ni un archivo mappers.py vacío. El constructor del dominio sigue ejecutando invariantes al reconstruir entidades.

Para diferencias de estructura, proporcionar funciones pequeñas en model_fields y domain_fields:

```python
super().__init__(
    ShipmentModel,
    Shipment,
    db_alias,
    model_fields=lambda entity: {"weight_kg": entity.weight.kg},
    domain_fields=lambda model: {"weight": PackageWeight(model.weight_kg)},
)
```

Estas funciones se evalúan para cada objeto. Los campos coincidentes se resuelven por convención. Las comprobaciones del proveedor GraphQL continúan en su adaptador: validar semántica externa es una responsabilidad distinta del mapeo automático de persistencia.
