import httpx
from ..config.settings import settings


class AgentsClient:
    def __init__(self):
        self.base_url = settings.AGENTS_SERVICE_URL

    async def execute(self, agent_id: str, task_input: dict) -> dict:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.base_url}/execute",
                json={
                    "agent_id": agent_id,
                    "input": task_input,
                },
            )
            resp.raise_for_status()
            return resp.json()