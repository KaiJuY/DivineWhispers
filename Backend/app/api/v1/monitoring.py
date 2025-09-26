"""
System Monitoring API endpoints
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.deps import get_current_admin_user
from app.core.database import get_database_session
from app.models.user import User
from app.services.task_queue_service import task_queue_service
from app.services.poem_service import poem_service
from app.utils.timeout_utils import (
    rag_circuit_breaker, llm_circuit_breaker, chromadb_circuit_breaker
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitoring", tags=["System Monitoring"])


# Database dependency
async def get_db_session():
    """Database session dependency for this module"""
    async for session in get_database_session():
        yield session


@router.get("/dashboard")
async def get_monitoring_dashboard(
    hours: int = 24,
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get comprehensive monitoring dashboard data (admin only)
    """
    try:
        logger.info(f"Admin {admin_user.user_id} requested monitoring dashboard")

        # Get service metrics
        service_metrics = task_queue_service.get_service_metrics()

        # Get task statistics
        task_statistics = await task_queue_service.get_task_statistics(db, hours)

        # Get circuit breaker status
        circuit_breaker_status = {
            "rag_circuit_breaker": {
                "state": rag_circuit_breaker.state,
                "failure_count": rag_circuit_breaker.failure_count,
                "last_failure": rag_circuit_breaker.last_failure_time.isoformat() if rag_circuit_breaker.last_failure_time else None
            },
            "llm_circuit_breaker": {
                "state": llm_circuit_breaker.state,
                "failure_count": llm_circuit_breaker.failure_count,
                "last_failure": llm_circuit_breaker.last_failure_time.isoformat() if llm_circuit_breaker.last_failure_time else None
            },
            "chromadb_circuit_breaker": {
                "state": chromadb_circuit_breaker.state,
                "failure_count": chromadb_circuit_breaker.failure_count,
                "last_failure": chromadb_circuit_breaker.last_failure_time.isoformat() if chromadb_circuit_breaker.last_failure_time else None
            }
        }

        # Get report quality metrics (new)
        report_quality_metrics = await get_report_quality_metrics(db, hours)

        dashboard_data = {
            "monitoring_period_hours": hours,
            "generated_at": datetime.now().isoformat(),
            "service_metrics": service_metrics,
            "task_statistics": task_statistics,
            "circuit_breakers": circuit_breaker_status,
            "report_quality": report_quality_metrics,
            "system_health": {
                "overall_health": "healthy" if task_statistics.get('success_rate', 0) > 90 else "degraded",
                "critical_issues": [],
                "warnings": []
            }
        }

        # Add warnings based on metrics
        if task_statistics.get('success_rate', 0) < 95:
            dashboard_data["system_health"]["warnings"].append(f"Success rate below 95%: {task_statistics.get('success_rate', 0)}%")

        if report_quality_metrics.get('invalid_reports_count', 0) > 0:
            dashboard_data["system_health"]["warnings"].append(f"Invalid reports detected: {report_quality_metrics.get('invalid_reports_count', 0)}")

        return dashboard_data

    except Exception as e:
        logger.error(f"Error generating monitoring dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def get_report_quality_metrics(db: AsyncSession, hours: int = 24) -> Dict[str, Any]:
    """Get report quality and validation metrics from logs and database."""
    try:
        from sqlalchemy import select, func, text
        from app.models.chat_task import ChatTask, TaskStatus

        cutoff_time = datetime.now() - timedelta(hours=hours)

        # Get basic report generation stats
        result = await db.execute(
            select(
                func.count(ChatTask.task_id).label('total_reports'),
                func.count().filter(ChatTask.status == TaskStatus.COMPLETED).label('completed_reports'),
                func.count().filter(ChatTask.status == TaskStatus.FAILED).label('failed_reports'),
                func.avg(ChatTask.processing_time_ms).label('avg_processing_time')
            ).where(ChatTask.created_at >= cutoff_time)
        )

        stats = result.first()

        # Calculate derived metrics
        total_reports = stats.total_reports or 0
        completed_reports = stats.completed_reports or 0
        failed_reports = stats.failed_reports or 0

        success_rate = (completed_reports / max(1, total_reports)) * 100
        failure_rate = (failed_reports / max(1, total_reports)) * 100

        # Get error patterns from recent failed tasks
        error_query = select(
            func.substring(ChatTask.error_message, 1, 100).label('error_pattern'),
            func.count(ChatTask.task_id).label('error_count')
        ).where(
            ChatTask.status == TaskStatus.FAILED,
            ChatTask.created_at >= cutoff_time,
            ChatTask.error_message.isnot(None)
        ).group_by(
            func.substring(ChatTask.error_message, 1, 100)
        ).limit(10)

        error_result = await db.execute(error_query)
        error_patterns = [{
            'pattern': row.error_pattern,
            'count': row.error_count
        } for row in error_result]

        # Count validation-related errors
        validation_errors = 0
        for pattern in error_patterns:
            if 'validation' in pattern['pattern'].lower() or 'empty' in pattern['pattern'].lower():
                validation_errors += pattern['count']

        return {
            'period_hours': hours,
            'total_reports_generated': total_reports,
            'completed_reports': completed_reports,
            'failed_reports': failed_reports,
            'success_rate': round(success_rate, 2),
            'failure_rate': round(failure_rate, 2),
            'avg_processing_time_ms': round(stats.avg_processing_time or 0, 2),
            'validation_related_failures': validation_errors,
            'invalid_reports_count': validation_errors,  # For backwards compatibility
            'error_patterns': error_patterns,
            'quality_score': max(0, 100 - (failure_rate * 2) - (validation_errors / max(1, total_reports) * 100)),
            'generated_at': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting report quality metrics: {e}")
        return {
            'error': str(e),
            'period_hours': hours,
            'generated_at': datetime.now().isoformat()
        }


@router.get("/report-quality")
async def get_report_quality_dashboard(
    hours: int = 24,
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get detailed report quality metrics (admin only)"""
    try:
        logger.info(f"Admin {admin_user.user_id} requested report quality dashboard")
        return await get_report_quality_metrics(db, hours)

    except Exception as e:
        logger.error(f"Error generating report quality dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/circuit-breakers")
async def get_circuit_breaker_status(
    admin_user: User = Depends(get_current_admin_user)
):
    """
    Get detailed circuit breaker status (admin only)
    """
    try:
        circuit_breakers = get_circuit_breaker_status()

        # Add detailed analysis
        analysis = {
            "total_breakers": len(circuit_breakers),
            "open_breakers": len([cb for cb in circuit_breakers.values() if cb["state"] == "OPEN"]),
            "half_open_breakers": len([cb for cb in circuit_breakers.values() if cb["state"] == "HALF_OPEN"]),
            "closed_breakers": len([cb for cb in circuit_breakers.values() if cb["state"] == "CLOSED"]),
            "overall_health": "healthy" if all(cb["state"] != "OPEN" for cb in circuit_breakers.values()) else "degraded"
        }

        return {
            "circuit_breakers": circuit_breakers,
            "analysis": analysis,
            "generated_at": datetime.now().isoformat(),
            "admin_user": admin_user.username
        }

    except Exception as e:
        logger.error(f"Error getting circuit breaker status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get circuit breaker status")


@router.post("/circuit-breakers/{breaker_name}/reset")
async def reset_circuit_breaker(
    breaker_name: str,
    admin_user: User = Depends(get_current_admin_user)
):
    """
    Reset a specific circuit breaker (admin only)
    """
    try:
        breaker_map = {
            "rag": rag_circuit_breaker,
            "llm": llm_circuit_breaker,
            "chromadb": chromadb_circuit_breaker
        }

        if breaker_name not in breaker_map:
            raise HTTPException(
                status_code=404,
                detail=f"Circuit breaker '{breaker_name}' not found. Available: {list(breaker_map.keys())}"
            )

        breaker = breaker_map[breaker_name]
        old_state = breaker.state
        old_failures = breaker.failure_count

        # Reset the circuit breaker
        breaker.failure_count = 0
        breaker.state = "CLOSED"
        breaker.last_failure_time = None

        logger.info(f"Admin {admin_user.username} reset circuit breaker '{breaker_name}' "
                   f"(was {old_state} with {old_failures} failures)")

        return {
            "success": True,
            "message": f"Circuit breaker '{breaker_name}' has been reset",
            "previous_state": old_state,
            "previous_failure_count": old_failures,
            "new_state": breaker.state,
            "reset_by": admin_user.username,
            "reset_at": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting circuit breaker {breaker_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset circuit breaker")


@router.get("/worker-pool")
async def get_worker_pool_details(
    admin_user: User = Depends(get_current_admin_user)
):
    """
    Get detailed worker pool information (admin only)
    """
    try:
        metrics = task_queue_service.worker_pool.get_metrics()

        # Add recommendations based on metrics
        recommendations = []
        pool_status = metrics['pool_status']
        performance = metrics['performance']

        # Check if workers are overloaded
        if pool_status['active_workers'] >= pool_status['max_workers'] * 0.8:
            recommendations.append("Consider increasing max_workers - pool is near capacity")

        # Check success rate
        if performance['success_rate'] < 90:
            recommendations.append(f"Low success rate ({performance['success_rate']:.1f}%) - investigate task failures")

        # Check for stuck workers
        stuck_workers = []
        for worker in metrics['workers']:
            if worker['status'] == 'busy' and worker['current_task_id']:
                stuck_workers.append(worker['worker_id'])

        if stuck_workers:
            recommendations.append(f"Workers may be stuck: {', '.join(stuck_workers)}")

        return {
            "worker_pool_metrics": metrics,
            "recommendations": recommendations,
            "generated_at": datetime.now().isoformat(),
            "admin_user": admin_user.username
        }

    except Exception as e:
        logger.error(f"Error getting worker pool details: {e}")
        raise HTTPException(status_code=500, detail="Failed to get worker pool details")


@router.get("/alerts")
async def get_system_alerts(
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get system alerts and warnings (admin only)
    """
    try:
        alerts = []
        warnings = []

        # Check circuit breakers
        circuit_breakers = get_circuit_breaker_status()
        for name, cb in circuit_breakers.items():
            if cb["state"] == "OPEN":
                alerts.append({
                    "type": "circuit_breaker_open",
                    "severity": "high",
                    "message": f"Circuit breaker '{name}' is OPEN ({cb['failure_count']} failures)",
                    "component": name
                })
            elif cb["failure_count"] > cb["failure_threshold"] * 0.7:
                warnings.append({
                    "type": "circuit_breaker_degraded",
                    "severity": "medium",
                    "message": f"Circuit breaker '{name}' has {cb['failure_count']} failures (threshold: {cb['failure_threshold']})",
                    "component": name
                })

        # Check worker pool health
        pool_metrics = task_queue_service.worker_pool.get_metrics()
        error_workers = pool_metrics['pool_status']['error_workers']
        if error_workers > 0:
            alerts.append({
                "type": "worker_errors",
                "severity": "medium",
                "message": f"{error_workers} workers are in error state",
                "component": "worker_pool"
            })

        # Check task queue backlog
        queue_size = pool_metrics['queue_status']['queue_size']
        if queue_size > 10:
            warnings.append({
                "type": "queue_backlog",
                "severity": "medium",
                "message": f"Task queue has {queue_size} pending tasks",
                "component": "task_queue"
            })

        # Check poem service health
        poem_health = await poem_service.health_check()
        if poem_health.chroma_db_status != "healthy":
            alerts.append({
                "type": "chroma_db_unhealthy",
                "severity": "high",
                "message": f"ChromaDB status: {poem_health.chroma_db_status}",
                "component": "chroma_db"
            })

        # Check recent task failure rate
        task_stats = await task_queue_service.get_task_statistics(db, 1)  # Last 1 hour
        if task_stats.get('success_rate', 100) < 80:
            alerts.append({
                "type": "high_failure_rate",
                "severity": "high",
                "message": f"Task success rate is {task_stats['success_rate']:.1f}% in the last hour",
                "component": "task_processing"
            })

        alert_summary = {
            "total_alerts": len(alerts),
            "total_warnings": len(warnings),
            "high_severity": len([a for a in alerts if a["severity"] == "high"]),
            "medium_severity": len([a for a in alerts + warnings if a["severity"] == "medium"]),
            "system_status": "critical" if any(a["severity"] == "high" for a in alerts) else
                           "warning" if warnings or alerts else "healthy"
        }

        return {
            "alert_summary": alert_summary,
            "alerts": alerts,
            "warnings": warnings,
            "generated_at": datetime.now().isoformat(),
            "admin_user": admin_user.username
        }

    except Exception as e:
        logger.error(f"Error getting system alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system alerts")


def get_circuit_breaker_status() -> Dict[str, Any]:
    """Get status of all circuit breakers"""
    return {
        "rag_circuit_breaker": {
            "state": rag_circuit_breaker.state,
            "failure_count": rag_circuit_breaker.failure_count,
            "failure_threshold": rag_circuit_breaker.failure_threshold,
            "recovery_timeout": rag_circuit_breaker.recovery_timeout,
            "last_failure_time": rag_circuit_breaker.last_failure_time
        },
        "llm_circuit_breaker": {
            "state": llm_circuit_breaker.state,
            "failure_count": llm_circuit_breaker.failure_count,
            "failure_threshold": llm_circuit_breaker.failure_threshold,
            "recovery_timeout": llm_circuit_breaker.recovery_timeout,
            "last_failure_time": llm_circuit_breaker.last_failure_time
        },
        "chromadb_circuit_breaker": {
            "state": chromadb_circuit_breaker.state,
            "failure_count": chromadb_circuit_breaker.failure_count,
            "failure_threshold": chromadb_circuit_breaker.failure_threshold,
            "recovery_timeout": chromadb_circuit_breaker.recovery_timeout,
            "last_failure_time": chromadb_circuit_breaker.last_failure_time
        }
    }


def get_system_info() -> Dict[str, Any]:
    """Get basic system information"""
    import psutil
    import platform
    import sys
    from pathlib import Path

    try:
        # Memory info
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Process info
        process = psutil.Process()
        process_memory = process.memory_info()

        return {
            "platform": {
                "system": platform.system(),
                "python_version": sys.version,
                "architecture": platform.architecture()[0]
            },
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_percent": memory.percent,
                "process_memory_mb": round(process_memory.rss / (1024**2), 2)
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "used_percent": round((disk.used / disk.total) * 100, 1)
            },
            "process": {
                "pid": process.pid,
                "cpu_percent": process.cpu_percent(),
                "num_threads": process.num_threads(),
                "create_time": datetime.fromtimestamp(process.create_time()).isoformat()
            }
        }

    except Exception as e:
        logger.warning(f"Could not get full system info: {e}")
        return {
            "platform": {
                "system": platform.system(),
                "python_version": sys.version.split()[0],
                "architecture": "unknown"
            },
            "error": str(e)
        }