import httpx
from ..config.settings import settings

class AIServicesClient:
    def __init__(self):
        self.base_url = settings.AI_SERVICES_URL

    async def chat_completion(self, model: str, messages: list, temperature: float = 0.7) -> dict:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.base_url}/v1/chat/completions",
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature
                }
            )
            resp.raise_for_status()
            return resp.json()