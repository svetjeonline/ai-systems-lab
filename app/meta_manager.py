from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests


class MetaAPIError(RuntimeError):
    """Raised when Meta Graph API returns an error response."""


@dataclass
class MetaResponse:
    endpoint: str
    payload: dict[str, Any]


class MetaPlatformManager:
    """Unified manager for Meta Graph API interactions."""

    base_url = "https://graph.facebook.com/v18.0"

    def __init__(self, access_token: str, timeout_s: int = 15):
        if not access_token:
            raise ValueError("META access token is required")
        self.access_token = access_token
        self.timeout_s = timeout_s

    def _post(self, endpoint: str, payload: dict[str, Any]) -> MetaResponse:
        url = f"{self.base_url}/{endpoint}"
        data = {**payload, "access_token": self.access_token}
        response = requests.post(url, data=data, timeout=self.timeout_s)
        body = response.json()
        if not response.ok or body.get("error"):
            raise MetaAPIError(f"POST {url} failed: {body}")
        return MetaResponse(endpoint=endpoint, payload=body)

    def _get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.base_url}/{endpoint}"
        merged = {"access_token": self.access_token}
        if params:
            merged.update(params)
        response = requests.get(url, params=merged, timeout=self.timeout_s)
        body = response.json()
        if not response.ok or body.get("error"):
            raise MetaAPIError(f"GET {url} failed: {body}")
        return body


class InstagramManager(MetaPlatformManager):
    def publish_post(self, ig_user_id: str, image_url: str, caption: str) -> str:
        container = self._post(
            f"{ig_user_id}/media",
            {
                "image_url": image_url,
                "caption": caption,
            },
        )
        container_id = container.payload.get("id")
        if not container_id:
            raise MetaAPIError("Instagram media container ID missing")

        publish = self._post(
            f"{ig_user_id}/media_publish",
            {
                "creation_id": container_id,
            },
        )
        media_id = publish.payload.get("id")
        if not media_id:
            raise MetaAPIError("Instagram published media ID missing")
        return media_id

    def get_comments(self, media_id: str) -> list[dict[str, Any]]:
        response = self._get(f"{media_id}/comments")
        return response.get("data", [])

    def reply_to_comment(self, comment_id: str, message: str) -> str:
        result = self._post(f"{comment_id}/replies", {"message": message})
        reply_id = result.payload.get("id")
        if not reply_id:
            raise MetaAPIError("Instagram comment reply ID missing")
        return reply_id


class FacebookManager(MetaPlatformManager):
    def publish_post(self, page_id: str, message: str, image_url: str | None = None) -> str:
        if image_url:
            endpoint = f"{page_id}/photos"
            payload = {"message": message, "url": image_url}
        else:
            endpoint = f"{page_id}/feed"
            payload = {"message": message}

        result = self._post(endpoint, payload)
        post_id = result.payload.get("post_id") or result.payload.get("id")
        if not post_id:
            raise MetaAPIError("Facebook post ID missing")
        return post_id
