from django.urls import path
from .views import health, breakfast_window_status

urlpatterns = [
    path("health/", health),
    path("breakfast-window/", breakfast_window_status),
]
