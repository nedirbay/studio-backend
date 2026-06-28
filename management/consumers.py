import json
from channels.generic.websocket import AsyncWebsocketConsumer

class OrderConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = 'orders'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # We don't process messages sent from clients, we only broadcast events to them.
        pass

    # Receive message from room group
    async def order_created(self, event):
        order = event['order']
        await self.send(text_data=json.dumps({
            'type': 'order.created',
            'order': order
        }))

    async def order_updated(self, event):
        order = event['order']
        await self.send(text_data=json.dumps({
            'type': 'order.updated',
            'order': order
        }))

    async def order_deleted(self, event):
        order_id = event['order_id']
        await self.send(text_data=json.dumps({
            'type': 'order.deleted',
            'order_id': order_id
        }))

    async def commerce_order_created(self, event):
        order = event['order']
        await self.send(text_data=json.dumps({
            'type': 'commerce_order.created',
            'order': order
        }))

    async def commerce_order_updated(self, event):
        order = event['order']
        await self.send(text_data=json.dumps({
            'type': 'commerce_order.updated',
            'order': order
        }))

    async def commerce_order_deleted(self, event):
        order_id = event['order_id']
        await self.send(text_data=json.dumps({
            'type': 'commerce_order.deleted',
            'order_id': order_id
        }))

    # Main Order Events
    async def main_order_created(self, event):
        order = event['order']
        await self.send(text_data=json.dumps({
            'type': 'main_order.created',
            'order': order
        }))

    async def main_order_updated(self, event):
        order = event['order']
        await self.send(text_data=json.dumps({
            'type': 'main_order.updated',
            'order': order
        }))

    async def main_order_deleted(self, event):
        order_id = event['order_id']
        await self.send(text_data=json.dumps({
            'type': 'main_order.deleted',
            'order_id': order_id
        }))

    # Message Events
    async def message_created(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
            'type': 'message.created',
            'message': message
        }))

    async def message_updated(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
            'type': 'message.updated',
            'message': message
        }))

    async def message_deleted(self, event):
        message_id = event['message_id']
        await self.send(text_data=json.dumps({
            'type': 'message.deleted',
            'message_id': message_id
        }))

    # Review Events
    async def review_created(self, event):
        review = event['review']
        await self.send(text_data=json.dumps({
            'type': 'review.created',
            'review': review
        }))

    async def review_updated(self, event):
        review = event['review']
        await self.send(text_data=json.dumps({
            'type': 'review.updated',
            'review': review
        }))

    async def review_deleted(self, event):
        review_id = event['review_id']
        await self.send(text_data=json.dumps({
            'type': 'review.deleted',
            'review_id': review_id
        }))
