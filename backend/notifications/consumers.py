import json
from channels.generic.websocket import AsyncWebsocketConsumer


class ScrapeProgressConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Extract task_id from the URL path: ws/progress/<task_id>/
        self.task_id = self.scope['url_route']['kwargs']['task_id']
        self.room_group_name = f"progress_{self.task_id}"

        # Join task group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Send initial connection confirmation
        await self.send(text_data=json.dumps({
            'status': 'connected',
            'task_id': self.task_id,
            'message': 'Subscribed to task progress.'
        }))

    async def disconnect(self, close_code):
        # Leave task group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from channel layer group and push to client
    async def task_progress(self, event):
        await self.send(text_data=json.dumps(event['data']))