from rest_framework.routers import DefaultRouter
from .views import AdminRecordViewSet

router = DefaultRouter()
router.register(r"admin/record", AdminRecordViewSet, basename="admin-record")

urlpatterns = router.urls
