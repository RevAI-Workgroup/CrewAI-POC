"""
Async execution service for CrewAI crews using Celery.
"""

import json
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import UUID

try:
    from celery import current_task
    from celery.utils.log import get_task_logger
    CELERY_AVAILABLE = True
except ImportError:
    # Fallback for development without Celery installed
    def get_task_logger(name): 
        import logging
        return logging.getLogger(name)
    current_task = None
    CELERY_AVAILABLE = False

from sqlalchemy.orm import Session

from models.execution import Execution, ExecutionStatus
from models.graph import Graph
from services.graph_translation import GraphTranslationService
from db_config import SessionLocal

logger = get_task_logger(__name__)

# Only import celery_app if Celery is available
if CELERY_AVAILABLE:
    try:
        from celery_app import celery_app
    except ImportError:
        CELERY_AVAILABLE = False
        celery_app = None
else:
    celery_app = None


class AsyncExecutionService:
    """Service for managing async execution of CrewAI crews."""
    
    @staticmethod
    def queue_execution(
        graph_id: UUID,
        thread_id: UUID,
        user_id: UUID,
        inputs: Dict[str, Any],
        priority: int = 5
    ) -> str:
        """Queue a crew execution task."""
        if not CELERY_AVAILABLE or celery_app is None:
            raise RuntimeError("Celery is not available")
            
        try:
            task = execute_crew_async.apply_async(
                args=[str(graph_id), str(thread_id), str(user_id), inputs],
                priority=priority,
                queue="crew_execution"
            )
            logger.info(f"Queued crew execution task {task.id} for graph {graph_id}")
            return task.id
        except Exception as e:
            logger.error(f"Failed to queue execution: {e}")
            raise
    
    @staticmethod
    def get_task_status(task_id: str) -> Dict[str, Any]:
        """Get status of a Celery task."""
        if not CELERY_AVAILABLE or celery_app is None:
            return {"task_id": task_id, "status": "UNAVAILABLE", "error": "Celery not available"}
            
        try:
            result = celery_app.AsyncResult(task_id)
            return {
                "task_id": task_id,
                "status": result.status,
                "result": result.result if result.ready() else None,
                "traceback": result.traceback if result.failed() else None,
                "date_done": result.date_done.isoformat() if result.date_done else None
            }
        except Exception as e:
            logger.error(f"Failed to get task status: {e}")
            return {"task_id": task_id, "status": "UNKNOWN", "error": str(e)}
    
    @staticmethod
    def cancel_task(task_id: str) -> bool:
        """Cancel a running task."""
        if not CELERY_AVAILABLE or celery_app is None:
            logger.warning("Cannot cancel task: Celery not available")
            return False
            
        try:
            celery_app.control.revoke(task_id, terminate=True)
            logger.info(f"Cancelled task {task_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {e}")
            return False


