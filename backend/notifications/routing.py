from django.urls import re_path
from .consumers import ScrapeProgressConsumer

websocket_urlpatterns = [
    re_path(r'^ws/progress/(?P<task_id>[\w-]+)/$', ScrapeProgressConsumer.as_asgi()),
]