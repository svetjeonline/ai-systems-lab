from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from pydantic import BaseModel

from app.agent import MasterAgent
from app.config import get_settings
from app.scheduler import build_scheduler


class PlatformStatusResponse(BaseModel):
    instagram_status: str
    facebook_status: str
    posledni_publikace: datetime | None
    engagement_24h: int
    dalsi_planovany_post: datetime | None
    chyby: list[str]


settings = get_settings()
agent = MasterAgent(settings)
scheduler = build_scheduler(agent)


@asynccontextmanager
async def lifespan(_: FastAPI):
    scheduler.start()
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)


app = FastAPI(title=settings.app_name, lifespan=lifespan)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "env": settings.app_env}


@app.post("/api/publish-now")
def publish_now() -> dict[str, str]:
    return agent.run_cycle()


@app.get("/api/platformy", response_model=PlatformStatusResponse)
def platformy() -> PlatformStatusResponse:
    metrics = agent.collect_metrics()
    state = agent.state
    return PlatformStatusResponse(
        instagram_status=state.instagram_status,
        facebook_status=state.facebook_status,
        posledni_publikace=state.last_publish_at,
        engagement_24h=metrics["engagement_24h"],
        dalsi_planovany_post=state.next_planned_post_at,
        chyby=state.errors[-10:],
    )
