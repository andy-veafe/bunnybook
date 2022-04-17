from asyncio import Queue, QueueFull, get_event_loop
from dataclasses import dataclass
from typing import List, Dict, Union, Set
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from injector import singleton, inject

from auth.models import User
from common.log import logger
from notification.models import Notification, NotificationData
from notification.service import NotificationService
from pubsub.websocket import WebSockets


class NewNotification:
    """通知的基础类，包含事件和数据，其他的通知需要继承这个类"""

    def __init__(self, event: str, payload: Dict):
        self.event = event
        self.payload = jsonable_encoder(payload)


@singleton
class NotificationManager:
    @dataclass
    class QueueItem:
        event: str
        payload: Dict
        recipients: List[UUID]

    @inject
    def __init__(self, ws: WebSockets, service: NotificationService):
        self._ws = ws
        self._service = service
        # 必须在FastAPI启动后，才能能创建消息队列
        self._notification_queue = None

    def start(self):
        self._notification_queue: Queue[NotificationManager.QueueItem] = Queue()
        get_event_loop().create_task(self._listen_for_notifications())

    def subscribe_to_on_connect(self):
        self._ws.subscribe_to_on_connect(self._on_ws_connect)

    def add_notification(
        self, notification: NewNotification, recipients: Union[List[UUID], Set[UUID]]
    ) -> None:
        """
        创建并发送新通知给指定的接收者，通知调度是非阻塞的，可以在任意时刻发送通知。
        notification: 要发送的通知
        recipients: 要接受新的的人员
        """
        if not recipients:
            return
        try:
            self._notification_queue.put_nowait(
                NotificationManager.QueueItem(
                    event=notification.event,
                    payload=notification.payload,
                    recipients=recipients,
                )
            )
        except QueueFull:
            logger.error("通知队列已满，通知将被丢弃")
            pass

    async def _on_ws_connect(self, sid: str, user: User):
        count = await self._service.count_unread_notifications_by_profile_id(user.id)
        await self._ws.send("unread_notifications_count", count, to=sid)

    async def _listen_for_notifications(self):
        """监听通知"""
        while True:
            notification = await self._notification_queue.get()
            for recipient in notification.recipients:
                try:
                    await self._service.create_notification(
                        Notification(
                            profile_id=recipient,
                            data=NotificationData(
                                event=notification.event, payload=notification.payload
                            ),
                        )
                    )
                    await self._ws.send(
                        event="new_unread_notification", payload=1, to=recipient
                    )
                except Exception as e:
                    logger.error("通知发送失败：%s", e)
