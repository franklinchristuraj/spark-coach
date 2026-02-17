"""
APScheduler Configuration for SPARK Coach
Manages scheduled tasks: morning briefing, abandonment checks, weekly digest
"""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = AsyncIOScheduler()


async def run_morning_briefing():
    """
    Morning briefing job (07:00 daily)
    Note: This is called automatically, actual briefing is generated on-demand
    """
    try:
        logger.info(f"⏰ Morning briefing time check: {datetime.now()}")
        # The briefing is generated when user requests it via API
        # This job just logs that it's briefing time
        # In production, this would trigger a push notification
    except Exception as e:
        logger.error(f"Morning briefing job failed: {str(e)}")


async def run_abandonment_check():
    """
    Abandonment detection job (20:00 daily)
    Scans for stale resources and generates nudges
    """
    try:
        logger.info(f"🔍 Running scheduled abandonment check: {datetime.now()}")

        from agents.abandonment_detector import abandonment_detector_agent

        result = await abandonment_detector_agent.run()

        logger.info(f"✓ Abandonment check complete: {result['at_risk_count']} at-risk, {result['nudges_created']} nudges")

        # In production, this would trigger push notifications for nudges
        if result['nudges_created'] > 0:
            logger.info(f"📱 Would send {result['nudges_created']} push notifications")

    except Exception as e:
        logger.error(f"Abandonment check job failed: {str(e)}")


async def run_weekly_digest():
    """
    Weekly digest job (Sunday 18:00)
    Generates weekly learning summary
    """
    try:
        logger.info(f"📊 Running scheduled weekly digest: {datetime.now()}")
        # Placeholder for Day 5+ weekly digest agent
        logger.info("Weekly digest not yet implemented (Day 5+)")
    except Exception as e:
        logger.error(f"Weekly digest job failed: {str(e)}")


def setup_scheduler():
    """
    Configure all scheduled jobs

    Schedule:
    - Morning briefing: 07:00 daily
    - Abandonment check: 20:00 daily
    - Weekly digest: Sunday 18:00
    """
    # Morning briefing (07:00 daily)
    scheduler.add_job(
        run_morning_briefing,
        CronTrigger(hour=7, minute=0),
        id="morning_briefing",
        name="Morning Briefing Check",
        replace_existing=True
    )

    # Abandonment detection (20:00 daily)
    scheduler.add_job(
        run_abandonment_check,
        CronTrigger(hour=20, minute=0),
        id="abandonment_check",
        name="Abandonment Detection",
        replace_existing=True
    )

    # Weekly digest (Sunday 18:00)
    scheduler.add_job(
        run_weekly_digest,
        CronTrigger(day_of_week='sun', hour=18, minute=0),
        id="weekly_digest",
        name="Weekly Learning Digest",
        replace_existing=True
    )

    logger.info("✓ Scheduler configured with 3 jobs")


def start_scheduler():
    """Start the scheduler"""
    if not scheduler.running:
        scheduler.start()
        logger.info("✓ Scheduler started")

        # Log scheduled jobs
        jobs = scheduler.get_jobs()
        for job in jobs:
            logger.info(f"  📅 {job.name} - Next run: {job.next_run_time}")


def stop_scheduler():
    """Stop the scheduler"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("✓ Scheduler stopped")
