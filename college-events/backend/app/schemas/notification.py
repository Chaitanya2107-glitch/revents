from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.notification import NotificationType
from app.schemas.common import Output


class NotificationOut(Output):
    id: UUID
    title: str
    message: str
    type: NotificationType
    is_read: bool
    created_at: datetime


class NotificationsRead(BaseModel):
    updated_count: int
    message: str
