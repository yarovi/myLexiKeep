# myLexiKeep

## Descripcion general

`myLexiKeep` es el backend serverless de una aplicacion de notas de vocabulario. Expone cuatro funciones web que permiten:

- crear una palabra o expresion con sus traducciones;
- listar registros con paginacion;
- actualizar un registro existente;
- eliminar un registro.

El servidor actua como una capa HTTP/JSON controlada entre un cliente y Google Apps Script. Las funciones reciben argumentos, validan la entrada, realizan una solicitud HTTP al endpoint configurado y normalizan la respuesta en una estructura con `statusCode` y `body`.

**Estado real del repositorio:** no contiene una aplicacion iOS, proyecto Xcode, targets, Swift, frameworks UIKit/SwiftUI ni dependencias Swift. Por tanto, este README documenta el backend Python que existe en el repositorio; no se puede afirmar una version minima de iOS, un entorno Xcode, ni los detalles de una app cliente a partir del codigo disponible.

## Arquitectura y stack tecnologico

### Plataforma

- Python `3.11`
- DigitalOcean Serverless Functions
- Google Apps Script como proveedor externo persistente/API upstream
- CLI `doctl`

### Patron observado

El proyecto utiliza funciones independientes con responsabilidad unica. Cada accion tiene el siguiente flujo:

1. recibe un diccionario `args`;
2. valida campos requeridos y tipos basicos;
3. lee su URL upstream desde una variable de entorno;
4. construye una solicitud con `urllib`;
5. ejecuta la llamada con timeout de 20 segundos;
6. valida el contrato de respuesta esperado;
7. devuelve un objeto con `statusCode` y `body`.

No hay clases de dominio, controladores HTTP separados, ORM, modelos persistidos ni inyeccion de dependencias formal. No se observa una implementacion de Clean Architecture, MVVM, VIPER, TCA ni modularizacion iOS.

### Dependencias

No existe gestor de paquetes externo ni archivo de dependencias:

- no hay `requirements.txt` ni `pyproject.toml`;
- no hay `Package.swift`, `Podfile` ni `Cartfile`;
- no hay dependencias de terceros;
- las acciones usan exclusivamente la biblioteca estandar de Python: `json`, `os`, `re`, `urllib.request`, `urllib.error`, `urllib.parse`.

## Estructura del proyecto

```text
myLexiKeep/
├── project.yml
├── example_deploy.md
├── config/
│   ├── .env              # ignorado por Git; contiene secretos locales
│   └── .env.example      # actualmente existe pero esta vacio
├── packages/
│   └── default/
│       ├── savelanguagenote.py
│       ├── listlanguagenotes.py
│       ├── updatelanguagenote.py
│       └── deletelanguagenote.py
├── .deployed/
│   └── versions.json
└── .gitignore
```

### Responsabilidades

| Archivo | Accion | Metodo upstream | Entradas principales |
|---|---|---|---|
| [`packages/default/savelanguagenote.py`](packages/default/savelanguagenote.py) | `savelanguagenote` | `POST` | `word`, `translations`, `gamy` |
| [`packages/default/listlanguagenotes.py`](packages/default/listlanguagenotes.py) | `listlanguagenotes` | `GET` | `page`, `pageSize` |
| [`packages/default/updatelanguagenote.py`](packages/default/updatelanguagenote.py) | `updatelanguagenote` | `POST` | `id`, `word`, `translations`, `gamy` |
| [`packages/default/deletelanguagenote.py`](packages/default/deletelanguagenote.py) | `deletelanguagenote` | `POST` | `id` |

`project.yml` declara las cuatro acciones, habilita el acceso web y conecta las URLs upstream mediante variables de entorno.

## Requisitos previos

Para desarrollar y desplegar se necesitan:

- Python 3.11;
- `doctl` autenticado con una cuenta de DigitalOcean;
- acceso a los cuatro endpoints de Google Apps Script;
- opcionalmente `curl` para probar acciones desplegadas.

No se requiere Xcode ni macOS para este backend segun la configuracion actual.

## Puesta en marcha

