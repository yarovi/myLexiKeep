# Implementacion tecnica y evolucion futura

## 1. Alcance y realidad del repositorio

Este documento describe exactamente lo que esta implementado. El repositorio contiene cuatro acciones serverless de Python destinadas a DigitalOcean Functions. **No contiene una aplicacion iOS**: no hay proyecto Xcode, Swift, SwiftUI/UIKit, persistencia local iOS, navegacion, modelos compartidos con iOS ni tests Xcode.

El Google Apps Script externo es un proveedor desconocido desde el repositorio. Solo se conoce su contrato observado por las respuestas que cada accion valida.

## 2. Arquitectura de implementacion

### Patrón de flujo

Cada handler sigue un pipeline imperativo:

```text
args
  -> validacion de entrada
  -> lectura de entorno
  -> construccion de payload o query
  -> solicitud HTTP a Google Apps Script
  -> parseo JSON
  -> validacion funcional
  -> validacion del contrato
  -> respuesta estructurada
```

No hay una infraestructura compartida reutilizable. Los cuatro archivos duplican intencionalmente validaciones y conversiones de excepciones, aunque mantienen una estructura consistente.

### Responsabilidades por accion

#### Crear nota

[`packages/default/savelanguagenote.py`](packages/default/savelanguagenote.py)

- valida `word`, `translations` y `gamy`;
- convierte elementos de `translations` con `str(item).strip()`;
- exige al menos una traduccion no vacia;
- utiliza `type(gamy) is int` para excluir bool y clases distintas de `int`;
- envia `POST` con JSON;
- exige `success is True`;
- valida los campos `id`, `date`, `word`, `translations`, `gamy`;
- devuelve `201` con el cuerpo upstream.

#### Listar notas

[`packages/default/listlanguagenotes.py`](packages/default/listlanguagenotes.py)

- transforma `page` y `pageSize` mediante `parse_positive_integer`;
- acepta `int` o cadena compuesta solo por digitos;
- rechaza cero, negativos, tipos inesperados y valores mayores que `9007199254740991`;
- por defecto usa `page=1` y `pageSize=20`;
- serializa parametros con `urllib.parse.urlencode`;
- ejecuta `GET`;
- valida:
  - estructura de `data`;
  - estructura de `pagination`;
  - tipo entero de `page`, `pageSize`, `totalItems` y `totalPages`;
  - coherencia de pagina y tamano;
  - numero total esperado de paginas;
  - numero esperado de registros;
  - contrato completo de cada registro.

Un registro valido exige:

- `id`: cadena no vacia;
- `date`: cadena con formato exacto `dd/mm/YYYY`;
- `word`: cadena no vacia;
- `translations`: lista no vacia de cadenas no vacias;
- `gamy`: entero exacto.

La validacion no transforma el resultado; solo comprueba el contenido recibido.

#### Actualizar nota

[`packages/default/updatelanguagenote.py`](packages/default/updatelanguagenote.py)

- valida `id`, `word`, `translations` y `gamy`;
- envia un objeto con `id`, `word`, `translations` y `gamy`;
- interpreta `NOT_FOUND` como `404`;
- interpreta `BAD_REQUEST` como `400`;
- valida que el `id` de la respuesta coincida con el solicitado;
- exige que `translations` sea una lista de cadenas;
- exige que `gamy` sea un entero exacto;
- devuelve `200`.

#### Eliminar nota

[`packages/default/deletelanguagenote.py`](packages/default/deletelanguagenote.py)

- valida un `id` string no vacio;
- envia `{"id": "<id>"}`;
- interpreta `NOT_FOUND` como `404`;
- interpreta `BAD_REQUEST` como `400`;
- valida que la respuesta tenga el mismo `id` y un `message` string;
- devuelve `200`.

## 3. Configuracion detallada

### Manifiesto serverless

[`project.yml`](project.yml) declara:

```yaml
packages:
  - name: default
    functions:
      - name: savelanguagenote
        runtime: python:3.11
        web: true
        environment:
          GOOGLE_SCRIPT_SAVE_URL: "${GOOGLE_SCRIPT_SAVE_URL}"
```

Las cuatro declaraciones presentan la misma forma. Las variables son:

- `GOOGLE_SCRIPT_SAVE_URL`
- `GOOGLE_SCRIPT_LIST_URL`
- `GOOGLE_SCRIPT_UPDATE_URL`
- `GOOGLE_SCRIPT_DELETE_URL`

El archivo [`config/.env.example`](config/.env.example) esta vacio. [`config/.env`](config/.env) existe localmente y esta excluido por Git. No debe abrirse ni registrarse en documentos publicos porque puede contener URLs privadas o credenciales codificadas.

### Sustitucion de entorno

DigitalOcean recibe `config/.env` mediante:

```bash
doctl serverless deploy . --env config/.env
```

El nombre de cada variable dentro de `project.yml` coincide con `os.environ.get(...)` en el handler correspondiente.

