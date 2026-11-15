# Manual general

## 1. Alcance

La demo permite crear/listar sucursales, actualizar sus datos y crear/listar/consultar envíos internacionales. Antes de crear un envío verifica sucursal, capacidad, peso y país mediante GraphQL.

Tiene acceso público. No incluye registro/login, permisos, eliminación de sucursales ni modificación de envíos. El historial se consulta localmente.

## 2. Contenido del repositorio

La raíz es GoCargoDemo_Structure/. Se versionan código, migraciones, pruebas, plantillas, .docs/, .env.example, Ruff y dependencias. .gitignore excluye secretos, entornos virtuales, SQLite, cachés, salidas generadas y AGENTS.md.

La .docs externa conserva referencias/protocolo académico y queda fuera del repositorio. La .docs interna contiene documentación del proyecto y sí se versiona. El PDF no es necesario para ejecutar el sistema.

## 3. Instalación nueva

El entorno verificado utiliza Python 3.15.2 y las dependencias exactas de requirements-lock.txt, incluidas las herramientas de desarrollo. Otras combinaciones requieren validar compatibilidad.

Desde una copia nueva del repositorio:

```powershell
python -m venv ..\.venv
$env:PYYAML_FORCE_LIBYAML = '0'
..\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
Copy-Item .env.example ..\.env
```

PYYAML_FORCE_LIBYAML evita compilar la extensión C opcional cuando no hay rueda compatible para Python 3.15 Windows. No instala compiladores.

Editar el archivo externo ..\.env y sustituir DJANGO_SECRET_KEY. Se puede generar una clave local con:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Si ya existen entorno y configuración, reutilizarlos y no sobrescribirlos con Copy-Item. Activar configuración y crear el esquema:

```powershell
$env:GOCARGO_ENV_FILE = (Resolve-Path ..\.env).Path
..\.venv\Scripts\python.exe manage.py migrate
..\.venv\Scripts\python.exe manage.py runserver
```

En este equipo el entorno, la configuración y la base ya existen fuera de GoCargoDemo_Structure; basta definir GOCARGO_ENV_FILE y ejecutar runserver.

## 4. Configuración

| Variable | Función |
| --- | --- |
| GOCARGO_ENV_FILE | Archivo .env opcional; por defecto se busca en la raíz del proyecto |
| DJANGO_SECRET_KEY | Clave obligatoria de Django |
| DJANGO_DEBUG | true para desarrollo |
| DJANGO_ALLOWED_HOSTS | Hosts separados por comas |
| DB_ENGINE | Backend Django; SQLite por defecto |
| DB_NAME | Nombre/ruta; el ejemplo usa ../db.sqlite3 para dejarla fuera |
| DB_USER, DB_PASSWORD, DB_HOST, DB_PORT | Conexión a otros motores |
| DB_ODBC_DRIVER | Driver previsto para SQL Server |
| COUNTRIES_API_URL | Proveedor GraphQL de la demo |
| COUNTRIES_CONNECT_TIMEOUT | Espera positiva de conexión, segundos |
| COUNTRIES_READ_TIMEOUT | Espera positiva de lectura, segundos |

Las variables de sesión tienen prioridad sobre el archivo. Las rutas relativas de SQLite se resuelven desde la raíz del proyecto. GOCARGO_ENV_FILE debe definirse en cada terminal nueva si se utiliza configuración externa. Ningún archivo privado actual es imprescindible: todos los valores se pueden recrear desde .env.example o variables del entorno.

## 5. API y documentación

http://127.0.0.1:8000/api/docs/ muestra Scalar, que requiere acceso a su CDN. http://127.0.0.1:8000/api/schema/ genera el contrato local sin consultar GraphQL.

| Método | Ruta | Operación |
| --- | --- | --- |
| GET | /api/branches/ | Listar sucursales |
| POST | /api/branches/ | Crear sucursal |
| PUT | /api/branches/{id}/ | Actualización completa |
| PATCH | /api/branches/{id}/ | Actualización parcial |
| GET | /api/shipments/ | Listar envíos |
| POST | /api/shipments/ | Crear envío |
| GET | /api/shipments/{id}/ | Consultar envío |

## 6. Ejemplo de uso

Con el servidor iniciado, abrir otra terminal:

```powershell
$branch = Invoke-RestMethod http://127.0.0.1:8000/api/branches/ -Method Post -ContentType 'application/json' -Body '{"name":"Managua","city":"Managua","max_weight_kg":"25.00","is_active":true}'
$body = @{
    origin_branch_id = $branch.data.id
    description = 'Documentos'
    weight_kg = '2.50'
    destination_country_code = 'CR'
} | ConvertTo-Json
$shipment = Invoke-RestMethod http://127.0.0.1:8000/api/shipments/ -Method Post -ContentType 'application/json' -Body $body
Invoke-RestMethod "http://127.0.0.1:8000/api/shipments/$($shipment.data.id)/"
```

Crear el envío requiere Internet. Countries no reproduce los permisos, la identidad o la paginación de PIAR; esta ejecución no certifica la integración institucional.

## 7. Reglas y errores

La sucursal necesita nombre/ciudad válidos y capacidad positiva con hasta dos decimales. El envío necesita descripción, peso mayor que cero y máximo 50 kg, sucursal existente/activa con capacidad suficiente y país válido. Moneda y nombres se guardan como snapshots.

| HTTP | Significado habitual |
| --- | --- |
| 201 | Creación correcta |
| 400 | Formato HTTP inválido |
| 404 | Sucursal, envío o país inexistente según respuesta válida |
| 409 | Conflicto de persistencia |
| 422 | Regla de negocio incumplida |
| 503 | Proveedor o persistencia no disponibles |

Las respuestas incluyen isSuccess, errorMessages, successMessages, httpCode, data y meta. Los errores técnicos se identifican en meta.errorCode y la validación por campos en meta.validationErrors. Si el proveedor falla, no se inserta el envío y el historial local sigue accesible. No se publican detalles de conexiones ni credenciales.

## 8. Verificar y detener

Ejecutar los comandos del [README](../README.md). Las pruebas usan una base temporal y dobles GraphQL. Detener runserver con Ctrl+C. Los datos quedan en la base configurada fuera del repositorio.

## 9. Evolución prevista

Autenticación propia con Django/Simple JWT, autorización local y cuenta PIAR con permisos mínimos de lectura están documentadas. PostgreSQL es el destino previsto y SQL Server una alternativa sujeta a compatibilidad. GraphQL de entrada se evaluará después. Ninguna de estas funcionalidades está implementada solo por estar documentada.


## 10. Formato de resultados

Todas las operaciones de negocio devuelven la envoltura documentada en [contrato API](contrato-api.md). Los datos están en data; la información adicional en meta. Los listados son data=[...]. isSuccess y httpCode reflejan el resultado HTTP real.