### 1. Clonar y entrar al repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd myLexiKeep
```

La URL de clonacion no esta registrada en el codigo.

### 2. Crear la configuracion local

Crear `config/.env` con las cuatro variables usadas por `project.yml`:

```dotenv
GOOGLE_SCRIPT_SAVE_URL=https://...
GOOGLE_SCRIPT_LIST_URL=https://...
GOOGLE_SCRIPT_UPDATE_URL=https://...
GOOGLE_SCRIPT_DELETE_URL=https://...
```

`config/.env` esta excluido por `.gitignore`. Todas las URLs deben usar HTTPS; el codigo rechaza cualquier valor que no comience con `https://`.

El archivo `config/.env.example` existe pero no contiene claves ni valores de ejemplo, por lo que esta documentacion es la unica fuente basada en el codigo.

### 3. Validar Python

El repositorio no tiene entorno virtual ni comando de dependencias. Se puede realizar al menos una comprobacion sintactica sin instalar paquetes:

```bash
python3 -m compileall -q packages
```

### 4. Desplegar

Ejemplo del repositorio:

```bash
doctl serverless deploy . \
  --env config/.env \
  --include default/deletelanguagenote
```

`--include` limita el despliegue a una accion. Para desplegar todas las acciones definidas:

```bash
doctl serverless deploy . --env config/.env
```

No se incluyen scripts de CI/CD ni workflow de GitHub Actions.

## Configuracion y entornos

### `project.yml`

Cada accion declara:

- paquete `default`;
- runtime `python:3.11`;
- acceso web mediante `web: true`;
- una variable de entorno interpolada desde el `.env`.

No existen esquemas separados de Debug, Staging o Release, ni `.xcconfig`, `Info.plist`, entitlements, capabilities o flags de compilacion iOS.

### Despliegue desplegado

`.deployed/versions.json` registra metadatos locales del ultimo despliegue observado:

- API host;
- namespace;
- versiones/digests de las cuatro acciones.

Este archivo no contiene secretos ni debe interpretarse como un manifiesto necesario para construir el proyecto.

## Contratos de las funciones

Todos los handlers devuelven diccionarios con la forma:

```json
{
  "statusCode": 200,
  "body": {}
}
```

### Crear

```text
POST savelanguagenote
```

Argumentos:

```json
{
  "word": "Hello",
  "translations": ["Hola"],
  "gamy": 1
}
```

Respuestas relevantes: `201`, `400`, `500`, `502`.

### Listar

```text
GET listlanguagenotes
```

Argumentos opcionales:

```json
{
  "page": 1,
  "pageSize": 20
}
```

- `page` acepta enteros positivos expresados como `int` o cadena numerica;
- `pageSize` usa las mismas reglas;
- el limite superior es `9007199254740991`;
- si no se proporcionan, usa `1` y `20`;
- respuesta exitosa: `200`.

### Actualizar

```text
POST updatelanguagenote
```

Argumentos:

```json
{
  "id": "record-id",
  "word": "Hello",
  "translations": ["Hola"],
  "gamy": 1
}
```

Respuestas relevantes: `200`, `400`, `404`, `500`, `502`.

### Eliminar

```text
POST deletelanguagenote
```

Argumentos:

```json
{
  "id": "record-id"
}
```

Respuestas relevantes: `200`, `400`, `404`, `500`, `502`.

## Funcionalidades implementadas

- CRUD completo de recursos de vocabulario a nivel de proxy.
- Validacion de tipos, cadenas vacias y traducciones normalizadas.
- Validacion especifica de paginacion y contratos upstream.
- Timeout HTTP fijo de 20 segundos.
- Transformacion de errores HTTP, JSON invalido y fallos internos a respuestas estructuradas.
- Diferenciacion de `NOT_FOUND` y `BAD_REQUEST` para actualizar y eliminar.
- Configuracion externa de endpoints mediante variables de entorno.

Las validaciones, respuestas y persistencia del Google Apps Script upstream no estan implementadas en este repositorio y no pueden verificarse desde aqui.

## Testing

No existen pruebas unitarias, pruebas de integracion, fixtures, mocks ni configuracion de un framework de testing. No hay un directorio `tests/` ni comandos automatizados.

La unica comprobacion automatizable sin dependencias es:

```bash
python3 -m compileall -q packages
```

Antes de considerar el proyecto listo para produccion, conviene agregar pruebas para validacion de entrada, contratos upstream, paginacion, errores HTTP, timeout y respuestas malformadas.
