import os
import sys
import logging
import atexit
from django.conf import settings
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django_apscheduler.jobstores import DjangoJobStore, register_events
from django.core.management import call_command
from django.db import connection

logger = logging.getLogger(__name__)

_scheduler = None

def check_deadlines_job(project_id=None):
    try:
        if project_id:
            call_command("check_deadlines", project_id=project_id)
        else:
            call_command("check_deadlines")
    except Exception as e:
        logger.error(f"Scheduler job error (Project {project_id}): {e}")

def start():
    global _scheduler
    if os.environ.get('RUN_MAIN') != 'true' and settings.DEBUG:
        return
    if 'runserver' not in sys.argv and not os.environ.get('SERVER_SOFTWARE'):
        return
    
    if _scheduler and _scheduler.running:
        return

    # PRE-FLIGHT CHECK: Ensure the project table and scheduler columns exist
    # This prevents the app from crashing during migrations or fresh installs.
    try:
        with connection.cursor() as cursor:
            cursor.execute("SHOW COLUMNS FROM authentication_project LIKE 'scheduler_hour'")
            if not cursor.fetchone():
                logger.warning("Scheduler startup skipped: 'scheduler_hour' column not found yet.")
                return
    except Exception:
        logger.warning("Scheduler startup skipped: Database/Project table not accessible yet.")
        return

    _scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE)
    _scheduler.add_jobstore(DjangoJobStore(), "default")
    
    # Register jobs for each project
    from authentication.models import Project
    projects = Project.objects.all()
    
    for project in projects:
        job_id = f"check_deadlines_project_{project.id}"
        _scheduler.add_job(
            check_deadlines_job,
            trigger=CronTrigger(hour=project.scheduler_hour, minute=project.scheduler_minute),
            id=job_id,
            args=[project.id],
            max_instances=1,
            replace_existing=True,
            coalesce=True,
        )
        logger.info(f"Scheduled scan for project '{project.name}' at {project.scheduler_hour:02d}:{project.scheduler_minute:02d}")

    register_events(_scheduler)
    try:
        _scheduler.start()
        logger.info(f"Background Scheduler started (Timezone: {settings.TIME_ZONE})")
    except Exception as e:
        logger.error(f"Scheduler start error: {e}")
        _scheduler.shutdown()
    atexit.register(lambda: _scheduler.shutdown() if _scheduler else None)

def restart():
    global _scheduler
    if not _scheduler:
        start()
        return

    from authentication.models import Project
    try:
        projects = Project.objects.all()
        
        # Remove existing project jobs
        for job in _scheduler.get_jobs():
            if job.id.startswith("check_deadlines_project_"):
                _scheduler.remove_job(job.id)

        # Add fresh jobs
        for project in projects:
            job_id = f"check_deadlines_project_{project.id}"
            _scheduler.add_job(
                check_deadlines_job,
                trigger=CronTrigger(hour=project.scheduler_hour, minute=project.scheduler_minute),
                id=job_id,
                args=[project.id],
                max_instances=1,
                replace_existing=True,
                coalesce=True,
            )
            logger.info(f"Rescheduled project '{project.name}' to {project.scheduler_hour:02d}:{project.scheduler_minute:02d}")
    except Exception as e:
        logger.error(f"Error rescheduling jobs: {e}")
