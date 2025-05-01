import json
from channels.generic.websocket import AsyncWebsocketConsumer

class SalesConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
    
    async def notify_sale(self, event):
        await self.send(text_data=json.dumps({
            'type': 'sales_update',
            'amount': event['amount']
        }))