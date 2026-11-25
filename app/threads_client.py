"""Client goi Threads Graph API (keyword search)."""

import logging
from dataclasses import dataclass
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)

THREADS_GRAPH_BASE = "https://graph.threads.com/v1.0"
SEARCH_FIELDS = (
    "id,text,media_type,permalink,timestamp,username,"
    "has_replies,is_quote_post,is_reply"
)
DEFAULT_TIMEOUT_SECONDS = 30.0


class ThreadsApiError(RuntimeError):
    """Loi khi goi Threads Graph API (HTTP loi, response sai khuon dang...)."""


@dataclass(frozen=True, slots=True)
class ThreadPost:
    """Bai viet tra ve tu keyword_search."""

    post_id: str
    text: str
    media_type: str
    permalink: str
    timestamp: str
    username: str

    def timestamp_unix(self) -> int:
        """Unix timestamp (giay) cua bai viet, 0 neu khong parse duoc."""
        return parse_iso_to_unix(self.timestamp)


def parse_iso_to_unix(iso: str) -> int:
    """Parse chuoi ISO 8601 sang Unix timestamp (giay).

    Threads tra ve dang "2023-10-17T05:42:03+0000" (offset khong dau
    hai cham). Thu fromisoformat truoc, fallback chuan hoa offset.
    Tra ve 0 neu khong parse duoc (khong lam chet pipeline).
    """
    candidate = iso.strip()
    variants = [candidate]
    if candidate.endswith("+0000"):
        variants.append(candidate[:-5] + "+00:00")

    for value in variants:
        try:
            return int(datetime.fromisoformat(value).timestamp())
        except ValueError:
            continue

    logger.warning("Khong parse duoc timestamp: %r", iso)
    return 0


class ThreadsClient:
    """Goi Threads Graph API.

    Neu khong truyen `client`, tu tao httpx.AsyncClient voi base_url
    graph.threads.com va header Authorization (Bearer token). Co the
    inject client tuy chinh (VD httpx.MockTransport trong test).
    """

    def __init__(
        self,
        access_token: str,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            base_url=THREADS_GRAPH_BASE,
            timeout=DEFAULT_TIMEOUT_SECONDS,
            headers={"Authorization": f"Bearer {access_token}"},
        )

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def keyword_search(
        self,
        keyword: str,
        since_unix: int | None = None,
        limit: int = 100,
        search_type: str = "RECENT",
    ) -> list[ThreadPost]:
        """Tim bai viet cong khai theo tu khoa.

        Raises:
            ThreadsApiError: HTTP loi hoac response sai khuon dang.
        """
        params: dict[str, object] = {
            "q": keyword,
            "search_type": search_type,
            "search_mode": "KEYWORD",
            "fields": SEARCH_FIELDS,
            "limit": limit,
        }
        if since_unix is not None:
            params["since"] = since_unix

        try:
            response = await self._client.get("/keyword_search", params=params)
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            raise ThreadsApiError(
                f"HTTP loi khi search {keyword!r}: {exc}"
            ) from exc
        except ValueError as exc:
            raise ThreadsApiError(
                f"Response khong phai JSON khi search {keyword!r}: {exc}"
            ) from exc

        if not isinstance(payload, dict):
            raise ThreadsApiError(
                f"Response sai khuon dang khi search {keyword!r}"
            )

        posts: list[ThreadPost] = []
        for item in payload.get("data") or []:
            try:
                posts.append(self._parse_post(item))
            except (KeyError, TypeError) as exc:
                logger.warning("Bo qua bai viet sai khuon dang: %s", exc)
        return posts

    @staticmethod
    def _parse_post(item: dict) -> ThreadPost:
        return ThreadPost(
            post_id=str(item["id"]),
            text=str(item.get("text") or ""),
            media_type=str(item.get("media_type") or ""),
            permalink=str(item.get("permalink") or ""),
            timestamp=str(item.get("timestamp") or ""),
            username=str(item.get("username") or ""),
        )
