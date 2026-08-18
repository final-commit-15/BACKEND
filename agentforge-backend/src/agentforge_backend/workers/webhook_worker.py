from .celery_app import celery_app
import httpx

@celery_app.task(bind=True, max_retries=3)
def deliver_webhook(self, url: str, payload: dict, secret: str):
    headers = {"X-Webhook-Secret": secret}
    try:
        with httpx.Client() as client:
            resp = client.post(url, json=payload, headers=headers, timeout=10)
            resp.raise_for_status()
    except Exception as e:
        # Retry with exponential backoff
        self.retry(exc=e, countdown=60 * (2 ** self.request.retries))