No existe un esquema de entornos. Para aislamiento por ambientes habria que desplegar namespaces/proyectos separados y mantener archivos `.env` separados; no hay implementacion actual.

### Transporte HTTP

Todos los metodos usan `urllib.request`, sin libreria HTTP externa.

- timeout: 20 segundos;
- JSON POST:
  - header `Content-Type: application/json`;
  - payload construido con `json.dumps(...).encode("utf-8")`;
- lista:
  - metodo `GET`;
  - header `Accept: application/json`;
  - parametros codificados con `urlencode`;
- no hay reintentos;
- no hay backoff;
- no hay pooling/caching propio;
- no hay autenticacion entre DigitalOcean y Google Apps Script;
- no se utilizan certificates pinning ni cliente de confianza personalizado.

La seguridad actual depende por completo de que las URLs upstream sean secretas o protegidas en el extremo. Los handlers validan solamente HTTPS.

## 4. Modelos y contratos

No hay dataclasses, Pydantic, TypedDict ni un esquema formal compartido. Los modelos son diccionarios y validaciones manuales.

### Entrada base

Crear:

```python
payload = {
    "word": word.strip(),
    "translations": normalized_translations,
    "gamy": gamy
}
```

Actualizar:

```python
payload = {
    "id": record_id.strip(),
    "word": word.strip(),
    "translations": normalized_translations,
    "gamy": gamy
}
```

Eliminar:

```python
payload = {
    "id": record_id.strip()
}
```

### Respuesta base

Todas las rutas usan:

```python
{
    "statusCode": <entero>,
    "body": <diccionario>
}
```

La lista upstream valida paginacion, pero las demas acciones tienen validaciones menores y no normalizan completamente los campos opcionales.

### Manejo de errores

Clases principales observadas:

- entrada: `400 BAD_REQUEST`;
- configuracion: `500 CONFIGURATION_ERROR`;
- Google Apps Script rechaza: `502 UPSTREAM_ERROR`;
- no encontrado: `404 NOT_FOUND`;
- respuesta JSON o tipo invalido: `502 INVALID_UPSTREAM_RESPONSE`;
- excepcion interna: `500 INTERNAL_SERVER_ERROR`.

Cada archivo contiene variantes propias. Por ejemplo, la lista distingue `BAD_REQUEST` de forma especial, mientras que guardar solo transforma cualquier rechazo distinto de `success is True` en `502`.

Las acciones registran en consola `[INFO]` y `[ERROR]`. No hay un logger estructurado, request ID, correlation ID ni reporting externo.

## 5. Persistencia y almacenamiento

No existe persistencia local en este repositorio. No hay:

- SQLite;
- CoreData;
- SwiftData;
- Redis;
- UserDefaults;
- Keychain;
- base de datos embebida;
- migraciones.

La persistencia queda fuera del repositorio y se delega a Google Apps Script. El esquema real de Google Sheets o del servicio, sus permisos y su logica no son verificables desde el codigo.

## 6. Concurrencia y consistencia

Las funciones son sincronas. Cada handler bloquea hasta obtener la respuesta upstream o alcanzar el timeout de 20 segundos. DigitalOcean puede ejecutar instancias concurrentes, pero no existe logica local de colas, trabajos de fondo, transacciones o controles de concurrencia.

No hay versionado de recursos, ETag, If-Match ni control optimista observado.

## 7. Metadatos de despliegue

[`./.deployed/versions.json`](./.deployed/versions.json) incluye:

- host `faas-nyc1-2ef2e6cc.doserverless.co`;
- namespace `fn-abf6a1c8-05af-4b3e-923c-1859895f3096`;
- versiones observadas de las acciones;
- digests de los paquetes desplegados.

El host y namespace son metadatos de infraestructura. Las versiones son descriptivas; no existe automatizacion que recorte o regenere este archivo.

## 8. Testing actual

No hay tests ni dependencias de testing. Los riesgos no estan cubiertos por:

- pruebas de validacion;
- mocks de `urllib`;
- pruebas de timeout;
- pruebas de paginacion;
- pruebas de contrato JSON;
- pruebas end-to-end;
- pruebas iOS.

La comprobacion disponible es sintactica:

```bash
python3 -m compileall -q packages
```

## 9. Como extender el proyecto

### 9.1 Agregar una nueva accion

1. Crear `packages/default/<nombreaccion>.py`.
2. Implementar `main(args)` y conservar el formato `{statusCode, body}`.
3. Agregar la accion a [`project.yml`](project.yml):

```yaml
- name: <nombreaccion>
  runtime: python:3.11
  web: true
  environment:
    GOOGLE_SCRIPT_<ACCION>_URL: "${GOOGLE_SCRIPT_<ACCION>_URL}"
```

4. Agregar la variable a `config/.env` local.
5. Actualizar `config/.env.example` con el nombre de la variable, sin valores reales.
6. Desplegar con `doctl serverless deploy . --env config/.env`.
7. Agregar pruebas antes de una accion compartida o endpoint externo.

La convencion actual usa nombres en minusculas sin separadores.

