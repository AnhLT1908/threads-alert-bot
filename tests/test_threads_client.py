"""Test ThreadsClient voi respx (mock HTTP)."""

from datetime import datetime, timezone

import httpx
import pytest
import respx

from app.threads_client import (
    ThreadPost,
    ThreadsApiError,
    ThreadsClient,
    parse_iso_to_unix,
)

POST_JSON = {
    "id": "1234567890",
    "text": "Miễn phí AI course",
    "media_type": "TEXT_POST",
    "permalink": "https://www.threads.com/@user/post/abc",
    "timestamp": "2026-11-25T05:42:03+0000",
    "username": "user",
}


@respx.mock
async def test_keyword_search_returns_parsed_posts():
    route = respx.get("https://graph.threads.com/v1.0/keyword_search").mock(
        return_value=httpx.Response(200, json={"data": [POST_JSON]})
    )
    client = ThreadsClient("token")
    posts = await client.keyword_search("free", since_unix=123)

    assert len(posts) == 1
    post = posts[0]
    assert post.post_id == "1234567890"
    assert post.username == "user"
    assert post.permalink == "https://www.threads.com/@user/post/abc"

    params = route.calls[0].request.url.params
    assert params["q"] == "free"
    assert params["search_type"] == "RECENT"
    assert params["search_mode"] == "KEYWORD"
    assert params["since"] == "123"
    assert params["limit"] == "100"
    await client.aclose()


@respx.mock
async def test_keyword_search_without_since_omits_param():
    route = respx.get("https://graph.threads.com/v1.0/keyword_search").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    client = ThreadsClient("token")
    await client.keyword_search("free")
    assert "since" not in route.calls[0].request.url.params
    await client.aclose()


@respx.mock
async def test_skips_items_with_missing_id():
    respx.get("https://graph.threads.com/v1.0/keyword_search").mock(
        return_value=httpx.Response(
            200,
            json={"data": [POST_JSON, {"text": "thieu id"}]},
        )
    )
    client = ThreadsClient("token")
    posts = await client.keyword_search("free")
    assert len(posts) == 1
    assert posts[0].post_id == "1234567890"
    await client.aclose()


@respx.mock
async def test_http_error_raises_threads_api_error():
    respx.get("https://graph.threads.com/v1.0/keyword_search").mock(
        return_value=httpx.Response(500, json={"error": "server"})
    )
    client = ThreadsClient("token")
    with pytest.raises(ThreadsApiError):
        await client.keyword_search("free")
    await client.aclose()


@respx.mock
async def test_non_object_payload_raises_threads_api_error():
    respx.get("https://graph.threads.com/v1.0/keyword_search").mock(
        return_value=httpx.Response(200, json=[])
    )
    client = ThreadsClient("token")
    with pytest.raises(ThreadsApiError):
        await client.keyword_search("free")
    await client.aclose()


def test_parse_iso_to_unix_with_compact_offset():
    expected = int(
        datetime(2026, 11, 25, 5, 42, 3, tzinfo=timezone.utc).timestamp()
    )
    assert parse_iso_to_unix("2026-11-25T05:42:03+0000") == expected


def test_parse_iso_to_unix_with_colon_offset():
    expected = int(
        datetime(2026, 11, 25, 5, 42, 3, tzinfo=timezone.utc).timestamp()
    )
    assert parse_iso_to_unix("2026-11-25T05:42:03+00:00") == expected


def test_parse_iso_to_unix_invalid_returns_zero():
    assert parse_iso_to_unix("khong-phai-ngay") == 0
    assert parse_iso_to_unix("") == 0


def test_post_timestamp_unix_property():
    post = ThreadPost(
        post_id="1",
        text="",
        media_type="TEXT_POST",
        permalink="",
        timestamp="2026-11-25T05:42:03+0000",
        username="u",
    )
    expected = int(
        datetime(2026, 11, 25, 5, 42, 3, tzinfo=timezone.utc).timestamp()
    )
    assert post.timestamp_unix() == expected
