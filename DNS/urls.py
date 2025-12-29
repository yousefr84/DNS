from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # path("admin/", admin.site.urls),

    # Admin API
    path("", include("records.urls")),

    # DoH API
    path("", include("doh.urls")),
]
