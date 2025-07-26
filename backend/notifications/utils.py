from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def send_task_progress(task_id, step, progress_percent, message, data=None):
    """
    Broadcasts real-time progress to any WebSocket client listening on 'progress_<task_id>'.
    """
    channel_layer = get_channel_layer()
    room_group_name = f"progress_{task_id}"

    payload = {
        'type': 'task_progress',
        'data': {
            'task_id': task_id,
            'step': step,
            'progress': progress_percent,
            'message': message,
            'data': data or {}
        }
    }

    async_to_sync(channel_layer.group_send)(room_group_name, payload)