from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, field_serializer


def serialize_datetime_utc(value: datetime) -> str:
    """Serializa datetime em ISO-8601 no fuso UTC."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)
    return value.isoformat().replace("+00:00", "Z")


class AppResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    @field_serializer("*", when_used="json")
    def serialize_datetime_fields(self, value):
        if isinstance(value, datetime):
            return serialize_datetime_utc(value)
        return value