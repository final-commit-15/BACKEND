from fastapi import Request, status
from fastapi.responses import JSONResponse
from ..utils.exceptions import AgentForgeException

async def agentforge_exception_handler(request: Request, exc: AgentForgeException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": {"code": exc.code, "message": exc.message}}
    )

def register_exception_handlers(app):
    from ..utils.exceptions import AgentForgeException
    app.add_exception_handler(AgentForgeException, agentforge_exception_handler)