from apscheduler.schedulers.background import BackgroundScheduler

from app.agent import MasterAgent


def build_scheduler(agent: MasterAgent) -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(agent.run_cycle, "cron", hour=9, minute=0, id="publish-daily", replace_existing=True)
    scheduler.add_job(agent.collect_metrics, "interval", hours=2, id="metrics-2h", replace_existing=True)
    return scheduler
