from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def broadcast_order_event(event_type, payload):
    channel_layer = get_channel_layer()
    if channel_layer:
        async_to_sync(channel_layer.group_send)(
            "orders",
            {
                "type": event_type,
                **payload
            }
        )
