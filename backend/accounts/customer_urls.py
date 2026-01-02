from django.urls import path
from .views import CustomerViewSet

customer = CustomerViewSet.as_view

urlpatterns = [
    path("me/", customer({"get": "me"})),
]
