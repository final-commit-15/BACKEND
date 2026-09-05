import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from ..utils.logging import get_logger


logger = get_logger("request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests with timing and metadata."""
    
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Add request ID to state for use in route handlers
        request.state.request_id = request_id
        
        # Log request
        logger.info(
            "request_started",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params),
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                "request_completed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round(process_time * 1000, 2),
            )
            
            # Add headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{process_time:.4f}"
            
            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                "request_failed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                duration_ms=round(process_time * 1000, 2),
                error=str(e),
                exc_info=True,
            )
            raise


def add_request_logging_middleware(app):
    """Add request logging middleware to the app."""
    app.add_middleware(RequestLoggingMiddleware)