def _execute_crew_logic(
    task_context,
    graph_id: str,
    thread_id: str,
    user_id: str,
    inputs: Dict[str, Any]
) -> Dict[str, Any]:
    """Core logic for executing a CrewAI crew (separated for testing)."""
    execution_id = None
    db = None
    
    try:
        # Get database session
        db = SessionLocal()
        
        # Create execution entry
        execution_log = Execution(
            graph_id=UUID(graph_id),
            trigger_message_id=None,
            status=ExecutionStatus.RUNNING,
            execution_config={"inputs": inputs, "task_id": getattr(task_context.request, 'id', 'unknown') if hasattr(task_context, 'request') else 'unknown'}
        )
        execution_log.start_execution()
        db.add(execution_log)
        db.commit()
        execution_id = execution_log.id
        
        logger.info(f"Starting crew execution {execution_id} for graph {graph_id}")
        
        # Update task progress
        if hasattr(task_context, 'update_state'):
            task_context.update_state(
                state="PROGRESS",
                meta={"execution_id": str(execution_id), "status": "starting", "progress": 0}
            )
        
        # Get graph from database
        graph = db.query(Graph).filter(Graph.id == UUID(graph_id)).first()
        if not graph:
            raise ValueError(f"Graph {graph_id} not found")
        
        # Translate graph to CrewAI objects
        translation_service = GraphTranslationService(db)
        crew = translation_service.translate_graph(graph)
        
        logger.info(f"Translated graph to crew")
        
        # Update progress
        if hasattr(task_context, 'update_state'):
            task_context.update_state(
                state="PROGRESS",
                meta={"execution_id": str(execution_id), "status": "executing", "progress": 25}
            )
        
        # Execute the crew
        logger.info(f"Executing crew for graph {graph_id}")
        result = crew.kickoff(inputs=inputs)
        
        # Process result
        if hasattr(result, 'raw'):
            output = result.raw
        else:
            output = str(result)
        
        # Update execution with success
        execution_log.complete_execution({"result": output})
        db.commit()
        
        logger.info(f"Completed crew execution {execution_id}")
        
        # Final progress update
        if hasattr(task_context, 'update_state'):
            task_context.update_state(
                state="SUCCESS",
                meta={"execution_id": str(execution_id), "status": "success", "progress": 100, "result": output}
            )
        
        return {
            "execution_id": str(execution_id),
            "status": "success",
            "result": output,
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        error_msg = str(exc)
        error_traceback = traceback.format_exc()
        
        logger.error(f"Crew execution failed: {error_msg}")
        
        # Handle error with enhanced error service
        try:
            from services.execution_error_service import ExecutionErrorService
            error_service = ExecutionErrorService(db)
            
            # Get current attempt number
            current_attempt = 1
            if hasattr(task_context, 'request') and hasattr(task_context.request, 'retries'):
                current_attempt = task_context.request.retries + 1
            
            # Handle the error  
            if execution_id is not None:
                error_result = error_service.handle_execution_error(
                    UUID(str(execution_id)),
                    exc,
                    current_attempt
                )
            else:
                # Can't handle error without execution_id
                raise exc
            
            # Retry logic based on error service recommendation
            if (error_result.get("should_retry", False) and 
                hasattr(task_context, 'request') and hasattr(task_context, 'retry') and hasattr(task_context, 'max_retries')):
                
                retry_delay = error_result.get("retry_delay", 60)
                logger.info(f"Retrying task {task_context.request.id} in {retry_delay} seconds")
                raise task_context.retry(exc=exc, countdown=retry_delay)
            
            error_service.close()
            
        except ImportError:
            # Fallback to original error handling if error service not available
            if db is not None and execution_id is not None:
                try:
                    execution_log = db.query(Execution).filter(Execution.id == execution_id).first()
                    if execution_log:
                        execution_log.fail_execution(error_msg, {"traceback": error_traceback})
                        db.commit()
                except Exception as db_error:
                    logger.error(f"Failed to update execution log: {db_error}")
            
            # Original retry logic
            if hasattr(task_context, 'request') and hasattr(task_context, 'retry') and hasattr(task_context, 'max_retries'):
                if task_context.request.retries < task_context.max_retries:
                    logger.info(f"Retrying task {task_context.request.id} (attempt {task_context.request.retries + 1})")
                    raise task_context.retry(exc=exc, countdown=60)
        
        return {
            "execution_id": str(execution_id) if execution_id is not None else None,
            "status": "failed",
            "error": error_msg
        }
    
    finally:
        if db:
            db.close()


def execute_crew_async(
    self,
    graph_id: str,
    thread_id: str,
    user_id: str,
    inputs: Dict[str, Any]
) -> Dict[str, Any]:
    """Async task to execute a CrewAI crew."""
    return _execute_crew_logic(self, graph_id, thread_id, user_id, inputs)


def cleanup_execution(execution_id: str) -> Dict[str, Any]:
    """Cleanup task for completed executions."""
    db = None
    try:
        db = SessionLocal()
        
        execution_log = db.query(Execution).filter(Execution.id == UUID(execution_id)).first()
        
        if execution_log:
            logger.info(f"Cleaned up execution {execution_id}")
            return {"status": "cleaned", "execution_id": execution_id}
        else:
            logger.warning(f"Execution {execution_id} not found for cleanup")
            return {"status": "not_found", "execution_id": execution_id}
            
    except Exception as exc:
        logger.error(f"Cleanup failed for execution {execution_id}: {exc}")
        return {"status": "failed", "execution_id": execution_id, "error": str(exc)}
    
    finally:
        if db:
            db.close()


# Register Celery tasks if Celery is available
if CELERY_AVAILABLE and celery_app is not None:
    execute_crew_async = celery_app.task(bind=True, max_retries=3, default_retry_delay=60, name='services.async_execution_service.execute_crew_async')(execute_crew_async)
    cleanup_execution = celery_app.task(name='services.async_execution_service.cleanup_execution')(cleanup_execution) 