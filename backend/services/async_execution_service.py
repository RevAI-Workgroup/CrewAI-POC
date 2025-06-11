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
except ImportError:
    # Fallback for development without Celery installed
    def get_task_logger(name): 
        import logging
        return logging.getLogger(name)
    current_task = None

from sqlalchemy.orm import Session

from celery_app import celery_app
from models.execution import Execution, ExecutionStatus
from models.graph import Graph
from services.graph_translation import GraphTranslationService
from db_config import SessionLocal

logger = get_task_logger(__name__)


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
        try:
            celery_app.control.revoke(task_id, terminate=True)
            logger.info(f"Cancelled task {task_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {e}")
            return False


try:
    @celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
    def execute_crew_async(
        self,
        graph_id: str,
        thread_id: str,
        user_id: str,
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Async task to execute a CrewAI crew."""
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
                execution_config={"inputs": inputs, "task_id": self.request.id}
            )
            execution_log.start_execution()
            db.add(execution_log)
            db.commit()
            execution_id = execution_log.id
            
            logger.info(f"Starting crew execution {execution_id} for graph {graph_id}")
            
            # Update task progress
            if hasattr(self, 'update_state'):
                self.update_state(
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
            if hasattr(self, 'update_state'):
                self.update_state(
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
            if hasattr(self, 'update_state'):
                self.update_state(
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
            
            # Update execution with failure
            if db and execution_id:
                try:
                    execution_log = db.query(Execution).filter(Execution.id == execution_id).first()
                    if execution_log:
                        execution_log.fail_execution(error_msg, {"traceback": error_traceback})
                        db.commit()
                except Exception as db_error:
                    logger.error(f"Failed to update execution log: {db_error}")
            
            # Retry logic
            if hasattr(self, 'request') and hasattr(self, 'retry') and self.request.retries < self.max_retries:
                logger.info(f"Retrying task {self.request.id} (attempt {self.request.retries + 1})")
                raise self.retry(exc=exc, countdown=60)
            
            return {
                "execution_id": str(execution_id) if execution_id else None,
                "status": "failed",
                "error": error_msg
            }
        
        finally:
            if db:
                db.close()

except NameError:
    # Celery not available - create placeholder function
    def execute_crew_async(graph_id: str, thread_id: str, user_id: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Placeholder for when Celery is not available."""
        return {"status": "error", "error": "Celery not available"}


try:
    @celery_app.task
    def cleanup_execution(execution_id: str) -> Dict[str, Any]:
        """Cleanup task for completed executions."""
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

except NameError:
    # Celery not available - create placeholder function
    def cleanup_execution(execution_id: str) -> Dict[str, Any]:
        """Placeholder for when Celery is not available."""
        return {"status": "error", "error": "Celery not available"} 