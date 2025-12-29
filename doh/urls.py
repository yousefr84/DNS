from django.urls import path
from .views import DNSQueryView

urlpatterns = [
    path("dns-query", DNSQueryView.as_view(), name="dns-query"),
]
