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

## Estructura esperada

```text
.
├── index.py
├── requirements.txt
└── README.md
```

## Dependencias

El archivo `requirements.txt` debe contener:

```txt
esdk-obs-python
huaweicloudsdkcore
huaweicloudsdksmn
```

Para instalar las dependencias localmente y armar el ZIP:

```bash
mkdir fg-backup-check
cd fg-backup-check

# Copiar index.py dentro de esta carpeta

cat > requirements.txt <<EOF
esdk-obs-python
huaweicloudsdkcore
huaweicloudsdksmn
EOF

pip3 install -r requirements.txt -t .
zip -r fg-backup-check.zip .
```

Luego se sube `fg-backup-check.zip` a FunctionGraph.

## Handler

En FunctionGraph configurar el handler como:

```text
index.handler
```

## Variables de entorno requeridas

Configurar estas variables en FunctionGraph:

```env
REGION=la-south-2
OBS_ENDPOINT=https://obs.la-south-2.myhuaweicloud.com
SMN_ENDPOINT=https://smn.la-south-2.myhuaweicloud.com

PROJECT_ID=<project_id>
BUCKET_NAME=<nombre_del_bucket>
TOPIC_URN=<topic_urn_de_smn>

CLOUD_SDK_AK=<access_key>
CLOUD_SDK_SK=<secret_key>

LOCAL_TZ=America/Santiago
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

## Ejecución programada

Crear un **Timer Trigger** en FunctionGraph para ejecutar la función todos los días después de la ventana esperada de backup.

Ejemplo:

```text
Todos los días a las 08:00 o 09:00
```

La hora exacta depende de cuándo debería haber finalizado el proceso de backup.

## Respuesta esperada

### Caso 1: existe backup del día

```json
{
  "status": "OK",
  "message": "Se encontró backup de hoy.",
  "checked_count": 10,
  "object": "backups/archivo.bak"
}
```

### Caso 2: no existe backup del día

```json
{
  "status": "ALERT_SENT",
  "message": "No se hizo backup",
  "checked_count": 10,
  "smn_response": {}
}
```

## Pruebas recomendadas

1. Crear o subir manualmente un archivo al bucket OBS.
2. Ejecutar la función desde **Debug** en FunctionGraph.
3. Validar que la función devuelva `status: OK`.
4. Borrar el archivo o probar con un bucket sin archivos modificados en el día.
5. Ejecutar nuevamente la función.
6. Validar que publique el mensaje en SMN.

## Consideraciones

- La función compara la fecha `LastModified` de los objetos contra la fecha actual en la zona horaria definida en `LOCAL_TZ`.
- Si el bucket tiene más de 1000 objetos, la función pagina usando `marker`.
- Si encuentra un objeto modificado hoy, deja de seguir listando para reducir tiempo de ejecución.
- Si no encuentra objetos del día, envía la alerta mediante SMN.

## Mensaje de alerta

El mensaje enviado a SMN es:

```text
No se hizo backup
```
