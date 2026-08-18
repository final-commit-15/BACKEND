import pytest
from sqlalchemy import select
from src.agentforge_backend.models.user import User

@pytest.mark.asyncio
async def test_db_connection(db_session):
    result = await db_session.execute(select(User))
    assert result is not None