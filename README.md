# GoCargo Demo Structure

Demo Django de sucursales y envíos internacionales con DDD, arquitectura limpia/hexagonal, Repository y SOLID. **Esta carpeta es la raíz que se sube a Git.** Incluye código, migraciones, pruebas, plantillas y documentación.

```text
apps/<modulo>/
  domain/                     entidades, excepciones y objetos de valor
  application/                servicios, DTO, puertos y errores
  infrastructure/
    persistence/              modelos ORM y repositorios; mapeo automático compartido
    integrations/             proveedores e integración entre módulos
  presentation/               serializers, vistas y rutas REST
  models.py                   descubrimiento de modelos Django
  apps.py
  migrations/
  tests/
config/                       configuración y composición
core/                         persistencia mínima compartida
templates/                    visor Scalar
.docs/                        arquitectura y manuales versionables
```

## Ejecutar en este equipo

Desde esta carpeta, reutilizando el entorno y la configuración externa existentes:

```powershell
$env:GOCARGO_ENV_FILE = (Resolve-Path ..\.env).Path
..\.venv\Scripts\python.exe manage.py runserver
```

Documentación: http://127.0.0.1:8000/api/docs/
Esquema: http://127.0.0.1:8000/api/schema/

## Instalar desde una copia independiente

No se necesita código ni documentación del directorio padre. Entorno, configuración y base se recrean durante la instalación:

```powershell
# Desde la raíz de una copia nueva del repositorio.
python -m venv ..\.venv
$env:PYYAML_FORCE_LIBYAML = '0' # Python 3.15/Windows sin extensión C de PyYAML.
..\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
Copy-Item .env.example ..\.env # Solo instalación nueva; no sobrescribir configuración existente.
# Sustituir DJANGO_SECRET_KEY en ..\.env por una clave aleatoria propia.
$env:GOCARGO_ENV_FILE = (Resolve-Path ..\.env).Path
..\.venv\Scripts\python.exe manage.py migrate
..\.venv\Scripts\python.exe manage.py runserver
```

GOCARGO_ENV_FILE selecciona expresamente el archivo externo. Sin esa variable se busca `.env` en la raíz del proyecto. También se pueden definir todas las variables directamente en el entorno. El ejemplo configura SQLite fuera del repositorio. No hay rutas personales codificadas en el proyecto.

## Verificar

```powershell
$env:GOCARGO_ENV_FILE = (Resolve-Path ..\.env).Path
..\.venv\Scripts\python.exe manage.py check
..\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
..\.venv\Scripts\python.exe manage.py test
..\.venv\Scripts\python.exe manage.py spectacular --validate --fail-on-warn
..\.venv\Scripts\python.exe -m ruff check .
..\.venv\Scripts\python.exe -m ruff format --check .
```

## Documentación

- [Arquitectura](.docs/arquitectura.md).
- [Manual general](.docs/manual-general.md): instalar, configurar y utilizar.
- [Manual detallado](.docs/manual-detallado.md): código, extensión y mantenimiento.
- [DTO, mapeo y contrato API](.docs/contrato-api.md).
- [Validación](.docs/validacion.md).

La `.docs` interna sí se versiona. La documentación académica externa, `.venv`, `.env`, SQLite y AGENTS.md quedan fuera; el `.gitignore` también protege archivos locales creados accidentalmente dentro.

La demo tiene acceso público y consume Countries GraphQL. Autenticación propia, consumo institucional de PIAR y GraphQL de entrada están documentados como evolución. PostgreSQL y SQL Server requieren validación con sus drivers y motores reales.
