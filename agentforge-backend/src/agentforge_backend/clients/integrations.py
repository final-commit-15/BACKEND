import httpx
from ..config.settings import settings

class IntegrationsClient:
    def __init__(self):
        self.base_url = settings.INTEGRATIONS_SERVICE_URL

    async def trigger(self, integration_id: str, event: dict) -> dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.base_url}/trigger/{integration_id}",
                json=event
            )
            resp.raise_for_status()
            return resp.json()