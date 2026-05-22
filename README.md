# FunctionGraph OBS Backup Checker

Este proyecto ejecuta una función en **Huawei Cloud FunctionGraph** para validar si un bucket de **OBS** recibió archivos de backup durante el día actual.

Si la función no encuentra objetos creados o modificados en el día, publica una alerta en **SMN** con el mensaje:

```text
No se hizo backup
```

## Flujo de funcionamiento

```text
Timer Trigger en FunctionGraph
        ↓
Función Python
        ↓
Lista objetos del bucket OBS
        ↓
Compara LastModified contra la fecha actual
        ↓
¿Hay objetos modificados hoy?
        ↓
Sí → finaliza sin enviar alerta
No → publica mensaje en SMN
```

## Servicios utilizados

- **FunctionGraph**: ejecuta la lógica serverless.
- **OBS**: bucket donde se almacenan los backups.
- **SMN**: servicio usado para enviar la alerta.
- **API Explorer / SDK Huawei Cloud**: referencia para probar las APIs de OBS y SMN.

## Variables de entorno requeridas

Configurar estas variables en FunctionGraph:

```env
REGION= la-south-2
OBS_ENDPOINT= obs.la-south-2.myhuaweicloud.com
SMN_ENDPOINT= smn.la-south-2.myhuaweicloud.com

PROJECT_ID= <project_id>
BUCKET_NAME= <nombre_del_bucket>
TOPIC_URN= <topic_urn_de_smn>

CLOUD_SDK_AK= <access_key>
CLOUD_SDK_SK= <secret_key>

LOCAL_TZ= America/Santiago
PREFIX=
```

### Descripción de variables

| Variable | Descripción |
|---|---|
| `REGION` | Región de Huawei Cloud. Ejemplo: `la-south-2`. |
| `OBS_ENDPOINT` | Endpoint regional de OBS. |
| `SMN_ENDPOINT` | Endpoint regional de SMN. |
| `PROJECT_ID` | Project ID de Huawei Cloud. |
| `BUCKET_NAME` | Nombre del bucket OBS donde se guardan los backups. |
| `TOPIC_URN` | URN del topic SMN donde se publicará la alerta. |
| `CLOUD_SDK_AK` | Access Key usada por el SDK. |
| `CLOUD_SDK_SK` | Secret Key usada por el SDK. |
| `LOCAL_TZ` | Zona horaria usada para comparar si el backup corresponde al día actual. |
| `PREFIX` | Prefijo opcional dentro del bucket, por ejemplo `backups/`. |

## Recomendación sobre `PREFIX`

Si los backups se guardan siempre dentro de una carpeta o ruta específica, conviene usar `PREFIX`.

Ejemplo:

```env
PREFIX=backups/
```

Esto evita listar objetos innecesarios y reduce el tiempo de ejecución de la función.

## Permisos necesarios

La credencial utilizada por la función debe tener permisos para:

- Listar objetos del bucket OBS.
- Publicar mensajes en el topic SMN.

Permisos mínimos esperados:

```text
OBS: ListBucket
SMN: PublishMessage
```
