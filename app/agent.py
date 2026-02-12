from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from app.config import Settings
from app.meta_manager import FacebookManager, InstagramManager, MetaAPIError

logger = logging.getLogger(__name__)


@dataclass
class PublishingState:
    instagram_status: str = "neaktivní"
    facebook_status: str = "neaktivní"
    last_publish_at: datetime | None = None
    last_engagement_at: datetime | None = None
    engagement_24h: int = 0
    next_planned_post_at: datetime | None = None
    errors: list[str] = field(default_factory=list)


class MasterAgent:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.instagram = InstagramManager(settings.meta_access_token, settings.publish_timeout_s) if settings.meta_access_token else None
        self.facebook = FacebookManager(settings.meta_access_token, settings.publish_timeout_s) if settings.meta_access_token else None
        self.state = PublishingState(next_planned_post_at=self._next_publish_time())
        self._reply_history: list[datetime] = []

    def scan_trends(self) -> str:
        return "AI automatizace marketingu"

    def generate_content(self, trend: str) -> str:
        return f"Dnešní trend: {trend}. Přinášíme praktický tip pro růst účtu bez spam taktik."

    def collect_metrics(self) -> dict[str, int]:
        self.state.engagement_24h = len([ts for ts in self._reply_history if ts > datetime.now(timezone.utc) - timedelta(hours=24)])
        return {"engagement_24h": self.state.engagement_24h}

    def run_cycle(self) -> dict[str, str]:
        if not self.instagram or not self.facebook:
            self.state.errors.append("Meta token není nastavený")
            self.state.instagram_status = "neaktivní"
            self.state.facebook_status = "neaktivní"
            return {"instagram": "disabled", "facebook": "disabled"}

        trend = self.scan_trends()
        content = self.generate_content(trend)
        image_url = "https://picsum.photos/1080/1080"

        result = {"instagram": "skipped", "facebook": "skipped"}
        try:
            media_id = self.instagram.publish_post(self.settings.ig_user_id, image_url, content)
            self.state.instagram_status = "aktivní"
            result["instagram"] = media_id
        except MetaAPIError as exc:
            logger.exception("Instagram publish failed")
            self.state.instagram_status = "chyba"
            self.state.errors.append(str(exc))

        try:
            post_id = self.facebook.publish_post(self.settings.fb_page_id, content, image_url)
            self.state.facebook_status = "aktivní"
            result["facebook"] = post_id
        except MetaAPIError as exc:
            logger.exception("Facebook publish failed")
            self.state.facebook_status = "chyba"
            self.state.errors.append(str(exc))

        self.state.last_publish_at = datetime.now(timezone.utc)
        self.state.next_planned_post_at = self._next_publish_time()
        return result

    def engage_recent_comments(self, media_id: str) -> int:
        if not self.instagram:
            return 0

        comments = self.instagram.get_comments(media_id)
        replies_sent = 0

        for comment in comments:
            if self._daily_limit_reached():
                logger.info("Daily engagement limit reached")
                break

            comment_id = comment.get("id")
            if not comment_id:
                continue
            message = "Díky za komentář! 🙌"
            self.instagram.reply_to_comment(comment_id, message)
            replies_sent += 1
            self._reply_history.append(datetime.now(timezone.utc))
            time.sleep(random.uniform(self.settings.engagement_min_delay_s, self.settings.engagement_max_delay_s))

        if replies_sent:
            self.state.last_engagement_at = datetime.now(timezone.utc)
        return replies_sent

    def _daily_limit_reached(self) -> bool:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        recent = [ts for ts in self._reply_history if ts > cutoff]
        self._reply_history = recent
        return len(recent) >= self.settings.engagement_daily_limit

    @staticmethod
    def _next_publish_time() -> datetime:
        now = datetime.now(timezone.utc)
        return now.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)
