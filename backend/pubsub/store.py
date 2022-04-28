import datetime as dt
from typing import Union, List
from uuid import UUID

from injector import singleton, inject

from common.injection import PubSubStore
from common.schemas import dt_to_iso8601z


@singleton
class WebSocketsStore:
    ONLINE_STATUS_EX: int = int(dt.timedelta(seconds=11).total_seconds())

    @inject
    def __init__(self, store: PubSubStore):
        self._store = store

    async def renew_online_status(self, profile_id: Union[str, UUID]):
        """刷新用户的在线状态。"""
        await self._store.set(
            f"websockets:{profile_id}",
            dt_to_iso8601z(dt.datetime.now(dt.timezone.utc)),
            expire=WebSocketsStore.ONLINE_STATUS_EX,
        )

    async def get_online_statuses(
        self, profile_ids: List[Union[str, UUID]]
    ) -> List[str]:
        """返回在线的用户ID列表。"""
        if not profile_ids:
            return []
        result = await self._store.mget(
            *[f"websockets:{profile_id}" for profile_id in profile_ids]
        )
        return [
            str(friend_id)
            for friend_id, is_online in zip(profile_ids, result)
            if is_online
        ]
