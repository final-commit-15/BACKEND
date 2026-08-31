import structlog
import logging
import sys
from typing import Any, Dict
from ..config.settings import settings


def setup_logging() -> None:
    """Configure structured logging with sensitive field masking."""
    
    sensitive_fields = set(settings.log_sensitive_fields_list)
    
    def mask_sensitive_data(logger, method_name, event_dict):
        """Mask sensitive fields in log output."""
        for key in list(event_dict.keys()):
            if any(sensitive in key.lower() for sensitive in sensitive_fields):
                event_dict[key] = "***MASKED***"
        return event_dict
    
    def add_log_level(logger, method_name, event_dict):
        """Add log level to event dict."""
        event_dict["level"] = method_name.upper()
        return event_dict
    
    def add_timestamp(logger, method_name, event_dict):
        """Add timestamp to event dict."""
        import datetime
        event_dict["timestamp"] = datetime.datetime.utcnow().isoformat() + "Z"
        return event_dict
    
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        add_log_level,
        add_timestamp,
        structlog.processors.add_logger_name,
        mask_sensitive_data,
        structlog.processors.format_exc_info,
    ]
    
    if settings.STRUCTURED_LOGGING:
        processors = shared_processors + [
            structlog.processors.JSONRenderer()
        ]
    else:
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer()
        ]
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.LOG_LEVEL)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL),
    )
    
    # Set specific loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


class AuditLogger:
    """Audit logger for sensitive actions."""
    
    def __init__(self):
        self.logger = get_logger("audit")
    
    def log(
        self,
        action: str,
        user_id: str,
        resource_type: str,
        resource_id: str = None,
        ip_address: str = None,
        details: Dict[str, Any] = None,
        success: bool = True,
    ) -> None:
        """Log an audit event."""
        self.logger.info(
            "audit_event",
            action=action,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            details=details or {},
            success=success,
        )
    
    def log_auth(self, action: str, user_id: str, ip_address: str, success: bool, details: Dict = None):
        """Log authentication events."""
        self.log(
            action=f"auth.{action}",
            user_id=user_id,
            resource_type="authentication",
            ip_address=ip_address,
            details=details,
            success=success,
        )
    
    def log_permission(self, action: str, user_id: str, resource_type: str, resource_id: str, ip_address: str, success: bool):
        """Log permission/authorization events."""
        self.log(
            action=f"permission.{action}",
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            success=success,
        )


audit_logger = AuditLogger()