### 9.2 Agregar un endpoint con POST

Reutilizar la estructura existente:

```python
import json
import os
import urllib.request
import urllib.error

def main(args):
    endpoint = os.environ.get("GOOGLE_SCRIPT_<ACCION>_URL")
    if not endpoint or not endpoint.startswith("https://"):
        return {
            "statusCode": 500,
            "body": {
                "error": "CONFIGURATION_ERROR",
                "message": "GOOGLE_SCRIPT_<ACCION>_URL is not configured"
            }
        }

    payload = json.dumps(args).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        result = json.loads(response.read().decode("utf-8"))

    return {"statusCode": 200, "body": result}
```

Este ejemplo solo ilustra el patron; no sustituye la validacion actual ni el manejo completo de excepciones.

### 9.3 Modificar una accion existente

- agregar primero validaciones locales;
- normalizar entradas una sola vez;
- mantener `id` y campos identificadores sin cambios;
- validar `success` y todos los campos usados por clientes;
- extender las respuestas sin eliminar codigos usados por el cliente;
- evitar loggear datos sensibles;
- mantener timeout y conversiones HTTP consistentes;
- agregar una prueba por comportamiento cambiado.

### 9.4 Agregar persistencia distinta

No existe una abstraccion para persistencia. Si se reemplaza Google Apps Script:

1. extraer cliente HTTP compartido;
2. definir un protocolo/servicio Python con metodos CRUD;
3. validar respuestas en un adaptador dedicado;
4. ocultar detalles externos a los handlers;
5. agregar configuracion por proveedor;
6. mantener el contrato externo `{statusCode, body}`;
7. agregar reintentos y timeout configurable solo si hay una politica definida.

### 9.5 Agregar pruebas

No se debe introducir una dependencia sin necesidad. Para pruebas unitarias se puede usar `unittest` y `mock` de la biblioteca estandar. Mockear:

- `os.environ`;
- `urllib.request.urlopen`;
- respuestas HTTP;
- JSON valido, invalido y incompleto.

Agrupacion recomendada:

```text
tests/
  test_savelanguagenote.py
  test_listlanguagenotes.py
  test_updatelanguagenote.py
  test_deletelanguagenote.py
```

Comandos objetivo a establecer:

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q packages tests
```

## 10. Riesgos y mejoras recomendadas

### Prioridad alta

1. **No hay pruebas:** agregar tests unitarios antes de cambiar los contratos.
2. **Credenciales o URLs:** no compartir ni versionar `.env`; completar `.env.example` y documentar rotacion.
3. **Duplicacion:** extraer utilidades comunes para validar entornos, parsear JSON, convertir errores HTTP y construir respuestas.
4. **Dependencia del contrato upstream:** Google Apps Script no esta versionado ni documentado en el repositorio.
5. **Timeout fijo:** pasar el timeout a una configuracion por entorno si el proveedor requiere otra latencia.
6. **Sin autenticacion propia:** determinar si las acciones web requieren autenticacion/autorizacion independiente.
7. **Sin CORS explicado:** no se observa implementacion CORS. La compatibilidad con el cliente real debe verificarse en el gateway y no se puede asumir.

### Prioridad media

1. Unificar el manejo de `urllib.error.URLError`, timeout y `UnicodeDecodeError`.
2. Validar tambien tipos de traducciones en guardar y actualizar antes de convertir elementos con `str()`.
3. Revisar si `gamy` permite rangos o signos distintos de cualquier entero Python.
4. Introducir paginacion maxima para evitar cargas o costos excesivos.
5. Añadir `retry-after`, reintentos controlados y backoff solo con idempotencia definida.
6. Agregar logging estructurado sin exponer URLs ni payloads sensibles.
7. Versionar el contrato con una especificacion OpenAPI o JSON Schema.

### Prioridad baja

1. Añadir un archivo `requirements.txt` solo si aparecen dependencias externas; no es necesario ahora.
2. Separar utilidades de transporte HTTP de validacion de negocio.
3. Añadir scripts de despliegue o CI repetibles.
4. Congelar un proceso de actualizacion de `.deployed/versions.json`.

## 11. Recomendaciones de seguridad

- usar HTTPS y mantener las URLs de Google privadas;
- no registrar payloads completos si contienen notas personales;
- validar tamaños maximos de `word` y `translations`;
- limitar pagina y paginaSize si el proveedor no garantiza un limite interno;
- evitar respuestas detalladas que revelen infraestructura upstream;
- implementar autenticacion de cliente antes de exponer acciones a internet;
- agregar rate limiting en el gateway o en el proveedor;
- rotar URLs si son secretos accidentales.

## 12. Deuda tecnica visible

- no hay abstracciones compartidas;
- no hay pruebas;
- no hay CI;
- no hay esquema formal de datos;
- no hay persistencia verificable;
- no hay administracion de secretos formal;
- no hay observabilidad estructurada;
- no hay versionado de API;
- no hay entorno de staging documentado;
- no hay especificacion del cliente iOS ni codigo que pueda auditarse.
