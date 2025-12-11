import ssl
from datetime import date
from typing import Any, Dict, List

import aiohttp
import certifi
from aiohttp import BasicAuth

from app.config import Config


class HseApiClient:
    def __init__(self, config: Config):
        self._base_url = config.api.base_url
        self._auth = BasicAuth(config.api.user, config.api.password)
        self._ssl_context = ssl.create_default_context(cafile=certifi.where())

    async def get_channel_stats(self, for_date: date) -> List[Dict[str, Any]]:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                self._base_url,
                params={"date": for_date.isoformat()},
                auth=self._auth,
                ssl=self._ssl_context,
            ) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"API error: HTTP {resp.status}")
                return await resp.json()
