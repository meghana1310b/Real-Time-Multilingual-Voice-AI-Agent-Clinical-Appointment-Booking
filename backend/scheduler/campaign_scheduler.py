"""Outbound campaign scheduler for reminders and follow-ups."""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import structlog

logger = structlog.get_logger("campaign_scheduler")

_scheduler: BackgroundScheduler | None = None


def _run_reminder_campaign() -> None:
    logger.info("campaign_run", type="appointment_reminder")
    # In production: query DB for appointments tomorrow, initiate outbound calls
    # For now: stub
    pass


def _run_followup_campaign() -> None:
    logger.info("campaign_run", type="followup_checkup")
    pass


def start_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        return
    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        _run_reminder_campaign,
        IntervalTrigger(minutes=60),
        id="reminders",
    )
    _scheduler.add_job(
        _run_followup_campaign,
        IntervalTrigger(hours=24),
        id="followups",
    )
    _scheduler.start()
    logger.info("campaign_scheduler_started")


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("campaign_scheduler_stopped")
