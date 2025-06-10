from channels.generic.websocket import AsyncWebsocketConsumer
import json
from asgiref.sync import async_to_sync
from celery.result import AsyncResult


class GeminiConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.task_id = self.scope["url_route"]["kwargs"]["task_id"]
        await self.accept()

        # Poll for result every 2 seconds
        await self.check_result()

    async def check_result(self):
        from celery.result import AsyncResult
        import asyncio

        result = AsyncResult(self.task_id)
        while not result.ready():
            await asyncio.sleep(2)
            result = AsyncResult(self.task_id)

        answer = result.get()
        await self.send(json.dumps({"answer": answer}))
        await self.close()
