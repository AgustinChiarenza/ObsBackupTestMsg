import os
from datetime import datetime, timezone

from obs import ObsClient
from huaweicloudsdkcore.auth.credentials import BasicCredentials
from huaweicloudsdksmn.v2 import SmnClient, PublishMessageRequest, PublishMessageRequestBody
from huaweicloudsdksmn.v2.region.smn_region import SmnRegion

try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None


def env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Falta variable de entorno: {name}")
    return value


def parse_date(value):
    if isinstance(value, datetime):
        dt = value
    else:
        raw = str(value).strip()
        formats = [
            "%Y/%m/%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%a, %d %b %Y %H:%M:%S GMT",
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(raw, fmt)
                break
            except ValueError:
                dt = None

        if dt is None:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))

    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def has_backup_today():
    ak = env("CLOUD_SDK_AK")
    sk = env("CLOUD_SDK_SK")
    bucket = env("BUCKET_NAME")

    region = os.getenv("REGION", "la-south-2")
    endpoint = os.getenv("OBS_ENDPOINT", f"https://obs.{region}.myhuaweicloud.com")
    prefix = os.getenv("PREFIX", "")
    local_tz = ZoneInfo(os.getenv("LOCAL_TZ", "America/Santiago")) if ZoneInfo else timezone.utc
    today = datetime.now(local_tz).date()

    obs = ObsClient(access_key_id=ak, secret_access_key=sk, server=endpoint)

    marker = None
    checked = 0

    while True:
        resp = obs.listObjects(bucket, prefix or None, marker, 1000)

        if resp.status >= 300:
            raise RuntimeError(f"OBS error: {resp.status} - {resp.errorCode} - {resp.errorMessage}")

        objects = resp.body.contents or []

        for obj in objects:
            checked += 1

            if obj.key.endswith("/") and getattr(obj, "size", 0) == 0:
                continue

            obj_date = parse_date(obj.lastModified).astimezone(local_tz).date()

            if obj_date == today:
                return True, checked, obj.key

        if not getattr(resp.body, "is_truncated", False):
            return False, checked, None

        marker = getattr(resp.body, "next_marker", None) or (objects[-1].key if objects else None)


def publish_alert():
    ak = env("CLOUD_SDK_AK")
    sk = env("CLOUD_SDK_SK")
    project_id = env("PROJECT_ID")
    topic_urn = env("TOPIC_URN")

    region = os.getenv("REGION", "la-south-2")
    smn_endpoint = os.getenv("SMN_ENDPOINT")

    credentials = BasicCredentials(ak, sk, project_id)

    builder = SmnClient.new_builder().with_credentials(credentials)

    if smn_endpoint:
        builder = builder.with_endpoint(smn_endpoint)
    else:
        builder = builder.with_region(SmnRegion.value_of(region))

    client = builder.build()

    request = PublishMessageRequest()
    request.topic_urn = topic_urn
    request.body = PublishMessageRequestBody(
        subject="Alerta backup OBS",
        message="No se hizo backup",
        time_to_live="3600"
    )

    return client.publish_message(request).to_dict()


def handler(event, context):
    found, checked, object_key = has_backup_today()

    if found:
        return {
            "status": "OK",
            "message": "Se encontró backup de hoy.",
            "checked_count": checked,
            "object": object_key
        }

    response = publish_alert()

    return {
        "status": "ALERT_SENT",
        "message": "No se hizo backup",
        "checked_count": checked,
        "smn_response": response
    }
