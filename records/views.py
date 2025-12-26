from rest_framework import viewsets, status
from rest_framework.response import Response

from .models import DNSRecord
from .serializers import DNSRecordSerializer


class AdminRecordViewSet(viewsets.ModelViewSet):
    """
    /admin/record
    """

    queryset = DNSRecord.objects.all().order_by("domain")
    serializer_class = DNSRecordSerializer

    def create(self, request, *args, **kwargs):
        data = request.data.copy()

        if "type" in data:
            data["record_type"] = data.pop("type")

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return Response(
            {
                "status": "success",
                "message": "record added",
                "data": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )

    def destroy(self, request, *args, **kwargs):
        domain = kwargs.get("pk")

        deleted_count, _ = DNSRecord.objects.filter(domain=domain).delete()

        if deleted_count == 0:
            return Response(
                {"status": "error", "message": "record not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {"status": "success", "message": "record deleted"},
            status=status.HTTP_200_OK,
        )
