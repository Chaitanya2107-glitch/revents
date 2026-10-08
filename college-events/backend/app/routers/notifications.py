from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import func, select, update

from app.dependencies import CurrentUser, Db
from app.errors import fail
from app.models import Notification
from app.schemas.common import Page, page_result
from app.schemas.notification import NotificationOut, NotificationsRead

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("", response_model=Page[NotificationOut])
def list_notifications(
    user: CurrentUser,
    db: Db,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    is_read: bool | None = None,
) -> dict:
    filters = [Notification.user_id == user.id]
    if is_read is not None:
        filters.append(Notification.is_read == is_read)
    total = db.scalar(select(func.count()).select_from(Notification).where(*filters)) or 0
    items = list(db.scalars(select(Notification).where(*filters)
        .order_by(Notification.created_at.desc(), Notification.id)
        .offset((page - 1) * page_size).limit(page_size)))
    return page_result(items, total, page, page_size)


@router.patch("/read-all", response_model=NotificationsRead)
def read_all_notifications(user: CurrentUser, db: Db) -> dict:
    result = db.execute(update(Notification).where(
        Notification.user_id == user.id, Notification.is_read.is_(False)
    ).values(is_read=True))
    return {"updated_count": result.rowcount, "message": "Notifications marked as read."}


@router.patch("/{notification_id}/read", response_model=NotificationOut)
def read_notification(notification_id: UUID, user: CurrentUser, db: Db) -> Notification:
    notification = db.scalar(select(Notification).where(
        Notification.id == notification_id, Notification.user_id == user.id
    ))
    if notification is None:
        fail(404, "NOTIFICATION_NOT_FOUND", "Notification not found.")
    notification.is_read = True
    db.flush()
    return notification
