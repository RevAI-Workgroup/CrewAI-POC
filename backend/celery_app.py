"""
Celery application configuration for async execution of CrewAI crews.
"""

import os
from celery import Celery
from celery.utils.log import get_task_logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create Celery instance
celery_app = Celery(
    "crewai_backend",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
    include=["services.async_execution_service"]
)

# Celery configuration
celery_app.conf.update(
    # Task execution settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task routing and queue settings
    task_routes={
        "services.async_execution_service.execute_crew_async": {"queue": "crew_execution"},
        "services.async_execution_service.cleanup_execution": {"queue": "cleanup"},
    },
    
    # Result settings
    result_expires=3600,  # Results expire after 1 hour
    result_extended=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    
    # Error handling
    task_reject_on_worker_lost=True,
    task_default_max_retries=3,
    task_default_retry_delay=60,
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)

# Task logger
logger = get_task_logger(__name__)

@celery_app.task(bind=True)
def health_check(self):
    """Health check task for Celery worker."""
    return {"status": "healthy", "worker_id": self.request.id}


if __name__ == "__main__":
    celery_app.start() 